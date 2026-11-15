import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("media_gaming_review", ROOT / "scripts/media-gaming-review.py")
gaming = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gaming)


class GamingReviewTests(unittest.TestCase):
    def test_related_chair_galleries_and_every_gaming_desk_are_in_scope(self):
        catalog = {"products": [{"id": "4583", "title": "Oyuncu Masası"}, {"id": "4934", "title": "ProX Ergo Oyuncu Koltuğu"}, {"id": "4935", "title": "ProX Ergo Oyuncu Koltuğu"}, {"id": "4936", "title": "ProX Ergo Oyuncu Koltuğu"}, {"id": "7", "title": "Normal yemek masası"}]}
        self.assertEqual({str(p["id"]) for p in gaming.family_products(catalog)}, {"4583", "4934", "4935", "4936"})

    def test_actual_source_texture_is_copied_only_inside_mask_and_alpha_never_changes(self):
        random = np.random.default_rng(7)
        rgba = np.concatenate([random.integers(20, 60, (100, 100, 3), dtype=np.uint8), np.full((100, 100, 1), 255, np.uint8)], axis=2)
        original = rgba.copy()
        mask = np.zeros((100, 100), np.uint8)
        mask[10:20, 10:20] = 255
        output = gaming.texture_shift(rgba, mask, [30, 0])
        self.assertTrue(np.array_equal(output[10:20, 10:20, :3], original[10:20, 40:50, :3]))
        self.assertTrue(np.array_equal(output[mask == 0], original[mask == 0]))
        self.assertTrue(np.array_equal(output[:, :, 3], original[:, :, 3]))
        self.assertTrue(np.array_equal(rgba, original))
        with self.assertRaises(ValueError):
            gaming.texture_shift(rgba, mask, [-20, 0])
        rgba[10:20, 40:50, :3] = 255
        with self.assertRaises(ValueError):
            gaming.texture_shift(rgba, mask, [30, 0])

    def test_print_mask_preserves_unprinted_gray_material_and_structural_edges(self):
        rgba = np.full((120, 160, 4), 80, np.uint8)
        rgba[:, :, 3] = 255
        rgba[53:57, 65:69, :3] = 210
        rgba[53:57, 80:85, :3] = [190, 70, 25]
        mask = gaming.ink_mask(rgba, [[30, 49], [120, 49], [120, 61], [30, 61]])
        self.assertTrue(np.any(mask[53:57, 65:69]))
        self.assertTrue(np.any(mask[53:57, 80:85]))
        self.assertEqual(mask[51, 40], 0)
        self.assertEqual(mask[59, 110], 0)

    def test_exact_rgb_frame_cache_reuses_work_but_never_confuses_changed_frames(self):
        rgb = np.full((20, 20, 3), 30, np.uint8)
        class Matcher:
            calls = 0
            def detect(self, image):
                self.calls += 1
                return [{"pixel": int(image[0, 0, 0])}]
        detector = Matcher()
        with patch.object(gaming, "matcher", return_value=detector):
            first = gaming.cached_detect(rgb)
            self.assertEqual(gaming.cached_detect(rgb.copy()), first)
            self.assertEqual(detector.calls, 1)
            changed = rgb.copy(); changed[0, 0, 0] = 31
            self.assertNotEqual(gaming.cached_detect(changed), first)
            self.assertEqual(detector.calls, 2)

    def test_blue_source_illumination_is_kept_in_small_leg_print_fill(self):
        rgb = np.full((220, 220, 3), 255, np.uint8)
        rgb[20:200, 90:105] = [4, 36, 91]
        rgb[20:200, 105:110] = [8, 1, 20]
        mask = np.zeros((220, 220), np.uint8)
        mask[60:130, 96:101] = 255
        rgb[mask != 0] = [240, 180, 70]
        output = gaming.source_row_retouch(rgb, mask)
        self.assertTrue(np.all(output[mask != 0] == [4, 36, 91]))
        self.assertTrue(np.array_equal(output[mask == 0], rgb[mask == 0]))


if __name__ == "__main__":
    unittest.main()
