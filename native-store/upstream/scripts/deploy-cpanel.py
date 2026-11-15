"""Verified-TLS cPanel deployment. Default mode is a read-only plan."""
from __future__ import annotations

import argparse
import base64
from contextlib import contextmanager
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import http.client
import importlib.util
import json
import mimetypes
from pathlib import Path, PurePosixPath
import re
import secrets
import ssl
import sys
import urllib.parse

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from lib.blog_publication import validate_blog_publication
HOME = "/home/nodenoho"
PUBLIC = HOME + "/public_html"
DOMAIN = "nodenohome.com.tr"
ALIAS = "nodenohome.com"
IP = "94.199.205.78"
HOST = "srvc77.trwww.com"
PORT = 2083
CRITICAL = ("index.php", ".htaccess")
KNOWN_TEXT = (".htaccess", ".user.ini", "index.php5", "index.php8", "php.ini", "index.php")
PRIVATE_FILES = {"catalog.json", "config.json", "media.json", "index.html", "release.json", "account.php", "media-approved.json", "oauth-jwt.php", "social-auth.php", "social-provider.php", "social-http.php", "collections.php", "seo.php", "control-store.php", "control-auth.php", "control-http.php", "control-catalog.php", "control-operations.php", "control-marketing.php", "control-kolaybi.php", "control-analytics.php", "control-indexnow.php", "wholesale.php", "furniture-sets.php", "visitor-market.php", "geo-v4.bin", "geo-v6.bin", "geo-license.json"}
PUBLIC_EXTENSIONS = {".html", ".js", ".css", ".svg", ".json", ".webmanifest", ".txt", ".woff", ".woff2", ".ttf", ".ico", ".png", ".jpg", ".jpeg", ".webp", ".gif", ".avif"}
OWNER_PRIVATE_FILES={'door-commerce.php','exchange-rates.php','cabinet-fronts.php','door-catalog.json','cabinet-fronts.json'}
SUPPLIER_PRIVATE_FILES={'suppliers.php','supplier-watch.php','supplier-catalog.json','supplier-products.php','supplier-details.json','supplier-details.bin','supplier-media-approved.json'}
PAYMENT_PRIVATE_FILES={'payment-core.php','payment-store.php','payment-stripe.php','payment-admin.php','payments.php'}
PAYMENT_PRIVATE_FILES |= {'localization.php', *{'locale.'+lang+suffix+'.json' for lang in ['de','az','kk','tk','uz','ky','fa'] for suffix in ['','.catalogue']}, 'legal.php','payment-documents.php','membership-legal.php', *{'site-documents.'+lang+'.json' for lang in ['tr','en','ru','ar','de','az','kk','tk','uz','ky','fa']}}
PAYMENT_PRIVATE_FILES |= {'social-campaigns.php','social-engine.php','social-providers.php','social-media.php','social-worker.php','social-admin.php'}
PAYMENT_PRIVATE_FILES |= {'blog-store.php','blog-worker.php','blog-admin.php','blog-http.php','blog.php','blog-i18n.php','blog-admin.html','blog-bank.json','blog-surface.php','date-time.php'}
PAYMENT_PRIVATE_FILES |= {'blog-images.bin','blog-images.json'}
PAYMENT_PRIVATE_FILES |= {'date-time-regions.json'}
PAYMENT_PRIVATE_FILES |= {'search-notifications.php'}
FORBIDDEN_PUBLIC_PARTS = {"private", "cache", "hosting", "data", "lib", "scripts", "tests", "node_modules", "artifacts", "dist", ".git", ".env", "package.json", "package-lock.json", "catalog.json", "config.json", "media.json", "release.json", "nodeno-runtime.php", "social-auth.json"}
PUBLIC_ASSET_MAX_BYTES = 20000000
PUBLIC_BACKUP_MAX_BYTES = 100000000
PUBLIC_HEALTH_MAX_BYTES = 131072


class DeployError(Exception):
    """Controlled codes only; never include remote error bodies or credentials."""


def component(name):
    if not isinstance(name, str) or name in {".", ".."} or not re.fullmatch(r"[A-Za-z0-9_.-]+", name):
        raise DeployError("unsafe_path_component")
    return name


def remote_path(value, private=False):
    if not isinstance(value, str) or "\\" in value or "," in value or not value.startswith(HOME + "/"):
        raise DeployError("unsafe_remote_path")
    if any(part in {"", ".", ".."} for part in value[len(HOME) + 1:].split("/")):
        raise DeployError("unsafe_remote_path")
    for part in value[len(HOME) + 1:].split("/"):
        component(part)
    if private and (value == PUBLIC or value.startswith(PUBLIC + "/")):
        raise DeployError("private_path_inside_public")
    return value


def sha256(body):
    return hashlib.sha256(body).hexdigest()


def public_asset_path(relative):
    if not isinstance(relative, str) or not relative or relative.startswith("/") or "\\" in relative:
        raise DeployError("unsafe_public_asset_path")
    parts = relative.split("/")
    for part in parts:
        component(part)
        if part.startswith(".") or part.lower() in FORBIDDEN_PUBLIC_PARTS:
            raise DeployError("unsafe_public_asset_path")
    if relative in CRITICAL or PurePosixPath(relative).suffix.lower() not in PUBLIC_EXTENSIONS:
        raise DeployError("unsafe_public_asset_path")
    return relative


def load_release(directory):
    directory = Path(directory).resolve()
    try:
        manifest = json.loads((directory / "private/release.json").read_bytes())
        listed = manifest["files"]
        if manifest.get("runtime") != "php" or manifest.get("checkoutEnabled") is not False or not isinstance(listed, dict):
            raise DeployError("invalid_release_contract")
        if manifest.get("testOnly", False) is not False:
            raise DeployError("test_release_not_deployable")
        expected = set(listed) | {"private/release.json"}
        all_bytes = {}
        for entry in directory.rglob("*"):
            if entry.is_symlink():
                raise DeployError("package_symlink_rejected")
            if not entry.is_file():
                continue
            relative = entry.relative_to(directory).as_posix()
            if relative.startswith("private/cache/") and re.fullmatch(r"private/cache/[a-f0-9]{64}\.bin", relative):
                continue  # Runtime cache is never uploaded as a release input.
            if relative not in expected:
                raise DeployError("unexpected_package_file")
            parts = PurePosixPath(relative).parts
            if len(parts) < 2 or any(part in {".", ".."} for part in parts):
                raise DeployError("invalid_package_path")
            for part in parts:
                component(part)
            if parts[0] == "public":
                if any(part.lower() in FORBIDDEN_PUBLIC_PARTS for part in parts[1:]):
                    raise DeployError("forbidden_public_source")
                if relative not in {"public/index.php", "public/.htaccess"} and (any(part.startswith(".") for part in parts) or Path(relative).suffix.lower() not in PUBLIC_EXTENSIONS):
                    raise DeployError("forbidden_public_source")
            elif parts[0] != "private" or len(parts) != 2 or parts[1] not in (PRIVATE_FILES | OWNER_PRIVATE_FILES | SUPPLIER_PRIVATE_FILES | PAYMENT_PRIVATE_FILES):
                raise DeployError("forbidden_private_source")
            all_bytes[relative] = entry.read_bytes()
        if set(all_bytes) != expected or not {"public/index.php", "public/.htaccess", *["private/" + name for name in PRIVATE_FILES]} <= expected:
            raise DeployError("incomplete_release")
        fingerprint = hashlib.sha256()
        for relative in sorted(listed):
            actual = sha256(all_bytes[relative])
            if actual != listed[relative]:
                raise DeployError("package_hash_mismatch")
            fingerprint.update((relative + "\0" + actual + "\0").encode())
        if fingerprint.hexdigest() != manifest.get("releaseHash"):
            raise DeployError("release_fingerprint_mismatch")
        catalog = json.loads(all_bytes["private/catalog.json"])
        config = json.loads(all_bytes["private/config.json"])
        if len(catalog.get("products", [])) != manifest.get("products") or not manifest["products"] or config.get("checkoutEnabled") is not False or config.get("mode") != "catalogue":
            raise DeployError("catalogue_contract_mismatch")
        return {"directory": directory, "manifest": manifest, "all_bytes": all_bytes}
    except DeployError:
        raise
    except Exception:
        raise DeployError("unreadable_release_package") from None


def validate_media_publication(root, release):
    """A previously built package cannot bypass the current image audit."""
    if 'private/blog-bank.json' in release['all_bytes'] and release.get('manifest', {}).get('testOnly'):
        raise DeployError('blog_test_only_rejected')
    try:
        validate_blog_publication(release['all_bytes'])
    except (ValueError, TypeError) as error:
        raise DeployError(str(error) if re.fullmatch(r'[a-z_]+', str(error)) else 'blog_publication_invalid') from None
    catalog = json.loads(release["all_bytes"]["private/catalog.json"])
    validate_supplier_publication(root, release, catalog)
    if any(p.get('productType') in {'door','door-profile','cabinet-front','cabinet-profile'} for p in catalog.get('products', [])):
        if not {"private/"+name for name in OWNER_PRIVATE_FILES} <= set(release['all_bytes']):
            raise DeployError('owner_catalogue_files_missing')
        owner_spec = importlib.util.spec_from_file_location('nodeno_owner_media_gate', ROOT / 'lib/owner_media_gate.py')
        owner_gate = importlib.util.module_from_spec(owner_spec)
        owner_spec.loader.exec_module(owner_gate)
        owner_gate.verify_owner_catalogues(root,release)
    media_version = release["manifest"].get("mediaVersion")
    if not isinstance(media_version, str) or not re.fullmatch(r"[a-f0-9]{64}", media_version) or catalog.get("meta", {}).get("mediaVersion") != media_version:
        raise DeployError("catalog_media_version_must_match_reviewed_release")
    spec = importlib.util.spec_from_file_location("nodeno_media_publication", ROOT / "scripts/finalize-media.py")
    finalizer_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(finalizer_module)
    finalizer = finalizer_module.Finalizer(root)
    finalizer.verify_published()
    approved_body = release["all_bytes"]["private/media-approved.json"]
    approved = json.loads(approved_body)
    cleanup = finalizer.manifest
    if sha256(approved_body) != release["manifest"].get("mediaVersion") or approved.get("references") != cleanup["references"] or set(approved.get("images", {})) != set(cleanup["images"]):
        raise DeployError("release_media_publication_identity_mismatch")
    for key, row in approved["images"].items():
        if any(row.get(field) != cleanup["images"][key].get(field) for field in ("state", "sourceSha", "outputSha", "mime", "bytes", "width", "height")):
            raise DeployError("release_media_not_current_reviewed_output")


def validate_supplier_publication(root, release, catalog=None):
    """New supplier rows retain their separate visual, price and description approvals."""
    catalog = catalog or json.loads(release['all_bytes']['private/catalog.json'])
    products = [p for p in catalog.get('products', []) if p.get('productType') == 'supplier-item']
    if not products:
        return
    projection = json.loads((Path(root) / 'data/supplier-storefront.json').read_bytes())
    if projection.get('publicationReady') is not True or projection.get('testOnly') or projection.get('products') != products:
        raise DeployError('supplier_catalogue_projection_mismatch')
    for proof in projection['review']['files']:
        if sha256((Path(root)/proof['path']).read_bytes()) != proof['sha256']:
            raise DeployError('supplier_review_changed')
    for filename, hash_field in [('supplier-media-approved.json','mediaSha256'),('supplier-details.json','detailIndexSha256'),('supplier-details.bin','detailBlobSha256')]:
        body = release['all_bytes'].get('private/'+filename)
        if body is None or sha256(body) != projection[hash_field]:
            raise DeployError('supplier_private_approval_changed')
    approval = json.loads(release['all_bytes']['private/supplier-media-approved.json'])
    if approval.get('publicationReady') is not True or approval.get('testOnly'):
        raise DeployError('supplier_visual_review_required')
    references = {}
    for product in products:
        for index, url in enumerate(product['images']):
            row = approval['images'].get(url, {})
            if not re.fullmatch(r'/assets/suppliers/[a-f0-9]{64}\.(jpg|png|webp)', url) or row.get('visualReview') is not True or sha256(release['all_bytes'].get('public'+url,b'')) != row.get('outputSha256'):
                raise DeployError('supplier_image_approval_mismatch')
            references[product['id']+':'+str(index)] = url
    if references != approval['references']:
        raise DeployError('supplier_image_references_changed')


def multipart(fields, files):
    for name in fields:
        component(name)
    for filename in files:
        component(filename)
    upload_files = {f"file-{index}": (filename, body, mimetypes.guess_type(filename)[0] or "application/octet-stream") for index, (filename, body) in enumerate(files.items(), 1)}
    # Prepare only: TLS, authentication and transport remain in CpanelBackend.post.
    prepared = requests.Request("POST", "https://invalid.local/", data={name: str(value) for name, value in fields.items()}, files=upload_files).prepare()
    return prepared.headers["Content-Type"], prepared.body


def successful_upload(payload, error_code="cpanel_upload_failed"):
    # upload_files returns a direct UAPI envelope on this cPanel host; other
    # UAPI transports wrap the same envelope in a result property.
    if not isinstance(payload, dict):
        raise DeployError(error_code)
    result = payload.get("result", payload)
    if not isinstance(result, dict) or result.get("status") not in (1, "1") or result.get("errors"):
        raise DeployError(error_code)
    data = result.get("data")
    failed = data.get("failed") if isinstance(data, dict) else None
    if failed not in (None, False, 0, "0", [], {}):
        raise DeployError(error_code)
    return result


def load_probe():
    specification = importlib.util.spec_from_file_location("nodeno_hosting_probe", ROOT / "scripts/hosting-probe.py")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


class CpanelBackend:
    def __init__(self, allow_writes=False):
        self.probe = load_probe()
        self.allow_writes = allow_writes
        self.public_paths = frozenset()

    def read(self, module, function, **params):
        return self.probe.api(module, function, **params)

    def _public_get(self, request_path, maximum):
        # This connection never reads credentials or shares cPanel headers.
        connection = http.client.HTTPSConnection(ALIAS, 443, timeout=45, context=ssl.create_default_context())
        try:
            query = "?nodeno-deploy-check=" + secrets.token_hex(12)
            connection.request("GET", request_path + query, headers={"Accept-Encoding": "identity", "Cache-Control": "no-cache, no-store", "Pragma": "no-cache"})
            response = connection.getresponse()
            length = response.getheader("Content-Length")
            encoding = (response.getheader("Content-Encoding") or "identity").strip().lower()
            if response.status != 200 or encoding != "identity" or (length is not None and (not re.fullmatch(r"[0-9]+", length) or int(length) > maximum)):
                raise DeployError("public_https_read_rejected")
            body = response.read(maximum + 1)
            if len(body) > maximum or (length is not None and len(body) != int(length)):
                raise DeployError("public_https_read_size_mismatch")
            return body
        except DeployError:
            raise
        except Exception:
            raise DeployError("public_https_read_failed") from None
        finally:
            connection.close()

    def public_read(self, relative):
        relative = public_asset_path(relative)
        if relative not in self.public_paths:
            raise DeployError("public_asset_not_in_release")
        return self._public_get("/" + urllib.parse.quote(relative, safe="/"), PUBLIC_ASSET_MAX_BYTES)

    def public_health(self):
        try:
            result = json.loads(self._public_get("/api/health", PUBLIC_HEALTH_MAX_BYTES))
            if not isinstance(result, dict):
                raise DeployError("public_health_invalid")
            return result
        except DeployError:
            raise
        except Exception:
            raise DeployError("public_health_invalid") from None

    def post(self, path, body, content_type):
        if not self.allow_writes:
            raise DeployError("remote_write_not_enabled")
        if b'filename="nodeno-runtime.php"' in body:
            require_deployment_lease(self)
        user, password = self.probe.credentials()
        authorization = base64.b64encode((user + ":" + password).encode()).decode("ascii")
        connection = http.client.HTTPSConnection(HOST, PORT, timeout=90, context=ssl.create_default_context())
        try:
            connection.request("POST", path, body=body, headers={"Authorization": "Basic " + authorization, "Content-Type": content_type, "Accept": "application/json"})
            response = connection.getresponse()
            payload = response.read(16000001)
            if response.status != 200 or len(payload) > 16000000:
                raise DeployError("cpanel_post_rejected")
            return json.loads(payload)
        except DeployError:
            raise
        except Exception:
            raise DeployError("cpanel_post_failed") from None
        finally:
            connection.close()

    def api2(self, function, **params):
        body = urllib.parse.urlencode({"cpanel_jsonapi_apiversion": "2", "cpanel_jsonapi_module": "Fileman", "cpanel_jsonapi_func": function, **params}).encode()
        result = self.post("/json-api/cpanel", body, "application/x-www-form-urlencoded").get("cpanelresult", {})
        if result.get("event", {}).get("result") != 1 or any(row.get("result") == 0 for row in result.get("data", []) if isinstance(row, dict)):
            raise DeployError("cpanel_file_operation_failed")
        return result

    def upload(self, directory, files):
        remote_path(directory)
        for filename in files:
            component(filename)
        # This host can concatenate adjacent file parts; keep one file per request.
        for filename, content in files.items():
            content_type, body = multipart({"dir": directory, "overwrite": "1"}, {filename: content})
            successful_upload(self.post("/execute/Fileman/upload_files", body, content_type))


def listing(backend, directory):
    result = backend.read("Fileman", "list_files", dir=directory, show_hidden=1)
    if result.get("status") != 1 or not isinstance(result.get("data"), list):
        raise DeployError("remote_listing_failed")
    records = {}
    for record in result["data"]:
        name = record.get("file")
        if not isinstance(name, str) or name in {".", ".."} or "/" in name or "\\" in name:
            raise DeployError("invalid_remote_listing")
        records[name] = record
    return records


def text_content(backend, directory, filename):
    result = backend.read("Fileman", "get_file_content", dir=directory, file=component(filename), from_charset="UTF-8", to_charset="UTF-8", update_html_document_encoding=0)
    if result.get("status") != 1 or not isinstance(result.get("data", {}).get("content"), str):
        raise DeployError("remote_original_read_failed")
    return result["data"]["content"].encode("utf-8")


def make_plan(release, backend):
    result = backend.read("DomainInfo", "domains_data", format="hash")
    data = result.get("data", {})
    main = data.get("main_domain", {})
    if result.get("status") != 1 or main.get("domain") != DOMAIN or main.get("documentroot") != PUBLIC or main.get("ip") != IP:
        raise DeployError("live_account_target_mismatch")
    if ALIAS not in data.get("parked_domains", []) or ALIAS not in main.get("serveralias", "").split():
        raise DeployError("shared_alias_missing")
    existing = listing(backend, PUBLIC)
    if any(record.get("type") not in {"file", "dir"} or record.get("is_link") or record.get("link") for record in existing.values()):
        raise DeployError("public_symlink_or_type_rejected")
    fingerprint = release["manifest"]["releaseHash"]
    private = remote_path(HOME + "/nodeno-releases/" + fingerprint + "/private", private=True)
    return {"mode": "plan", "status": "ready_for_review", "host": HOST, "domain": DOMAIN, "alias": ALIAS, "publicRoot": PUBLIC, "privateRoot": private,
            "releaseHash": fingerprint, "products": release["manifest"]["products"], "publicFileCount": sum(name.startswith("public/") for name in release["all_bytes"]),
            "privateFileCount": len(PRIVATE_FILES), "existingPublicEntryCount": len(existing), "existingKnownFiles": [name for name in KNOWN_TEXT if name in existing],
            "stages": ["recheck_live_target", "backup_overwritten_public_bytes", "backup_public_tree_and_runtime_config", "stage_versioned_private", "upload_public_assets", "upload_runtime_pointer", "upload_index_php", "upload_htaccess", "readback_critical_files", "verify_public_https_health"],
            "remoteDeletions": False, "publicVerification": "health_in_apply_browser_acceptance_separate"}


def ensure_directory(backend, directory, private=False, permissions="0755"):
    remote_path(directory, private=private)
    current = HOME
    for name in directory[len(HOME) + 1:].split("/"):
        entries = listing(backend, current)
        if name in entries:
            if entries[name].get("type") != "dir" or entries[name].get("is_link") or entries[name].get("link"):
                raise DeployError("remote_directory_collision")
        else:
            backend.api2("mkdir", path=current, name=name, permissions=permissions)
        current += "/" + name


def emit(stage, status="ok", **safe):
    print(json.dumps({"stage": stage, "status": status, **safe}, ensure_ascii=True), flush=True)


def snapshot_public_assets(release, backend, existing):
    paths = sorted(public_asset_path(name[len("public/"):]) for name in release["all_bytes"] if name.startswith("public/") and name[len("public/"):] not in CRITICAL)
    backend.public_paths = frozenset(paths)
    directories = {PUBLIC: existing}
    originals = {}
    total = 0
    for relative in paths:
        parts = relative.split("/")
        directory = PUBLIC
        absent_parent = False
        for part in parts[:-1]:
            if directory not in directories:
                directories[directory] = listing(backend, directory)
            records = directories[directory]
            record = records.get(part)
            if record is None:
                absent_parent = True
                break
            if record.get("type") != "dir" or record.get("is_link") or record.get("link"):
                raise DeployError("public_asset_parent_not_directory")
            directory += "/" + part
        if absent_parent:
            continue
        if directory not in directories:
            directories[directory] = listing(backend, directory)
        record = directories[directory].get(parts[-1])
        if record is None:
            continue
        if record.get("type") != "file" or record.get("is_link") or record.get("link"):
            raise DeployError("public_asset_target_not_regular")
        size = str(record.get("size", ""))
        if not re.fullmatch(r"[0-9]+", size) or int(size) > PUBLIC_ASSET_MAX_BYTES or total + int(size) > PUBLIC_BACKUP_MAX_BYTES:
            raise DeployError("public_backup_size_limit")
        body = backend.public_read(relative)
        if not isinstance(body, bytes) or len(body) != int(size):
            raise DeployError("public_backup_byte_count_mismatch")
        originals[relative] = body
        total += len(body)
    return originals


@contextmanager
def deployment_lease(backend):
    """Atomic mkdir serializes all repository runtime-pointer writers.

    The directory is never stolen or expired. Rename on release retains a
    protected ownership audit and avoids a recursive delete. Fileman mkdir
    must report a collision as failure, never use ensure_directory here.
    """
    directory = HOME + '/nodeno-deploy-lock'
    backend.api2('mkdir', path=HOME, name='nodeno-deploy-lock', permissions='0700')
    owner = json.dumps({'token': secrets.token_hex(32)}, sort_keys=True).encode()
    backend.upload(directory, {'owner.json': owner})
    if text_content(backend, directory, 'owner.json') != owner:
        raise DeployError('deployment_lease_ownership_failed')
    backend._deployment_lease_owner = owner
    try:
        yield
    finally:
        require_deployment_lease(backend)
        target = 'nodeno-deploy-lock-released-' + sha256(owner)[:24]
        backend.api2('fileop', op='rename', sourcefiles='nodeno-deploy-lock', destfiles=target, doubledecode='0')
        backend._deployment_lease_owner = None


def require_deployment_lease(backend):
    owner = getattr(backend, '_deployment_lease_owner', None)
    if not isinstance(owner, bytes) or text_content(backend, HOME + '/nodeno-deploy-lock', 'owner.json') != owner:
        raise DeployError('active_deployment_lease_required')


def apply_release(release, backend, plan, *, expected_checkout_enabled=False):
    # The private payment configuration is persistent and independent of the
    # static catalogue manifest. Verify the caller's known live state; never edit it.
    if type(expected_checkout_enabled) is not bool:
        raise DeployError('checkout_state_expectation_required')
    fresh = make_plan(release, backend)
    if fresh["releaseHash"] != plan["releaseHash"] or fresh["privateRoot"] != plan["privateRoot"]:
        raise DeployError("deployment_plan_changed")
    existing = listing(backend, PUBLIC)
    home_entries = listing(backend, HOME)
    originals = {name: text_content(backend, PUBLIC, name) for name in KNOWN_TEXT if name in existing}
    asset_originals = snapshot_public_assets(release, backend, existing)
    runtime_name = "nodeno-runtime.php"
    old_runtime = text_content(backend, HOME, runtime_name) if runtime_name in home_entries else None
    backup_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + plan["releaseHash"][:12] + "-" + secrets.token_hex(3)
    backup = remote_path(HOME + "/nodeno-backups/" + backup_id, private=True)
    local_backup = ROOT / "artifacts/hosting-backups" / backup_id
    local_backup.mkdir(parents=True, exist_ok=False)
    for name, body in originals.items():
        (local_backup / name).write_bytes(body)
    for relative, body in asset_originals.items():
        target = local_backup / "public" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(body)
    (local_backup / "public-assets.json").write_text(json.dumps({name: {"bytes": len(body), "sha256": sha256(body)} for name, body in asset_originals.items()}, sort_keys=True), encoding="utf-8")
    if old_runtime is not None:
        (local_backup / runtime_name).write_bytes(old_runtime)
    with deployment_lease(backend):
        locked_home = listing(backend, HOME)
        locked_runtime = text_content(backend, HOME, runtime_name) if runtime_name in locked_home else None
        if locked_runtime != old_runtime or any(text_content(backend, PUBLIC, name) != body for name, body in originals.items()):
            raise DeployError('deployment_base_changed_before_lease')
        ensure_directory(backend, backup, private=True)
        backend.api2("fileop", op="copy", sourcefiles="public_html", destfiles=backup[len(HOME) + 1:], doubledecode="0")
        if old_runtime is not None:
            backend.api2("fileop", op="copy", sourcefiles=runtime_name, destfiles=backup[len(HOME) + 1:], doubledecode="0")
        backed_up = listing(backend, backup + "/public_html")
        if any(name not in backed_up or backed_up[name]["type"] != record["type"] or (record["type"] == "file" and str(backed_up[name].get("size")) != str(record.get("size"))) for name, record in existing.items()):
            raise DeployError("remote_backup_verification_failed")
        emit("backup", backupRoot=backup, localBackup=str(local_backup))
        private = plan["privateRoot"]
        ensure_directory(backend, private, private=True)
        ensure_directory(backend, private + "/cache", private=True)
        # Account data survives release changes and is never overwritten by uploads.
        storage = remote_path(HOME + "/nodeno-data", private=True)
        ensure_directory(backend, storage, private=True, permissions="0700")
        media_root = remote_path(HOME + "/nodeno-media", private=True)
        ensure_directory(backend, media_root, private=True, permissions="0700")
        backend.upload(private, {name: release["all_bytes"]["private/" + name] for name in sorted(PRIVATE_FILES | {n for n in (OWNER_PRIVATE_FILES | SUPPLIER_PRIVATE_FILES | PAYMENT_PRIVATE_FILES) if 'private/'+n in release['all_bytes']})})
        emit("private_staged", releaseHash=plan["releaseHash"])
        changed_public = False
        try:
            # Shared filenames can be requested before the runtime switch. Publish
            # assets and module dependencies before their new application entrypoint.
            root_module_order = {"i18n.js": 1, "shop-i18n.js": 2, "product-specs.js": 3, "shop-core.js": 4, "app.js": 5}
            grouped = defaultdict(dict)
            for relative, body in release["all_bytes"].items():
                if relative.startswith("public/") and relative[len("public/"):] not in CRITICAL:
                    destination = PurePosixPath(relative[len("public/"):])
                    grouped[str(destination.parent)][destination.name] = body
            for relative, files in sorted(grouped.items(), key=lambda item: (item[0] == ".", item[0])):
                if relative == ".":
                    files = dict(sorted(files.items(), key=lambda item: (root_module_order.get(item[0], 0), item[0])))
                destination = PUBLIC if relative == "." else remote_path(PUBLIC + "/" + relative)
                if destination != PUBLIC:
                    ensure_directory(backend, destination)
                changed_public = True
                backend.upload(destination, files)
            emit("public_assets_uploaded")
            pointer = ("<?php\nreturn ['privateRoot' => '" + private + "', 'storageRoot' => '" + storage + "', 'mediaRoot' => '" + media_root + "'];\n").encode()
            # HOME itself is allowed only for this explicitly named protected pointer.
            changed_public = True
            content_type, body = multipart({"dir": HOME, "overwrite": "1"}, {runtime_name: pointer})
            successful_upload(backend.post("/execute/Fileman/upload_files", body, content_type), "runtime_pointer_upload_failed")
            for name in CRITICAL:
                backend.upload(PUBLIC, {name: release["all_bytes"]["public/" + name]})
            for name in CRITICAL:
                if sha256(text_content(backend, PUBLIC, name)) != sha256(release["all_bytes"]["public/" + name]):
                    raise DeployError("critical_readback_mismatch")
            if text_content(backend, HOME, runtime_name) != pointer:
                raise DeployError("runtime_pointer_readback_mismatch")
            health = backend.public_health()
            if health.get("status") != "ok" or health.get("releaseHash") != plan["releaseHash"] or health.get("checkoutEnabled") is not expected_checkout_enabled:
                raise DeployError("public_health_release_mismatch")
            emit("uploaded_verified_health", releaseHash=plan["releaseHash"], backupRoot=backup, browserAcceptance="required")
        except Exception:
            rollback_ok = True
            if changed_public:
                for relative, original in sorted(asset_originals.items()):
                    destination = PurePosixPath(relative)
                    directory = PUBLIC if str(destination.parent) == "." else remote_path(PUBLIC + "/" + str(destination.parent))
                    try:
                        backend.upload(directory, {destination.name: original})
                    except Exception:
                        rollback_ok = False
                try:
                    content_type, body = multipart({"dir": HOME, "overwrite": "1"}, {runtime_name: old_runtime if old_runtime is not None else b"<?php return [];\n"})
                    successful_upload(backend.post("/execute/Fileman/upload_files", body, content_type), "rollback_pointer_failed")
                except Exception:
                    rollback_ok = False
                for name in CRITICAL:
                    original = originals.get(name)
                    if name == "index.php" and original is None:
                        original = originals.get("index.php8") or originals.get("index.php5") or b'<?php http_response_code(503); header("Retry-After: 60"); echo "Site maintenance";'
                    if original is not None:
                        try:
                            backend.upload(PUBLIC, {name: original})
                        except Exception:
                            rollback_ok = False
                # An acknowledgement alone is not proof that old behavior returned.
                # Verify after the old routing and runtime pointer are back in place.
                for relative, original in sorted(asset_originals.items()):
                    try:
                        restored = backend.public_read(relative)
                        if len(restored) != len(original) or sha256(restored) != sha256(original):
                            raise DeployError("rollback_asset_readback_mismatch")
                    except Exception:
                        rollback_ok = False
                expected_pointer = old_runtime if old_runtime is not None else b"<?php return [];\n"
                try:
                    if text_content(backend, HOME, runtime_name) != expected_pointer:
                        raise DeployError("rollback_pointer_readback_mismatch")
                except Exception:
                    rollback_ok = False
                for name in CRITICAL:
                    original = originals.get(name)
                    if name == "index.php" and original is None:
                        original = originals.get("index.php8") or originals.get("index.php5") or b'<?php http_response_code(503); header("Retry-After: 60"); echo "Site maintenance";'
                    if original is not None:
                        try:
                            if text_content(backend, PUBLIC, name) != original:
                                raise DeployError("rollback_entry_readback_mismatch")
                        except Exception:
                            rollback_ok = False
            emit("rollback", "restored_public_files" if rollback_ok else "manual_restore_required", backupRoot=backup)
            raise DeployError("deployment_failed_rollback_completed" if rollback_ok else "deployment_failed_manual_restore_required") from None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--plan", action="store_true", help="read-only remote discovery and local package validation (default)")
    mode.add_argument("--apply", action="store_true", help="upload the reviewed release with backups")
    parser.add_argument("--expect-release", help="require this exact reviewed PHP release hash")
    args = parser.parse_args()
    release = load_release(ROOT / "artifacts/cpanel-release")
    if args.expect_release and args.expect_release != release["manifest"]["releaseHash"]:
        raise DeployError("reviewed_release_changed")
    validate_media_publication(ROOT, release)
    backend = CpanelBackend(allow_writes=args.apply)
    plan = make_plan(release, backend)
    print(json.dumps(plan, ensure_ascii=True), flush=True)
    if args.apply:
        apply_release(release, backend, plan)


if __name__ == "__main__":
    try:
        main()
    except DeployError as error:
        emit("stopped", "error", code=str(error))
        raise SystemExit(1)
    except Exception:
        emit("stopped", "error", code="unexpected_deployment_failure")
        raise SystemExit(1)
