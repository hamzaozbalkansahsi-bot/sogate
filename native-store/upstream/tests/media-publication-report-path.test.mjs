import test from 'node:test';
import assert from 'node:assert/strict';
import * as approvals from '../lib/media-approvals.mjs';
const digest='a'.repeat(64);
test('observed plaque recalibration reports remain confined to exact audit directories',()=>{
 for(const dir of ['web-supplemental','web-supplemental-v2'])assert.equal(approvals.isPublicationReportPath('whole_object_supplemental',`artifacts/media-object-removal-20261102/${dir}/reports/${digest}.json`),true);
 for(const p of [`artifacts/media-object-removal-20261102/web-supplemental-v2/reports/../${digest}.json`,`artifacts/arbitrary/reports/${digest}.json`,`artifacts/media-object-removal-20261102/web-supplemental-v2/reports/not-a-hash.json`])assert.equal(approvals.isPublicationReportPath('whole_object_supplemental',p),false);
 assert.equal(approvals.isPublicationReportPath('flame',`artifacts/media-object-removal-20261102/web-supplemental-v2/reports/${digest}.json`),false);
 assert.equal(approvals.isPublicationReportPath('flame',`artifacts/media-symbol-audit/reports/${digest}.json`),true);
});
