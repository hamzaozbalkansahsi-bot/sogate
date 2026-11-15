# Complete catalogue media refresh implementation plan

> For agentic workers: execute inline with superpowers:executing-plans, test-driven-development and verification-before-completion. Obtain one independent final review of the concrete candidate and its evidence.

**Goal:** Update the last synchronized 168-page complete catalogue, retaining all 709 records (667 site products and 42 PDF-only records).

**Architecture:** Freeze the current complete PDF and its identity proof. Match outdated appendix photos by reproducing their exact source JPEG bytes. Transfer only reviewed cleanup masks to native PDF samples, preserving page content and image geometry. Audit every displayed native image with the frozen expanded brand matchers; inspect candidates and final retouches. Promote the validated candidate to the canonical filename and update only PDF identity/hash metadata.

**Tech stack:** PyMuPDF, Pillow, NumPy/OpenCV, Poppler, existing Node tests.

**Spec:** Root AGENTS.md and the user's latest instruction to work from the last catalogue/site synchronization, not the older 86-page example.

## Global constraints

- Baseline canonical file: `output/pdf/NODENO_Mobilya_Katalogu_2026_Tam_Katalog.pdf`, SHA-256 `37a49d0b5d76a54f48accec53f2ab25bac34525079c0dbf40510ef89531be0d1`.
- Preserve page count, page boxes, text and text positions, product names/codes/technical facts, links, TOC, image placements/resolution, ICC semantics and soft masks.
- Preserve native RGB outside each approved print mask; no whole-photo recompression or unverified image substitution.
- Keep source PDFs and current website media unchanged. Retain an immutable baseline copy. Author only in the ignored PDF workspace before validated promotion.
- No website deployment, cloud upload, changes to prices or inclusion of the 42 deferred records in the site.
- Only PDF identity metadata and its dependent model identity hash may change in canonical data; product and model records must remain equal.

## Review focus

- A similar-looking sibling photo must never replace the intended SKU: require exact JPEG reconstruction and one matching displayed xref on the product's recorded page.
- Alpha, ICC profiles, PDF Decode/ColorSpace and native dimensions must remain valid; unsupported image encodings must fail closed.
- A shared image xref can appear on several pages: enumerate and verify every placement.
- Zero template hits are not blanket visual approval. Independently update all 20 known stale photos and review every scan candidate.
- Metadata promotion must not break the 667-product identity mapping or stale the model hash; guard inputs against concurrent changes.

## Task 1: freeze, synchronize and audit

Files: ignored workspace `tmp/pdfs/full-catalogue-media-20261101/`; durable evidence `artifacts/pdf-media-refresh-20261101/`.

- [x] Freeze canonical bytes, identity proof and media manifest hashes. Verify the PDF contains the 709 recorded codes and includes all 667 live site IDs/codes.
- [x] Inventory all displayed xrefs, native sample/mask hashes, ColorSpace, Decode, dimensions and placements. Extract lossless audit images.
- [x] Reconstruct old panel JPEGs with the original `quality=92,optimize=True,subsampling=0` recipe; require exactly one byte-identical match per changed photo. The observed initial set is 20 panels, including `3547:0` on page 96.
- [x] Scan all distinct audit images with the frozen physical, bare-word, legacy-small and flame matchers on white/black composites and a size pyramid. Bind caches to native pixels, matcher/reference bytes and background/scale. Visually resolve every relevant hit.

## Task 2: patch native rasters with RED/GREEN preservation tests

Interface: `patch_image(doc, xref, replacement_rgb, mask) -> validation dict` in the ignored workspace's `native_patch.py`.

- [x] Write tests before implementation. A no-op patch must fail a literal changed-pixel assertion; wrong masks/dimensions and alpha-zero masks must be rejected. A real PDF round trip must preserve soft-mask bytes, ICC/ColorSpace, image size, text, page boxes and link destinations.

```python
before = np.array([[[10,20,30],[40,50,60]]], dtype=np.uint8)
after = np.array([[[90,80,70],[40,50,60]]], dtype=np.uint8)
mask = np.array([[True,False]])
assert patch_samples(before, after, mask).tolist() == [[[90,80,70],[40,50,60]]]
```

- [x] Implement the minimal lossless stream update. Validate mask hashes and current approved-image hashes before applying. Preserve native samples outside masks and all soft masks; reject indexed/unsupported streams until explicitly handled and tested if actually needed.
- [x] Generate a candidate only after running the PDF artifact-operation marker exactly once. Inspect every changed field before/after at native zoom and every full changed product. Reject residual glyphs or misplaced masks; add only observed additional PDF findings.
- [x] Rescan changed outputs with the same frozen matcher fingerprint. Confirm every known stale panel now maps to a modified clean raster.

## Task 3: complete verification and delivery

- [x] Reopen the saved candidate. Compare all 168 pages' text/spans, boxes, TOC, links, native image geometry and alpha. Unchanged pages/images must remain exact. Changed images must have zero RGB differences outside approved masks.
- [x] Render all pages and inspect contact sheets; inspect changed pages and the Studia 510 page at full resolution.
- [x] Independently review the candidate, patch code, evidence, identity preservation and scan dispositions; resolve material findings with RED/GREEN tests.
- [x] Promote only after all checks pass. Preserve the old canonical PDF in durable evidence. Update `complete-identities.json.outputPdf`, `catalog-identities.json.sourcePdf`, affected photo provenance, and the dependent `product-models.json.identitiesSha256`; assert all semantic product/model records unchanged.
- [x] Run the identity importer/validation and full Node suite with PHP, and the production build. Verify all 667 live IDs/codes still match the updated PDF. Record the final PDF SHA, source hashes, review scope and tests; deliver the canonical complete PDF.

## Ledger

- Baseline and scope confirmed: 168 pages, 709 records; 667 site products plus 42 intentionally retained PDF-only records. The old 86-page sharing PDF is not the editing base.
- Exact JPEG reconstruction found all 20 stale appendix panels without ambiguous matches. The immutable source was matched before authoring; subsequent candidates were generated only in scratch.
- Artifact editing uses an ignored scratch directory; repository implementation files and other ongoing website work are preserved. This is not a new application feature branch.

- Task 1 complete: 1,129 displayed xrefs plus 11 inline instances, 1,133 distinct native audit images; exact JPEG matches for all 20 stale panels; all 371 expanded-pass and 80 oblique-pass source hits visually resolved.
- Task 2 complete: 28 images / 36 print fields. Seven preservation tests RED/GREEN, three supplemental calibration tests RED/GREEN, and one historical-builder guard test RED/GREEN pass (11 total). Native glyph-tip previews were rejected and refined before acceptance.
- Task 3 verification: saved candidate SHA 2d9d3a6c47c3dd585f1361d571ff91a99bd683a6b2e6c3f642fd2a85b45d7547; all 168 pages / 709 identities / links and text spans verified; 1,101 unchanged rasters and 2,842 non-target streams exact; zero native differences outside reviewed masks.
- Two frozen full-coverage final scans each cover 1,133 distinct images. All 432 final candidates resolved as actual visually inspected false positives or byte-identical reviewed-crop reuse. Final native output sheets and all page layout contacts inspected; changed pages inspected at full page resolution.
- Ruling: Native PDF samples and ICC semantics are preserved instead of replacing/recompressing whole photos — this protects product geometry/color and catalogue layout; unsupported stream types fail closed.
- Ruling: The expanded website matchers missed oblique vanity plaques exposed by full-page visual QA. Added two observed PDF specimens in a separate hash-bound supplemental pass, preserving the initial frozen pass; five more native images were corrected. No failed candidate was delivered.
- Ruling: Review the artifact package and staged metadata rather than a branch diff — this is a local PDF revision amid unrelated active website changes, with ignored canonical artifacts. Existing application changes are outside this task.
- Ruling: The historical 86-page builder now refuses a complete proof with mediaRevision before reading its old source — rebuilding from it would reintroduce native plaques. A meaningful failing then passing guard test records this regression.
- Disk-full recovery: only this task's superseded generated PDFs were removed. The baseline PDF and original source photos remained intact. Interrupted report writes were regenerated; all actual visual decisions were restored from the reviewed index snapshots and bound again to report/image hashes.
- Fresh independent review and canonical metadata promotion subsequently passed; see final ledger below. Pre-promotion Node suite: 174 pass / 0 fail / 0 skipped, with local PHP on PATH. Metadata is staged and semantic records compare equal.

- Final review: /root/pdf_final_review on gpt-6-astra independently approved exact candidate and staged promotion, with no P0/P1/P2 findings and an empty Declined to judge list. Independent checks covered all page text/geometry/links, all 28 changed rasters, both full scan key sets and dispositions, exact Studia JPEG reconstruction and staged metadata semantics.
- Canonical promotion complete: reviewed acceptance publicationReady=true; candidate moved atomically to output/pdf/NODENO_Mobilya_Katalogu_2026_Tam_Katalog.pdf with SHA-256 2d9d3a6c47c3dd585f1361d571ff91a99bd683a6b2e6c3f642fd2a85b45d7547. Immutable baseline and old 86-page source hashes verified intact.
- Post-promotion importer passed (667 matched / 42 PDF-only retained). Regenerated mapping bytes exactly match staged bytes; dependent model identity SHA verified; all semantic records unchanged. Historical builder was exercised against the real current proof and refused before reading its old source. Current live API IDs/codes match all 667 mapped products.
- Final tests: 11 PDF preservation/calibration/guard tests pass; full Node suite with PHP 174 pass / 0 fail / 0 skipped; production build passes with 667 products and 667 catalogue identities. Final native inventory contains zero samples matching the 28 known branded before-hashes, including alternate xrefs.
- Delivery record: artifacts/pdf-media-refresh-20261101/delivery-record.json. No website deployment, source-photo modification, price change, or inclusion of the 42 deferred records occurred in this PDF task.
