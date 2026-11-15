import {readFile} from 'node:fs/promises';
import {loadMediaApprovals} from '../lib/media-approvals.mjs';
const [root,release]=process.argv.slice(2),media=JSON.parse(await readFile(release+'/private/media.json'));
const proof=await loadMediaApprovals({root,media});
console.log(JSON.stringify({mediaVersion:proof.mediaVersion,references:proof.manifest.referenceCount,testOnly:proof.testOnly||false}));
