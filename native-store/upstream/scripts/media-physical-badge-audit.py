"""Supplement the frozen badge scan with real Studia plaque specimens.

Read-only: produces candidates, never image approvals. The old scan and reports
stay unchanged. Every decoded frame and alpha composite remains hash-bound.
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
spec = importlib.util.spec_from_file_location("physical_legacy", ROOT / "scripts/media-small-badge-audit.py")
legacy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(legacy)
audit = legacy.audit
DEST = ROOT / "artifacts/media-physical-badge-audit"
CONFIG = {
    "widths": [8,10,12,14,16,18,20,22,24,26,28,32,36,40],
    "score": .90, "smallScore": .98, "ambiguousScore": .98,
    "ambiguousReferences": ["studia-life.png", "studia-open-front.png"],
    "minContrast": 35, "peakPolicy": "exhaustive",
    "references": ["adore-physical-badge.png", "catalog-thin-adore-badge.png", "ktp-desk.png", "ktp-top.png", "shc-life.png", "studia-angle.png", "studia-computer-angle.png", "studia-computer-front.png", "studia-flat.png", "studia-front.png", "studia-laptop-angle.png", "studia-life-front.png", "studia-life.png", "studia-oblique.png", "studia-open-front.png", "studia-open-side.png", "studia-small-life.png", "studia-small.png", "tiny-collapsed-word.png", "tiny-oblique-word.png", "tiny-real-badge.png"]
}
LOCAL = threading.local()


class PhysicalBadgeMatcher:
    def __init__(self):
        self.paths = sorted((ROOT / "data/media-badge-templates").glob("*.png"))
        if [path.name for path in self.paths] != CONFIG["references"]:
            raise ValueError("physical_badge_calibration_references_missing")
        self.variants = []
        for path in self.paths:
            original = np.array(Image.open(path).convert("L"))
            native_width = original.shape[1]
            widths = sorted(set(CONFIG["widths"] + [max(8, native_width + offset) for offset in [-2,-1,0,1,2]]))
            for width in widths:
                height = max(4, round(width * original.shape[0] / original.shape[1]))
                template = cv2.resize(original, (width, height))
                self.variants.append((path.name, width, template))

    def detect(self, rgb, targeted=False):
        gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
        if int(gray.max()) - int(gray.min()) < 8:
            return []
        found, contrast_masks = [], {}
        for name, width, template in self.variants:
            h, w = template.shape
            if h >= gray.shape[0] or w >= gray.shape[1]:
                continue
            scores = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)
            threshold = CONFIG["smallScore"] if width < 12 else CONFIG["ambiguousScore"] if name in CONFIG["ambiguousReferences"] else CONFIG["score"]
            if (h,w) not in contrast_masks:
                contrast = cv2.morphologyEx(gray, cv2.MORPH_GRADIENT, np.ones((h,w),np.uint8), anchor=(0,0))
                contrast_masks[(h,w)] = contrast[:scores.shape[0],:scores.shape[1]] < CONFIG["minContrast"]
            scores[contrast_masks[(h,w)]] = -1
            while True:
                _, score, _, point = cv2.minMaxLoc(scores)
                if not np.isfinite(score) or score < threshold:
                    break
                x, y = point
                crop = gray[y:y+h, x:x+w]
                if int(crop.max()) - int(crop.min()) >= CONFIG["minContrast"]:
                    found.append({"box": [x, y, x + w, y + h], "confidence": round(score, 6), "template": name, "scaleWidth": width, "rotation": 0, "kind": "physical_word_plaque_candidate", "visualAccepted": False})
                scores[max(0, y-h//2):y+h//2+1, max(0, x-w//2):x+w//2+1] = -1
        kept = []
        for hit in sorted(found, key=lambda h: h["confidence"], reverse=True):
            if not any(audit.media.box_iou(hit["box"], previous["box"]) > .2 for previous in kept):
                kept.append(hit)
        return kept


def matcher():
    if not hasattr(LOCAL, "matcher"):
        LOCAL.matcher = PhysicalBadgeMatcher()
    return LOCAL.matcher


def version():
    paths = sorted(PhysicalBadgeMatcher().paths + legacy.SmallBadgeMatcher().paths)
    # A helper implementation change invalidates cached frame results too.
    code = b"".join((ROOT / "scripts" / name).read_bytes() for name in ["media-physical-badge-audit.py", "media-small-badge-audit.py", "media-symbol-audit.py", "media-clean.py"])
    return audit.media.sha(code + json.dumps(CONFIG, sort_keys=True).encode() + b"".join(p.read_bytes() for p in paths))


def scan(job, pass_version):
    report = audit.scan_file(job)
    # Reuse the exact frozen legacy report only for the same immutable file.
    previous_path = legacy.DEST / "reports" / (job[0] + ".json")
    if previous_path.exists():
        previous = json.loads(previous_path.read_bytes())
        if previous.get("passVersion") != "b5f2f3ed18e09a9d94a1de57d564204cf68b1aa0d437525ddb49420da814c117" or previous.get("fileSha256") != job[0] or previous.get("frames") != report["frames"]:
            # scanReuse/hit counts are operational fields, not frame identity.
            old_frames = [(x["frame"], x["background"], x["rgbSha256"]) for x in previous.get("frames", [])]
            new_frames = [(x["frame"], x["background"], x["rgbSha256"]) for x in report["frames"]]
            if previous.get("passVersion") != "b5f2f3ed18e09a9d94a1de57d564204cf68b1aa0d437525ddb49420da814c117" or previous.get("fileSha256") != job[0] or old_frames != new_frames:
                raise ValueError("frozen_legacy_badge_report_mismatch")
        report["legacyReportSha256"] = audit.media.sha(previous_path.read_bytes())
        report["hits"].extend({**h, "legacyHitId": h["id"]} for h in previous["hits"])
    else:
        # Changed outputs have no frozen report; scan every decoded composite.
        old_matcher = legacy.SmallBadgeMatcher()
        with Image.open(job[1]) as image:
            for frame in report["frames"]:
                image.seek(frame["frame"])
                canvas = Image.new("RGBA", image.size, frame["background"])
                canvas.alpha_composite(image.convert("RGBA"))
                report["hits"].extend({**h, "frame": frame["frame"], "background": frame["background"]} for h in old_matcher.detect(np.array(canvas.convert("RGB"))))
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
    args = parser.parse_args()
    DEST.mkdir(parents=True, exist_ok=True)
    pass_version = version()
    audit.matcher = matcher
    jobs, manifest, download, _, _ = audit.jobs_from_manifests()
    reports, todo = [], []
    for job in jobs:
        path = DEST / "reports" / (job[0] + ".json")
        if path.exists():
            previous = json.loads(path.read_bytes())
            if previous.get("passVersion") == pass_version and audit.media.sha(job[1].read_bytes()) == job[0]:
                previous["roles"] = job[3]
                reports.append(previous)
                continue
        todo.append(job)
    print(json.dumps({"event": "started", "files": len(jobs), "cached": len(reports), "passVersion": pass_version}), flush=True)
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for future in as_completed([pool.submit(scan, job, pass_version) for job in todo]):
            report = future.result()
            audit.media.atomic_json(DEST / "reports" / (report["fileSha256"] + ".json"), report)
            reports.append(report)
            if len(reports) % 100 == 0:
                print(json.dumps({"event": "progress", "files": len(reports), "total": len(jobs), "hitFiles": sum(bool(r["hits"]) for r in reports)}), flush=True)
    reports.sort(key=lambda r: r["fileSha256"])
    audit.DEST = DEST
    sources = {role["urlSha"] for r in reports for role in r["roles"] if role["role"] == "source"}
    outputs = {role["urlSha"] for r in reports for role in r["roles"] if role["role"] == "current_output"}
    receipt = {"schemaVersion": 1, "basePipelineVersion": audit.FROZEN_PIPELINE, "passVersion": pass_version, "referenceSha256": {p.name: audit.media.sha(p.read_bytes()) for p in PhysicalBadgeMatcher().paths}, "sourceReferences": len(download["references"]), "sourceUrlsScanned": len(sources), "currentOutputUrlsScanned": len(outputs), "allSourceUrlsScanned": sources == set(download["images"]), "uniqueFilesScanned": len(reports), "filesWithCandidateHits": sum(bool(r["hits"]) for r in reports), "publicationReady": False, "hitSheets": audit.hit_sheets(reports), "reports": [{"fileSha256": r["fileSha256"], "path": "artifacts/media-physical-badge-audit/reports/" + r["fileSha256"] + ".json", "hits": len(r["hits"]), "roles": r["roles"]} for r in reports]}
    audit.media.atomic_json(DEST / "receipt.json", receipt)
    print(json.dumps({k: v for k, v in receipt.items() if k not in {"reports", "hitSheets", "referenceSha256"}}), flush=True)


if __name__ == "__main__":
    main()
