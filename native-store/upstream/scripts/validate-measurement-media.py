"""Run the full existing publication gate; record its immutable media inputs."""
from pathlib import Path
import importlib.util,json,sys,hashlib
R=Path(__file__).resolve().parents[1];E=R/'artifacts/measurement-orders';s=importlib.util.spec_from_file_location('measurement_full_media_gate',R/'scripts/deploy-cpanel.py');d=importlib.util.module_from_spec(s);sys.modules[s.name]=d;s.loader.exec_module(d)
release=d.load_release(R/'artifacts/cpanel-release-measurements-20261110');print(json.dumps({'stage':'full_media_audit_started','releaseHash':release['manifest']['releaseHash']}),flush=True)
d.validate_media_publication(R,release)
names=['private/media.json','private/media-approved.json','private/door-catalog.json','private/cabinet-fronts.json'];proof={'passed':True,'auditReleaseHash':release['manifest']['releaseHash'],'mediaVersion':release['manifest']['mediaVersion'],'files':{name:hashlib.sha256(release['all_bytes'][name]).hexdigest()for name in names},'sourceReportSha256':hashlib.sha256((R/'artifacts/media-cleanup.json').read_bytes()).hexdigest()};(E/'full-media-audit.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps({'stage':'all_media_verified',**proof}),flush=True)
