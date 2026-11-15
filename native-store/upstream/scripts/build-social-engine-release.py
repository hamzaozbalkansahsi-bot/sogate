"""Build an isolated social-management delta from the exact current live base."""
from pathlib import Path
import hashlib, importlib.util, json, os, re, sys, urllib.request
R=Path(__file__).resolve().parents[1];E=R/'artifacts/social-engine-20261112';B=R/'artifacts/cpanel-release-social-links-pinterest-20261112';O=R/'artifacts/cpanel-release-social-engine-20261112-r5'
spec=importlib.util.spec_from_file_location('social_engine_deployer',R/'scripts/deploy-cpanel.py');d=importlib.util.module_from_spec(spec);sys.modules[spec.name]=d;spec.loader.exec_module(d)

def admin_patch(source):
 s=source.decode();s="import {renderSocial} from './admin-social.js?v=20261112-social-r4';\n"+s
 needle="${allowed('analytics.read')?navItem('analytics'";assert s.count(needle)==1;s=s.replace(needle,"${allowed('marketing.read')?navItem('social','Sosyal medya','message'):''}"+needle)
 needle="'audit','guide','suppliers'].includes(route)";assert s.count(needle)==1;s=s.replace(needle,"'audit','guide','suppliers','social'].includes(route)")
 s=s.replace("analytics:'Ziyaretçi analizi',guide:'Yönetim rehberi'","analytics:'Ziyaretçi analizi',social:'Sosyal medya',guide:'Yönetim rehberi'",1)
 needle="const data=await api(route==='integrations'?'system':route)";assert s.count(needle)==1;s=s.replace(needle,"const data=await api(route==='social'?'social/overview':route==='integrations'?'system':route)")
 needle="else if(route==='suppliers')renderSuppliers";assert s.count(needle)==1;s=s.replace(needle,"else if(route==='social')renderSocial({container:$('#main'),dialog:$('#editor'),data,api,canWrite:allowed('marketing.write'),canConfigure:allowed('settings.write'),canConnect:allowed('integrations.read'),refresh:loadRoute,toast,isCurrent:()=>own===epoch&&Boolean(session.user)});"+needle)
 return s.encode()

def main():
 E.mkdir(exist_ok=True);base=d.load_release(B);expected='52aa2c581c50a205b40f222254e698c28a9a001e784688ad7b132c3329fb5df1';assert base['manifest']['releaseHash']==expected
 with urllib.request.urlopen('https://nodenohome.com/api/health',timeout=40)as response:health=json.load(response)
 assert health['releaseHash']==expected and health['checkoutEnabled'] and health['mediaReady']
 assert not O.exists(),'candidate already exists; do not overwrite immutable release files'
 changes={}
 for name in ['social-engine.php','social-providers.php','social-media.php','social-worker.php','social-admin.php']:changes['private/'+name]=(R/'hosting'/name).read_bytes()
 for name in ['admin-social.js','admin-social.css']:changes['public/'+name]=(R/'web'/name).read_bytes()
 for name in ['social-logo.png','social-mark.png']:changes['public/assets/brand/'+name]=(R/'web/assets/brand'/name).read_bytes()
 changes['public/admin.js']=admin_patch(base['all_bytes']['public/admin.js'])
 html=base['all_bytes']['public/admin.html'].decode();html=re.sub(r'((?:admin\.css|admin\.js)\?v=)[^"\s]+',r'\g<1>20261112-social-r4',html);assert '20261112-social-r4'in html
 html=html.replace('<script type="module"','<link rel="stylesheet" href="/admin-social.css?v=20261112-social-r4"><script type="module"',1);changes['public/admin.html']=html.encode()
 source=(R/'hosting/index.php').read_text(encoding='utf8');a=source.index("        if(preg_match('~^/social-media/");b=source.index("        if($path==='/legal'",a);block=source[a:b]
 index=base['all_bytes']['public/index.php'].decode();needle='        $private = nodenoPrivateRoot();';assert index.count(needle)==1;changes['public/index.php']=index.replace(needle,needle+'\n'+block,1).encode()
 control=base['all_bytes']['private/control-http.php'].decode();source=(R/'hosting/control-http.php').read_text(encoding='utf8');line=next(line for line in source.splitlines(True)if "if($resource==='social')"in line);needle=" if($route==='team')return nodenoControlTeam($ctx,$method,$body);";assert control.count(needle)==1;changes['private/control-http.php']=control.replace(needle,needle+'\n'+line,1).encode()
 for name in sorted(set(base['manifest']['files'])|set(changes)):
  target=O/name;target.parent.mkdir(parents=True,exist_ok=True)
  if name in changes:target.write_bytes(changes[name])
  else:os.link(B/name,target)
 hashes={name:d.sha256((O/name).read_bytes())for name in sorted(set(base['manifest']['files'])|set(changes))};fp=hashlib.sha256()
 for name,digest in hashes.items():fp.update((name+'\0'+digest+'\0').encode())
 manifest={**base['manifest'],'files':hashes,'releaseHash':fp.hexdigest()};(O/'private/release.json').write_text(json.dumps(manifest,indent=2)+'\n');d.load_release(O)
 for name in ['private/catalog.json','private/config.json','private/media.json','private/media-approved.json','private/door-catalog.json','private/cabinet-fronts.json','private/supplier-details.bin']:assert (O/name).read_bytes()==base['all_bytes'][name],name
 proof={'prepared':True,'base':B.relative_to(R).as_posix(),'release':O.relative_to(R).as_posix(),'baseReleaseHash':expected,'releaseHash':manifest['releaseHash'],'changedFiles':sorted(changes),'cataloguePricesMediaAndCheckoutUnchanged':True,'sourceAdminMatchesCandidate':changes['public/admin.js']==(R/'web/admin.js').read_bytes(),'products':health['products'],'paidProductionEnabled':False}
 (E/'release.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof))
if __name__=='__main__':main()
