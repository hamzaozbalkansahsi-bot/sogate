"""Hash-bound incremental word audit over the completed physical-plaque scan.

New real word specimens are scanned independently; the expensive, frozen
physical scan is reused only for exactly matching files and decoded frames.
Neither pass can approve an image or modify the publication manifest.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import importlib.util
import json
from pathlib import Path
import threading

import cv2
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("frozen_physical_badge", ROOT / "scripts/media-physical-badge-audit.py")
physical = importlib.util.module_from_spec(spec)
spec.loader.exec_module(physical)
audit = physical.audit
BASE_PASS = "9482d713b5255b91b20ac24b7a144d2e06e6af16d1772cc46dd327cf181becd9"
BASE_DEST = physical.DEST
DEST = ROOT / "artifacts/media-complete-badge-audit"
REFERENCE_NAMES = ["bare-black-desk-word.png", "bare-shelf-word.png", "office-micro-word.png", "shelf-gray-word.png", "shelf-left-word.png", "shelf-red-front.png", "shelf-wood-front.png"]
LOCAL = threading.local()


class BareWordMatcher(physical.PhysicalBadgeMatcher):
    def __init__(self):
        self.paths = sorted((ROOT / "data/media-bare-badge-templates").glob("*.png"))
        if [path.name for path in self.paths] != REFERENCE_NAMES:
            raise ValueError("bare_word_calibration_references_missing")
        self.variants = []
        for path in self.paths:
            gray = np.array(Image.open(path).convert("L"))
            widths = sorted(set(physical.CONFIG["widths"] + [max(8, gray.shape[1]+offset) for offset in [-2,-1,0,1,2]]))
            for width in widths:
                height = max(4, round(width * gray.shape[0] / gray.shape[1]))
                self.variants.append((path.name, width, cv2.resize(gray, (width, height))))


def matcher():
    if not hasattr(LOCAL, "matcher"):
        LOCAL.matcher = BareWordMatcher()
    return LOCAL.matcher


def version():
    if physical.version() != BASE_PASS:
        raise ValueError("frozen_physical_scanner_changed")
    return audit.media.sha(Path(__file__).read_bytes() + BASE_PASS.encode() + b"".join(p.read_bytes() for p in BareWordMatcher().paths))


def scan(job, pass_version):
    report = audit.scan_file(job)
    path = BASE_DEST / "reports" / (job[0] + ".json")
    previous_body = path.read_bytes()
    previous = json.loads(previous_body)
    frames = lambda r: [(f["frame"], f["background"], f["rgbSha256"]) for f in r.get("frames", [])]
    if previous.get("fileSha256") != job[0] or previous.get("passVersion") != BASE_PASS or frames(previous) != frames(report) or previous.get("frameCount") != report["frameCount"]:
        raise ValueError("complete_frozen_physical_frame_evidence_required")
    report["upstreamPhysicalReportSha256"] = audit.media.sha(previous_body)
    report["upstreamPhysicalPass"] = BASE_PASS
    report["hits"].extend({**hit, "upstreamPhysicalHitId": hit["id"]} for hit in previous["hits"])
    report["passVersion"] = pass_version
    for hit in report["hits"]:
        hit.pop("id", None)
        hit["id"] = audit.media.sha((pass_version + job[0] + json.dumps(hit, sort_keys=True)).encode())
    report["candidateHits"] = len(report["hits"])
    for frame in report["frames"]:
        frame["hits"] = sum(h["frame"] == frame["frame"] and h["background"] == frame["background"] for h in report["hits"])
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, choices=range(1, 25), default=12)
    parser.add_argument("--checkpoint", action="store_true", help="Cache available files while upstream scan runs; never issue an incomplete receipt")
    args = parser.parse_args()
    DEST.mkdir(parents=True, exist_ok=True)
    pass_version = version()
    audit.matcher = matcher
    jobs, manifest, download, _, _ = audit.jobs_from_manifests()
    reports, todo, waiting = [], [], []
    # Validate upstream coverage before spending time on the new pass.
    for job in jobs:
        upstream = BASE_DEST / "reports" / (job[0] + ".json")
        if not upstream.exists() or json.loads(upstream.read_bytes()).get("passVersion") != BASE_PASS:
            if args.checkpoint:
                waiting.append(job[0])
                continue
            raise ValueError("complete_physical_scan_required_before_incremental_word_audit")
        path = DEST / "reports" / (job[0] + ".json")
        if path.exists():
            previous = json.loads(path.read_bytes())
            if previous.get("passVersion") == pass_version and previous.get("upstreamPhysicalReportSha256") == audit.media.sha(upstream.read_bytes()) and audit.media.sha(job[1].read_bytes()) == job[0]:
                previous["roles"] = job[3]
                reports.append(previous)
                continue
        todo.append(job)
    print(json.dumps({"event": "started", "files": len(jobs), "cached": len(reports), "waitingForUpstream": len(waiting), "passVersion": pass_version}), flush=True)
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for future in as_completed([pool.submit(scan, job, pass_version) for job in todo]):
            report = future.result()
            audit.media.atomic_json(DEST / "reports" / (report["fileSha256"] + ".json"), report)
            reports.append(report)
            if len(reports) % 200 == 0:
                print(json.dumps({"event": "progress", "files": len(reports), "total": len(jobs)}), flush=True)
    reports.sort(key=lambda r: r["fileSha256"])
    if waiting:
        print(json.dumps({"event": "checkpoint_only", "cached": len(reports), "waitingForUpstream": len(waiting), "publicationReady": False}), flush=True)
        return
    sources = {role["urlSha"] for row in reports for role in row["roles"] if role["role"] == "source"}
    outputs = {role["urlSha"] for row in reports for role in row["roles"] if role["role"] == "current_output"}
    references = physical.PhysicalBadgeMatcher().paths + BareWordMatcher().paths
    audit.DEST = DEST
    receipt = {"schemaVersion": 1, "basePipelineVersion": audit.FROZEN_PIPELINE, "passVersion": pass_version, "referenceSha256": {p.name: audit.media.sha(p.read_bytes()) for p in references}, "sourceReferences": len(download["references"]), "sourceUrlsScanned": len(sources), "currentOutputUrlsScanned": len(outputs), "allSourceUrlsScanned": sources == set(download["images"]), "uniqueFilesScanned": len(reports), "filesWithCandidateHits": sum(bool(r["hits"]) for r in reports), "publicationReady": False, "hitSheets": audit.hit_sheets(reports), "reports": [{"fileSha256": r["fileSha256"], "path": "artifacts/media-complete-badge-audit/reports/" + r["fileSha256"] + ".json", "hits": len(r["hits"]), "roles": r["roles"]} for r in reports]}
    audit.media.atomic_json(DEST / "receipt.json", receipt)
    print(json.dumps({k: v for k, v in receipt.items() if k not in {"reports", "hitSheets", "referenceSha256"}}), flush=True)


if __name__ == "__main__":
    main()
