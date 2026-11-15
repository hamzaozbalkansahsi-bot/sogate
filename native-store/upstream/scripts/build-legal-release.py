"""Apply the reviewed legal-document delta to the immutable live catalogue release."""
from pathlib import Path
import difflib, hashlib, importlib.util, json, os, re, sys, urllib.request
R=Path(__file__).resolve().parents[1];E=R/'artifacts/legal-20261110'
spec=importlib.util.spec_from_file_location('nodeno_legal_deploy',R/'scripts/deploy-cpanel.py');d=importlib.util.module_from_spec(spec);sys.modules[spec.name]=d;spec.loader.exec_module(d)
with urllib.request.urlopen('https://nodenohome.com/api/health',timeout=30)as response:health=json.load(response)
candidates=[p for p in(R/'artifacts').glob('cpanel-release*')if(p/'private/release.json').is_file()and json.loads((p/'private/release.json').read_bytes()).get('releaseHash')==health['releaseHash']]
assert len(candidates)==1,'unique_live_artifact_required';B=candidates[0];base=d.load_release(B);O=R/'artifacts/cpanel-release-legal-20261110-r3';assert not O.exists(),'use_a_new_release_directory';changes={};applied={}
def patch_source(source,target):
 before=(E/'baseline'/source).read_text(encoding='utf8');after=(R/source).read_text(encoding='utf8');text=base['all_bytes'][target].decode().replace('\r\n','\n');a=before.splitlines(keepends=True);b=after.splitlines(keepends=True);count=0
 if not text.endswith('\n'):text+='\n'
 for group in reversed(list(difflib.SequenceMatcher(None,a,b,autojunk=False).get_grouped_opcodes(1))):
  old=''.join(a[group[0][1]:group[-1][2]]);new=''.join(b[group[0][3]:group[-1][4]])
  if text.count(old)==0 and new and text.count(new)==1:continue
  if group[-1][2]==len(a)and text.endswith(old):text=text[:-len(old)]+new
  elif group[0][1]==0 and text.startswith(old):text=new+text[len(old):]
  else:
   assert old and text.count(old)==1,'source_delta_drift:'+source+':'+str(group[0][1]);text=text.replace(old,new,1)
  count+=1
 changes[target]=text.encode();applied[source]=count
for source,target in [('web/app.js','public/app.js'),('web/payments.js','public/payments.js'),('web/shop-i18n.js','public/shop-i18n.js'),('hosting/index.php','public/index.php'),('hosting/payments.php','private/payments.php'),('hosting/account.php','private/account.php')]:patch_source(source,target)
for source,target in [('web/store-insights.js','public/store-insights.js'),('hosting/control-analytics.php','private/control-analytics.php')]:changes[target]=(R/source).read_bytes()
# The source shopping module has older cache query strings unrelated to this task; retain the live dependency URLs.
shopping=(R/'web/shopping-ui.js').read_text(encoding='utf8');old=base['all_bytes']['public/shopping-ui.js'].decode()
for filename in ['door-core.js','shop-core.js','shopping-core.js']:
 pattern=re.escape(filename)+r'\?v=[^\'\"]+';live=re.search(pattern,old);assert live;shopping=re.sub(pattern,lambda m:live.group(),shopping)
changes['public/shopping-ui.js']=shopping.encode()
for name in ['legal.css','legal.js','legal-links.js','privacy-preferences.js']:changes['public/'+name]=(R/'web'/name).read_bytes()
for name in ['legal.php','payment-documents.php','membership-legal.php']:changes['private/'+name]=(R/'hosting'/name).read_bytes()
for locale in ['tr','en','ru','ar']:changes['private/site-documents.'+locale+'.json']=(R/'data/legal'/('site-documents.'+locale+'.json')).read_bytes()
html=base['all_bytes']['private/index.html'].decode();html,count=re.subn(r'/app.js\?v=[^"\s]+','/app.js?v=nodeno-legal-20261110-r1',html);assert count==1;changes['private/index.html']=html.encode()
for name in set(base['manifest']['files'])|set(changes):
 target=O/name;target.parent.mkdir(parents=True,exist_ok=True)
 if name in changes:target.write_bytes(changes[name])
 else:os.link(B/name,target)
hashes={name:hashlib.sha256((O/name).read_bytes()).hexdigest()for name in sorted(set(base['manifest']['files'])|set(changes))};fingerprint=hashlib.sha256()
for name,digest in hashes.items():fingerprint.update((name+'\0'+digest+'\0').encode())
manifest={**base['manifest'],'releaseHash':fingerprint.hexdigest(),'files':hashes};(O/'private/release.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8');release=d.load_release(O)
for name,body in base['all_bytes'].items():
 if name not in changes and name!='private/release.json':assert release['all_bytes'][name]==body
record={'prepared':True,'base':str(B.relative_to(R)),'release':str(O.relative_to(R)),'baseReleaseHash':base['manifest']['releaseHash'],'releaseHash':manifest['releaseHash'],'changedFiles':sorted(changes),'sourceHunksApplied':applied,'catalogueAndMediaUnchanged':True,'liveCheckoutPreserved':True};(E/'release-preparation.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))
