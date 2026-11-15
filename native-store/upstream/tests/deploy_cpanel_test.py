"""Offline deployment safety tests; no hosting calls or credentials."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from contextlib import redirect_stdout
from email.parser import BytesParser
from email import policy
import io
import ssl
import hashlib
import requests

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("deploy_cpanel", ROOT / "scripts/deploy-cpanel.py")
DEPLOY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DEPLOY)


def release_fixture():
    """Self-contained fake-backend payload; never writes a deployable workspace package."""
    files = {
        "public/index.php": b"<?php echo 'new application';",
        "public/.htaccess": b"DirectoryIndex index.php\n",
        "public/app.js": b"import {specifications} from './product-specs.js'; import {product} from './shop-core.js';",
        "public/styles.css": b"#page{display:grid}",
        "public/i18n.js": b"export const locale='new';",
        "public/assets/fonts/NODENOSans-Regular.woff": b"\x00\xff\x80NEW-FONT\x00",
        "public/shop-core.js": b"import {labels} from './shop-i18n.js'; export const product={};",
        "public/product-specs.js": b"import {labels} from './shop-i18n.js'; export const specifications=labels;",
        "public/shop-i18n.js": b"import {locale} from './i18n.js'; export const labels={locale};",
    }
    private = {name: b"{}" for name in DEPLOY.PRIVATE_FILES}
    private["catalog.json"] = json.dumps({"products": [{"id": str(index)} for index in range(667)]}).encode()
    private["config.json"] = b'{"checkoutEnabled":false,"mode":"catalogue"}'
    private["account.php"] = b"<?php // fake account fixture"
    private["index.html"] = b'<main id="page"></main><script src="/app.js"></script>'
    files.update({"private/" + name: body for name, body in private.items() if name != "release.json"})
    hashes = {name: hashlib.sha256(body).hexdigest() for name, body in sorted(files.items())}
    fingerprint = hashlib.sha256()
    for name, sha in hashes.items():
        fingerprint.update((name + "\0" + sha + "\0").encode())
    manifest = {"schema": 1, "runtime": "php", "products": 667, "checkoutEnabled": False, "releaseHash": fingerprint.hexdigest(), "files": hashes}
    files["private/release.json"] = json.dumps(manifest).encode()
    return {"directory": Path("offline-fixture"), "manifest": manifest, "all_bytes": files}


class FakeBackend:
    def __init__(self):
        self.writes = []

    def read(self, module, function, **params):
        if (module, function) == ("DomainInfo", "domains_data"):
            return {"status": 1, "data": {"main_domain": {"domain": DEPLOY.DOMAIN, "documentroot": DEPLOY.PUBLIC, "ip": DEPLOY.IP, "serveralias": "nodenohome.com www.nodenohome.com"}, "parked_domains": ["nodenohome.com"]}}
        if (module, function) == ("Fileman", "list_files"):
            return {"status": 1, "data": []}
        raise AssertionError("Unexpected read")

    def mutate(self, *args, **kwargs):
        self.writes.append((args, kwargs))
        raise AssertionError("Plan attempted a write")


class FakeDeployBackend(FakeBackend):
    def __init__(self, fail_htaccess=False, health=None):
        super().__init__()
        self.directories = {DEPLOY.HOME, DEPLOY.PUBLIC, DEPLOY.PUBLIC + "/assets", DEPLOY.PUBLIC + "/assets/fonts", DEPLOY.PUBLIC + "/.well-known", DEPLOY.PUBLIC + "/.well-known/acme-challenge"}
        self.files = {DEPLOY.PUBLIC + "/.htaccess": b"old rewrite", DEPLOY.PUBLIC + "/.user.ini": b"provider defaults", DEPLOY.PUBLIC + "/index.php8": b"<?php echo 'previous landing';", DEPLOY.PUBLIC + "/.well-known/acme-challenge/example": b"acme-verification"}
        self.files.update({DEPLOY.PUBLIC + "/app.js": b"const hero=document.querySelector('#hero');const catalog='#catalog';", DEPLOY.PUBLIC + "/styles.css": b"#hero{display:block}", DEPLOY.PUBLIC + "/i18n.js": b"export const locale='old';", DEPLOY.PUBLIC + "/assets/fonts/NODENOSans-Regular.woff": b"\x00\xff\x80\r\nOLD-FONT\x00"})
        self.fail_htaccess = fail_htaccess
        self.health = health
        self.public_reads = []
        self.rollback_reads = []

    def public_read(self, relative):
        assert relative in self.public_paths
        (self.rollback_reads if self.writes else self.public_reads).append(relative)
        return self.files[DEPLOY.PUBLIC + "/" + relative]

    def public_health(self):
        self.writes.append(("health",))
        if self.health is not None:
            if isinstance(self.health, Exception):
                raise self.health
            return self.health
        pointer = self.files[DEPLOY.HOME + "/nodeno-runtime.php"].decode()
        private_root = pointer.split("'privateRoot' => '", 1)[1].split("'", 1)[0]
        manifest = json.loads(self.files[private_root + "/release.json"])
        return {"status": "ok", "releaseHash": manifest["releaseHash"], "checkoutEnabled": False}

    def read(self, module, function, **params):
        if module == "DomainInfo":
            return super().read(module, function, **params)
        if function == "get_file_content":
            body = self.files[params["dir"] + "/" + params["file"]]
            return {"status": 1, "data": {"content": body.decode()}}
        directory = params["dir"]
        records = []
        for entry in self.directories:
            if str(Path(entry).parent).replace("\\", "/") == directory:
                records.append({"file": entry.rsplit("/", 1)[1], "type": "dir"})
        for entry, body in self.files.items():
            if entry.rsplit("/", 1)[0] == directory:
                records.append({"file": entry.rsplit("/", 1)[1], "type": "file", "size": str(len(body))})
        # Unrelated cPanel home symlinks must not prevent using our own directories.
        if directory == DEPLOY.HOME:
            records.append({"file": "www", "type": "link", "is_link": True})
        return {"status": 1, "data": records}

    def api2(self, function, **params):
        self.writes.append((function, params))
        if function == "mkdir":
            directory=params["path"] + "/" + params["name"]
            if directory in self.directories:
                raise DEPLOY.DeployError('directory_exists')
            self.directories.add(directory)
        elif params['op']=='rename':
            source=DEPLOY.HOME+'/'+params['sourcefiles'];target=DEPLOY.HOME+'/'+params['destfiles']
            for entry in list(self.directories):
                if entry==source or entry.startswith(source+'/'):
                    self.directories.remove(entry);self.directories.add(target+entry[len(source):])
            for entry in list(self.files):
                if entry==source or entry.startswith(source+'/'):
                    self.files[target+entry[len(source):]]=self.files.pop(entry)
        else:
            assert params["op"] == "copy"
            source = DEPLOY.HOME + "/" + params["sourcefiles"]
            destination = DEPLOY.HOME + "/" + params["destfiles"] + "/" + source.rsplit("/", 1)[1]
            for entry in list(self.directories):
                if entry == source or entry.startswith(source + "/"):
                    self.directories.add(destination + entry[len(source):])
            for entry, body in list(self.files.items()):
                if entry == source or entry.startswith(source + "/"):
                    self.files[destination + entry[len(source):]] = body

    def upload(self, directory, files):
        self.writes.append(("upload", directory, list(files)))
        if self.fail_htaccess and ".htaccess" in files:
            self.fail_htaccess = False
            raise DEPLOY.DeployError("injected_failure")
        for name, body in files.items():
            self.files[directory + "/" + name] = body

    def post(self, path, body, content_type):
        assert path == "/execute/Fileman/upload_files"
        message = BytesParser(policy=policy.default).parsebytes(("Content-Type: " + content_type + "\r\nMIME-Version: 1.0\r\n\r\n").encode() + body)
        directory = None
        files = {}
        for part in message.iter_parts():
            name = part.get_param("name", header="content-disposition")
            filename = part.get_filename()
            if name == "dir":
                directory = part.get_payload(decode=True).decode()
            if filename:
                files[filename] = part.get_payload(decode=True)
        self.upload(directory, files)
        return {"status": 1, "errors": None, "data": {"failed": 0, "succeeded": len(files)}}


class DeploymentSafetyTests(unittest.TestCase):
    def test_explicit_live_checkout_state_is_verified_without_changing_customer_data(self):
        release = release_fixture()
        backend = FakeDeployBackend(health={"status": "ok", "releaseHash": release["manifest"]["releaseHash"], "checkoutEnabled": True})
        data_root = DEPLOY.HOME + "/nodeno-data"
        backend.directories.add(data_root)
        backend.files[data_root + "/accounts.sqlite"] = b"existing payments and encrypted keys"
        plan = DEPLOY.make_plan(release, backend)
        with tempfile.TemporaryDirectory(prefix="nodeno-deploy-test-") as directory, patch.object(DEPLOY, "ROOT", Path(directory)), redirect_stdout(io.StringIO()):
            DEPLOY.apply_release(release, backend, plan, expected_checkout_enabled=True)
        self.assertEqual(backend.files[data_root + "/accounts.sqlite"], b"existing payments and encrypted keys")

    def test_checkout_expectation_must_be_boolean_before_backend_writes(self):
        backend = FakeDeployBackend()
        with self.assertRaises(DEPLOY.DeployError):
            DEPLOY.apply_release(release_fixture(), backend, {}, expected_checkout_enabled=1)
        self.assertFalse(backend.writes)

    def test_remote_paths_cannot_escape_account_or_put_private_data_in_public(self):
        for path in ["/etc/passwd", DEPLOY.HOME, DEPLOY.HOME + "/../other", DEPLOY.PUBLIC + "/private", DEPLOY.HOME + "/public_html/private", DEPLOY.HOME + "/x\\evil", DEPLOY.HOME + "/x,evil"]:
            with self.assertRaises(DEPLOY.DeployError, msg=path):
                DEPLOY.remote_path(path, private=True)
        self.assertEqual(DEPLOY.remote_path(DEPLOY.HOME + "/nodeno-releases/abc/private", private=True), DEPLOY.HOME + "/nodeno-releases/abc/private")

    def test_package_integrity_and_forbidden_files_fail_before_any_backend_call(self):
        release = release_fixture()
        self.assertEqual(release["manifest"]["runtime"], "php")
        self.assertEqual(release["manifest"]["products"], 667)
        with tempfile.TemporaryDirectory(prefix="nodeno-deploy-test-") as directory:
            clone = Path(directory)
            for relative, body in release["all_bytes"].items():
                target = clone / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(body)
            self.assertEqual(DEPLOY.load_release(clone)["manifest"]["releaseHash"], release["manifest"]["releaseHash"])
            (clone / "public/.env").write_text("FORBIDDEN=1")
            with self.assertRaises(DEPLOY.DeployError):
                DEPLOY.load_release(clone)
            (clone / "public/.env").unlink()
            original_manifest = json.loads((clone / "private/release.json").read_bytes())
            (clone / "private/release.json").write_text(json.dumps({**original_manifest, "testOnly": True}))
            with self.assertRaisesRegex(DEPLOY.DeployError, "test_release_not_deployable"):
                DEPLOY.load_release(clone)
            (clone / "private/release.json").write_text(json.dumps(original_manifest))
            (clone / "public/index.php").write_text("modified")
            with self.assertRaises(DEPLOY.DeployError):
                DEPLOY.load_release(clone)

    def test_plan_is_read_only_and_bound_to_live_main_domain_docroot(self):
        backend = FakeBackend()
        release = release_fixture()
        plan = DEPLOY.make_plan(release, backend)
        self.assertEqual(plan["mode"], "plan")
        self.assertEqual(plan["publicRoot"], DEPLOY.PUBLIC)
        self.assertFalse(backend.writes)
        original = backend.read
        def changed(module, function, **params):
            result = original(module, function, **params)
            if module == "DomainInfo":
                result["data"]["main_domain"]["documentroot"] = "/home/another/public_html"
            return result
        backend.read = changed
        with self.assertRaises(DEPLOY.DeployError):
            DEPLOY.make_plan(release, backend)
        self.assertFalse(backend.writes)

    def test_multipart_preserves_arbitrary_binary_bytes_and_rejects_path_filenames(self):
        data = b"\x00\xff\x80\r\nfont\x00"
        content_type, body = DEPLOY.multipart({"dir": DEPLOY.PUBLIC, "overwrite": "1"}, {"font.woff": data})
        self.assertIn("multipart/form-data; boundary=", content_type)
        self.assertIn(data, body)
        self.assertIn(b'name="file-1"; filename="font.woff"', body)
        with self.assertRaises(DEPLOY.DeployError):
            DEPLOY.multipart({"dir": DEPLOY.PUBLIC}, {"../.env": data})

    def test_multipart_uses_standard_boundary_real_mime_and_exact_bytes_without_sending(self):
        files = {"photo.jpg": b"\xff\xd8\x00\xff\x80\r\nphoto\x00\xff\xd9", "picture.png": b"\x89PNG\r\n\x1a\n\x00\xff", "unknown.nodeno_binary": b"\x00\xffopaque\r\n"}
        with patch.object(requests.sessions.Session, "send", side_effect=AssertionError("Preparation must never send a request")):
            content_type, body = DEPLOY.multipart({"dir": DEPLOY.PUBLIC, "overwrite": "1"}, files)
        message = BytesParser(policy=policy.default).parsebytes(("Content-Type: " + content_type + "\r\nMIME-Version: 1.0\r\n\r\n").encode() + body)
        boundary = message.get_boundary()
        self.assertRegex(boundary, r"^[a-f0-9]{32}$")
        self.assertTrue(body.endswith(("--" + boundary + "--\r\n").encode()))
        fields, uploaded, mimes = {}, {}, {}
        for part in message.iter_parts():
            filename = part.get_filename()
            if filename:
                uploaded[filename] = part.get_payload(decode=True)
                mimes[filename] = part.get_content_type()
            else:
                fields[part.get_param("name", header="content-disposition")] = part.get_payload(decode=True).decode()
        self.assertEqual(fields, {"dir": DEPLOY.PUBLIC, "overwrite": "1"})
        self.assertEqual(uploaded, files)
        self.assertEqual(mimes, {"photo.jpg": "image/jpeg", "picture.png": "image/png", "unknown.nodeno_binary": "application/octet-stream"})

    def test_multipart_validates_all_field_and_file_names_before_preparation(self):
        with patch.object(requests, "Request") as prepare:
            for fields, files in [({"dir": DEPLOY.PUBLIC, "invalid\r\nname": "x"}, {"photo.jpg": b"photo"}), ({"dir": DEPLOY.PUBLIC}, {"photo.jpg": b"photo", "../bad.jpg": b"bad"})]:
                with self.assertRaises(DEPLOY.DeployError):
                    DEPLOY.multipart(fields, files)
            prepare.assert_not_called()

    def test_upload_accepts_actual_direct_and_wrapped_envelopes_and_rejects_partial_failure(self):
        success = {"status": 1, "errors": None, "data": {"failed": 0, "succeeded": 1}}
        backend = object.__new__(DEPLOY.CpanelBackend)
        for payload in [success, {"result": success}]:
            backend.post = lambda *args, **kwargs: payload
            backend.upload(DEPLOY.PUBLIC, {"font.woff": b"\x00\xff\x80"})
        for payload in [{"status": 1, "errors": None, "data": {"failed": 1, "succeeded": 0}}, {"status": 0, "errors": ["redacted"]}, {"result": {"status": 1, "data": {"failed": "1"}}}]:
            backend.post = lambda *args, **kwargs: payload
            with self.assertRaises(DEPLOY.DeployError):
                backend.upload(DEPLOY.PUBLIC, {"font.woff": b"\x00\xff\x80"})

    def test_real_upload_sends_each_binary_file_sequentially_in_a_separate_request(self):
        backend = object.__new__(DEPLOY.CpanelBackend)
        files = {"font.woff": b"\x00\xff\x80\r\nfont\x00", "catalog.json": b'{"binary":"\xc4\xb1"}', ".htaccess": b"DirectoryIndex index.php\r\n"}
        captured = []
        success = {"status": 1, "errors": None, "data": {"failed": 0, "succeeded": 1}}
        def post(path, body, content_type):
            self.assertEqual(path, "/execute/Fileman/upload_files")
            message = BytesParser(policy=policy.default).parsebytes(("Content-Type: " + content_type + "\r\nMIME-Version: 1.0\r\n\r\n").encode() + body)
            fields, uploaded = {}, {}
            for part in message.iter_parts():
                filename = part.get_filename()
                if filename:
                    uploaded[filename] = part.get_payload(decode=True)
                else:
                    fields[part.get_param("name", header="content-disposition")] = part.get_payload(decode=True).decode()
            self.assertEqual(fields, {"dir": DEPLOY.PUBLIC, "overwrite": "1"})
            self.assertEqual(len(uploaded), 1)
            captured.extend(uploaded.items())
            return success if len(captured) % 2 else {"result": success}
        backend.post = post
        backend.upload(DEPLOY.PUBLIC, files)
        self.assertEqual(captured, list(files.items()))

    def test_real_upload_validates_every_filename_before_first_request_and_stops_on_failure(self):
        backend = object.__new__(DEPLOY.CpanelBackend)
        captured = []
        success = {"status": 1, "data": {"failed": 0, "succeeded": 1}}
        backend.post = lambda *args: captured.append(args) or success
        with self.assertRaises(DEPLOY.DeployError):
            backend.upload(DEPLOY.PUBLIC, {"valid.js": b"safe", "../invalid.js": b"unsafe"})
        self.assertFalse(captured)
        files = {"first.js": b"first", "second.css": b"second", "third.woff": b"\x00\xff\x80"}
        for failure in [{"status": 0, "errors": ["redacted"]}, {"result": {"status": 1, "data": {"failed": 1}}}]:
            with self.subTest(failure=failure):
                captured.clear()
                def post(path, body, content_type):
                    message = BytesParser(policy=policy.default).parsebytes(("Content-Type: " + content_type + "\r\nMIME-Version: 1.0\r\n\r\n").encode() + body)
                    uploaded = [(part.get_filename(), part.get_payload(decode=True)) for part in message.iter_parts() if part.get_filename()]
                    self.assertEqual(len(uploaded), 1)
                    captured.extend(uploaded)
                    return success if len(captured) == 1 else failure
                backend.post = post
                with self.assertRaises(DEPLOY.DeployError):
                    backend.upload(DEPLOY.PUBLIC, files)
                self.assertEqual(captured, list(files.items())[:2])

    def test_apply_orders_uploads_preserves_provider_and_acme_files_and_stages_private_outside_public(self):
        release = release_fixture()
        backend = FakeDeployBackend()
        data_root = DEPLOY.HOME + "/nodeno-data"
        backend.directories.add(data_root)
        account_database = b"SQLite format 3\x00existing customer records"
        backend.files[data_root + "/accounts.sqlite"] = account_database
        backend.files[data_root + "/accounts.sqlite-wal"] = b"pending transaction bytes"
        plan = DEPLOY.make_plan(release, backend)
        with tempfile.TemporaryDirectory(prefix="nodeno-deploy-test-") as directory, patch.object(DEPLOY, "ROOT", Path(directory)), redirect_stdout(io.StringIO()):
            DEPLOY.apply_release(release, backend, plan)
        self.assertEqual(backend.files[DEPLOY.PUBLIC + "/.user.ini"], b"provider defaults")
        self.assertEqual(backend.files[DEPLOY.PUBLIC + "/.well-known/acme-challenge/example"], b"acme-verification")
        self.assertEqual(backend.files[data_root + "/accounts.sqlite"], account_database)
        self.assertEqual(backend.files[data_root + "/accounts.sqlite-wal"], b"pending transaction bytes")
        self.assertIn(("'storageRoot' => '" + data_root + "'").encode(), backend.files[DEPLOY.HOME + "/nodeno-runtime.php"])
        self.assertIn(("'mediaRoot' => '" + DEPLOY.HOME + "/nodeno-media'").encode(), backend.files[DEPLOY.HOME + "/nodeno-runtime.php"])
        for relative, body in release["all_bytes"].items():
            destination = DEPLOY.PUBLIC + relative[len("public"):] if relative.startswith("public/") else plan["privateRoot"] + relative[len("private"):]
            self.assertEqual(backend.files[destination], body)
        uploads = [entry for entry in backend.writes if entry[0] == "upload"]
        self.assertEqual(uploads[-2][2], ["index.php"])
        self.assertEqual(uploads[-1][2], [".htaccess"])
        self.assertEqual(backend.writes[-2], ("health",))
        self.assertEqual(backend.writes[-1][1]['op'], 'rename')
        self.assertTrue(any(entry[0] == "fileop" and entry[1]["op"] == "copy" for entry in backend.writes))

    def test_apply_publishes_module_dependencies_before_new_app_and_runtime_switch(self):
        for reverse in (False, True):
            with self.subTest(reverse=reverse):
                release = release_fixture()
                release["all_bytes"] = dict(sorted(release["all_bytes"].items(), reverse=reverse))
                backend = FakeDeployBackend()
                self.assertNotIn(DEPLOY.PUBLIC + "/product-specs.js", backend.files)
                plan = DEPLOY.make_plan(release, backend)
                with tempfile.TemporaryDirectory(prefix="nodeno-deploy-test-") as directory, patch.object(DEPLOY, "ROOT", Path(directory)), redirect_stdout(io.StringIO()):
                    DEPLOY.apply_release(release, backend, plan)
                uploads = []
                for entry in backend.writes:
                    if entry[0] == "upload":
                        uploads.extend(entry[1] + "/" + name for name in entry[2])
                public_assets = [path for path in uploads if path.startswith(DEPLOY.PUBLIC + "/") and path.rsplit("/", 1)[-1] not in DEPLOY.CRITICAL]
                position = {path[len(DEPLOY.PUBLIC) + 1:]: index for index, path in enumerate(public_assets)}
                self.assertLess(position["assets/fonts/NODENOSans-Regular.woff"], position["i18n.js"])
                self.assertLess(position["styles.css"], position["i18n.js"])
                self.assertLess(position["i18n.js"], position["shop-i18n.js"])
                self.assertLess(position["shop-i18n.js"], position["product-specs.js"])
                self.assertLess(position["product-specs.js"], position["shop-core.js"])
                self.assertEqual(public_assets[-1], DEPLOY.PUBLIC + "/app.js")
                self.assertLess(uploads.index(DEPLOY.PUBLIC + "/app.js"), uploads.index(DEPLOY.HOME + "/nodeno-runtime.php"))
                first_public_write = next(index for index, entry in enumerate(backend.writes) if entry[0] == "upload" and entry[1].startswith(DEPLOY.PUBLIC))
                backup_writes = [index for index, entry in enumerate(backend.writes) if entry[0] == "fileop" and entry[1]['op']=='copy']
                self.assertTrue(backup_writes)
                self.assertLess(max(backup_writes), first_public_write)

    def test_public_binary_read_has_verified_fixed_tls_no_auth_no_redirects_and_bounds(self):
        requests = []
        response_options = {"status": 200, "body": b"\x00\xff\x80OLD-FONT", "headers": {}}
        class Connection:
            def __init__(self, host, port, timeout, context):
                self_outer.assertEqual((host, port), (DEPLOY.ALIAS, 443))
                self_outer.assertEqual(context.verify_mode, ssl.CERT_REQUIRED)
                self_outer.assertTrue(context.check_hostname)
            def request(self, method, path, headers):
                requests.append((method, path, headers))
                self_outer.assertFalse({"authorization", "cookie", "proxy-authorization"} & {name.lower() for name in headers})
                self_outer.assertEqual(headers["Accept-Encoding"], "identity")
            def getresponse(self):
                return self
            @property
            def status(self):
                return response_options["status"]
            def getheader(self, name):
                if name == "Content-Length":
                    return str(len(response_options["body"]))
                return response_options["headers"].get(name)
            def read(self, maximum):
                return response_options["body"][:maximum]
            def close(self):
                pass
        self_outer = self
        backend = object.__new__(DEPLOY.CpanelBackend)
        backend.public_paths = frozenset({"assets/fonts/NODENOSans-Regular.woff"})
        with patch.object(DEPLOY.http.client, "HTTPSConnection", Connection):
            self.assertEqual(backend.public_read("assets/fonts/NODENOSans-Regular.woff"), response_options["body"])
            self.assertTrue(requests[-1][1].startswith("/assets/fonts/NODENOSans-Regular.woff?"))
            for invalid in ["https://evil.test/a.js", "../app.js", "/app.js", "app.js?url=x", "data/config.json", "index.php", "unlisted.js"]:
                count = len(requests)
                with self.assertRaises(DEPLOY.DeployError):
                    backend.public_read(invalid)
                self.assertEqual(len(requests), count)
            response_options["status"] = 302
            response_options["headers"] = {"Location": "https://evil.test"}
            count = len(requests)
            with self.assertRaises(DEPLOY.DeployError):
                backend.public_read("assets/fonts/NODENOSans-Regular.woff")
            self.assertEqual(len(requests), count + 1)
            response_options["status"] = 200
            response_options["headers"] = {"Content-Encoding": "gzip"}
            with self.assertRaises(DEPLOY.DeployError):
                backend.public_read("assets/fonts/NODENOSans-Regular.woff")
            response_options["headers"] = {}
            with patch.object(DEPLOY, "PUBLIC_ASSET_MAX_BYTES", 2):
                with self.assertRaises(DEPLOY.DeployError):
                    backend.public_read("assets/fonts/NODENOSans-Regular.woff")
            response_options["body"] = b'{"status":"ok","releaseHash":"hash","checkoutEnabled":false}'
            self.assertEqual(backend.public_health()["status"], "ok")
            self.assertTrue(requests[-1][1].startswith("/api/health?"))

    def test_missing_or_invalid_binary_backup_prevents_all_remote_mutations(self):
        release = release_fixture()
        for fault in ["read_error", "wrong_size", "parent_symlink"]:
            with self.subTest(fault=fault):
                backend = FakeDeployBackend()
                plan = DEPLOY.make_plan(release, backend)
                if fault == "read_error":
                    def fail_read(relative):
                        raise DEPLOY.DeployError("simulated_public_failure")
                    backend.public_read = fail_read
                elif fault == "wrong_size":
                    backend.public_read = lambda relative: b""
                else:
                    original = backend.read
                    def unsafe_parent(module, function, **params):
                        result = original(module, function, **params)
                        if function == "list_files" and params.get("dir") == DEPLOY.PUBLIC + "/assets":
                            for record in result["data"]:
                                if record["file"] == "fonts":
                                    record["type"] = "link"
                        return result
                    backend.read = unsafe_parent
                with tempfile.TemporaryDirectory(prefix="nodeno-deploy-test-") as directory, patch.object(DEPLOY, "ROOT", Path(directory)), redirect_stdout(io.StringIO()):
                    with self.assertRaises(DEPLOY.DeployError):
                        DEPLOY.apply_release(release, backend, plan)
                    self.assertFalse((Path(directory) / "artifacts").exists())
                self.assertFalse(backend.writes)

    def test_health_failure_restores_old_html_assets_pointer_and_binary_fonts(self):
        release = release_fixture()
        expected = release["manifest"]["releaseHash"]
        for health in [{"status": "failed", "releaseHash": expected, "checkoutEnabled": False}, {"status": "ok", "releaseHash": "wrong", "checkoutEnabled": False}, {"status": "ok", "releaseHash": expected, "checkoutEnabled": True}, DEPLOY.DeployError("pdo_or_vault_unavailable")]:
            with self.subTest(health_type=type(health).__name__):
                backend = FakeDeployBackend(health=health)
                backend.files[DEPLOY.PUBLIC + "/index.php"] = b"<?php echo '<main id=hero><div id=catalog></div></main>';"
                old_pointer = b"<?php return ['privateRoot'=>'/home/nodenoho/old/private','storageRoot'=>'/home/nodenoho/nodeno-data','mediaRoot'=>'/home/nodenoho/nodeno-media'];"
                backend.files[DEPLOY.HOME + "/nodeno-runtime.php"] = old_pointer
                backend.directories.update({DEPLOY.HOME + "/nodeno-data", DEPLOY.HOME + "/nodeno-media"})
                backend.files[DEPLOY.HOME + "/nodeno-data/accounts.sqlite"] = b"SQLite format 3\x00durable"
                backend.files[DEPLOY.HOME + "/nodeno-media/immutable.webp"] = b"immutable cleaned media"
                before = dict(backend.files)
                plan = DEPLOY.make_plan(release, backend)
                with tempfile.TemporaryDirectory(prefix="nodeno-deploy-test-") as directory, patch.object(DEPLOY, "ROOT", Path(directory)), redirect_stdout(io.StringIO()):
                    with self.assertRaisesRegex(DEPLOY.DeployError, "deployment_failed_rollback_completed"):
                        DEPLOY.apply_release(release, backend, plan)
                    snapshots = list((Path(directory) / "artifacts/hosting-backups").glob("*/public"))
                    self.assertEqual(len(snapshots), 1)
                    for relative in backend.public_reads:
                        self.assertEqual((snapshots[0] / relative).read_bytes(), before[DEPLOY.PUBLIC + "/" + relative])
                for filename, body in before.items():
                    self.assertEqual(backend.files[filename], body, filename)
                health_index = backend.writes.index(("health",))
                rollback = [entry for entry in backend.writes[health_index + 1:] if not(entry[0]=='fileop'and entry[1]['op']=='rename')]
                self.assertEqual(rollback[-3][1:], (DEPLOY.HOME, ["nodeno-runtime.php"]))
                self.assertEqual(rollback[-2][1:], (DEPLOY.PUBLIC, ["index.php"]))
                self.assertEqual(rollback[-1][1:], (DEPLOY.PUBLIC, [".htaccess"]))
                self.assertEqual(len(rollback[:-3]), len(backend.public_reads))
                self.assertEqual(sorted(backend.rollback_reads), sorted(backend.public_reads))

    def test_silently_corrupted_rollback_upload_requires_manual_restore(self):
        release = release_fixture()
        backend = FakeDeployBackend(health=DEPLOY.DeployError("new_runtime_health_failed"))
        old_styles = backend.files[DEPLOY.PUBLIC + "/styles.css"]
        original_upload = backend.upload
        def silently_corrupt(directory, files):
            original_upload(directory, files)
            if ("health",) in backend.writes and directory == DEPLOY.PUBLIC and files.get("styles.css") == old_styles:
                backend.files[DEPLOY.PUBLIC + "/styles.css"] = b"silently corrupted old stylesheet"
        backend.upload = silently_corrupt
        plan = DEPLOY.make_plan(release, backend)
        with tempfile.TemporaryDirectory(prefix="nodeno-deploy-test-") as directory, patch.object(DEPLOY, "ROOT", Path(directory)), redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(DEPLOY.DeployError, "deployment_failed_manual_restore_required"):
                DEPLOY.apply_release(release, backend, plan)
        self.assertEqual(backend.files[DEPLOY.PUBLIC + "/.htaccess"], b"old rewrite")
        self.assertEqual(backend.files[DEPLOY.HOME + "/nodeno-runtime.php"], b"<?php return [];\n")

    def test_unrelated_home_symlink_is_tolerated_but_selected_directory_symlink_is_rejected(self):
        backend = FakeDeployBackend()
        entries = DEPLOY.listing(backend, DEPLOY.HOME)
        self.assertEqual(entries["www"]["type"], "link")
        original = backend.read
        def selected_symlink(module, function, **params):
            result = original(module, function, **params)
            if function == "list_files" and params.get("dir") == DEPLOY.HOME:
                result["data"].append({"file": "nodeno-releases", "type": "link"})
            return result
        backend.read = selected_symlink
        with self.assertRaises(DEPLOY.DeployError):
            DEPLOY.ensure_directory(backend, DEPLOY.HOME + "/nodeno-releases/abc/private", private=True)
        self.assertFalse(backend.writes)

    def test_apply_failure_restores_critical_originals_without_remote_deletion(self):
        release = release_fixture()
        backend = FakeDeployBackend(fail_htaccess=True)
        plan = DEPLOY.make_plan(release, backend)
        with tempfile.TemporaryDirectory(prefix="nodeno-deploy-test-") as directory, patch.object(DEPLOY, "ROOT", Path(directory)), redirect_stdout(io.StringIO()):
            with self.assertRaises(DEPLOY.DeployError):
                DEPLOY.apply_release(release, backend, plan)
        self.assertEqual(backend.files[DEPLOY.PUBLIC + "/.htaccess"], b"old rewrite")
        self.assertEqual(backend.files[DEPLOY.PUBLIC + "/index.php"], b"<?php echo 'previous landing';")
        self.assertEqual(backend.files[DEPLOY.HOME + "/nodeno-runtime.php"], b"<?php return [];\n")
        self.assertFalse(any(entry[0] in {"delete", "remove", "trash"} for entry in backend.writes))


class MediaVersionPreflightTests(unittest.TestCase):
    def test_stale_catalog_image_url_version_is_rejected_before_reading_audit_files(self):
        release={"manifest":{"mediaVersion":"a"*64},"all_bytes":{"private/catalog.json":json.dumps({"meta":{"mediaVersion":"b"*64}}).encode()}}
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(DEPLOY.DeployError, "catalog_media_version"):
                DEPLOY.validate_media_publication(Path(folder),release)


if __name__ == "__main__":
    unittest.main()
