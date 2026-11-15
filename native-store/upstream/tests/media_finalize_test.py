"""Small offline fixtures for the final visual-selection and publication gate."""
import copy
import importlib.util
import json
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("media_finalize", ROOT / "scripts/finalize-media.py")
media = importlib.util.module_from_spec(spec)
spec.loader.exec_module(media)


class MediaFinalizeTests(unittest.TestCase):
    def test_nonfixture_changed_reference_count_still_requires_whole_object_gate(self):
        finalizer=self.merge();self.symbol_receipt(finalizer)
        finalizer.isolated_test_fixture=False
        with self.assertRaisesRegex(media.FinalizeError,'current_whole_object_publication_evidence_required'):
            self.publish(finalizer)
    def test_identical_footprint_for_duplicate_source_urls_is_unambiguous(self):
        pin={'sourceSha256':'a'*64,'outputSha256':'b'*64,'maskSha256':'c'*64,'outputRgbaSha256':'d'*64}
        with mock.patch.object(media,'OBJECT_POLICY',{'footprintExceptions':[pin,copy.deepcopy(pin)]}):
            self.assertEqual(media.object_footprint_pin({'sha256':'a'*64},{'outputSha':'b'*64},{'maskSha':'c'*64}),pin)
        with mock.patch.object(media,'OBJECT_POLICY',{'footprintExceptions':[pin,{**pin,'outputRgbaSha256':'e'*64}]}):
            with self.assertRaises(media.FinalizeError):media.object_footprint_pin({'sha256':'a'*64},{'outputSha':'b'*64},{'maskSha':'c'*64})
    def test_publish_and_verify_cannot_bypass_missing_production_whole_object_review(self):
        finalizer=self.merge()
        self.symbol_receipt(finalizer)
        proposed=self.publish(finalizer)
        finalizer.reference_count=media.OBJECT_POLICY['referenceCount']
        with self.assertRaisesRegex(media.FinalizeError,'whole_object'):
            self.publish(finalizer)
        for relative,body in finalizer.evidence_copies.items():media.immutable_write(self.root,relative,body)
        self.write('artifacts/media-cleanup.json',proposed)
        reopened=self.finalizer();reopened.reference_count=media.OBJECT_POLICY['referenceCount']
        with self.assertRaisesRegex(media.FinalizeError,'whole_object'):
            reopened.verify_published()
    def test_production_whole_object_publish_requires_all_source_supplemental_scan(self):
        finalizer=self.merge();self.symbol_receipt(finalizer);row=finalizer.manifest['images'][self.key];pixels=np.array(Image.open(self.root/row['path']).convert('RGBA'));rgba_sha=media.sha(pixels.tobytes());policy={'version':'whole-object-v1','referenceCount':1,'required':{self.key:{'sourceSha256':row['sourceSha'],'acceptedOutputSha256':row['outputSha'],'outputRgbaSha256':rgba_sha,'fields':[]}},'rejectedOutputSha256':[],'footprintExceptions':[],'supplementalPass':'test-extra','supplementalReferences':{'observed.png':'a'*64}};policy_bytes=media.json_bytes(policy);receipt={'version':'whole-object-v1','images':{self.key:{'sourceSha256':row['sourceSha'],'outputSha256':row['outputSha'],'outputRgbaSha256':rgba_sha,'width':20,'height':20,'reviewer':'actual fixture visual review','fields':[]}}};path='artifacts/media-finalization/whole-object-test.json';self.write(path,receipt);finalizer.manifest['wholeObjectAudit']={'policySha256':media.sha(policy_bytes),'receiptPath':path,'receiptSha256':media.sha((self.root/path).read_bytes())}
        with mock.patch.object(media,'OBJECT_POLICY',policy),mock.patch.object(media,'OBJECT_POLICY_BYTES',policy_bytes):
            with self.assertRaisesRegex(media.FinalizeError,'supplemental'):
                self.publish(finalizer)
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="nodeno-finalize-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        (self.root / "data").mkdir()
        self.url = "https://witcdn.adoremobilya.com/fixture.png"
        self.key = media.sha(self.url.encode())
        self.source_path = "artifacts/media-originals/" + self.key + ".png"
        self.candidate_path = "artifacts/media-review/" + self.key + ".png"
        self.mask_path = "artifacts/media-review/" + self.key + "-mask.png"
        source = np.full((20, 20, 4), [40, 50, 60, 255], np.uint8)
        output = source.copy()
        output[2, 2, :3] = [20, 30, 40]
        self.save_image(self.source_path, source)
        self.save_image(self.candidate_path, output)
        mask = np.zeros((20, 20), np.uint8)
        mask[2, 2] = 255
        self.save_image(self.mask_path, mask)
        self.source = {"status": "verified", "url": self.url, "path": self.source_path, "sha256": media.sha((self.root / self.source_path).read_bytes()), "bytes": (self.root / self.source_path).stat().st_size, "width": 20, "height": 20, "mime": "image/png"}
        self.candidate = {"sourceSha": self.source["sha256"], "sourcePath": self.source_path, "path": self.candidate_path, "outputSha": media.sha((self.root / self.candidate_path).read_bytes()), "bytes": (self.root / self.candidate_path).stat().st_size, "width": 20, "height": 20, "mime": "image/png", "maskPath": self.mask_path, "maskSha": media.sha((self.root / self.mask_path).read_bytes()), "state": "candidate_ready", "postDetections": [], "postScan": {"ocr": [], "templateHits": []}}
        self.report_path = "artifacts/media-cleanup/reports/" + self.key + ".json"
        self.row = {"state": "review_required", "sourceSha": self.source["sha256"], "sourcePath": self.source_path, "sourceBytes": self.source["bytes"], "outputSha": None, "path": None, "width": 20, "height": 20, "report": self.report_path, "pipelineVersion": media.FROZEN}
        self.write(self.report_path, {**self.row, "key": self.key})
        self.write("data/catalog-source.json", {"products": [{"id": "7", "images": [self.url]}]})
        self.write("artifacts/media-download.json", {"schemaVersion": 1, "references": {"7:0": self.key}, "images": {self.key: self.source}})
        self.write("artifacts/media-cleanup.json", {"schemaVersion": 1, "pipelineVersion": media.FROZEN, "publicationReady": False, "references": {"7:0": self.key}, "images": {self.key: self.row}})
        self.write_candidates()
        self.selection = {"candidateSha": self.candidate["outputSha"], "reviewer": "root-fixture", "notes": "Full image and close-up structure inspected in test fixture", "structureReview": True}
        self.write_selections()

    def write(self, path, value):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(media.json_bytes(value))

    def save_image(self, path, array):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        Image.fromarray(array).save(target)

    def write_candidates(self):
        self.write("artifacts/candidates.json", {"pipelineVersion": media.FROZEN, "publicationReady": False, "images": {self.key: self.candidate}})

    def write_selections(self):
        self.write("artifacts/selections.json", {"schemaVersion": 1, "basePipelineVersion": media.FROZEN, "selections": {self.key: self.selection}})

    def finalizer(self):
        return media.Finalizer(self.root, expected_references=1, isolated_test_fixture=True)

    def merge(self):
        finalizer = self.finalizer()
        proposed, copies = finalizer.prepare(["artifacts/candidates.json"], "artifacts/selections.json")
        finalizer.write_merge(proposed, copies)
        return self.finalizer()

    def publish(self, finalizer):
        return finalizer.publish("artifacts/symbol-receipt.json", "artifacts/dispositions.json", "artifacts/small-badge-receipt.json", "artifacts/small-badge-dispositions.json")

    def symbol_receipt(self, finalizer, source_hit=True, output_hit=False, family="flame"):
        row = finalizer.manifest["images"][self.key]
        version = media.FLAME_PASS if family == "flame" else media.SMALL_BADGE_PASS
        references = media.FLAME_REFERENCES if family == "flame" else media.SMALL_BADGE_REFERENCES
        receipt_path = "artifacts/symbol-receipt.json" if family == "flame" else "artifacts/small-badge-receipt.json"
        dispositions_path = "artifacts/dispositions.json" if family == "flame" else "artifacts/small-badge-dispositions.json"
        reports, decisions = [], {}
        for role, file_sha, path in [("source", self.source["sha256"], self.source_path), ("current_output", row["outputSha"], row["path"])]:
            hit = (source_hit if role == "source" else output_hit)
            hits = [{"id": media.sha((file_sha + role).encode()), "frame": 0, "background": "white", "box": [2, 2, 3, 3]}] if hit else []
            bindings = media.symbol_frame_bindings(self.root / path)
            report = {"fileSha256": file_sha, "passVersion": version, "candidateHits": len(hits), "hits": hits, "frameCount": len({index for index, _ in bindings}), "compositesScanned": len(bindings), "frames": [{"frame": index, "background": background, "rgbSha256": sha} for (index, background), sha in bindings.items()]}
            report_path = "artifacts/" + family + "-reports/" + file_sha + ".json"
            self.write(report_path, report)
            report_sha = media.sha((self.root / report_path).read_bytes())
            reports.append({"fileSha256": file_sha, "path": report_path, "hits": len(hits), "roles": [{"urlSha": self.key, "role": role, "path": path}]})
            if hits:
                decisions[hits[0]["id"]] = {"fileSha256": file_sha, "reportSha256": report_sha, "reviewer": "root-fixture", "notes": "Exact hit crop visually reviewed", "visualReview": True, "disposition": "true_brand_cleaned" if role == "source" else "false_positive", **({"cleanedOutputs": {self.key: row["outputSha"]}} if role == "source" else {})}
        receipt = {"schemaVersion": 1, "basePipelineVersion": media.FROZEN, "passVersion": version, "referenceSha256": copy.deepcopy(references), "allSourceUrlsScanned": True, "sourceReferences": 1, "reports": reports}
        self.write(receipt_path, receipt)
        dispositions = {"schemaVersion": 1, "basePipelineVersion": media.FROZEN, "passVersion": version, "receiptSha256": media.sha((self.root / receipt_path).read_bytes()), "hits": decisions}
        self.write(dispositions_path, dispositions)
        if family == "flame":
            self.symbol_receipt(finalizer, source_hit, output_hit, family="small_badge")
        return receipt, dispositions

    def test_plan_does_not_write_and_merge_preserves_frozen_audits_and_gate_false(self):
        finalizer = self.finalizer()
        original = finalizer.path.read_bytes()
        original_report = (self.root / self.report_path).read_bytes()
        proposed, copies = finalizer.prepare(["artifacts/candidates.json"], "artifacts/selections.json")
        self.assertEqual(finalizer.path.read_bytes(), original)
        self.assertFalse(proposed["publicationReady"])
        finalizer.write_merge(proposed, copies)
        merged = self.finalizer()
        self.assertFalse(merged.manifest["publicationReady"])
        row = merged.manifest["images"][self.key]
        self.assertEqual(row["state"], "approved_cleaned")
        self.assertEqual(Path(row["path"]).stem, row["outputSha"])
        self.assertEqual((self.root / self.report_path).read_bytes(), original_report)
        self.assertEqual((self.root / merged.manifest["frozen37fb"]["manifestPath"]).read_bytes(), original)

    def test_confirmed_bad_image_is_blocked_even_if_a_scanner_has_no_hits(self):
        finalizer = self.merge()
        bad_sha = finalizer.manifest["images"][self.key]["outputSha"]
        media.KNOWN_BRAND_FILES.add(bad_sha)
        try:
            with self.assertRaisesRegex(media.FinalizeError, "known_reported_brand"):
                finalizer.verify_final_images()
        finally:
            media.KNOWN_BRAND_FILES.discard(bad_sha)

    def test_published_evidence_is_revalidated_and_stale_boolean_is_rejected(self):
        finalizer = self.merge()
        self.symbol_receipt(finalizer)
        proposed = self.publish(finalizer)
        for relative, body in finalizer.evidence_copies.items():
            media.immutable_write(self.root, relative, body)
        self.write("artifacts/media-cleanup.json", proposed)
        self.finalizer().verify_published()
        proposed["publicationAudit"]["manifestBindingSha256"] = "a" * 64
        self.write("artifacts/media-cleanup.json", proposed)
        with self.assertRaisesRegex(media.FinalizeError, "publication_evidence"):
            self.finalizer().verify_published()

    def test_missing_visual_selection_cannot_approve_existing_machine_cleaned(self):
        report = {**self.row, **self.candidate, "state": "approved_cleaned", "pipelineVersion": media.FROZEN}
        self.write(self.report_path, report)
        main, _ = media.read_json(self.root / "artifacts/media-cleanup.json")
        main["images"][self.key] = {**report, "report": self.report_path}
        self.write("artifacts/media-cleanup.json", main)
        proposed, _ = self.finalizer().prepare([])
        self.assertEqual(proposed["images"][self.key]["state"], "review_required")
        for field, value in [("reviewer", ""), ("notes", None), ("structureReview", False), ("candidateSha", "a" * 64)]:
            invalid = copy.deepcopy(self.selection)
            invalid[field] = value
            self.write("artifacts/selections.json", {"schemaVersion": 1, "basePipelineVersion": media.FROZEN, "selections": {self.key: invalid}})
            with self.assertRaises(media.FinalizeError):
                self.finalizer().prepare(["artifacts/candidates.json"], "artifacts/selections.json")

    def test_hash_outside_alpha_dimensions_and_unbounded_masks_reject(self):
        original = np.array(Image.open(self.root / self.candidate_path).convert("RGBA"))
        for fault in ("outside", "alpha", "dimensions", "whole_mask"):
            candidate = copy.deepcopy(self.candidate)
            changed = original.copy()
            if fault == "outside":
                changed[15, 15, :3] = [1, 2, 3]
            elif fault == "alpha":
                changed[2, 2, 3] = 254
            elif fault == "dimensions":
                changed = changed[:, :-1]
            else:
                self.save_image(self.mask_path, np.full((20, 20), 255, np.uint8))
                candidate["maskSha"] = media.sha((self.root / self.mask_path).read_bytes())
            self.save_image(self.candidate_path, changed)
            candidate.update(outputSha=media.sha((self.root / self.candidate_path).read_bytes()), bytes=(self.root / self.candidate_path).stat().st_size, width=changed.shape[1])
            with self.assertRaises(media.FinalizeError, msg=fault):
                media.validate_candidate(self.root, self.source, candidate)
        (self.root / self.source_path).write_bytes(b"changed immutable source")
        with self.assertRaises(media.FinalizeError):
            self.finalizer()

    def test_visible_translucent_print_can_change_rgb_while_alpha_and_invisible_rgb_stay_exact(self):
        source = np.array(Image.open(self.root / self.source_path).convert("RGBA"))
        source[2, 2, 3] = 244
        source[0, 0, 3] = 0
        output = source.copy()
        output[2, 2, :3] = [20, 30, 40]
        self.save_image(self.source_path, source)
        self.save_image(self.candidate_path, output)
        source_record = {**self.source, "sha256": media.sha((self.root / self.source_path).read_bytes()), "bytes": (self.root / self.source_path).stat().st_size}
        candidate = {**self.candidate, "sourceSha": source_record["sha256"], "outputSha": media.sha((self.root / self.candidate_path).read_bytes()), "bytes": (self.root / self.candidate_path).stat().st_size}
        media.validate_candidate(self.root, source_record, candidate)
        output[2, 2, 3] = 245
        self.save_image(self.candidate_path, output)
        candidate.update(outputSha=media.sha((self.root / self.candidate_path).read_bytes()), bytes=(self.root / self.candidate_path).stat().st_size)
        with self.assertRaisesRegex(media.FinalizeError, "alpha_changed"):
            media.validate_candidate(self.root, source_record, candidate)

    def test_fully_invisible_pixels_cannot_be_selected_for_retouch(self):
        source = np.full((3, 3, 4), [20, 30, 40, 255], np.uint8)
        source[1, 1, 3] = 0
        output = source.copy()
        output[1, 1, :3] = [0, 0, 0]
        mask = np.zeros((3, 3), bool)
        mask[1, 1] = True
        with self.assertRaisesRegex(media.FinalizeError, "mask_intersects_transparency"):
            media.compare_frame(source, output, mask)

    def test_known_machine_residuals_and_unresolved_candidates_cannot_be_selected(self):
        for change in [{"state": "rejected_residual_brand"}, {"reason": "rejected_residual_brand"}, {"state": "review_required"}, {"postDetections": [{"text": "adore"}]}, {"postDetectionCount": 1}, {"postFlameHitCount": 1}, {"postGamingHitCount": 1}, {"postGamingTemplates": [{"score": 1}]}, {"postScan": {"templateHits": [{"score": 1}]}}]:
            with self.assertRaises(media.FinalizeError):
                media.validate_candidate(self.root, self.source, {**self.candidate, **change})
        bindings = media.symbol_frame_bindings(self.root / self.source_path)
        actual_rgb = Image.open(self.root / self.source_path).convert("RGB").tobytes()
        self.assertEqual(bindings[(0, "white")], hashlib.sha256(b"((20, 20, 3), 'uint8')" + actual_rgb).hexdigest())

    def test_color_profile_and_display_orientation_are_preserved(self):
        from PIL import ImageCms
        profile = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
        source_path = self.root / self.source_path
        with Image.open(source_path) as image:
            image.save(source_path, icc_profile=profile)
        source = {**self.source, "sha256": media.sha(source_path.read_bytes()), "bytes": source_path.stat().st_size}
        candidate = {**self.candidate, "sourceSha": source["sha256"]}
        with self.assertRaisesRegex(media.FinalizeError, "profile"):
            media.validate_candidate(self.root, source, candidate)
        output_path = self.root / self.candidate_path
        with Image.open(output_path) as image:
            image.save(output_path, icc_profile=profile)
        candidate.update(outputSha=media.sha(output_path.read_bytes()), bytes=output_path.stat().st_size)
        media.validate_candidate(self.root, source, candidate)
        with Image.open(output_path) as image:
            exif = image.getexif(); exif[274] = 6
            image.save(output_path, icc_profile=profile, exif=exif)
        candidate.update(outputSha=media.sha(output_path.read_bytes()), bytes=output_path.stat().st_size)
        with self.assertRaisesRegex(media.FinalizeError, "orientation"):
            media.validate_candidate(self.root, source, candidate)

    def test_gaming_template_false_positive_needs_exact_hit_and_output_visual_review(self):
        candidate = copy.deepcopy(self.candidate)
        hit = {"box": [10, 15, 15, 16], "confidence": .89, "kind": "stylized_joined_brand_candidate"}
        candidate["postGamingTemplates"] = [hit]
        with self.assertRaises(media.FinalizeError):
            media.validate_candidate(self.root, self.source, candidate)
        candidate["postGamingTemplateReview"] = {**self.selection, "visualReview": True, "disposition": "false_positive", "falsePositiveHitHashes": [media.sha(media.json_bytes({"frame": None, "hit": hit}))]}
        media.validate_candidate(self.root, self.source, candidate)
        candidate["postGamingTemplateReview"]["candidateSha"] = "a" * 64
        with self.assertRaises(media.FinalizeError):
            media.validate_candidate(self.root, self.source, candidate)

    def test_joined_adoregaming_residuals_block_even_when_frozen_classifier_missed_them(self):
        for text in ["AdoreGaming", "doregaming", "sdoregaming", "ADOR GAMING", "adoregame"]:
            candidate = copy.deepcopy(self.candidate)
            candidate["postScan"]["ocr"] = [{"text": text}]
            with self.assertRaisesRegex(media.FinalizeError, "joined_brand", msg=text):
                media.validate_candidate(self.root, self.source, candidate)
        candidate = copy.deepcopy(self.candidate)
        candidate["postScan"]["ocr"] = [{"text": "Gaming desk"}]
        media.validate_candidate(self.root, self.source, candidate)

    def test_known_joined_source_word_revokes_automatic_unmodified_without_any_override(self):
        body = (self.root / self.source_path).read_bytes()
        clean_path = "artifacts/media-cleaned/" + self.key + ".png"
        (self.root / clean_path).parent.mkdir(parents=True)
        (self.root / clean_path).write_bytes(body)
        report, _ = media.read_json(self.root / self.report_path)
        report["scan"] = {"frames": [{"frame": 4, "ocr": [{"text": "doregaming"}]}]}
        self.write(self.report_path, report)
        main, _ = media.read_json(self.root / "artifacts/media-cleanup.json")
        main["images"][self.key].update(state="approved_unmodified", path=clean_path, outputSha=self.source["sha256"], mime="image/png", bytes=len(body))
        self.write("artifacts/media-cleanup.json", main)
        proposed, _ = self.finalizer().prepare([])
        self.assertEqual(proposed["images"][self.key]["state"], "review_required")
        self.assertIn("joined_brand", proposed["images"][self.key]["reason"])

    def test_new_known_candidate_revokes_unreviewed_automatic_unmodified_status(self):
        source_body = (self.root / self.source_path).read_bytes()
        clean_path = "artifacts/media-cleaned/" + self.key + ".png"
        (self.root / clean_path).parent.mkdir(parents=True)
        (self.root / clean_path).write_bytes(source_body)
        main, _ = media.read_json(self.root / "artifacts/media-cleanup.json")
        main["images"][self.key].update(state="approved_unmodified", outputSha=self.source["sha256"], path=clean_path, mime="image/png", bytes=len(source_body))
        self.write("artifacts/media-cleanup.json", main)
        proposed, _ = self.finalizer().prepare(["artifacts/candidates.json"])
        self.assertEqual(proposed["images"][self.key]["state"], "review_required")
        self.assertIn(self.key, proposed["finalization"]["knownCandidateSources"])

    def test_animation_timeline_allows_only_equivalent_frame_merges(self):
        folder = self.root / "artifacts/animation"
        folder.mkdir()
        arrays = [np.full((20, 20, 3), [40, 50, 60], np.uint8) for _ in range(3)]
        arrays[0][2, 2] = [100, 100, 100]
        arrays[1][2, 2] = [110, 110, 110]
        arrays[2][:] = [70, 80, 90]
        source_frames = [Image.fromarray(value) for value in arrays]
        source_file = self.root / "artifacts/media-originals/animation.gif"
        source_frames[0].save(source_file, save_all=True, append_images=source_frames[1:], duration=[100, 200, 300], loop=0, disposal=2, optimize=False)
        clean_arrays = [value.copy() for value in arrays]
        clean_arrays[0][2, 2] = clean_arrays[1][2, 2] = [40, 50, 60]
        clean_frames = [Image.fromarray(value) for value in clean_arrays]
        output_file = folder / "output.webp"
        clean_frames[0].save(output_file, format="WEBP", save_all=True, append_images=clean_frames[1:], lossless=True, exact=True, duration=[100, 200, 300], loop=0)
        source = {"path": str(source_file.relative_to(self.root)), "sha256": media.sha(source_file.read_bytes())}
        frame_audits = [{"frame": index, "durationMs": duration, "maskPath": self.mask_path, "maskSha": self.candidate["maskSha"], "postDetections": [], "postScan": {"templateHits": []}} for index, duration in enumerate([100, 200, 300])]
        candidate = {"sourceSha": source["sha256"], "outputSha": media.sha(output_file.read_bytes()), "path": str(output_file.relative_to(self.root)), "mime": "image/webp", "bytes": output_file.stat().st_size, "width": 20, "height": 20, "frameAudits": frame_audits, "candidateState": "validated_candidate", "postDetectionCount": 0, "postFlameHitCount": 0}
        _, _, proof = media.validate_candidate(self.root, source, candidate)
        self.assertTrue(proof["timelineEquivalent"])
        self.assertEqual(proof["sourceDurationsMs"], [100, 200, 300])
        self.assertEqual(sum(proof["outputDurationsMs"]), 600)
        clean_frames[0].save(output_file, format="WEBP", save_all=True, append_images=clean_frames[1:], lossless=True, exact=True, duration=[100, 210, 300], loop=0)
        candidate.update(outputSha=media.sha(output_file.read_bytes()), bytes=output_file.stat().st_size)
        with self.assertRaisesRegex(media.FinalizeError, "timeline_or_loop"):
            media.validate_candidate(self.root, source, candidate)

    def test_exact_coverage_and_final_symbol_gate_require_real_hashes_and_reviewed_ids(self):
        with self.assertRaisesRegex(media.FinalizeError, "coverage"):
            media.Finalizer(self.root, expected_references=2)
        merged = self.merge()
        receipt, dispositions = self.symbol_receipt(merged, output_hit=True)
        published = self.publish(merged)
        self.assertTrue(published["publicationReady"])
        self.assertFalse(merged.manifest["publicationReady"])
        missing = copy.deepcopy(dispositions)
        missing["hits"].pop(next(iter(missing["hits"])))
        self.write("artifacts/dispositions.json", missing)
        with self.assertRaisesRegex(media.FinalizeError, "hit_disposition"):
            self.publish(merged)
        self.write("artifacts/dispositions.json", dispositions)
        stale = copy.deepcopy(receipt)
        stale["reports"] = stale["reports"][:1]
        self.write("artifacts/symbol-receipt.json", stale)
        dispositions["receiptSha256"] = media.sha((self.root / "artifacts/symbol-receipt.json").read_bytes())
        self.write("artifacts/dispositions.json", dispositions)
        with self.assertRaisesRegex(media.FinalizeError, "coverage"):
            self.publish(merged)

    def test_current_true_hit_or_incomplete_frame_scan_never_opens_gate(self):
        merged = self.merge()
        receipt, dispositions = self.symbol_receipt(merged, output_hit=True)
        output_sha = merged.manifest["images"][self.key]["outputSha"]
        for decision in dispositions["hits"].values():
            if decision["fileSha256"] == output_sha:
                decision["disposition"] = "true_brand_cleaned"
        self.write("artifacts/dispositions.json", dispositions)
        with self.assertRaisesRegex(media.FinalizeError, "current_output_brand_hit"):
            self.publish(merged)
        report_path = receipt["reports"][1]["path"]
        report, _ = media.read_json(self.root / report_path)
        report["frames"] = []
        self.write(report_path, report)
        with self.assertRaisesRegex(media.FinalizeError, "frame_background"):
            self.publish(merged)

    def test_substituted_or_older_scanner_family_cannot_replace_required_flame_evidence(self):
        merged = self.merge()
        receipt, dispositions = self.symbol_receipt(merged)
        for field, invalid in [("passVersion", "a" * 64), ("referenceSha256", {"tiny-word-only.png": "a" * 64})]:
            changed = copy.deepcopy(receipt)
            changed[field] = invalid
            self.write("artifacts/symbol-receipt.json", changed)
            rebound = copy.deepcopy(dispositions)
            rebound.update(passVersion=changed["passVersion"], receiptSha256=media.sha((self.root / "artifacts/symbol-receipt.json").read_bytes()))
            self.write("artifacts/dispositions.json", rebound)
            with self.assertRaisesRegex(media.FinalizeError, "flame_scan_family"):
                self.publish(merged)

    def test_both_independent_scan_families_are_mandatory_and_not_interchangeable(self):
        merged = self.merge()
        self.symbol_receipt(merged)
        with self.assertRaisesRegex(media.FinalizeError, "both_frozen_scan_families"):
            merged.publish("artifacts/symbol-receipt.json", "artifacts/dispositions.json")
        with self.assertRaisesRegex(media.FinalizeError, "small_badge_scan_family"):
            merged.publish("artifacts/symbol-receipt.json", "artifacts/dispositions.json", "artifacts/symbol-receipt.json", "artifacts/dispositions.json")
        published = self.publish(merged)
        self.assertEqual(set(published["publicationAudit"]["requiredFamilies"]), {"flame", "small_badge"})
        small, _ = media.read_json(self.root / "artifacts/small-badge-receipt.json")
        small["passVersion"] = "9e07a153d66070b90626ad630b83ebace040a374ec31b809b3e1b5b3293e8fd1"
        self.write("artifacts/small-badge-receipt.json", small)
        with self.assertRaisesRegex(media.FinalizeError, "small_badge_scan_family"):
            self.publish(merged)


if __name__ == "__main__":
    unittest.main()
