"""Real, previously missed physical brand plaques must be detected without OCR."""
import importlib.util
from pathlib import Path
import unittest
import copy
import json
import tempfile
from unittest.mock import patch

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("small_badge", ROOT / "scripts/media-physical-badge-audit.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)
complete_spec = importlib.util.spec_from_file_location("complete_badge", ROOT / "scripts/media-complete-badge-audit.py")
complete = importlib.util.module_from_spec(complete_spec)
complete_spec.loader.exec_module(complete)


class SmallBadgeRegressionTests(unittest.TestCase):
    def test_reported_studia_magnet_is_detected_without_ocr(self):
        rgb = np.array(Image.open(ROOT / "tests/fixtures/media-badges/studia-reported.png").convert("RGB"))
        hits = audit.PhysicalBadgeMatcher().detect(rgb)
        self.assertTrue(any(h["box"][0] <= 41 and h["box"][2] >= 45 and h["box"][1] <= 27 and h["box"][3] >= 28 for h in hits), hits)

    def test_uniform_background_is_not_a_brand_hit(self):
        self.assertEqual(audit.PhysicalBadgeMatcher().detect(np.full((80, 120, 3), 255, np.uint8)), [])

    def test_bare_word_on_a_dark_shelf_endpoint_is_detected(self):
        spec=importlib.util.spec_from_file_location('bare_word',ROOT/'scripts/media-complete-badge-audit.py')
        bare=importlib.util.module_from_spec(spec);spec.loader.exec_module(bare)
        rgb=np.array(Image.open(ROOT/'tests/fixtures/media-badges/bare-shelf-word.png').convert('RGB'))
        self.assertTrue(bare.BareWordMatcher().detect(rgb))

    def test_extended_real_shelf_and_background_fields_are_detected(self):
        matcher = complete.BareWordMatcher()
        for path in sorted((ROOT / "tests/fixtures/media-badges").glob("extended-*.png")):
            with self.subTest(field=path.name):
                rgb = np.array(Image.open(path).convert("RGB"))
                self.assertTrue(any(h["box"][0] <= 14 and h["box"][2] >= rgb.shape[1]-14 and h["box"][1] <= 14 and h["box"][3] >= rgb.shape[0]-14 for h in matcher.detect(rgb)))

    def test_all_sixteen_reported_gallery_fields_are_detected_without_hash_denylist(self):
        matcher = audit.PhysicalBadgeMatcher()
        for path in sorted((ROOT / "tests/fixtures/media-badges").glob("[0-9]*.png")):
            with self.subTest(field=path.stem):
                rgb = np.array(Image.open(path).convert("RGB"))
                hits = matcher.detect(rgb)
                self.assertTrue(any(h["box"][0] < rgb.shape[1]-10 and h["box"][2] > 10 and h["box"][1] < rgb.shape[0]-10 and h["box"][3] > 10 for h in hits), hits)

    def test_five_real_plaques_are_all_reported_in_a_single_frame(self):
        plaque=np.array(Image.open(ROOT / "data/media-badge-templates/studia-oblique.png").convert("RGB"))
        rgb=np.full((60,400,3),255,np.uint8)
        for x in [10,80,150,220,290]:
            rgb[20:20+plaque.shape[0],x:x+plaque.shape[1]]=plaque
        matcher=audit.PhysicalBadgeMatcher()
        matcher.variants=[variant for variant in matcher.variants if variant[0]=='studia-oblique.png' and variant[1]==plaque.shape[1]]
        hits=matcher.detect(rgb)
        for x in [10,80,150,220,290]:
            self.assertTrue(any(abs(h["box"][0]-x)<=1 and abs(h["box"][1]-20)<=1 for h in hits),(x,hits))


class CompleteEvidenceTests(unittest.TestCase):
    def test_incremental_audit_preserves_upstream_hits_and_frame_identity(self):
        frame = {"frame": 0, "background": "opaque", "rgbSha256": "b"*64, "hits": 1}
        hit = {"id": "c"*64, "frame": 0, "background": "opaque", "box": [1, 2, 15, 8], "template": "real.png", "confidence": .99}
        prior = {"fileSha256": "a"*64, "passVersion": complete.BASE_PASS, "frameCount": 1, "frames": [frame], "hits": [hit]}
        fresh = {"fileSha256": "a"*64, "frameCount": 1, "frames": [copy.deepcopy(frame)], "hits": [{**hit, "id": "d"*64, "template": "new.png"}]}
        with tempfile.TemporaryDirectory() as folder:
            dest = Path(folder);(dest / "reports").mkdir();body = json.dumps(prior).encode();(dest / "reports" / ("a"*64+".json")).write_bytes(body)
            with patch.object(complete, "BASE_DEST", dest), patch.object(complete.audit, "scan_file", return_value=fresh):
                result = complete.scan(("a"*64, None, None, []), "e"*64)
        self.assertEqual(result["candidateHits"], 2)
        self.assertEqual(result["frames"][0]["hits"], 2)
        self.assertEqual(result["hits"][1]["upstreamPhysicalHitId"], "c"*64)
        self.assertEqual(result["upstreamPhysicalReportSha256"], complete.audit.media.sha(body))
        self.assertEqual(len({h["id"] for h in result["hits"]}), 2)

    def test_incremental_audit_rejects_changed_decoded_frame(self):
        prior = {"fileSha256": "a"*64, "passVersion": complete.BASE_PASS, "frameCount": 1, "frames": [{"frame": 0, "background": "opaque", "rgbSha256": "b"*64}], "hits": []}
        fresh = copy.deepcopy(prior);fresh["frames"][0]["rgbSha256"] = "f"*64
        with tempfile.TemporaryDirectory() as folder:
            dest = Path(folder);(dest / "reports").mkdir();(dest / "reports" / ("a"*64+".json")).write_text(json.dumps(prior))
            with patch.object(complete, "BASE_DEST", dest), patch.object(complete.audit, "scan_file", return_value=fresh):
                with self.assertRaisesRegex(ValueError, "frame_evidence_required"):
                    complete.scan(("a"*64, None, None, []), "e"*64)


if __name__ == "__main__":
    unittest.main()
