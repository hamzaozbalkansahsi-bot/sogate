"""Publish the reviewed storefront delta while retaining the current live runtime.

The default invocation verifies readiness without remote writes.  --apply is the
only publication switch; it retains the existing checkout and storage settings.
"""
from datetime import datetime, timezone
from pathlib import Path
import argparse
import importlib.util
import json
import re
import secrets
import subprocess
import sys
import time


R = Path(__file__).resolve().parents[1]
E = R / "artifacts/packaging-fix-20261111"
ALLOWED_CHANGED = {
    "private/index.html", "public/app.js", "public/shop-i18n.js",
    "public/styles.css",
}
REQUIRED_CHANGED = {"private/index.html", "public/app.js", "public/shop-i18n.js"}
PUBLIC_ORDER = ("styles.css", "shop-i18n.js", "app.js")


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def emit(stage, **safe):
    print(json.dumps({"stage": stage, **safe}), flush=True)


def read_json(path):
    return json.loads(path.read_bytes())


def artifact_directory(value):
    require(isinstance(value, str) and bool(value), "release_directory_missing")
    directory = (R / value).resolve()
    require(directory.is_relative_to((R / "artifacts").resolve()), "release_directory_outside_artifacts")
    return directory


def log_result(filename, key):
    rows = []
    for line in (E / filename).read_text(encoding="utf-8-sig").splitlines():
        if line.startswith("{"):
            row = json.loads(line)
            if isinstance(row, dict) and key in row:
                rows.append(row)
    require(len(rows) == 1 and rows[0][key] is True, "unsuccessful_" + filename)
    return rows[0]


def verify_test_logs(source):
    node = (E / "node-final.log").read_text(encoding="utf-8-sig")
    counts = {}
    for key in ("tests", "pass", "fail", "cancelled", "skipped", "todo"):
        values = re.findall(r"^(?:\s*\u2139\s+)?" + key + r"\s+(\d+)\s*$", node, flags=re.MULTILINE)
        require(len(values) == 1, "node_test_summary_missing_" + key)
        counts[key] = int(values[0])
    require(counts["tests"] == counts["pass"] >= 361, "node_test_count_incomplete")
    require(all(counts[key] == 0 for key in ("fail", "cancelled", "skipped", "todo")), "node_tests_not_all_successful")
    python = (E / "python-final.log").read_text(encoding="utf-8-sig")
    totals = re.findall(r"^Ran (\d+) tests? in .+$", python, flags=re.MULTILINE)
    require(len(totals) == 1 and int(totals[0]) >= 215, "python_test_count_incomplete")
    require(re.search(r"^OK\s*$", python, flags=re.MULTILINE) is not None, "python_tests_not_successful")
    require(re.search(r"^FAILED\b|^OK \(", python, flags=re.MULTILINE) is None, "python_tests_failed_or_skipped")
    built = log_result("build.log", "built")
    packaged = log_result("production-package.log", "built")
    validated = log_result("validate.log", "valid")
    manifest = source["manifest"]
    require(built.get("sourceComplete") is True, "source_build_incomplete")
    require(built.get("releaseHash") == manifest.get("workerReleaseHash"), "source_build_hash_changed")
    require(packaged.get("runtime") == "php" and packaged.get("releaseHash") == manifest["releaseHash"], "source_package_log_mismatch")
    require(Path(packaged.get("output", "")).resolve() == source["directory"], "source_package_output_mismatch")
    for result in (built, packaged, validated):
        require(result.get("products") == manifest["products"] and result.get("categories") == manifest["categories"], "source_validation_counts_mismatch")
    return {"nodeTests": counts["tests"], "pythonTests": int(totals[0])}


def verify_local_inputs(d):
    proof = read_json(E / "release.json")
    require(proof.get("prepared") is True, "release_not_prepared")
    require(proof.get("catalogueMediaPricesAndCommerceUnchanged") is True and proof.get("checkoutEnabledBefore") is True, "release_preservation_proof_missing")
    base = d.load_release(artifact_directory(proof["base"]))
    release = d.load_release(artifact_directory(proof["release"]))
    source = d.load_release(artifact_directory(proof["sourcePackage"]))
    require(base["manifest"]["releaseHash"] == proof["baseReleaseHash"], "base_proof_hash_changed")
    require(release["manifest"]["releaseHash"] == proof["releaseHash"], "candidate_proof_hash_changed")
    declared = proof.get("changedFiles")
    require(isinstance(declared, list) and all(isinstance(name, str) for name in declared), "changed_files_proof_missing")
    require(len(declared) == len(set(declared)) and REQUIRED_CHANGED <= set(declared) <= ALLOWED_CHANGED, "unapproved_release_delta")
    require(base["all_bytes"].keys() == release["all_bytes"].keys(), "release_file_inventory_changed")
    changed = {name for name, body in release["all_bytes"].items() if body != base["all_bytes"][name]}
    require(changed == set(declared) | {"private/release.json"}, "release_delta_differs_from_review")
    public = {name[7:]: release["all_bytes"][name] for name in declared if name.startswith("public/")}
    for name, body in public.items():
        require(body == source["all_bytes"].get("public/" + name), "public_delta_not_in_verified_source_" + name)
    for field in ("products", "categories", "mediaVersion", "mediaApproved"):
        require(base["manifest"].get(field) == release["manifest"].get(field) == source["manifest"].get(field), "source_catalogue_or_media_mismatch_" + field)
    browser = read_json(E / "browser-local.json")
    require(browser.get("passed") is True and browser.get("releaseHash") == proof["releaseHash"], "exact_candidate_browser_acceptance_missing")
    cases = browser.get("checks", [])
    expected_cases = {("chromium", 1440, "tr"), ("chromium", 390, "en"), ("chromium", 390, "ru"), ("webkit", 390, "ar")}
    require(len(cases) == 4 and {(row.get("engine"), row.get("width"), row.get("locale")) for row in cases} == expected_cases, "browser_cases_incomplete")
    require(all(row.get(flag) is True for row in cases for flag in ("correctHeadingAndFrontProducts", "imagesLoaded", "membershipVersionPreserved", "returnPolicyPreserved", "checkoutReviewAndTotals", "noOverflow", "noRuntimeErrors")), "browser_acceptance_flag_missing")
    counts = verify_test_logs(source)
    emit("local_tests_and_scope_verified", **counts, publicFiles=sorted(public))

    cleanup_file = R / "artifacts/media-cleanup.json"
    cleanup = read_json(cleanup_file)
    audit = read_json(R / "artifacts/measurement-orders/full-media-audit.json")
    require(cleanup.get("publicationReady") is True and cleanup.get("testOnly", False) is False, "media_not_publication_ready")
    require(audit.get("passed") is True and audit.get("sourceReportSha256") == d.sha256(cleanup_file.read_bytes()), "media_audit_not_current")
    require(audit.get("mediaVersion") == release["manifest"]["mediaVersion"], "media_audit_version_changed")
    for name, digest in audit.get("files", {}).items():
        require(d.sha256(release["all_bytes"].get(name, b"")) == digest, "audited_release_media_changed")
    images = cleanup.get("images")
    require(isinstance(images, dict) and bool(images), "media_audit_images_missing")
    emit("verifying_all_original_and_output_media", images=len(images))
    for index, row in enumerate(images.values(), 1):
        for field, digest, folder in (("sourcePath", "sourceSha", "media-originals"), ("path", "outputSha", "media-cleaned")):
            path = R / row[field]
            require(not path.is_symlink() and path.resolve().is_relative_to((R / "artifacts" / folder).resolve()), "media_source_or_output_path_rejected")
            require(d.sha256(path.read_bytes()) == row[digest], "media_source_or_output_hash_changed")
        if index % 500 == 0 or index == len(images):
            emit("media_hash_progress", verified=index, total=len(images))
    catalog = json.loads(release["all_bytes"]["private/catalog.json"])
    d.validate_supplier_publication(R, release, catalog)
    owner_spec = importlib.util.spec_from_file_location("packaging_owner_gate", R / "lib/owner_media_gate.py")
    owner = importlib.util.module_from_spec(owner_spec)
    owner_spec.loader.exec_module(owner)
    owner.verify_owner_catalogues(R, release)
    subprocess.run(["node", str(R / "scripts/verify-current-media.mjs"), str(R), str(release["directory"])], check=True)
    emit("all_current_media_and_supplier_owner_gates_verified")
    return proof, base, release, source, public, counts


def check_health(health, fingerprint, products):
    require(health.get("status") == "ok" and health.get("releaseHash") == fingerprint, "live_release_health_mismatch")
    require(health.get("products") == products, "live_catalogue_count_changed")
    require(health.get("mediaReady") is True, "live_media_not_ready")
    require(health.get("checkoutEnabled") is True, "live_checkout_not_enabled")


def health_readback(backend, fingerprint, products):
    for attempt in range(4):
        health = backend.public_health()
        if health.get("releaseHash") == fingerprint:
            check_health(health, fingerprint, products)
            return health
        if attempt < 3:
            time.sleep(1)
    check_health(health, fingerprint, products)


def verify_public(d, backend, expected, https=True):
    for name, body in expected.items():
        require(d.text_content(backend, d.PUBLIC, name) == body, "public_file_readback_mismatch_" + name)
        if https:
            require(d.sha256(backend.public_read(name)) == d.sha256(body), "public_https_readback_mismatch_" + name)


def pointer_storage_values(body):
    values = {}
    for key in (b"storageRoot", b"mediaRoot"):
        matches = re.findall(rb"['\"]" + key + rb"['\"]\s*=>\s*(['\"])([^'\"]+)\1", body)
        require(len(matches) == 1, "runtime_storage_root_not_unique")
        values[key] = matches[0][1]
    return values


def publish(d, backend, plan, proof, base, release, public, source, counts):
    products = base["manifest"]["products"]
    private = plan["privateRoot"]
    old_private = d.HOME + "/nodeno-releases/" + proof["baseReleaseHash"] + "/private"
    require(private != old_private, "candidate_already_live")

    def switch_pointer(body):
        d.require_deployment_lease(backend)
        content_type, payload = d.multipart({"dir": d.HOME, "overwrite": "1"}, {"nodeno-runtime.php": body})
        d.successful_upload(backend.post("/execute/Fileman/upload_files", payload, content_type))

    with d.deployment_lease(backend):
        check_health(backend.public_health(), proof["baseReleaseHash"], products)
        old_pointer = d.text_content(backend, d.HOME, "nodeno-runtime.php")
        require(old_pointer.count(old_private.encode()) == 1, "runtime_base_root_not_unique")
        require(private.encode() not in old_pointer, "candidate_root_already_in_pointer")
        storage = pointer_storage_values(old_pointer)
        new_pointer = old_pointer.replace(old_private.encode(), private.encode())
        require(new_pointer.count(private.encode()) == 1 and new_pointer.replace(private.encode(), old_private.encode()) == old_pointer, "runtime_pointer_delta_not_exact")
        require(pointer_storage_values(new_pointer) == storage, "runtime_storage_roots_changed")
        originals = {name: d.text_content(backend, d.PUBLIC, name) for name in public}
        for name, body in originals.items():
            require(body == base["all_bytes"]["public/" + name], "live_public_base_changed_" + name)
        verify_public(d, backend, originals)

        backup = d.HOME + "/nodeno-backups/" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-packaging-" + secrets.token_hex(4)
        d.ensure_directory(backend, backup, private=True, permissions="0700")
        d.ensure_directory(backend, backup + "/public", private=True, permissions="0700")
        backend.upload(backup, {"nodeno-runtime.php": old_pointer})
        require(d.text_content(backend, backup, "nodeno-runtime.php") == old_pointer, "runtime_backup_readback_failed")
        for name, body in originals.items():
            backend.upload(backup + "/public", {name: body})
            require(d.text_content(backend, backup + "/public", name) == body, "public_backup_readback_failed_" + name)
        emit("remote_originals_backed_up", publicFiles=sorted(originals))

        d.ensure_directory(backend, private, private=True, permissions="0700")
        d.ensure_directory(backend, private + "/cache", private=True, permissions="0700")
        private_files = {name[8:]: body for name, body in release["all_bytes"].items() if name.startswith("private/")}
        for index, (name, body) in enumerate(sorted(private_files.items()), 1):
            emit("staging_private_file", file=name, current=index, total=len(private_files))
            backend.upload(private, {name: body})
        for name in ("index.html", "release.json"):
            require(d.text_content(backend, private, name) == private_files[name], "staged_private_readback_failed_" + name)
        d.require_deployment_lease(backend)
        require(d.text_content(backend, d.HOME, "nodeno-runtime.php") == old_pointer, "runtime_pointer_changed_during_staging")
        verify_public(d, backend, originals, https=False)
        check_health(backend.public_health(), proof["baseReleaseHash"], products)

        try:
            for name in PUBLIC_ORDER:
                if name in public:
                    d.require_deployment_lease(backend)
                    emit("publishing_public_file", file=name)
                    backend.upload(d.PUBLIC, {name: public[name]})
            verify_public(d, backend, public, https=False)
            d.require_deployment_lease(backend)
            require(d.text_content(backend, d.HOME, "nodeno-runtime.php") == old_pointer, "runtime_pointer_changed_before_switch")
            switch_pointer(new_pointer)
            require(d.text_content(backend, d.HOME, "nodeno-runtime.php") == new_pointer, "runtime_pointer_readback_failed")
            health_readback(backend, proof["releaseHash"], products)
            verify_public(d, backend, public)
        except BaseException:
            emit("restoring_original_pointer_and_public_files")
            rollback_failed = False
            try:
                switch_pointer(old_pointer)
            except BaseException:
                rollback_failed = True
            for name in PUBLIC_ORDER:
                if name in originals:
                    try:
                        d.require_deployment_lease(backend)
                        backend.upload(d.PUBLIC, {name: originals[name]})
                    except BaseException:
                        rollback_failed = True
            try:
                require(d.text_content(backend, d.HOME, "nodeno-runtime.php") == old_pointer, "rollback_pointer_readback_failed")
                health_readback(backend, proof["baseReleaseHash"], products)
                verify_public(d, backend, originals)
            except BaseException:
                rollback_failed = True
            require(not rollback_failed, "packaging_release_rollback_failed")
            emit("rollback_verified", releaseHash=proof["baseReleaseHash"])
            raise

        result = {
            "passed": True, "live": True,
            "releaseHash": proof["releaseHash"], "baseReleaseHash": proof["baseReleaseHash"],
            "sourcePackageHash": source["manifest"]["releaseHash"],
            "backupRoot": backup, "publicFilesChanged": sorted(public),
            "publicReadbackSha256": {name: d.sha256(body) for name, body in public.items()},
            "products": products, "privateFilesStaged": len(private_files),
            "catalogueMediaPricesAndCommerceUnchanged": True,
            "liveCheckoutPreserved": True, "liveMediaReady": True,
            "accountAndPaymentStoragePreserved": True, "remoteDeletions": False,
            "exactCandidateBrowserAcceptance": True, **counts,
        }
    # A success record is written only after releasing our own deployment lease.
    (E / "deployment.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    emit("deployment_verified", **result)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="publish after all readiness gates pass; default is read-only")
    args = parser.parse_args()
    spec = importlib.util.spec_from_file_location("nodeno_packaging_publish", R / "scripts/deploy-cpanel.py")
    d = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = d
    spec.loader.exec_module(d)
    emit("verifying_local_release_and_acceptance", apply=args.apply)
    proof, base, release, source, public, counts = verify_local_inputs(d)
    backend = d.CpanelBackend(allow_writes=args.apply)
    backend.public_paths = frozenset(public)
    check_health(backend.public_health(), proof["baseReleaseHash"], base["manifest"]["products"])
    plan = d.make_plan(release, backend)
    emit("publication_ready", apply=args.apply, releaseHash=proof["releaseHash"], baseReleaseHash=proof["baseReleaseHash"], publicFiles=sorted(public), checkoutEnabled=True, mediaVerified=True, **counts)
    if args.apply:
        publish(d, backend, plan, proof, base, release, public, source, counts)


if __name__ == "__main__":
    main()
