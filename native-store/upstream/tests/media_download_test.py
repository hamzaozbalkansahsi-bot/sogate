"""Offline transport tests; the apply run separately verifies the real TLS CDN."""
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import ssl
import struct
import sys
import tempfile
import threading
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from PIL import Image

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "media-download.py"


def load_downloader():
    spec = importlib.util.spec_from_file_location("nodeno_media_download", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class Response(io.BytesIO):
    def __init__(self, body=b"", status=200, headers=None, url="https://witcdn.adoremobilya.com/image"):
        super().__init__(body)
        self.status = status
        self.headers = headers or {}
        self.url = url

    def geturl(self):
        return self.url


class Opener:
    def __init__(self, responses):
        self.responses = list(responses)
        self.urls = []

    def open(self, request, timeout):
        self.urls.append(request.full_url)
        response = self.responses.pop(0)
        if isinstance(response, BaseException):
            raise response
        return response


class MediaDownloadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.media = load_downloader()
        buffer = io.BytesIO()
        Image.new("RGB", (8, 6), "white").save(buffer, "PNG")
        cls.png = buffer.getvalue()

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="nodeno-media-download-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.output = self.root / "artifacts" / "media-originals"
        self.output.mkdir(parents=True)

    def client(self, responses, **kwargs):
        return self.media.HttpsImageClient(opener=Opener(responses), **kwargs)

    def image_response(self, **kwargs):
        return Response(self.png, headers={"Content-Type": "image/png", "Content-Length": str(len(self.png))}, **kwargs)

    def animation(self, name, frames, canvas):
        # Repeat a valid tiny GIF frame on a larger canvas without retaining decoded frames.
        buffer = io.BytesIO()
        Image.new("P", (1, 1), 0).save(buffer, "GIF", duration=40)
        data = buffer.getvalue()
        palette_bytes = 3 * (2 ** ((data[10] & 7) + 1)) if data[10] & 128 else 0
        boundary = 13 + palette_bytes
        header = data[:6] + struct.pack("<HH", *canvas) + data[10:boundary]
        target = self.output / name
        target.write_bytes(header + data[boundary:-1] * frames + b";")
        return target

    def test_exact_https_host_and_each_redirect_are_enforced(self):
        good = "https://witcdn.adoremobilya.com/image"
        for bad in ["http://witcdn.adoremobilya.com/a", "https://witcdn.adoremobilya.com.evil.test/a",
                    "https://user@witcdn.adoremobilya.com/a", "https://witcdn.adoremobilya.com:444/a",
                    "https://witcdn.adoremobilya.com/a#fragment", " https://witcdn.adoremobilya.com/a",
                    "https://witcdn.adoremobilya.com/a\\b", "https://127.0.0.1/a"]:
            with self.subTest(bad=bad), self.assertRaises(self.media.DownloadError):
                self.media.safe_url(bad)
        malicious = Response(status=302, headers={"Location": "https://evil.test/private"})
        client = self.client([malicious])
        with self.assertRaisesRegex(self.media.DownloadError, "unsafe_url"):
            client.fetch(good, self.output / "blocked.part")
        self.assertEqual(client.opener.urls, [good])
        self.assertTrue(malicious.closed)
        self.assertFalse((self.output / "blocked.part").exists())
        client = self.client([Response(status=302, headers={"Location": "/next"}), self.image_response(url="https://witcdn.adoremobilya.com/next")])
        result = client.fetch(good, self.output / "accepted.part")
        self.assertEqual(result["sha256"], hashlib.sha256(self.png).hexdigest())
        self.assertEqual(client.opener.urls, [good, "https://witcdn.adoremobilya.com/next"])

    def test_actual_bytes_are_bounded_even_without_a_trustworthy_length(self):
        for headers in [{"Content-Type": "image/png"}, {"Content-Type": "image/png", "Content-Length": "1"}]:
            target = self.output / "large.part"
            client = self.client([Response(b"x" * 300, headers=headers)], max_bytes=100)
            with self.assertRaisesRegex(self.media.DownloadError, "image_too_large"):
                client.fetch("https://witcdn.adoremobilya.com/image", target)
            self.assertFalse(target.exists())

    def test_claimed_mime_and_full_image_decode_must_match(self):
        cases = [
            Response(self.png, headers={"Content-Type": "image/jpeg"}),
            Response(b"<html>failure</html>", headers={"Content-Type": "image/png"}),
            Response(self.png[:35], headers={"Content-Type": "image/png"}),
        ]
        for index, response in enumerate(cases):
            target = self.output / f"invalid-{index}.part"
            with self.assertRaises(self.media.DownloadError):
                self.client([response]).fetch("https://witcdn.adoremobilya.com/image", target)
            self.assertFalse(target.exists())
        result = self.client([self.image_response()]).fetch("https://witcdn.adoremobilya.com/image", self.output / "valid.part")
        self.assertEqual((result["format"], result["mime"], result["width"], result["height"], result["frames"]), ("PNG", "image/png", 8, 6, 1))
        existing = self.output / "existing-original.png"
        existing.write_bytes(self.png)
        with self.assertRaises(FileExistsError):
            self.client([self.image_response()]).fetch("https://witcdn.adoremobilya.com/image", existing)
        self.assertEqual(existing.read_bytes(), self.png, "An existing original must never be removed on a failed exclusive open")

    def test_retries_are_bounded_and_tls_verification_is_required(self):
        sleeps = []
        client = self.client([Response(status=503), Response(status=429, headers={"Retry-After": "1000"}), self.image_response()])
        entry = self.media.download_one("https://witcdn.adoremobilya.com/image", self.output, client, attempts=3, sleeper=sleeps.append)
        self.assertEqual(entry["status"], "verified")
        self.assertEqual(entry["attempts"], 3)
        self.assertEqual(len(sleeps), 2)
        self.assertTrue(all(0 <= delay <= 5 for delay in sleeps))
        self.assertEqual(client.context.verify_mode, ssl.CERT_REQUIRED)
        self.assertTrue(client.context.check_hostname)
        failed = self.client([Response(status=503)] * 3)
        result = self.media.download_one("https://witcdn.adoremobilya.com/image", self.output, failed, attempts=3, sleeper=lambda _: None)
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["lastError"], "http_503")
        self.assertEqual(len(failed.opener.urls), 3)
        self.assertFalse(list(self.output.glob("*.part")))

    def test_catalog_dedup_preserves_all_references_without_editing_source(self):
        source = self.root / "source.json"
        content = json.dumps({"products": [{"id": "A", "images": ["https://witcdn.adoremobilya.com/a", "https://witcdn.adoremobilya.com/b"]}, {"id": "B", "images": ["https://witcdn.adoremobilya.com/a"]}]}).encode()
        source.write_bytes(content)
        plan = self.media.catalog_plan(source)
        self.assertEqual(plan["totals"]["references"], 3)
        self.assertEqual(plan["totals"]["uniqueUrls"], 2)
        self.assertEqual(plan["references"]["A:0"], plan["references"]["B:0"])
        self.assertNotEqual(plan["references"]["A:0"], plan["references"]["A:1"])
        self.assertEqual(source.read_bytes(), content)

    def test_resume_requires_verified_hash_and_cannot_escape_artifacts(self):
        url = "https://witcdn.adoremobilya.com/image"
        entry = self.media.download_one(url, self.output, self.client([self.image_response()]), sleeper=lambda _: None)
        entry["path"] = (Path("artifacts") / "media-originals" / Path(entry["path"]).name).as_posix()
        key = hashlib.sha256(url.encode()).hexdigest()
        self.assertTrue(self.media.resume_valid(self.root, self.output, key, entry))
        (self.root / entry["path"]).write_bytes(b"corrupted")
        self.assertFalse(self.media.resume_valid(self.root, self.output, key, entry))
        entry["path"] = "../../secret.png"
        self.assertFalse(self.media.resume_valid(self.root, self.output, key, entry))
        with self.assertRaises(ValueError):
            self.media.artifact_path(self.root, self.root / "source.json")
        target = self.root / "artifacts" / "media-download.json"
        self.media.atomic_json(target, {"verified": 2})
        self.assertEqual(json.loads(target.read_text()), {"verified": 2})
        self.assertFalse(list(target.parent.glob("*.tmp")))

    def test_top_level_error_diagnostics_never_include_exception_messages(self):
        output = io.StringIO()
        failure = PermissionError(13, "secret=https://credential@private.invalid/?token=do-not-log")
        failure.winerror = 32
        with patch.object(sys, "argv", ["media-download.py"]), patch.object(self.media, "run", side_effect=failure), redirect_stdout(output):
            status = self.media.main()
        self.assertEqual(status, 1)
        result = json.loads(output.getvalue())
        self.assertEqual(result["error"], "media_download_failed")
        self.assertEqual(result["diagnostic"]["exceptionType"], "PermissionError")
        self.assertEqual(result["diagnostic"]["errno"], 13)
        self.assertEqual(result["diagnostic"]["winerror"], 32)
        self.assertIsInstance(result["diagnostic"]["lastFrame"]["line"], int)
        self.assertNotIn("private.invalid", output.getvalue())
        self.assertNotIn("do-not-log", output.getvalue())

    def test_atomic_manifest_retries_transient_permission_error_then_succeeds(self):
        target = self.root / "artifacts" / "media-download.json"
        self.media.atomic_json(target, {"generation": 1})
        actual_replace = self.media.os.replace
        attempts = []

        def transient_replace(source, destination):
            attempts.append((source, destination))
            if len(attempts) <= 2:
                failure = PermissionError(13, "simulated sharing violation")
                failure.winerror = 5
                raise failure
            return actual_replace(source, destination)

        with patch.object(self.media.os, "replace", side_effect=transient_replace), patch.object(self.media.time, "sleep") as sleep:
            self.media.atomic_json(target, {"generation": 2})
        self.assertEqual(json.loads(target.read_text()), {"generation": 2})
        self.assertEqual(len(attempts), 3)
        self.assertEqual(sleep.call_count, 2)
        self.assertTrue(all(0 < call.args[0] <= 0.5 for call in sleep.call_args_list))
        self.assertFalse(list(target.parent.glob("*.tmp")))

    def test_atomic_manifest_permanent_permission_failure_preserves_previous_json(self):
        target = self.root / "artifacts" / "media-download.json"
        self.media.atomic_json(target, {"generation": 1})
        previous = target.read_bytes()
        failure = PermissionError(13, "permanent permission failure")
        failure.winerror = 5
        with patch.object(self.media.os, "replace", side_effect=failure) as replace, patch.object(self.media.time, "sleep") as sleep:
            with self.assertRaises(PermissionError):
                self.media.atomic_json(target, {"generation": 2})
        self.assertEqual(replace.call_count, 6)
        self.assertEqual(sleep.call_count, 5)
        self.assertLessEqual(sum(call.args[0] for call in sleep.call_args_list), 1.5)
        self.assertEqual(target.read_bytes(), previous)
        self.assertFalse(list(target.parent.glob("*.tmp")))

    @unittest.skipUnless(os.name == "nt", "Windows file-sharing regression")
    def test_atomic_manifest_survives_real_windows_reader_lock(self):
        target = self.root / "artifacts" / "media-download.json"
        self.media.atomic_json(target, {"generation": 1})
        opened = threading.Event()

        def reader():
            with target.open("rb"):
                opened.set()
                threading.Event().wait(0.12)

        thread = threading.Thread(target=reader)
        thread.start()
        try:
            self.assertTrue(opened.wait(2))
            self.media.atomic_json(target, {"generation": 2})
        finally:
            thread.join(2)
        self.assertEqual(json.loads(target.read_text()), {"generation": 2})

    def test_animation_above_old_budget_decodes_every_frame_without_retaining_frames(self):
        filename = self.animation("product-rotation.gif", 501, (1000, 1000))
        result = self.media.inspect_image(filename, "image/gif")
        self.assertEqual(result["frames"], 501)
        self.assertEqual(result["decodedFramePixels"], 501_000_000)
        self.assertEqual(result["durationMs"], 501 * 40)
        self.assertLessEqual(self.media.MAX_FRAME_PIXELS, 1_000_000_000)

    def test_animation_frame_count_pixel_and_time_budgets_remain_strict(self):
        excessive_frames = self.animation("too-many-frames.gif", 1001, (1, 1))
        with self.assertRaisesRegex(self.media.DownloadError, "image_frames_too_large"):
            self.media.inspect_image(excessive_frames, "image/gif")
        excessive_pixels = self.animation("canvas-too-large.gif", 1, (8000, 8000))
        with self.assertRaisesRegex(self.media.DownloadError, "unsupported_image"):
            self.media.inspect_image(excessive_pixels, "image/gif")
        excessive_total = self.animation("too-much-work.gif", 1000, (1100, 1100))
        with self.assertRaisesRegex(self.media.DownloadError, "image_frames_too_large"):
            self.media.inspect_image(excessive_total, "image/gif")
        ordinary = self.animation("decode-timeout.gif", 2, (1, 1))
        with patch.object(self.media.time, "monotonic", side_effect=[0.0, 61.0]):
            with self.assertRaisesRegex(self.media.DownloadError, "image_decode_timeout"):
                self.media.inspect_image(ordinary, "image/gif")


if __name__ == "__main__":
    unittest.main()
