"""Meaningful image invariants for the NODENO catalog retouch pipeline."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import cv2
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("media_clean", ROOT / "scripts/media-clean.py")
media = importlib.util.module_from_spec(spec)
spec.loader.exec_module(media)


class MediaCleanTests(unittest.TestCase):
    def test_brand_aliases_do_not_match_dimensions_or_product_words(self):
        for text in ["adore", "ADORE MOBİLYA", "adoremobilya.com", "адоре", "أدور", "ad0re"]:
            self.assertEqual(media.classify_brand_text(text, .95), "exact", text)
        for text in ["120 × 40 × 75 cm", "modern dolap", "store", "wood", "40KG"]:
            self.assertIsNone(media.classify_brand_text(text, .95), text)
        self.assertEqual(media.classify_brand_text("adorn", .6), "uncertain")

    def test_masked_inpaint_preserves_geometry_and_all_pixels_outside_mask(self):
        source = np.full((100, 200, 3), 215, np.uint8)
        source[:, 155:158] = (70, 90, 110)  # A real product edge must survive exactly.
        source[35:55, 55:120] = 8
        source[38:52, 60:116:7] = 245
        mask = np.zeros(source.shape[:2], np.uint8)
        mask[33:57, 53:122] = 255
        cleaned, audit = media.inpaint_preserving(source, mask)
        self.assertTrue(np.array_equal(cleaned[mask == 0], source[mask == 0]))
        self.assertLess(np.abs(cleaned[40:50, 70:110].astype(float) - 215).mean(), 6)
        self.assertEqual(audit["outsideMaskMaxDelta"], 0)
        self.assertEqual(audit["outsideMaskSsim"], 1.0)
        self.assertTrue(np.array_equal(cleaned[:, 155:158], source[:, 155:158]))

    def test_lossless_output_retains_the_outside_pixels_after_decode(self):
        rng = np.random.default_rng(42)
        source = rng.integers(0, 256, (90, 120, 3), dtype=np.uint8)
        mask = np.zeros((90, 120), np.uint8)
        mask[30:37, 50:65] = 255
        output = source.copy()
        output[mask != 0] = (180, 181, 182)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "retouch.webp"
            audit = media.save_lossless_validated(output, source, mask, path)
            self.assertEqual(audit["outsideMaskMaxDelta"], 0)
            self.assertEqual(audit["outsideMaskSsim"], 1.0)
            with Image.open(path) as decoded:
                self.assertEqual(decoded.size, (120, 90))

    def test_known_physical_badge_is_detected_at_two_sizes_and_then_rejected_as_residual(self):
        matcher = media.TemplateMatcher(ROOT / "artifacts/media-cleanup/templates")
        template = np.array(Image.open(matcher.paths[0]).convert("RGB"))
        for width in [60, 120]:
            badge = cv2.resize(template, (width, round(width * template.shape[0] / template.shape[1])))
            image = np.full((220, 360, 3), 205, np.uint8)
            image[55:55 + badge.shape[0], 170:170 + width] = badge
            hits = matcher.detect(image, extra_widths=[width])
            self.assertTrue(any(h["confidence"] >= .9 for h in hits), (width, hits))
            self.assertTrue(media.residual_brand(hits))

    def test_uniform_white_background_is_not_edited_or_template_matched(self):
        matcher = media.TemplateMatcher(ROOT / "artifacts/media-cleanup/templates")
        image = np.full((200, 300, 3), 255, np.uint8)
        self.assertEqual(matcher.detect(image), [])
        self.assertTrue(media.is_uniform(image))

    def test_orange_badge_rule_is_included_in_mask(self):
        image = np.full((120, 300, 3), 230, np.uint8)
        image[40:60, 160:230] = 5
        image[44:55:3, 166:224] = 245
        image[60:63, 160:230] = (224, 90, 20)
        detection = {"box":[160, 40, 230, 60],"source":"ocr","text":"adore","confidence":.98,"certainty":"exact"}
        mask, info = media.build_brand_mask(image, [detection])
        self.assertTrue(np.all(mask[60:63, 160:230] != 0), info)
        self.assertEqual(int(mask[80, 190]), 0)

    def test_changed_source_hash_is_rejected_before_ocr(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            original = root / "source.png"
            Image.new("RGB", (50, 50), "white").save(original)
            entry = {"path":"source.png","sha256":"0"*64,"status":"verified","frames":1}
            result = media.process_entry("a"*64, entry, root, root / "outputs", True, engines=None)
            self.assertEqual(result["state"], "failed")
            self.assertEqual(result["reason"], "source_sha_mismatch")
            self.assertFalse((root / "outputs").exists())

    def test_post_scan_residual_fails_closed_without_an_approved_output(self):
        class StillSeesBrand:
            def scan(self, rgb):
                return [{"box":[80,40,145,58],"source":"ocr","text":"adore","confidence":.99,"certainty":"exact"}], {"ocr":[]}
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = np.full((300, 600, 3), 210, np.uint8)
            source[40:58,80:145] = 5
            source[44:54:3,85:140] = 245
            path = root / "source.png"
            Image.fromarray(source).save(path)
            entry = {"path":"source.png","sha256":media.sha(path.read_bytes()),"status":"verified","frames":1,"mime":"image/png"}
            result = media.process_entry("b"*64,entry,root,root/"outputs",True,engines=StillSeesBrand())
            self.assertEqual(result["state"],"review_required")
            self.assertEqual(result["reason"],"residual_brand_after_inpaint")
            self.assertIsNone(result["path"])
            self.assertFalse((root / "outputs").exists())

    def test_multicolor_corner_is_not_hidden_by_a_majority_background_median(self):
        source = np.full((150,300,3),(65,120,95),np.uint8)
        source[40:60,20:200] = (140,100,66)
        source[60:120,185:200] = (140,100,66)
        source[39:61,145:201] = 6
        source[44:55:3,150:195] = 245
        _, regions = media.build_brand_mask(source,[{"box":[145,39,201,61],"source":"ocr","text":"adore","confidence":.99,"certainty":"exact"}])
        self.assertTrue(any(region['risks'] for region in regions),regions)

    def test_physical_plaque_cleanup_changes_only_its_own_interior(self):
        matcher=media.TemplateMatcher(ROOT/'artifacts/media-cleanup/templates')
        template=np.array(Image.open(ROOT/'artifacts/media-cleanup/templates-pending/catalog-thin-adore-badge.png').convert('RGB'))
        image=np.full((360,600,3),(70,120,95),np.uint8)
        image[50:85,20:230]=(150,95,55)
        y,x=53,170
        image[y:y+template.shape[0],x:x+template.shape[1]]=template
        detection={'box':[x,y,x+template.shape[1],y+template.shape[0]],'source':'ocr','text':'adore','confidence':.99,'certainty':'exact'}
        output,mask,info=media.clean_physical_plaque(image,[detection],matcher)
        self.assertTrue(info['accepted'],info)
        physical=np.zeros(image.shape[:2],bool)
        physical[y:y+template.shape[0],x:x+template.shape[1]]=True
        self.assertFalse(np.any((mask!=0)&~physical))
        self.assertTrue(np.array_equal(output[~physical],image[~physical]))
        self.assertTrue(np.array_equal(output[mask==0],image[mask==0]))
        self.assertFalse(matcher.detect(output,extra_widths=[template.shape[1]]))
        self.assertTrue(info['physicalPlaqueRetained'])

    def test_checkpoint_retries_temporary_windows_sharing_error_without_losing_old_json(self):
        with tempfile.TemporaryDirectory() as folder:
            target=Path(folder)/'manifest.json';target.write_text('{"old":true}',encoding='utf-8')
            original_replace=media.os.replace
            attempts=[]
            def intermittent(source,destination):
                attempts.append(1)
                if len(attempts)<=2:raise PermissionError(13,'temporarily opened by another reader')
                original_replace(source,destination)
            with mock.patch.object(media.os,'replace',side_effect=intermittent),mock.patch.object(media.time,'sleep'):
                media.atomic_json(target,{'new':True})
            self.assertEqual(len(attempts),3)
            self.assertIn('"new": true',target.read_text('utf-8'))

    def test_identical_decoded_frames_reuse_analysis_but_keep_sha_evidence(self):
        engine=object.__new__(media.Engines)
        engine.scan_config='unit-test-identical-frames'
        calls=[]
        def scan_frame(rgb):
            calls.append(rgb.shape)
            return [],{'ocr':[]}
        engine._scan_uncached=scan_frame
        image=np.random.default_rng(93).integers(0,256,(32,40,3),dtype=np.uint8)
        first=engine.scan(image)
        second=engine.scan(image.copy())
        self.assertEqual(len(calls),1)
        self.assertEqual(first[1]['decodedRgbSha256'],second[1]['decodedRgbSha256'])
        self.assertEqual(second[1]['scanReuse'],'identical_decoded_rgb_sha256')


if __name__ == "__main__":
    unittest.main()
