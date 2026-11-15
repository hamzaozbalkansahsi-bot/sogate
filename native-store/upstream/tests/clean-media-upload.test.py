"""Offline immutable-vault validation, batching and resume tests."""
import importlib.util
from pathlib import Path
import hashlib
import io
import json
import tempfile
import threading
import unittest
from contextlib import redirect_stdout
from email import policy
from email.parser import BytesParser
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("clean_media_upload", ROOT / "scripts/upload-clean-media.py")
media = importlib.util.module_from_spec(spec)
spec.loader.exec_module(media)
deploy = media.deploy_module()


def fixture(root, state="approved_cleaned"):
    output = io.BytesIO()
    Image.new("RGB", (2, 2), (10, 20, 30)).save(output, format="PNG")
    body = output.getvalue()
    sha = hashlib.sha256(body).hexdigest()
    url = "https://witcdn.adoremobilya.com/test.png"
    key = hashlib.sha256(url.encode()).hexdigest()
    entry = {"state": state, "sourceSha": sha, "outputSha": sha, "mime": "image/png", "bytes": len(body), "width": 2, "height": 2, "file": sha + ".png" if state == "approved_cleaned" else None}
    references = {"7:0": key}
    approved = {"schema": 1, "policy": "approved-only-v1", "referenceCount": 1, "uniqueCount": 1, "counts": {"approved_unmodified": int(state == "approved_unmodified"), "approved_cleaned": int(state == "approved_cleaned")}, "references": references, "images": {key: entry}}
    serialized = json.dumps(approved, separators=(",", ":")).encode()
    release = {"manifest": {"products": 1, "releaseHash": "b" * 64, "mediaVersion": hashlib.sha256(serialized).hexdigest(), "mediaSource": "approved-only", "mediaApproved": 1}, "all_bytes": {"private/media-approved.json": serialized, "private/media.json": json.dumps({"7": [url]}).encode()}}
    relative = ("artifacts/media-cleaned/" if state == "approved_cleaned" else "artifacts/media-originals/") + key + ".png"
    target = root / relative
    target.parent.mkdir(parents=True)
    target.write_bytes(body)
    cleanup = {"schemaVersion": 1, "publicationReady": True, "references": references, "images": {key: {**entry, "path": relative}}}
    return release, cleanup, target, entry["file"], body


class Backend:
    def __init__(self, lost_response=False):
        self.files = {}
        self.vault = False
        self.writes = []
        self.lost_response = lost_response

    def read(self, module, function, **params):
        if module == "DomainInfo":
            return {"status": 1, "data": {"main_domain": {"domain": deploy.DOMAIN, "documentroot": deploy.PUBLIC, "ip": deploy.IP, "serveralias": deploy.ALIAS}, "parked_domains": [deploy.ALIAS]}}
        directory = params["dir"]
        records = []
        if directory == deploy.HOME:
            records = [{"file": "public_html", "type": "dir"}, {"file": "www", "type": "link"}]
            if self.vault:
                records.append({"file": "nodeno-media", "type": "dir"})
        elif directory == deploy.HOME + "/nodeno-media":
            records = [{"file": name, "type": "file", "size": str(len(body))} for name, body in self.files.items()]
        return {"status": 1, "data": records}

    def api2(self, function, **params):
        assert function == "mkdir" and params["path"] == deploy.HOME and params["name"] == "nodeno-media"
        self.writes.append(("mkdir", params))
        self.vault = True

    def post(self, path, body, content_type):
        assert path == "/execute/Fileman/upload_files"
        message = BytesParser(policy=policy.default).parsebytes(("Content-Type: " + content_type + "\r\nMIME-Version: 1.0\r\n\r\n").encode() + body)
        fields, files = {}, {}
        for part in message.iter_parts():
            name = part.get_param("name", header="content-disposition")
            if part.get_filename():
                files[part.get_filename()] = part.get_payload(decode=True)
            else:
                fields[name] = part.get_payload(decode=True).decode()
        assert fields["overwrite"] == "0"
        assert fields["dir"] == deploy.HOME + "/nodeno-media"
        assert all(name not in self.files for name in files)
        self.files.update(files)
        self.writes.append(("upload", list(files)))
        if self.lost_response:
            self.lost_response = False
            raise RuntimeError("simulated_lost_response")
        return {"status": 1, "errors": None, "data": {"failed": 0, "succeeded": len(files)}}


def transport_fixture(root, count=12):
    release, cleanup, _, _, _ = fixture(root)
    prepared = media.prepare_upload(root, release, cleanup)
    # Transport tests receive already-verified content-addressed raster bytes.
    prepared["files"] = {}
    for index in range(count):
        output = io.BytesIO()
        Image.new("RGB", (2, 2), (index, 20, 30)).save(output, format="PNG")
        body = output.getvalue()
        prepared["files"][hashlib.sha256(body).hexdigest() + ".png"] = body
    return prepared


class SingleFileBackend(Backend):
    def __init__(self, *, lost_response=False, failures=None, concurrent_wave=False):
        super().__init__(lost_response=lost_response)
        self.lock = threading.Lock()
        self.first_wave = threading.Barrier(4, timeout=3) if concurrent_wave else None
        self.active = self.max_active = 0
        self.requests = []
        self.failures = dict(failures or {})

    def post(self, path, body, content_type):
        message = BytesParser(policy=policy.default).parsebytes(("Content-Type: " + content_type + "\r\nMIME-Version: 1.0\r\n\r\n").encode() + body)
        filenames = [part.get_filename() for part in message.iter_parts() if part.get_filename()]
        assert len(filenames) == 1, "Each HTTPS request must contain exactly one file"
        filename = filenames[0]
        with self.lock:
            self.active += 1
            self.max_active = max(self.max_active, self.active)
            self.requests.append(filename)
            first_wave = len(self.requests) <= 4
        try:
            if self.first_wave is not None and first_wave:
                self.first_wave.wait()
            with self.lock:
                if self.failures.get(filename, 0):
                    self.failures[filename] -= 1
                    raise RuntimeError("simulated_request_failure_before_write")
                return super().post(path, body, content_type)
        finally:
            with self.lock:
                self.active -= 1


class CleanMediaUploadTests(unittest.TestCase):
    def test_plan_is_read_only_and_unmodified_images_are_hosted(self):
        with tempfile.TemporaryDirectory(prefix="nodeno-clean-upload-") as directory:
            root = Path(directory)
            release, cleanup, _, _, _ = fixture(root, "approved_unmodified")
            prepared = media.prepare_upload(root, release, cleanup)
            backend = Backend()
            plan = media.make_plan(prepared, backend, deploy)
            self.assertEqual(plan["pendingFiles"], 1)
            self.assertFalse(backend.writes)

    def test_unmodified_source_tampering_blocks_upload(self):
        with tempfile.TemporaryDirectory(prefix="nodeno-clean-upload-") as directory:
            root = Path(directory)
            release, cleanup, target, _, _ = fixture(root, "approved_unmodified")
            target.write_bytes(b"unapproved original")
            with self.assertRaises(media.UploadError):
                media.prepare_upload(root, release, cleanup)

    def test_tamper_quarantine_and_unapproved_final_gate_reject(self):
        with tempfile.TemporaryDirectory(prefix="nodeno-clean-upload-") as directory:
            root = Path(directory)
            release, cleanup, target, _, _ = fixture(root)
            cleanup["publicationReady"] = False
            with self.assertRaises(media.UploadError):
                media.prepare_upload(root, release, cleanup)
            cleanup["publicationReady"] = True
            entry = next(iter(cleanup["images"].values()))
            entry["state"] = "review_required"
            with self.assertRaises(media.UploadError):
                media.prepare_upload(root, release, cleanup)
            entry["state"] = "approved_cleaned"
            target.write_bytes(b"unapproved")
            with self.assertRaises(media.UploadError):
                media.prepare_upload(root, release, cleanup)

    def test_batch_limits_are_bounded_by_bytes_and_file_count(self):
        groups = media.batches({f"{index:064x}.png": b"x" for index in range(101)})
        self.assertEqual([len(group) for group in groups], [50, 50, 1])
        groups = media.batches({"a.png": b"a" * 8000000, "b.png": b"b" * 8000000})
        self.assertEqual(len(groups), 2)
        self.assertTrue(all(sum(map(len, group.values())) <= media.MAX_BATCH_BYTES for group in groups))

    def test_original_animation_above_normal_batch_limit_is_uploaded_alone(self):
        large = b"g" * 15780884
        groups = media.batches({"a.png": b"a", "b.gif": large, "c.png": b"c"})
        self.assertEqual([list(group) for group in groups], [["a.png"], ["b.gif"], ["c.png"]])
        with self.assertRaises(media.UploadError):
            media.batches({"too-big.gif": b"g" * 20000001})

    def test_upload_is_immutable_and_resumes_after_a_lost_success_response(self):
        with tempfile.TemporaryDirectory(prefix="nodeno-clean-upload-") as directory:
            root = Path(directory)
            release, cleanup, _, filename, body = fixture(root)
            prepared = media.prepare_upload(root, release, cleanup)
            backend = Backend(lost_response=True)
            plan = media.make_plan(prepared, backend, deploy)
            with redirect_stdout(io.StringIO()):
                media.apply_upload(prepared, backend, deploy, plan, sleeper=lambda _: None)
            self.assertEqual(backend.files[filename], body)
            self.assertEqual(sum(entry[0] == "upload" for entry in backend.writes), 1)
            resumed = media.make_plan(prepared, backend, deploy)
            self.assertEqual(resumed["pendingFiles"], 0)
            self.assertEqual(resumed["skippedExistingSizeMatches"], 1)
            backend.files[filename] = b"wrong size"
            with self.assertRaises(media.UploadError):
                media.make_plan(prepared, backend, deploy)

    def test_single_files_use_separate_requests_with_at_most_four_in_flight(self):
        with tempfile.TemporaryDirectory(prefix="nodeno-single-upload-") as directory:
            prepared = transport_fixture(Path(directory))
            backend = SingleFileBackend(concurrent_wave=True)
            plan = media.make_plan(prepared, backend, deploy, single_files=True)
            self.assertEqual(plan["batches"], 1)
            self.assertEqual(plan["maxConcurrentRequests"], 4)
            self.assertFalse(backend.writes)
            with redirect_stdout(io.StringIO()):
                media.apply_upload(prepared, backend, deploy, plan, single_files=True, sleeper=lambda _: None)
            self.assertEqual(backend.files, prepared["files"])
            self.assertEqual(len(backend.requests), len(prepared["files"]))
            self.assertEqual(backend.max_active, 4)

    def test_single_files_retry_only_missing_after_partial_success_and_lost_response(self):
        with tempfile.TemporaryDirectory(prefix="nodeno-single-upload-") as directory:
            prepared = transport_fixture(Path(directory), count=6)
            missing = sorted(prepared["files"])[-1]
            backend = SingleFileBackend(lost_response=True, failures={missing: 1})
            plan = media.make_plan(prepared, backend, deploy, single_files=True)
            with redirect_stdout(io.StringIO()):
                media.apply_upload(prepared, backend, deploy, plan, single_files=True, sleeper=lambda _: None)
            self.assertEqual(backend.files, prepared["files"])
            self.assertEqual(backend.requests.count(missing), 2)
            self.assertTrue(all(backend.requests.count(name) == 1 for name in prepared["files"] if name != missing))

    def test_single_files_resume_after_exhausted_retry_without_reuploading_successes(self):
        with tempfile.TemporaryDirectory(prefix="nodeno-single-upload-") as directory:
            prepared = transport_fixture(Path(directory), count=6)
            missing = sorted(prepared["files"])[-1]
            backend = SingleFileBackend(failures={missing: 3})
            plan = media.make_plan(prepared, backend, deploy, single_files=True)
            with redirect_stdout(io.StringIO()), self.assertRaisesRegex(media.UploadError, "resume_safe"):
                media.apply_upload(prepared, backend, deploy, plan, single_files=True, sleeper=lambda _: None)
            self.assertEqual(set(backend.files), set(prepared["files"]) - {missing})
            resumed = media.make_plan(prepared, backend, deploy, single_files=True)
            self.assertEqual(resumed["pendingFiles"], 1)
            with redirect_stdout(io.StringIO()):
                media.apply_upload(prepared, backend, deploy, resumed, single_files=True, sleeper=lambda _: None)
            self.assertEqual(backend.files, prepared["files"])
            self.assertEqual(backend.requests.count(missing), 4)
            self.assertTrue(all(backend.requests.count(name) == 1 for name in prepared["files"] if name != missing))


if __name__ == "__main__":
    unittest.main()
