"""Publish the reviewed owner catalogue extension through all existing gates."""
from pathlib import Path
import argparse,importlib.util,json,sys,urllib.request
R=Path(__file__).resolve().parents[1];E=R/'artifacts/project-commerce'
parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');parser.add_argument('--expect-release',required=True);args=parser.parse_args()
spec=importlib.util.spec_from_file_location('guarded_project_deployment',R/'scripts/deploy-cpanel.py');deploy=importlib.util.module_from_spec(spec);sys.modules[spec.name]=deploy;spec.loader.exec_module(deploy)
build=json.loads((E/'build.json').read_bytes());release=deploy.load_release(R/'artifacts/cpanel-release-projects-20261110')
assert args.expect_release==build['releaseHash']==release['manifest']['releaseHash']
local=json.loads((E/'local-acceptance.json').read_bytes());assert local['passed']is True and local['releaseHash']==build['releaseHash']
print(json.dumps({'stage':'validate_all_media','releaseHash':build['releaseHash']}),flush=True)
deploy.validate_media_publication(R,release)
print(json.dumps({'stage':'all_media_verified','releaseHash':build['releaseHash']}),flush=True)
with urllib.request.urlopen(urllib.request.Request('https://nodenohome.com/api/health',headers={'Cache-Control':'no-cache'}),timeout=30)as response:health=json.loads(response.read(131072))
if health.get('status')!='ok'or health.get('releaseHash')!=build['baseReleaseHash']:raise deploy.DeployError('live_base_changed')
backend=deploy.CpanelBackend(allow_writes=args.apply);plan=deploy.make_plan(release,backend)
(E/'deployment-plan.json').write_text(json.dumps(plan,indent=2)+'\n');print(json.dumps(plan),flush=True)
if args.apply:
 # The exact reviewed package and acceptance may not change during the audit.
 final=deploy.load_release(R/'artifacts/cpanel-release-projects-20261110');assert final['manifest']['releaseHash']==build['releaseHash']
 assert json.loads((E/'local-acceptance.json').read_bytes())['releaseHash']==build['releaseHash']
 deploy.apply_release(release,backend,plan)
