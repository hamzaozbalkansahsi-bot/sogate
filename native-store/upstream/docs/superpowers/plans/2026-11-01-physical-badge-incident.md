# Physical badge incident implementation plan

Goal: correct physical supplier plaques missed in Studia 510 (`3547:5`) and related images, and require current image evidence for build/upload/deploy. Root AGENTS.md applies. Preserve originals, technical facts, geometry, color, full alpha, invisible RGB, ICC, orientation, RGB outside reviewed print masks, unrelated work and live account data.

## Progress

- [x] Reproduce reported real plaque with RED/GREEN regression evidence; inspect all five Studia color galleries.
- [x] Review related complete furniture galleries, montages and background furniture; record 308 newly confirmed source files and narrow masks in `data/media-brand-incidents.json`.
- [x] Inspect/refine/select/merge all 308 additions with hash-bound receipts: **552 cleaned / 4577 unchanged**, 5129 references. Original sources remain untouched.
- [x] Freeze physical scan (21 references) and bare-word extension (7 references), covering every source/output, animation frame and black/white alpha composite without a four-hit cap.
- [x] Bind current file/frame/report/disposition/selection hashes in Python and Node; independently reject known bad original bytes even with zero detections; require valid publication proof and matching catalog mediaVersion before writes.
- [x] RED/GREEN for visible semi-transparent print pixels: alpha >0 may be retouched while full alpha and invisible RGB stay exact; masks on fully invisible pixels remain forbidden.
- [x] Complete physical scan: 5427 unique source/output files, 5129/5129 references; all physical candidate fields reviewed. Complete flame scan and 4109 hit decisions; only exact report or identical reviewed raster reuse.
- [x] Finish all animated scans, final complete receipt/dispositions and publication gate (publicationReady true).
- [x] Final build/tests (158/158 Node; Python suites green); media-only package 02efc3db… based on exact live 33a750d6…; isolated PHP and Chromium/WebKit preview, 24 combinations /216 gallery image hash checks.
- [x] Upload all 308 immutable new files; backed-up media-only release 02efc3db… live. 308/308 live raster SHA/size/MIME/ETag checks, old-version/ETag request, four aliases with hostname preservation, Chromium desktop/mobile + WebKit mobile gallery/zoom, four languages/RTL PASS. Post-deploy public and private package readback checks PASS. Final evidence: `artifacts/media-badge-incident/delivery-record.json`.

## Exact identities and evidence

- Main pipeline `37fbdbdb594cb9d366fec3cb7f2662a694d4497ea7545607d471d23c3a9ecbd9`.
- Physical pass `9482d713b5255b91b20ac24b7a144d2e06e6af16d1772cc46dd327cf181becd9`, log `artifacts/media-badge-incident/physical-final552.log`.
- Required combined pass `a46caa002d99f3ff2ba83b4f8003b51febb0f8f74dddb245ea663d2e3e3ca78d`, 28 exact references in `data/media-audit-policy.json`. Checkpoints issue no coverage receipt.
- Flame pass `65506c85586787cd33916d83b7f978e08f94e2d6ac401faaf461d8a1a018a71d`, log `flame-final552.log`.
- Live base `33a750d6c4b199c8222b236ceaa0a68d8f78272126b423d87f7fdda3589825ee`; old media version `29bcdb19417fc48c616484561717c74070beb762cdc1b8cbc6bf51682a875249`. First base `f0836a66…` was superseded by other work; never restore it. Live was rechecked immediately before package/apply.
- Base snapshot `artifacts/cpanel-preview-33a750d6c4b199c8`. Media-only builder changes private catalog mediaVersion, approved media JSON and release metadata only. Assert public files/account/config/products/categories unchanged. Isolated deploy module uses exact base private inventory, preserving unrelated OAuth work.
- Retouch receipts under `artifacts/media-badge-incident/{candidates,selections}.json` and `{extra,round2,round3,round4,round5,round6,round7}/{candidates,selections}.json`; full/crop sheets and native coordinate grids retained. Round7: 64 fields/62 files, six rejected masks refined and final hashes reviewed separately.
- Invalid development checkpoint: wrong default matcher generated 39 reports; stopped/quarantined before publication, zero incremental descendants. All regenerated using correct frozen matcher and superseded by final full CLI scan. Evidence `invalid-checkpoint-reports.json`, `invalid-checkpoint-quarantine/`, `physical-new-outputs-valid.log`.
- Final tests: 158/158 Node (0 failed, 0 skipped), 81 Python media, 18 cPanel and 9 upload tests pass. Final-policy reruns: 18 finalizer and 8 scanner tests pass. Production build passes; the stale package-file expectation was corrected without changing the account implementation.

Zero automatic matches do not prove manual review of every unchanged image. Decisions apply to exact inspected fields or identical reviewed raster fields with provenance. Local and live acceptance are separate.

Final acceptance: local PASS and live PASS. Backup `20261101T022718Z-02efc3db7efc-be896f`; accounts/config/products/categories/prices/public assets preserved; no remote deletions. Verification-client cache-header and Fileman text-transcoding assumptions were corrected without production changes; exact successful final receipts are retained.
