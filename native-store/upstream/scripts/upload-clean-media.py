"""Stage every approved image in the immutable private cPanel media vault."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import re
import time

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
MAX_BATCH_BYTES = 14900000  # Reserve multipart framing below a 15 MB request.
MAX_BATCH_FILES = 50
MAX_IMAGE_BYTES = 20000000  # Same approved raster bound as the serving runtime.
MAX_REQUEST_BYTES = 20100000  # A larger approved original travels alone, unchanged.
MAX_SINGLE_FILE_REQUESTS = 4
EXTENSIONS = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp", "image/gif": "gif", "image/avif": "avif"}


class UploadError(Exception):
    pass


def deploy_module():
    spec = importlib.util.spec_from_file_location("nodeno_deploy_for_media", ROOT / "scripts/deploy-cpanel.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def digest(body):
    return hashlib.sha256(body).hexdigest()


def prepare_upload(root, release, cleanup):
    """Validate every approval and return all content-addressed image bytes."""
    try:
        metadata = release["manifest"]
        if metadata.get("testOnly", False) is not False or metadata.get("mediaSource") != "approved-only":
            raise UploadError("production_approved_release_required")
        body = release["all_bytes"]["private/media-approved.json"]
        approved = json.loads(body)
        media = json.loads(release["all_bytes"]["private/media.json"])
        if digest(body) != metadata.get("mediaVersion") or approved.get("schema") != 1 or approved.get("policy") != "approved-only-v1" or cleanup.get("schemaVersion") != 1 or cleanup.get("publicationReady") is not True:
            raise UploadError("media_approval_identity_mismatch")
        references = {}
        for product, urls in media.items():
            for index, url in enumerate(urls):
                references[f"{product}:{index}"] = digest(url.encode())
        if approved.get("references") != references or cleanup.get("references") != references or approved.get("referenceCount") != len(references) or metadata.get("mediaApproved") != len(references):
            raise UploadError("media_reference_coverage_mismatch")
        if set(approved.get("images", {})) != set(references.values()) or set(cleanup.get("images", {})) != set(references.values()) or approved.get("uniqueCount") != len(set(references.values())):
            raise UploadError("media_image_coverage_mismatch")
        files = {}
        counts = {"approved_unmodified": 0, "approved_cleaned": 0}
        root = Path(root).resolve()
        for key, entry in approved["images"].items():
            audit = cleanup["images"][key]
            if entry.get("state") not in counts or audit.get("state") != entry["state"]:
                raise UploadError("unapproved_image_blocks_upload")
            counts[entry["state"]] += 1
            for field in ("sourceSha", "outputSha", "mime", "bytes", "width", "height"):
                if audit.get(field) != entry.get(field):
                    raise UploadError("approval_changed_after_build")
            if not re.fullmatch(r"[a-f0-9]{64}", str(entry.get("outputSha", ""))) or entry.get("mime") not in EXTENSIONS:
                raise UploadError("invalid_output_identity")
            if entry["state"] == "approved_unmodified":
                if entry.get("sourceSha") != entry["outputSha"] or entry.get("file") is not None:
                    raise UploadError("invalid_unmodified_approval")
            filename = entry["outputSha"] + "." + EXTENSIONS[entry["mime"]]
            if entry["state"] == "approved_cleaned" and entry.get("file") != filename:
                raise UploadError("invalid_content_addressed_filename")
            relative = audit.get("path")
            allowed = ("artifacts/media-cleaned/",) if entry["state"] == "approved_cleaned" else ("artifacts/media-cleaned/", "artifacts/media-originals/")
            if not isinstance(relative, str) or not relative.startswith(allowed) or "\\" in relative or ".." in relative.split("/"):
                raise UploadError("unsafe_cleaned_artifact_path")
            candidate = root / relative
            if candidate.is_symlink():
                raise UploadError("cleaned_artifact_symlink")
            actual = candidate.resolve()
            source_root = root / "/".join(relative.split("/")[:2])
            if source_root.is_symlink() or not actual.is_relative_to(source_root):
                raise UploadError("cleaned_artifact_outside_vault_source")
            content = actual.read_bytes()
            if len(content) != entry["bytes"] or len(content) > MAX_IMAGE_BYTES or digest(content) != entry["outputSha"]:
                raise UploadError("cleaned_artifact_hash_or_size_mismatch")
            with Image.open(io.BytesIO(content)) as image:
                if image.size != (entry["width"], entry["height"]) or Image.MIME.get(image.format) != entry["mime"]:
                    raise UploadError("cleaned_artifact_raster_metadata_mismatch")
                image.verify()
            if filename in files and files[filename] != content:
                raise UploadError("content_address_collision")
            files[filename] = content
        if approved.get("counts") != counts:
            raise UploadError("approval_count_mismatch")
        return {"release": release, "files": dict(sorted(files.items())), "counts": counts, "referenceCount": len(references), "mediaVersion": metadata["mediaVersion"], "releaseHash": metadata["releaseHash"]}
    except UploadError:
        raise
    except Exception:
        raise UploadError("unreadable_or_invalid_clean_media") from None


def batches(files):
    result, current, size = [], {}, 0
    for filename, body in sorted(files.items()):
        if len(body) > MAX_IMAGE_BYTES:
            raise UploadError("image_exceeds_runtime_size")
        if len(body) > MAX_BATCH_BYTES:
            if current:
                result.append(current)
                current, size = {}, 0
            result.append({filename: body})
            continue
        if current and (len(current) >= MAX_BATCH_FILES or size + len(body) > MAX_BATCH_BYTES):
            result.append(current)
            current, size = {}, 0
        current[filename] = body
        size += len(body)
    if current:
        result.append(current)
    return result


def remaining_files(prepared, backend, deploy):
    home = deploy.listing(backend, deploy.HOME)
    record = home.get("nodeno-media")
    if record is None:
        return prepared["files"], {}
    if record.get("type") != "dir" or record.get("is_link") or record.get("link"):
        raise UploadError("media_vault_symlink_or_collision")
    inventory = deploy.listing(backend, deploy.HOME + "/nodeno-media")
    pending, skipped = {}, {}
    for filename, body in prepared["files"].items():
        entry = inventory.get(filename)
        if entry is None:
            pending[filename] = body
        elif entry.get("type") != "file" or entry.get("is_link") or entry.get("link") or str(entry.get("size")) != str(len(body)):
            raise UploadError("immutable_remote_media_collision")
        else:
            skipped[filename] = len(body)
    return pending, skipped


def make_plan(prepared, backend, deploy, *, single_files=False):
    deploy.make_plan(prepared["release"], backend)  # Verify actual domain, alias, IP and docroot.
    pending, skipped = remaining_files(prepared, backend, deploy)
    return {"mode": "plan", "status": "ready_for_review", "releaseHash": prepared["releaseHash"], "mediaVersion": prepared["mediaVersion"], "mediaRoot": deploy.HOME + "/nodeno-media", "approvedReferences": prepared["referenceCount"], "approvalCounts": prepared["counts"], "hostedUniqueFiles": len(prepared["files"]), "pendingFiles": len(pending), "skippedExistingSizeMatches": len(skipped), "pendingBytes": sum(map(len, pending.values())), "batches": len(batches(pending)), "maxBatchFiles": MAX_BATCH_FILES, "normalBatchBytes": MAX_BATCH_BYTES, "maxImageBytes": MAX_IMAGE_BYTES, "maxRequestBytes": MAX_REQUEST_BYTES, "singleFileRequests": single_files, "maxConcurrentRequests": MAX_SINGLE_FILE_REQUESTS if single_files else 1, "overwriteExisting": False, "remoteDeletions": False, "verification": "remote_size_then_runtime_hash_and_public_body_checks"}


def upload_group(group, backend, deploy, vault, *, single_files=False):
    def send(files):
        content_type, body = deploy.multipart({"dir": vault, "overwrite": "0"}, files)
        if len(body) > MAX_REQUEST_BYTES:
            raise UploadError("multipart_batch_exceeds_limit")
        deploy.successful_upload(backend.post("/execute/Fileman/upload_files", body, content_type))

    if not single_files:
        send(group)
        return
    failed = False
    with ThreadPoolExecutor(max_workers=MAX_SINGLE_FILE_REQUESTS) as executor:
        requests = [executor.submit(send, {name: content}) for name, content in group.items()]
        # Settle every request before inventory reconciliation or any retry.
        for request in as_completed(requests):
            try:
                request.result()
            except Exception:
                failed = True
    if failed:
        raise UploadError("single_file_request_failed")


def apply_upload(prepared, backend, deploy, plan, sleeper=time.sleep, *, single_files=False):
    current = make_plan(prepared, backend, deploy, single_files=single_files)
    if current["releaseHash"] != plan["releaseHash"] or current["mediaVersion"] != plan["mediaVersion"] or current["singleFileRequests"] != plan.get("singleFileRequests", False):
        raise UploadError("media_upload_plan_changed")
    vault = deploy.HOME + "/nodeno-media"
    deploy.ensure_directory(backend, vault, private=True, permissions="0700")
    uploaded = 0
    while True:
        pending, skipped = remaining_files(prepared, backend, deploy)
        if not pending:
            break
        group = batches(pending)[0]
        for attempt in range(3):
            try:
                upload_group(group, backend, deploy, vault, single_files=single_files)
                after, _ = remaining_files(prepared, backend, deploy)
                if any(filename in after for filename in group):
                    raise UploadError("media_batch_size_verification_failed")
                uploaded += len(group)
                deploy.emit("cleaned_media_batch", files=len(group), uploaded=uploaded)
                break
            except Exception:
                after, _ = remaining_files(prepared, backend, deploy)
                group = {name: content for name, content in group.items() if name in after}
                if not group:
                    break  # A completed request may have lost only its response.
                if attempt == 2:
                    raise UploadError("cleaned_media_upload_failed_resume_safe") from None
                sleeper(2 ** attempt)
    deploy.emit("cleaned_media_staged_pending_public_verification", files=len(prepared["files"]), approvedReferences=prepared["referenceCount"], mediaVersion=prepared["mediaVersion"], mediaRoot=vault)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--plan", action="store_true")
    modes.add_argument("--apply", action="store_true")
    parser.add_argument("--single-files", action="store_true", help="Send one file per request, with at most four concurrent HTTPS requests.")
    parser.add_argument("--expect-release")
    args = parser.parse_args()
    deploy = deploy_module()
    release = deploy.load_release(ROOT / "artifacts/cpanel-release")
    prepared = prepare_upload(ROOT, release, json.loads((ROOT / "artifacts/media-cleanup.json").read_bytes()))
    if args.expect_release and args.expect_release != prepared["releaseHash"]:
        raise UploadError("reviewed_release_changed")
    deploy.validate_media_publication(ROOT, release)
    backend = deploy.CpanelBackend(allow_writes=args.apply)
    plan = make_plan(prepared, backend, deploy, single_files=args.single_files)
    print(json.dumps(plan, ensure_ascii=True), flush=True)
    if args.apply:
        apply_upload(prepared, backend, deploy, plan, single_files=args.single_files)


if __name__ == "__main__":
    try:
        main()
    except UploadError as error:
        print(json.dumps({"stage": "stopped", "status": "error", "code": str(error)}))
        raise SystemExit(1)
    except Exception:
        print(json.dumps({"stage": "stopped", "status": "error", "code": "cleaned_media_upload_preparation_failed"}))
        raise SystemExit(1)
