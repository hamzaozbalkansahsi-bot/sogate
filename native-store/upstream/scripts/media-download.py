#!/usr/bin/env python3
"""Download and verify catalog originals. No image editing or deployment occurs here."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import closing
from datetime import datetime, timezone
import hashlib
from http.client import HTTPException
import json
import os
from pathlib import Path
import re
import ssl
import threading
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit
from urllib.request import HTTPRedirectHandler, HTTPSHandler, ProxyHandler, Request, build_opener
import uuid
import warnings

from PIL import Image, ImageFile


ALLOWED_HOST = "witcdn.adoremobilya.com"
MAX_BYTES = 20_000_000
MAX_PIXELS = 50_000_000
MAX_FRAME_PIXELS = 1_000_000_000
MAX_FRAMES = 1000
MAX_DECODE_SECONDS = 60
FORMATS = {"JPEG": ("image/jpeg", ".jpg"), "PNG": ("image/png", ".png"),
           "WEBP": ("image/webp", ".webp"), "AVIF": ("image/avif", ".avif"),
           "GIF": ("image/gif", ".gif")}
DECODE_LOCK = threading.BoundedSemaphore(2)
ImageFile.LOAD_TRUNCATED_IMAGES = False


def timestamp():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def safe_exception_details(exception):
    """Keep only structural diagnostics; never format an exception message or URL."""
    last = exception.__traceback__
    while last is not None and last.tb_next is not None:
        last = last.tb_next
    return {
        "exceptionType": type(exception).__name__,
        "errno": getattr(exception, "errno", None) if isinstance(getattr(exception, "errno", None), int) else None,
        "winerror": getattr(exception, "winerror", None) if isinstance(getattr(exception, "winerror", None), int) else None,
        "lastFrame": None if last is None else {"file": Path(last.tb_frame.f_code.co_filename).name,
            "line": last.tb_lineno, "function": last.tb_frame.f_code.co_name},
    }


class DownloadError(Exception):
    def __init__(self, code, retryable=False, retry_after=None):
        super().__init__(code)
        self.code = code
        self.retryable = retryable
        self.retry_after = retry_after


def safe_url(value):
    if not isinstance(value, str) or not value or any(ord(c) <= 32 or ord(c) == 127 or c == "\\" for c in value):
        raise DownloadError("unsafe_url")
    try:
        parts = urlsplit(value)
        valid = (parts.scheme == "https" and parts.hostname == ALLOWED_HOST
                 and parts.username is None and parts.password is None and not parts.fragment
                 and parts.port in (None, 443))
    except ValueError:
        valid = False
    if not valid:
        raise DownloadError("unsafe_url")
    return value


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, newurl):
        return None


class RateLimiter:
    """One shared request budget includes redirects and retries."""
    def __init__(self, requests_per_second):
        self.interval = 1 / requests_per_second
        self.next_request = 0.0
        self.lock = threading.Lock()

    def wait(self):
        with self.lock:
            now = time.monotonic()
            scheduled = max(now, self.next_request)
            self.next_request = scheduled + self.interval
        delay = scheduled - now
        if delay > 0:
            time.sleep(delay)


def inspect_image(filename, claimed_mime):
    try:
        with DECODE_LOCK, warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(filename) as image:
                image_format = image.format
                width, height = image.size
                if image_format not in FORMATS or width < 1 or height < 1 or width * height > MAX_PIXELS:
                    raise DownloadError("unsupported_image")
                mime, extension = FORMATS[image_format]
                if mime != claimed_mime:
                    raise DownloadError("mime_mismatch")
                image.verify()
            # verify() checks structure; reopening and loading every frame checks actual decoding.
            with Image.open(filename) as decoded:
                frames = getattr(decoded, "n_frames", 1)
                if frames > MAX_FRAMES:
                    raise DownloadError("image_frames_too_large")
                total_pixels = 0
                duration_ms = 0
                decode_started = time.monotonic()
                for frame in range(frames):
                    if time.monotonic() - decode_started > MAX_DECODE_SECONDS:
                        raise DownloadError("image_decode_timeout")
                    decoded.seek(frame)
                    frame_pixels = decoded.width * decoded.height
                    if decoded.width < 1 or decoded.height < 1 or frame_pixels > MAX_PIXELS:
                        raise DownloadError("unsupported_image")
                    total_pixels += frame_pixels
                    if total_pixels > MAX_FRAME_PIXELS:
                        raise DownloadError("image_frames_too_large")
                    decoded.load()
                    duration_ms += max(0, int(decoded.info.get("duration", 0)))
                    if time.monotonic() - decode_started > MAX_DECODE_SECONDS:
                        raise DownloadError("image_decode_timeout")
            return {"format": image_format, "mime": mime, "extension": extension,
                    "width": width, "height": height, "frames": frames,
                    "decodedFramePixels": total_pixels, "durationMs": duration_ms}
    except DownloadError:
        raise
    except Exception as exception:
        raise DownloadError("invalid_image") from exception


class HttpsImageClient:
    def __init__(self, *, opener=None, max_bytes=MAX_BYTES, timeout=30, limiter=None):
        if not 0 < max_bytes <= MAX_BYTES:
            raise ValueError("Invalid byte limit")
        self.context = ssl.create_default_context()
        self.context.check_hostname = True
        self.context.verify_mode = ssl.CERT_REQUIRED
        self.context.set_alpn_protocols(["http/1.1"])
        self.opener = opener
        self.local = threading.local()
        self.max_bytes = max_bytes
        self.timeout = timeout
        self.limiter = limiter

    def get_opener(self):
        if self.opener is not None:
            return self.opener
        if not hasattr(self.local, "opener"):
            # No environment proxies, credentials, cookies or global opener settings are used.
            self.local.opener = build_opener(ProxyHandler({}), NoRedirect(), HTTPSHandler(context=self.context))
        return self.local.opener

    def fetch(self, url, destination):
        destination = Path(destination)
        target = safe_url(url)
        started = time.monotonic()
        created = False
        try:
            for hop in range(4):
                safe_url(target)
                if self.limiter is not None:
                    self.limiter.wait()
                request = Request(target, headers={"User-Agent": "NODENO-MediaArchive/1.0",
                    "Accept": ", ".join(mime for mime, _ in FORMATS.values()), "Accept-Encoding": "identity"}, method="GET")
                try:
                    response = self.get_opener().open(request, timeout=self.timeout)
                except HTTPError as response_error:
                    response = response_error
                with closing(response):
                    safe_url(response.geturl())
                    status = response.status
                    if status in (301, 302, 303, 307, 308):
                        location = response.headers.get("Location", "")
                        if not location or any(ord(c) <= 32 or ord(c) == 127 or c == "\\" for c in location):
                            raise DownloadError("unsafe_url")
                        target = safe_url(urljoin(target, location))
                        if hop == 3:
                            raise DownloadError("redirect_limit")
                        continue
                    if status != 200:
                        retry_after = response.headers.get("Retry-After", "")
                        delay = min(5.0, float(retry_after)) if re.fullmatch(r"[0-9]+", retry_after) else None
                        raise DownloadError(f"http_{status}", status in (408, 425, 429, 500, 502, 503, 504), delay)
                    mime = response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
                    if mime not in {value[0] for value in FORMATS.values()}:
                        raise DownloadError("unsupported_mime")
                    if response.headers.get("Content-Encoding", "identity").strip().lower() not in ("", "identity"):
                        raise DownloadError("unexpected_content_encoding")
                    declared = response.headers.get("Content-Length")
                    if declared is not None and not re.fullmatch(r"[0-9]+", declared):
                        raise DownloadError("invalid_content_length")
                    if declared is not None and int(declared) > self.max_bytes:
                        raise DownloadError("image_too_large")
                    received = 0
                    digest = hashlib.sha256()
                    reader = getattr(response, "read1", response.read)
                    with destination.open("xb") as stream:
                        created = True
                        while True:
                            if time.monotonic() - started > 120:
                                raise DownloadError("transfer_timeout", True)
                            chunk = reader(min(65536, self.max_bytes - received + 1))
                            if not chunk:
                                break
                            received += len(chunk)
                            if received > self.max_bytes:
                                raise DownloadError("image_too_large")
                            stream.write(chunk)
                            digest.update(chunk)
                        stream.flush()
                        os.fsync(stream.fileno())
                    if declared is not None and received != int(declared):
                        raise DownloadError("content_length_mismatch", True)
                    details = inspect_image(destination, mime)
                    return {**details, "bytes": received, "sha256": digest.hexdigest(), "finalUrl": target}
            raise DownloadError("redirect_limit")
        except BaseException:
            if created:
                destination.unlink(missing_ok=True)
            raise


def download_one(url, output, client, *, attempts=3, sleeper=time.sleep):
    safe_url(url)
    output = Path(output)
    key = hashlib.sha256(url.encode("utf-8")).hexdigest()
    last_error = "download_failed"
    for attempt in range(1, attempts + 1):
        temporary = output / f".{key}.{uuid.uuid4().hex}.part"
        try:
            result = client.fetch(url, temporary)
            filename = output / (key + result["extension"])
            if filename.is_symlink():
                raise DownloadError("unsafe_output_path")
            os.replace(temporary, filename)
            return {**result, "url": url, "status": "verified", "path": str(filename),
                    "attempts": attempt, "downloadedAt": timestamp(), "lastError": None}
        except DownloadError as exception:
            last_error = exception.code
            retryable, retry_after = exception.retryable, exception.retry_after
        except (URLError, OSError, HTTPException) as exception:
            reason = getattr(exception, "reason", exception)
            if isinstance(reason, ssl.SSLCertVerificationError):
                last_error, retryable, retry_after = "certificate_verification_failed", False, None
            else:
                last_error, retryable, retry_after = "network_error", True, None
        except Exception:
            last_error, retryable, retry_after = "download_failed", False, None
        finally:
            temporary.unlink(missing_ok=True)
        if not retryable or attempt == attempts:
            break
        sleeper(min(5.0, retry_after if retry_after is not None else 0.5 * (2 ** (attempt - 1))))
    return {"url": url, "status": "failed", "attempts": attempt, "lastError": last_error, "failedAt": timestamp()}


def catalog_plan(filename):
    raw = Path(filename).read_bytes()
    catalog = json.loads(raw)
    images, references, product_ids = {}, {}, set()
    for product in catalog["products"]:
        product_id = str(product["id"])
        if not re.fullmatch(r"[A-Za-z0-9_-]+", product_id) or product_id in product_ids:
            raise ValueError("Invalid or duplicate product ID")
        product_ids.add(product_id)
        for index, url in enumerate(product.get("images", [])):
            safe_url(url)
            key = hashlib.sha256(url.encode("utf-8")).hexdigest()
            if key in images and images[key]["url"] != url:
                raise ValueError("URL hash collision")
            images.setdefault(key, {"url": url, "status": "pending", "attempts": 0})
            references[f"{product_id}:{index}"] = key
    return {"schemaVersion": 1, "sourceCatalogSha256": hashlib.sha256(raw).hexdigest(),
            "createdAt": timestamp(), "updatedAt": timestamp(), "references": references, "images": images,
            "totals": {"products": len(product_ids), "references": len(references), "uniqueUrls": len(images),
                       "verified": 0, "failed": 0, "pending": len(images), "bytes": 0}}


def artifact_path(workspace, value):
    workspace = Path(workspace).resolve()
    artifacts = workspace / "artifacts"
    target = Path(value)
    if not target.is_absolute():
        target = workspace / target
    resolved = target.resolve()
    if artifacts.is_symlink() or not resolved.is_relative_to(artifacts) or resolved == artifacts:
        raise ValueError("Outputs must stay within workspace artifacts")
    probe = target
    while probe != workspace and probe != probe.parent:
        if probe.is_symlink():
            raise ValueError("Symlink output paths are not permitted")
        probe = probe.parent
    return resolved


def atomic_json(filename, value):
    filename = Path(filename)
    filename.parent.mkdir(parents=True, exist_ok=True)
    temporary = filename.with_name(f".{filename.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temporary.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(value, stream, ensure_ascii=False, separators=(",", ":"))
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        # Windows readers may temporarily hold a destination without FILE_SHARE_DELETE.
        # Keep the previous manifest intact; retry the atomic operation, never truncate it.
        for attempt in range(6):
            try:
                os.replace(temporary, filename)
                break
            except PermissionError as exception:
                if attempt == 5 or getattr(exception, "winerror", None) not in (None, 5, 32, 33):
                    raise
                time.sleep(min(0.05 * (2 ** attempt), 0.5))
    finally:
        temporary.unlink(missing_ok=True)


def resume_valid(workspace, output, key, entry):
    try:
        if entry.get("status") != "verified" or not re.fullmatch(r"[a-f0-9]{64}", key):
            return False
        if not re.fullmatch(r"[a-f0-9]{64}", entry.get("sha256", "")) or entry.get("format") not in FORMATS:
            return False
        mime, extension = FORMATS[entry["format"]]
        expected = Path(output) / (key + extension)
        actual = Path(workspace) / entry["path"]
        if actual.resolve() != expected.resolve() or actual.is_symlink() or not actual.is_file():
            return False
        size = actual.stat().st_size
        if size < 1 or size > MAX_BYTES or size != entry.get("bytes") or entry.get("mime") != mime:
            return False
        if not isinstance(entry.get("width"), int) or not isinstance(entry.get("height"), int) or entry["width"] < 1 or entry["height"] < 1:
            return False
        with actual.open("rb") as stream:
            return hashlib.file_digest(stream, "sha256").hexdigest() == entry["sha256"]
    except (KeyError, OSError, TypeError, ValueError):
        return False


def update_totals(manifest):
    entries = list(manifest["images"].values())
    for status in ("verified", "failed", "pending"):
        manifest["totals"][status] = sum(entry["status"] == status for entry in entries)
    manifest["totals"]["bytes"] = sum(entry.get("bytes", 0) for entry in entries if entry["status"] == "verified")
    manifest["updatedAt"] = timestamp()


def run(args):
    workspace = Path(__file__).resolve().parents[1]
    catalog_file = Path(args.catalog)
    if not catalog_file.is_absolute():
        catalog_file = workspace / catalog_file
    manifest = catalog_plan(catalog_file)
    if not args.apply and not args.verify_only:
        print(json.dumps({"event": "plan", "networkRequests": 0, **manifest["totals"]}), flush=True)
        return 0
    output = artifact_path(workspace, args.output)
    manifest_file = artifact_path(workspace, args.manifest)
    progress_file = artifact_path(workspace, args.progress)
    if manifest_file == progress_file or catalog_file.resolve() in (manifest_file, progress_file) or catalog_file.resolve().is_relative_to(output):
        raise ValueError("Source and output paths must be distinct")
    if manifest_file.exists():
        if manifest_file.stat().st_size > 64_000_000:
            raise ValueError("Manifest exceeds limit")
        previous = json.loads(manifest_file.read_text(encoding="utf-8"))
        if previous.get("schemaVersion") != 1 or previous.get("sourceCatalogSha256") != manifest["sourceCatalogSha256"]:
            raise ValueError("Existing manifest does not match source catalog")
        manifest["createdAt"] = previous.get("createdAt", manifest["createdAt"])
        for key, entry in previous.get("images", {}).items():
            if key in manifest["images"] and entry.get("url") == manifest["images"][key]["url"] and resume_valid(workspace, output, key, entry):
                manifest["images"][key] = entry
    update_totals(manifest)
    if args.verify_only:
        print(json.dumps({"event": "verification", **manifest["totals"]}), flush=True)
        return 0 if manifest["totals"]["verified"] == manifest["totals"]["uniqueUrls"] else 2
    output.mkdir(parents=True, exist_ok=True)
    progress_file.parent.mkdir(parents=True, exist_ok=True)
    atomic_json(manifest_file, manifest)
    pending = [(key, entry["url"]) for key, entry in manifest["images"].items() if entry["status"] != "verified"]
    if args.limit:
        pending = pending[:args.limit]
    client = HttpsImageClient(timeout=args.timeout, limiter=RateLimiter(args.rate))
    print(json.dumps({"event": "started", "workers": args.workers, "requestsPerSecond": args.rate, **manifest["totals"]}), flush=True)
    completed, last_checkpoint = 0, time.monotonic()
    with progress_file.open("a", encoding="utf-8", newline="\n") as progress:
        with ThreadPoolExecutor(max_workers=args.workers, thread_name_prefix="nodeno-media") as pool:
            futures = {pool.submit(download_one, url, output, client, attempts=args.attempts): key for key, url in pending}
            try:
                for future in as_completed(futures):
                    key = futures[future]
                    result = future.result()
                    if result["status"] == "verified":
                        result["path"] = Path(result["path"]).relative_to(workspace).as_posix()
                    manifest["images"][key] = result
                    completed += 1
                    event = {"time": timestamp(), "event": result["status"], "urlSha256": key,
                             "bytes": result.get("bytes", 0), "attempts": result["attempts"], "error": result.get("lastError")}
                    progress.write(json.dumps(event, separators=(",", ":")) + "\n")
                    progress.flush()
                    if completed % 25 == 0 or time.monotonic() - last_checkpoint > 2:
                        update_totals(manifest)
                        atomic_json(manifest_file, manifest)
                        last_checkpoint = time.monotonic()
                    if completed % 100 == 0:
                        update_totals(manifest)
                        print(json.dumps({"event": "progress", **manifest["totals"]}), flush=True)
            except BaseException:
                for future in futures:
                    future.cancel()
                raise
            finally:
                update_totals(manifest)
                atomic_json(manifest_file, manifest)
    print(json.dumps({"event": "complete", **manifest["totals"]}), flush=True)
    return 0 if manifest["totals"]["failed"] == 0 and manifest["totals"]["pending"] == 0 else 2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", default="data/catalog-source.json")
    parser.add_argument("--output", default="artifacts/media-originals")
    parser.add_argument("--manifest", default="artifacts/media-download.json")
    parser.add_argument("--progress", default="artifacts/media-download-progress.jsonl")
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--apply", action="store_true", help="Download missing/unverified originals")
    action.add_argument("--verify-only", action="store_true", help="Hash-check every completed original; no network or writes")
    parser.add_argument("--workers", type=int, default=10, choices=range(1, 13), metavar="1..12")
    parser.add_argument("--rate", type=float, default=8, help="Global requests/second, including redirects/retries (0.5..12)")
    parser.add_argument("--attempts", type=int, default=3, choices=range(1, 4))
    parser.add_argument("--timeout", type=int, default=30, choices=range(5, 61), metavar="5..60")
    parser.add_argument("--limit", type=int, default=0, help="Optional smoke-run limit; 0 processes the full catalog")
    args = parser.parse_args()
    if not 0.5 <= args.rate <= 12 or args.limit < 0:
        parser.error("rate must be 0.5..12; limit must be nonnegative")
    try:
        return run(args)
    except KeyboardInterrupt:
        print(json.dumps({"event": "interrupted", "error": "interrupted_resume_with_apply"}), flush=True)
        return 130
    except Exception as exception:
        # Source URLs are public but raw network exceptions can contain URLs or system paths.
        print(json.dumps({"event": "error", "error": "media_download_failed", "diagnostic": safe_exception_details(exception)}), flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
