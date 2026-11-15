"""Deploy only the reviewed welcome candidate using the standard guarded uploader."""
from pathlib import Path
import argparse,importlib.util,json,sys,urllib.request

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();mode=parser.add_mutually_exclusive_group();mode.add_argument('--plan',action='store_true');mode.add_argument('--apply',action='store_true');parser.add_argument('--expect-release');args=parser.parse_args()
spec=importlib.util.spec_from_file_location('nodeno_guarded_deployment',ROOT/'scripts/deploy-cpanel.py')
deploy=importlib.util.module_from_spec(spec);sys.modules[spec.name]=deploy;spec.loader.exec_module(deploy)
build=json.loads((ROOT/'artifacts/welcome-poster/build.json').read_bytes())
release=deploy.load_release(ROOT/'artifacts/cpanel-release-welcome-20261103')
assert release['manifest']['releaseHash']==build['releaseHash']
if args.expect_release and args.expect_release!=build['releaseHash']:raise deploy.DeployError('reviewed_release_changed')
if args.apply and not args.expect_release:raise deploy.DeployError('explicit_reviewed_release_required')
print(json.dumps({'stage':'validate_existing_media_audit','releaseHash':build['releaseHash']}),flush=True)
deploy.validate_media_publication(ROOT,release)
print(json.dumps({'stage':'media_audit_verified','releaseHash':build['releaseHash']}),flush=True)
request=urllib.request.Request('https://nodenohome.com/api/health',headers={'Cache-Control':'no-cache'})
with urllib.request.urlopen(request,timeout=30)as response:health=json.loads(response.read(131072))
if health.get('status')!='ok' or health.get('releaseHash')!=build['baseReleaseHash']:raise deploy.DeployError('live_base_changed')
backend=deploy.CpanelBackend(allow_writes=args.apply)
plan=deploy.make_plan(release,backend)
(ROOT/'artifacts/welcome-poster/deployment-plan.json').write_text(json.dumps(plan,indent=2)+'\n')
print(json.dumps(plan),flush=True)
if args.apply:
 local=json.loads((ROOT/'artifacts/welcome-poster/local-acceptance.json').read_bytes())
 if local.get('passed')is not True or local.get('releaseHash')!=build['releaseHash']:raise deploy.DeployError('local_browser_acceptance_required')
 deploy.apply_release(release,backend,plan)
