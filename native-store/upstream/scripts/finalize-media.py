"""Offline, explicit visual selection and final hash-bound media publication gate."""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import tempfile
import unicodedata
from urllib.parse import urlsplit

import numpy as np
from PIL import Image, ImageSequence

ROOT = Path(__file__).resolve().parents[1]
FROZEN = "37fbdbdb594cb9d366fec3cb7f2662a694d4497ea7545607d471d23c3a9ecbd9"
FLAME_PASS = "65506c85586787cd33916d83b7f978e08f94e2d6ac401faaf461d8a1a018a71d"
FLAME_REFERENCES = {"adore-gaming-flame-frame14.png": "89678f31474fb69c88a5b0ff37e80fd5b601a7a3ea9974194c6dbee98c5ebca1", "adore-gaming-flame-gray-frame10.png": "795907d8c2a148d40b3113531aab6b02d90cc4ed55569f93ba534c2d8ab91924"}
PUBLICATION_POLICY = json.loads((ROOT / "data/media-audit-policy.json").read_bytes())
SMALL_BADGE_PASS = PUBLICATION_POLICY["smallBadgePass"]
SMALL_BADGE_REFERENCES = PUBLICATION_POLICY["smallBadgeReferences"]
KNOWN_BRAND_FILES = {row["sourceSha256"] for row in json.loads((ROOT / "data/media-brand-incidents.json").read_bytes())["findings"].values()}
HASH = re.compile(r"[a-f0-9]{64}\Z")
EXTENSIONS = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp", "image/gif": "gif", "image/avif": "avif"}
MAX_BYTES = 20000000
MAX_MASK_FRACTION = .05
OBJECT_POLICY_BYTES = (ROOT / 'data/media-object-policy.json').read_bytes()
OBJECT_POLICY = json.loads(OBJECT_POLICY_BYTES)
_object_modules = {}
for _name in ['media_object_gate','media_object_pixels','media_scan_lineage']:
    _spec = importlib.util.spec_from_file_location(_name, ROOT / 'lib' / (_name + '.py'))
    _module = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_module)
    _object_modules[_name] = _module
JOINED_GAMING_ALIASES = ("adoregaming", "doregaming", "adorgaming", "adoregame")


class FinalizeError(Exception):
    pass


def sha(body):
    return hashlib.sha256(body).hexdigest()


def publication_binding(manifest):
    value = [sorted([key, value] for key, value in manifest["references"].items()), [[key, row["state"], row["sourceSha"], row["outputSha"], row.get("finalReview", {}).get("candidateReceiptSha"), row.get("finalReview", {}).get("selectionReceiptSha"), row.get("finalReview", {}).get("selection", {}).get("candidateSha")] for key, row in sorted(manifest["images"].items())]]
    return sha(json.dumps(value, separators=(",", ":")).encode())


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()


def checked_hash(value):
    if not isinstance(value, str) or not HASH.fullmatch(value):
        raise FinalizeError("invalid_sha256")
    return value


def artifact(root, value, folder=None):
    if not isinstance(value, (str, Path)):
        raise FinalizeError("invalid_artifact_path")
    value = Path(value)
    if ".." in value.parts:
        raise FinalizeError("artifact_path_traversal")
    candidate = value if value.is_absolute() else root / value
    actual = candidate.resolve()
    allowed = root / "artifacts" / folder if folder else root / "artifacts"
    if not actual.is_relative_to(allowed):
        raise FinalizeError("artifact_path_outside_allowed_folder")
    current = root
    try:
        for part in candidate.relative_to(root).parts:
            current /= part
            if current.is_symlink():
                raise FinalizeError("artifact_symlink_rejected")
    except ValueError:
        raise FinalizeError("artifact_path_outside_workspace") from None
    return actual


def read_json(path):
    body = path.read_bytes()
    value = json.loads(body)
    if not isinstance(value, dict):
        raise FinalizeError("json_object_required")
    return value, sha(body)


def read_image(root, path, expected, folder=None):
    file = artifact(root, path, folder)
    body = file.read_bytes()
    if not body or len(body) > MAX_BYTES or sha(body) != checked_hash(expected):
        raise FinalizeError("image_bytes_hash_or_size_mismatch")
    with Image.open(file) as image:
        size, mime, count = image.size, Image.MIME.get(image.format), getattr(image, "n_frames", 1)
        if mime not in EXTENSIONS:
            raise FinalizeError("unsupported_raster")
        image.verify()
    return file, body, {"width": size[0], "height": size[1], "mime": mime, "bytes": len(body), "frames": count}


def decoded_frames(path):
    with Image.open(path) as image:
        loop = image.info.get("loop")
        frames, durations = [], []
        for frame in ImageSequence.Iterator(image):
            frames.append(np.array(frame.convert("RGBA")))
            durations.append(int(frame.info.get("duration", 0)))
    return frames, durations, loop


def load_mask(root, record, shape, footprint_pin=None):
    path = artifact(root, record.get("maskPath"))
    body = path.read_bytes()
    if record.get("maskSha") is not None and sha(body) != checked_hash(record["maskSha"]):
        raise FinalizeError("mask_hash_mismatch")
    with Image.open(path) as image:
        mask = np.array(image.convert("L"))
    if mask.shape != shape or not np.isin(mask, [0, 255]).all():
        raise FinalizeError("mask_dimensions_or_values_invalid")
    if footprint_pin is not None and (footprint_pin.get('maskSha256') != sha(body) or footprint_pin.get('maskPixels') != int(np.count_nonzero(mask)) or (footprint_pin.get('height'), footprint_pin.get('width')) != shape):
        raise FinalizeError('whole_object_footprint_mask_changed')
    if float(np.count_nonzero(mask)) / mask.size > MAX_MASK_FRACTION and footprint_pin is None:
        raise FinalizeError("mask_coverage_exceeds_five_percent")
    return mask != 0, sha(body)


def compare_frame(source, output, mask, footprint_pin=None):
    if source.shape != output.shape or mask.shape != source.shape[:2]:
        raise FinalizeError("image_dimensions_changed")
    if footprint_pin is not None:
        try:
            _object_modules['media_object_pixels'].verify_footprint_exception(footprint_pin, footprint_pin['sourceSha256'], footprint_pin['outputSha256'], footprint_pin['maskSha256'], source, output, mask)
        except ValueError as error:
            raise FinalizeError(str(error)) from None
    elif not np.array_equal(source[:, :, 3], output[:, :, 3]):
        raise FinalizeError("alpha_changed")
    # Printed edge pixels may be partially visible. Their opacity stays exact
    # above; fully invisible RGB must never be included in a retouch mask.
    if np.any(mask & (source[:, :, 3] == 0)):
        raise FinalizeError("mask_intersects_transparency")
    if not np.array_equal(source[:, :, :3][~mask], output[:, :, :3][~mask]):
        raise FinalizeError("rgb_outside_mask_changed")


def object_footprint_pin(source, candidate, record):
    matches = [pin for pin in OBJECT_POLICY['footprintExceptions'] if pin['sourceSha256'] == source['sha256'] and pin['outputSha256'] == candidate['outputSha'] and pin['maskSha256'] == record.get('maskSha')]
    matches = list({json.dumps(pin, sort_keys=True): pin for pin in matches}.values())
    if len(matches) > 1:
        raise FinalizeError('ambiguous_whole_object_footprint_exception')
    return matches[0] if matches else None


def joined_brand_hits(scan):
    hits = []
    if isinstance(scan, dict):
        if isinstance(scan.get("text"), str):
            compact = "".join(character for character in unicodedata.normalize("NFKD", scan["text"]).casefold().replace("ı", "i") if character.isalnum())
            if any(alias in compact for alias in JOINED_GAMING_ALIASES):
                hits.append(scan)
        for value in scan.values():
            hits.extend(joined_brand_hits(value))
    elif isinstance(scan, list):
        for value in scan:
            hits.extend(joined_brand_hits(value))
    return hits


def validate_gaming_template_review(candidate):
    findings = [{"frame": None, "hit": hit} for hit in candidate.get("postGamingTemplates", [])]
    for record in candidate.get("frameAudits", []):
        findings.extend({"frame": record.get("frame"), "hit": hit} for hit in record.get("postGamingTemplates", []))
    if not findings:
        if candidate.get("postGamingHitCount", 0) != 0:
            raise FinalizeError("known_residual_brand_blocks_selection")
        return
    review = candidate.get("postGamingTemplateReview", {})
    if not isinstance(review, dict) or review.get("visualReview") is not True or review.get("candidateSha") != candidate.get("outputSha") or not all(isinstance(review.get(field), str) and review[field].strip() for field in ("reviewer", "notes")):
        raise FinalizeError("gaming_template_exact_output_visual_review_required")
    expected = {sha(json_bytes(finding)) for finding in findings}
    supplied = review.get("falsePositiveHitHashes")
    if review.get("disposition") != "false_positive" or not isinstance(supplied, list) or len(supplied) != len(set(supplied)) or set(supplied) != expected:
        raise FinalizeError("gaming_template_false_positive_review_incomplete")


def validate_candidate(root, source, candidate):
    states = {candidate.get("state"), candidate.get("candidateState")}
    if any(value in {"failed", "pending", "review_required", "unresolved", "rejected_residual_brand"} or (isinstance(value, str) and value.startswith("rejected")) for value in states | {candidate.get("reason")}):
        raise FinalizeError("candidate_receipt_is_failed_or_unresolved")
    if not states & {"candidate_ready", "validated_candidate", "approved_cleaned", "approved_unmodified"}:
        raise FinalizeError("candidate_ready_state_required")
    validate_gaming_template_review(candidate)
    if candidate.get("postDetectionCount", 0) != 0 or candidate.get("postFlameHitCount", 0) != 0 or candidate.get("postDetections", []) != []:
        raise FinalizeError("known_residual_brand_blocks_selection")
    scans = candidate.get("frameAudits") or candidate.get("postScans")
    if scans:
        for record in scans:
            scan = record.get("postScan", record.get("scan"))
            if record.get("postDetections", record.get("detections")) != [] or not isinstance(scan, dict) or scan.get("templateHits") != [] or record.get("postFlame", {}).get("hits", []) != []:
                raise FinalizeError("known_residual_brand_or_missing_postscan")
            if joined_brand_hits(scan):
                raise FinalizeError("joined_brand_residual_in_candidate")
    elif not isinstance(candidate.get("postScan"), dict) or candidate["postScan"].get("templateHits") != [] or candidate.get("postDetections") != []:
        raise FinalizeError("clear_postscan_evidence_required")
    if joined_brand_hits(candidate.get("postScan")):
        raise FinalizeError("joined_brand_residual_in_candidate")
    if candidate.get("postFlame", {}).get("hits", []) != []:
        raise FinalizeError("known_residual_symbol_blocks_selection")
    if candidate.get("sourceSha") != source["sha256"]:
        raise FinalizeError("candidate_source_hash_mismatch")
    source_file, _, source_meta = read_image(root, source["path"], source["sha256"], "media-originals")
    output_file, body, output_meta = read_image(root, candidate.get("path"), candidate.get("outputSha"))
    with Image.open(source_file) as original_image, Image.open(output_file) as final_image:
        if original_image.info.get("icc_profile", b"") != final_image.info.get("icc_profile", b""):
            raise FinalizeError("original_color_profile_changed")
        source_orientation = original_image.getexif().get(274, 1) or 1
        final_orientation = final_image.getexif().get(274, 1) or 1
        if source_orientation != final_orientation:
            raise FinalizeError("original_display_orientation_changed")
    for field in ("width", "height", "mime", "bytes"):
        if candidate.get(field) != output_meta[field]:
            raise FinalizeError("candidate_metadata_mismatch")
    if (source_meta["width"], source_meta["height"]) != (output_meta["width"], output_meta["height"]):
        raise FinalizeError("image_dimensions_changed")
    if candidate["outputSha"] == source["sha256"]:
        return body, output_meta, {"unmodifiedBytes": True, "outsideMaskRgbMaxDelta": 0, "alphaMaxDelta": 0}
    original, source_durations, source_loop = decoded_frames(source_file)
    output, output_durations, output_loop = decoded_frames(output_file)
    frame_records = candidate.get("frameAudits")
    if len(original) == 1 and len(output) == 1:
        pin = object_footprint_pin(source, candidate, candidate)
        mask, mask_sha = load_mask(root, candidate, original[0].shape[:2], pin)
        compare_frame(original[0], output[0], mask, pin)
        return body, output_meta, {"outsideMaskRgbMaxDelta": 0, "alphaMaxDelta": int(np.abs(original[0][:,:,3].astype(np.int16)-output[0][:,:,3]).max()), "maskSha": mask_sha, "maskCoverage": float(np.mean(mask))}
    if source_loop != output_loop or sum(source_durations) != sum(output_durations) or any(value <= 0 for value in source_durations + output_durations):
        raise FinalizeError("animation_timeline_or_loop_changed")
    if not isinstance(frame_records, list) or {item.get("frame") for item in frame_records} != set(range(len(original))) or len(frame_records) != len(original):
        raise FinalizeError("animation_masks_incomplete")
    records = {item["frame"]: item for item in frame_records}
    masks, mask_hashes = [], []
    for index, frame in enumerate(original):
        if records[index].get("durationMs") != source_durations[index]:
            raise FinalizeError("animation_frame_duration_receipt_mismatch")
        pin = object_footprint_pin(source, candidate, records[index])
        mask, mask_sha = load_mask(root, records[index], frame.shape[:2], pin)
        masks.append(mask)
        mask_hashes.append(mask_sha)
    source_index = output_index = 0
    source_left, output_left = source_durations[0], output_durations[0]
    while source_index < len(original) and output_index < len(output):
        compare_frame(original[source_index], output[output_index], masks[source_index], object_footprint_pin(source, candidate, records[source_index]))
        elapsed = min(source_left, output_left)
        source_left -= elapsed
        output_left -= elapsed
        if source_left == 0:
            source_index += 1
            if source_index < len(original):
                source_left = source_durations[source_index]
        if output_left == 0:
            output_index += 1
            if output_index < len(output):
                output_left = output_durations[output_index]
    if source_index != len(original) or output_index != len(output):
        raise FinalizeError("animation_timeline_incomplete")
    return body, output_meta, {"outsideMaskRgbMaxDelta": 0, "alphaMaxDelta": 0, "sourceDurationsMs": source_durations, "outputDurationsMs": output_durations, "loop": source_loop, "maskSha256": mask_hashes, "timelineEquivalent": True}


def visual_selection(value, expected_sha=None):
    if not isinstance(value, dict) or value.get("structureReview") is not True or not all(isinstance(value.get(key), str) and value[key].strip() for key in ("reviewer", "notes")):
        raise FinalizeError("explicit_visual_structure_selection_required")
    checked_hash(value.get("candidateSha"))
    if expected_sha is not None and value["candidateSha"] != expected_sha:
        raise FinalizeError("visual_selection_candidate_hash_mismatch")
    return copy.deepcopy(value)


def symbol_frame_bindings(path):
    result = {}
    with Image.open(path) as image:
        for index, frame in enumerate(ImageSequence.Iterator(image)):
            rgba = frame.convert("RGBA")
            backgrounds = ["white", "black"] if rgba.getchannel("A").getextrema() != (255, 255) else ["white"]
            for background in backgrounds:
                canvas = Image.new("RGBA", rgba.size, background)
                canvas.alpha_composite(rgba)
                rgb = np.asarray(canvas.convert("RGB"), dtype=np.uint8)
                # Frozen symbol scanner 65506c uses shape/dtype plus RGB bytes.
                result[(index, background)] = sha(str((rgb.shape, str(rgb.dtype))).encode() + rgb.tobytes())
    return result


def immutable_write(root, relative, body):
    destination = artifact(root, relative)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if destination.read_bytes() != body:
            raise FinalizeError("immutable_artifact_collision")
        return
    descriptor, temporary = tempfile.mkstemp(prefix=".finalize-", dir=destination.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(body)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary, destination)
        except FileExistsError:
            if destination.read_bytes() != body:
                raise FinalizeError("immutable_artifact_collision")
    finally:
        Path(temporary).unlink(missing_ok=True)


def atomic_manifest(path, value, expected_sha):
    if sha(path.read_bytes()) != expected_sha:
        raise FinalizeError("manifest_changed_during_validation")
    descriptor, temporary = tempfile.mkstemp(prefix=".media-finalize-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(json_bytes(value))
            handle.flush()
            os.fsync(handle.fileno())
        if sha(path.read_bytes()) != expected_sha:
            raise FinalizeError("manifest_changed_during_validation")
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


class Finalizer:
    def verify_whole_objects(self):
        audit = self.manifest.get('wholeObjectAudit')
        if self.isolated_test_fixture and self.reference_count != OBJECT_POLICY['referenceCount'] and not audit:
            return
        if not audit or audit.get('policySha256') != sha(OBJECT_POLICY_BYTES):
            raise FinalizeError('current_whole_object_publication_evidence_required')
        receipt, receipt_sha = read_json(artifact(self.root, audit.get('receiptPath'), 'media-finalization'))
        if receipt_sha != audit.get('receiptSha256'):
            raise FinalizeError('whole_object_receipt_changed')
        try:
            _object_modules['media_object_gate'].validate_object_evidence(self.manifest, OBJECT_POLICY, receipt)
        except ValueError as error:
            raise FinalizeError(str(error)) from None
        checked_masks = set()
        for key, requirement in OBJECT_POLICY['required'].items():
            for field in [requirement] + requirement['fields']:
                if field.get('maskPath') and field['maskPath'] not in checked_masks:
                    if sha(artifact(self.root, field['maskPath']).read_bytes()) != field['maskSha256']:
                        raise FinalizeError('whole_object_actual_mask_bytes_changed')
                    checked_masks.add(field['maskPath'])
            with Image.open(artifact(self.root, self.manifest['images'][key]['path'], 'media-cleaned')) as image:
                if 'timeline' not in requirement:
                    if sha(np.array(image.convert('RGBA')).tobytes()) != requirement['outputRgbaSha256']:
                        raise FinalizeError('whole_object_actual_decoded_pixels_changed')
                    continue
                hashes, durations = [], []
                for index in range(image.n_frames):
                    image.seek(index);image.load();hashes.append(sha(np.array(image.convert('RGBA')).tobytes()));durations.append(int(image.info.get('duration',0)))
                timeline = requirement['timeline']
                if durations != timeline['outputDurationsMs'] or int(image.info.get('loop',0)) != timeline['loop']:
                    raise FinalizeError('whole_object_actual_frame_timing_changed')
                for field, mapping in zip(requirement['fields'], timeline['sourceToOutputMapping']):
                    if field['sourceFrame'] != mapping['sourceFrame'] or any(hashes[segment['outputFrame']] != field['outputRgbaSha256'] for segment in mapping['outputSegments']):
                        raise FinalizeError('whole_object_actual_decoded_frame_changed')

    def __init__(self, root, expected_references=5129, *, isolated_test_fixture=False):
        self.root = Path(root).resolve()
        if isolated_test_fixture and (self.root == ROOT or not self.root.name.startswith('nodeno-finalize-test-')):
            raise FinalizeError('isolated_test_fixture_restricted')
        self.isolated_test_fixture = isolated_test_fixture is True
        self.path = artifact(self.root, "artifacts/media-cleanup.json")
        self.manifest, self.manifest_sha = read_json(self.path)
        self.downloads, _ = read_json(artifact(self.root, "artifacts/media-download.json"))
        if self.manifest.get("pipelineVersion") != FROZEN or self.downloads.get("schemaVersion") != 1:
            raise FinalizeError("frozen_pipeline_or_download_schema_mismatch")
        catalog = json.loads((self.root / "data/catalog-source.json").read_bytes())
        references = {}
        for product in catalog["products"]:
            urls = []
            for url in product.get("images", []):
                parsed = urlsplit(url)
                if parsed.scheme == "https" and parsed.hostname == "witcdn.adoremobilya.com" and not parsed.username and not parsed.password and parsed.port in (None, 443) and not parsed.fragment:
                    urls.append(url)
            for index, url in enumerate(urls):
                key = sha(url.encode())
                reference = str(product["id"]) + ":" + str(index)
                if reference in references:
                    raise FinalizeError("duplicate_catalogue_reference")
                references[reference] = key
        self.keys = set(references.values())
        if len(references) != expected_references or self.downloads.get("references") != references or self.manifest.get("references") != references or set(self.manifest.get("images", {})) != self.keys or set(self.downloads.get("images", {})) != self.keys:
            raise FinalizeError("exact_reference_coverage_required")
        self.reference_count = len(references)
        self.evidence_copies = {}
        for key in self.keys:
            source = self.downloads["images"][key]
            row = self.manifest["images"][key]
            if source.get("status") != "verified" or sha(source.get("url", "").encode()) != key or row.get("sourceSha") != source.get("sha256"):
                raise FinalizeError("immutable_source_identity_mismatch")
            _, _, metadata = read_image(self.root, source["path"], source["sha256"], "media-originals")
            if any(source.get(field) != metadata[field] for field in ("bytes", "width", "height", "mime")):
                raise FinalizeError("immutable_source_metadata_changed")
        frozen = self.manifest.get("frozen37fb")
        if frozen is None:
            self.base = copy.deepcopy(self.manifest)
            self.base_body = self.path.read_bytes()
            self.base_sha = sha(self.base_body)
        else:
            frozen_path = artifact(self.root, frozen.get("manifestPath"), "media-finalization")
            self.base_body = frozen_path.read_bytes()
            self.base_sha = sha(self.base_body)
            if self.base_sha != frozen.get("manifestSha"):
                raise FinalizeError("frozen_manifest_audit_changed")
            self.base = json.loads(self.base_body)
            if set(frozen.get("reports", {})) != self.keys:
                raise FinalizeError("original_audit_bindings_incomplete")
            for binding in frozen["reports"].values():
                if sha(artifact(self.root, binding["path"]).read_bytes()) != binding["sha256"]:
                    raise FinalizeError("original_pipeline_report_changed")
        if self.base.get("pipelineVersion") != FROZEN or set(self.base.get("images", {})) != self.keys:
            raise FinalizeError("frozen_audit_coverage_mismatch")

    def candidate_registry(self, paths):
        registry = {}
        self.provided_candidates = {}
        for key, row in self.base["images"].items():
            if row.get("state") == "approved_cleaned":
                report, report_sha = read_json(artifact(self.root, row["report"]))
                receipt_path = self.archive_receipt(row["report"], report_sha, "candidate")
                registry[(key, row["outputSha"])] = {**report, **row, "candidateReceiptSha": report_sha, "candidateReceiptPath": receipt_path}
        for path in paths:
            document, document_sha = read_json(artifact(self.root, path))
            if document.get("pipelineVersion") != FROZEN:
                raise FinalizeError("candidate_receipt_pipeline_mismatch")
            receipt_path = self.archive_receipt(path, document_sha, "candidate")
            images = document.get("images")
            rows = images.items() if isinstance(images, dict) else ((row.get("urlSha"), row) for row in images or [])
            for key, row in rows:
                if key not in self.keys:
                    raise FinalizeError("candidate_unknown_source")
                checked_hash(row.get("outputSha"))
                self.provided_candidates.setdefault(key, set()).add(row["outputSha"])
                registry[(key, row["outputSha"])] = {**row, "candidateReceiptSha": document_sha, "candidateReceiptPath": receipt_path}
        return registry

    def archive_receipt(self, path, expected_sha, kind):
        body = artifact(self.root, path).read_bytes()
        if sha(body) != expected_sha:
            raise FinalizeError("receipt_changed_during_validation")
        relative = "artifacts/media-finalization/" + kind + "-" + expected_sha + ".json"
        self.evidence_copies[relative] = body
        return relative

    def prepare(self, candidate_paths, selection_path=None):
        registry = self.candidate_registry(candidate_paths)
        selections, selection_sha = {}, None
        selection_snapshot = None
        if selection_path:
            document, selection_sha = read_json(artifact(self.root, selection_path))
            if document.get("schemaVersion") != 1 or document.get("basePipelineVersion") != FROZEN or not isinstance(document.get("selections"), dict):
                raise FinalizeError("invalid_visual_selection_receipt")
            selections = document["selections"]
            selection_snapshot = self.archive_receipt(selection_path, selection_sha, "selection")
        if set(selections) - self.keys:
            raise FinalizeError("visual_selection_unknown_source")
        proposed = copy.deepcopy(self.manifest)
        proposed["publicationReady"] = False
        copies = {}
        joined_sources = set()
        for key, row in proposed["images"].items():
            selected = selections.get(key)
            if selected is None:
                if row.get("state") == "approved_unmodified":
                    source_report, _ = read_json(artifact(self.root, self.base["images"][key]["report"]))
                    if joined_brand_hits(source_report.get("scan", {})):
                        joined_sources.add(key)
                        row.update(state="review_required", reason="known_joined_brand_in_source_scan_requires_retouch")
                        continue
                review = row.get("finalReview")
                new_override_needs_review = key in self.provided_candidates and (not review or row.get("outputSha") not in self.provided_candidates[key])
                if new_override_needs_review or row.get("state") == "approved_cleaned":
                    if review:
                        visual_selection(review.get("selection"), row.get("outputSha"))
                    if not review or new_override_needs_review:
                        row.update(state="review_required", reason="final_visual_structure_selection_required")
                continue
            selection = visual_selection(selected)
            candidate = registry.get((key, selection["candidateSha"]))
            if candidate is None:
                raise FinalizeError("selected_candidate_hash_not_in_receipts")
            body, metadata, validation = validate_candidate(self.root, self.downloads["images"][key], candidate)
            extension = EXTENSIONS[metadata["mime"]]
            relative = "artifacts/media-cleaned/" + candidate["outputSha"] + "." + extension
            copies[relative] = body
            row["original37fb"] = copy.deepcopy(self.base["images"][key])
            row.update(state="approved_unmodified" if candidate["outputSha"] == row["sourceSha"] else "approved_cleaned", outputSha=candidate["outputSha"], path=relative, filename=Path(relative).name, reason="explicit_hash_bound_visual_structure_selection", **{field: metadata[field] for field in ("bytes", "width", "height", "mime")})
            row["finalReview"] = {"selection": selection, "selectionReceiptSha": selection_sha, "selectionReceiptPath": selection_snapshot, "candidateReceiptSha": candidate["candidateReceiptSha"], "candidateReceiptPath": candidate["candidateReceiptPath"], "candidate": candidate, "validation": validation}
        proposed["totals"] = totals(proposed)
        known_candidates = set(self.provided_candidates) | joined_sources | {key for key, row in self.base["images"].items() if row.get("state") == "approved_cleaned"} | set(self.manifest.get("finalization", {}).get("knownCandidateSources", []))
        proposed["finalization"] = {"version": 1, "basePipelineVersion": FROZEN, "baseManifestSha": self.base_sha, "knownCandidateSources": sorted(known_candidates), "visualReviewIsSeparateFromDetection": True}
        return proposed, copies

    def write_merge(self, proposed, copies):
        reports = {}
        for key, row in self.base["images"].items():
            report, report_sha = read_json(artifact(self.root, row["report"]))
            if report.get("pipelineVersion") != FROZEN or report.get("sourceSha") != row.get("sourceSha"):
                raise FinalizeError("original_pipeline_report_identity_changed")
            reports[key] = {"path": row["report"], "sha256": report_sha}
        base_path = "artifacts/media-finalization/frozen-" + self.base_sha + ".json"
        immutable_write(self.root, base_path, self.base_body)
        for relative, body in self.evidence_copies.items():
            immutable_write(self.root, relative, body)
        for relative, body in copies.items():
            immutable_write(self.root, relative, body)
        proposed["frozen37fb"] = {"pipelineVersion": FROZEN, "manifestPath": base_path, "manifestSha": self.base_sha, "reports": reports}
        proposed["publicationReady"] = False
        atomic_manifest(self.path, proposed, self.manifest_sha)

    def verify_final_images(self):
        for key, row in self.manifest["images"].items():
            if row.get("outputSha") in KNOWN_BRAND_FILES:
                raise FinalizeError("known_reported_brand_image_blocks_publication")
            if row.get("state") not in {"approved_unmodified", "approved_cleaned"}:
                raise FinalizeError("nonfinal_media_state_blocks_publication")
            if key in self.manifest.get("finalization", {}).get("knownCandidateSources", []) and not row.get("finalReview"):
                raise FinalizeError("known_override_visual_selection_required")
            _, _, metadata = read_image(self.root, row.get("path"), row.get("outputSha"), "media-cleaned")
            if any(row.get(field) != metadata[field] for field in ("width", "height", "bytes", "mime")):
                raise FinalizeError("final_output_metadata_changed")
            review = row.get("finalReview")
            if review:
                visual_selection(review.get("selection"), row["outputSha"])
                selection_document, selection_sha = read_json(artifact(self.root, review.get("selectionReceiptPath"), "media-finalization"))
                if selection_sha != review.get("selectionReceiptSha") or selection_document.get("selections", {}).get(key) != review["selection"]:
                    raise FinalizeError("final_visual_selection_receipt_changed")
                if sha(artifact(self.root, review.get("candidateReceiptPath"), "media-finalization").read_bytes()) != review.get("candidateReceiptSha"):
                    raise FinalizeError("final_candidate_receipt_changed")
            if row["state"] == "approved_unmodified":
                source_report, _ = read_json(artifact(self.root, self.base["images"][key]["report"]))
                if joined_brand_hits(source_report.get("scan", {})):
                    raise FinalizeError("joined_brand_in_unmodified_source")
                if row["outputSha"] != row["sourceSha"]:
                    raise FinalizeError("unmodified_output_bytes_changed")
            else:
                review = review or {}
                visual_selection(review.get("selection"), row["outputSha"])
                candidate = {**review.get("candidate", {}), "path": row["path"], "outputSha": row["outputSha"]}
                _, _, validation = validate_candidate(self.root, self.downloads["images"][key], candidate)
                if validation != review.get("validation"):
                    raise FinalizeError("final_candidate_validation_evidence_changed")
        frozen = self.manifest.get("frozen37fb", {})
        if set(frozen.get("reports", {})) != self.keys:
            raise FinalizeError("original_audit_bindings_incomplete")
        for key, binding in frozen["reports"].items():
            if sha(artifact(self.root, binding["path"]).read_bytes()) != binding["sha256"]:
                raise FinalizeError("original_pipeline_report_changed")

    def validate_scan_family(self, receipt_path, dispositions_path, expected_pass, expected_references, family):
        receipt_file = artifact(self.root, receipt_path)
        receipt, receipt_sha = read_json(receipt_file)
        dispositions, dispositions_sha = read_json(artifact(self.root, dispositions_path))
        if receipt.get("schemaVersion") != 1 or receipt.get("basePipelineVersion") != FROZEN or receipt.get("allSourceUrlsScanned") is not True or receipt.get("sourceReferences") != self.reference_count:
            raise FinalizeError("complete_hash_bound_symbol_scan_required")
        if receipt.get("passVersion") != expected_pass or receipt.get("referenceSha256") != expected_references:
            raise FinalizeError("required_frozen_" + family + "_scan_family_mismatch")
        if dispositions.get("schemaVersion") != 1 or dispositions.get("basePipelineVersion") != FROZEN or dispositions.get("passVersion") != receipt["passVersion"] or dispositions.get("receiptSha256") != receipt_sha or not isinstance(dispositions.get("hits"), dict):
            raise FinalizeError("symbol_dispositions_not_bound_to_final_receipt")
        source_coverage, output_coverage, all_hits, relevant, report_bindings = set(), set(), {}, [], []
        expected_files = {row["sha256"]: artifact(self.root, row["path"], "media-originals") for row in self.downloads["images"].values()}
        expected_files.update({row["outputSha"]: artifact(self.root, row["path"], "media-cleaned") for row in self.manifest["images"].values()})
        parent_index = None
        if family == 'whole_object_supplemental' and OBJECT_POLICY.get('supplementalParentPass'):
            parent, parent_sha = read_json(artifact(self.root, receipt.get('parentReceiptPath'), 'media-finalization'))
            if parent_sha != receipt.get('parentReceiptSha256') or parent.get('passVersion') != OBJECT_POLICY['supplementalParentPass'] or parent.get('allSourceAndOutputFilesAndFramesScanned') is not True:
                raise FinalizeError('supplemental_parent_receipt_lineage_changed')
            parent_index = {r['fileSha256']: r for r in parent['reports']}
        for reference in receipt.get("reports", []):
            report_path = artifact(self.root, reference.get("path"))
            report, report_sha = read_json(report_path)
            report_bindings.append([reference.get("fileSha256"), report_sha])
            file_sha = checked_hash(reference.get("fileSha256"))
            if report.get("fileSha256") != file_sha or report.get("passVersion") != receipt["passVersion"] or report.get("candidateHits") != len(report.get("hits", [])) or reference.get("hits") != len(report.get("hits", [])):
                raise FinalizeError("symbol_report_identity_or_hit_count_changed")
            if parent_index is not None:
                try:
                    _object_modules['media_scan_lineage'].validate_combined_report(report, parent_index, OBJECT_POLICY['supplementalParentPass'], lambda p: artifact(self.root,p).read_bytes())
                except ValueError as error:
                    raise FinalizeError(str(error)) from None
            roles = reference.get("roles", [])
            source_keys, output_keys = set(), set()
            for role in roles:
                key = role.get("urlSha")
                if key not in self.keys:
                    raise FinalizeError("symbol_report_unknown_source")
                if role.get("role") == "source" and self.downloads["images"][key]["sha256"] == file_sha:
                    source_keys.add(key)
                    source_coverage.add(key)
                if role.get("role") in {"current_output", "review_candidate", "final_output"} and self.manifest["images"][key]["outputSha"] == file_sha:
                    output_keys.add(key)
                    output_coverage.add(key)
            for hit in report.get("hits", []):
                hit_id = checked_hash(hit.get("id"))
                if hit_id in all_hits:
                    raise FinalizeError("duplicate_symbol_hit_id")
                all_hits[hit_id] = (file_sha, report_sha)
                if source_keys or output_keys:
                    relevant.append((hit_id, file_sha, report_sha, source_keys, output_keys))
            if source_keys or output_keys:
                expected_frames = symbol_frame_bindings(expected_files[file_sha])
                frames = report.get("frames", [])
                actual_frames = {(row.get("frame"), row.get("background")): row.get("rgbSha256") for row in frames}
                if len(frames) != len(expected_frames) or actual_frames != expected_frames or report.get("compositesScanned") != len(expected_frames) or report.get("frameCount") != len({index for index, _ in expected_frames}):
                    raise FinalizeError("symbol_frame_background_hash_coverage_incomplete")
                if any((hit.get("frame"), hit.get("background")) not in expected_frames for hit in report.get("hits", [])):
                    raise FinalizeError("symbol_hit_frame_or_background_invalid")
        if source_coverage != self.keys or output_coverage != self.keys:
            raise FinalizeError("final_symbol_source_or_output_coverage_incomplete")
        if set(dispositions["hits"]) - set(all_hits):
            raise FinalizeError("unknown_symbol_disposition_hit_id")
        for hit_id, file_sha, report_sha, source_keys, output_keys in relevant:
            decision = dispositions["hits"].get(hit_id, {})
            if decision.get("fileSha256") != file_sha or decision.get("reportSha256") != report_sha or decision.get("visualReview") is not True or not all(isinstance(decision.get(field), str) and decision[field].strip() for field in ("reviewer", "notes")):
                raise FinalizeError("reviewed_hash_bound_hit_disposition_required")
            if decision.get("disposition") == "false_positive":
                continue
            if decision.get("disposition") != "true_brand_cleaned" or output_keys:
                raise FinalizeError("current_output_brand_hit_blocks_publication")
            expected = {key: self.manifest["images"][key]["outputSha"] for key in source_keys}
            if not expected or decision.get("cleanedOutputs") != expected or any(self.manifest["images"][key]["state"] != "approved_cleaned" or final_sha == file_sha for key, final_sha in expected.items()):
                raise FinalizeError("true_brand_hit_not_cleaned_and_rescanned")
        archived_receipt = self.archive_receipt(receipt_path, receipt_sha, "symbol-receipt")
        archived_dispositions = self.archive_receipt(dispositions_path, dispositions_sha, "symbol-dispositions")
        return {"receiptPath": archived_receipt, "receiptSha256": receipt_sha, "passVersion": receipt["passVersion"], "dispositionsPath": archived_dispositions, "dispositionsSha256": dispositions_sha, "sourceUrls": len(source_coverage), "finalOutputUrls": len(output_coverage), "reportBindingsSha256": sha(json.dumps(sorted(report_bindings), separators=(",", ":")).encode()), "reviewedRelevantHits": len(relevant), "detectionIsNotVisualQa": True}

    def publish(self, receipt_path, dispositions_path, small_badge_receipt=None, small_badge_dispositions=None):
        if not __debug__:
            raise FinalizeError('optimized_python_publication_forbidden')
        if not small_badge_receipt or not small_badge_dispositions:
            raise FinalizeError("both_frozen_scan_families_required")
        self.verify_final_images()
        self.verify_whole_objects()
        flame = self.validate_scan_family(receipt_path, dispositions_path, FLAME_PASS, FLAME_REFERENCES, "flame")
        small_badge = self.validate_scan_family(small_badge_receipt, small_badge_dispositions, SMALL_BADGE_PASS, SMALL_BADGE_REFERENCES, "small_badge")
        families = {"flame": flame, "small_badge": small_badge}
        if OBJECT_POLICY.get('supplementalPass') and (not self.isolated_test_fixture or self.reference_count == OBJECT_POLICY['referenceCount'] or self.manifest.get('wholeObjectAudit')):
            binding = self.manifest.get('wholeObjectAudit', {}).get('supplemental')
            if not binding:
                raise FinalizeError('complete_whole_object_supplemental_scan_required')
            extra = self.validate_scan_family(binding.get('receiptPath'), binding.get('dispositionsPath'), OBJECT_POLICY['supplementalPass'], OBJECT_POLICY['supplementalReferences'], 'whole_object_supplemental')
            if any(extra.get(k) != binding.get(k) for k in ['receiptSha256','dispositionsSha256']):
                raise FinalizeError('whole_object_supplemental_binding_changed')
            families['whole_object_supplemental'] = extra
        proposed = copy.deepcopy(self.manifest)
        proposed["publicationReady"] = True
        proposed["publicationAudit"] = {"policy": PUBLICATION_POLICY["policy"], "manifestBindingSha256": publication_binding(proposed), "requiredFamilies": families, "detectionIsNotVisualQa": True}
        return proposed

    def verify_published(self):
        evidence = self.manifest.get("publicationAudit", {})
        if self.manifest.get("publicationReady") is not True or evidence.get("policy") != PUBLICATION_POLICY["policy"] or evidence.get("manifestBindingSha256") != publication_binding(self.manifest):
            raise FinalizeError("current_physical_badge_publication_evidence_required")
        families = evidence.get("requiredFamilies", {})
        flame, badge = families.get("flame", {}), families.get("small_badge", {})
        proposed = self.publish(flame.get("receiptPath"), flame.get("dispositionsPath"), badge.get("receiptPath"), badge.get("dispositionsPath"))
        if proposed["publicationAudit"] != evidence:
            raise FinalizeError("published_media_evidence_changed")
        return evidence


def totals(manifest):
    counts = {state: 0 for state in ("pending", "approved_unmodified", "approved_cleaned", "review_required", "failed")}
    for row in manifest["images"].values():
        if row.get("state") not in counts:
            raise FinalizeError("unknown_media_state")
        counts[row["state"]] += 1
    return {**counts, "images": len(manifest["images"]), "references": len(manifest["references"]), "approved": counts["approved_unmodified"] + counts["approved_cleaned"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--plan", action="store_true")
    modes.add_argument("--apply", action="store_true", help="merge only explicit selected hashes; gate remains false")
    modes.add_argument("--publish", action="store_true", help="validate final complete scan and reviewed hit dispositions, then open gate")
    parser.add_argument("--candidates", action="append", default=[])
    parser.add_argument("--selections")
    parser.add_argument("--symbol-receipt")
    parser.add_argument("--symbol-dispositions")
    parser.add_argument("--small-badge-receipt")
    parser.add_argument("--small-badge-dispositions")
    args = parser.parse_args()
    finalizer = Finalizer(ROOT)
    if args.publish:
        if args.candidates or args.selections:
            raise FinalizeError("publish_requires_prior_explicit_merge")
        if not all((args.symbol_receipt, args.symbol_dispositions, args.small_badge_receipt, args.small_badge_dispositions)):
            raise FinalizeError("both_frozen_scan_families_required")
        proposed = finalizer.publish(args.symbol_receipt, args.symbol_dispositions, args.small_badge_receipt, args.small_badge_dispositions)
        for relative, body in finalizer.evidence_copies.items():
            immutable_write(finalizer.root, relative, body)
        atomic_manifest(finalizer.path, proposed, finalizer.manifest_sha)
        print(json.dumps({"mode": "publish", "publicationReady": True, "totals": totals(proposed)}))
        return
    if args.apply and not args.selections:
        raise FinalizeError("explicit_selection_receipt_required_for_apply")
    proposed, copies = finalizer.prepare(args.candidates, args.selections)
    if args.apply:
        finalizer.write_merge(proposed, copies)
    missing = [key for key, row in proposed["images"].items() if row["state"] == "review_required"]
    print(json.dumps({"mode": "apply" if args.apply else "plan", "publicationReady": False, "totals": totals(proposed), "selectedCopies": len(copies), "remainingVisualSelections": missing, "finalSymbolAuditStillRequired": True}))


if __name__ == "__main__":
    try:
        main()
    except FinalizeError as error:
        print(json.dumps({"status": "blocked", "code": str(error)}))
        raise SystemExit(1)
    except Exception as error:
        print(json.dumps({"status": "blocked", "code": "invalid_or_unavailable_finalization_input", "exceptionType": type(error).__name__}))
        raise SystemExit(1)
