"""Build only the reviewed mobile-management and home-furniture campaign delta."""
from pathlib import Path
import hashlib,importlib.util,json,os,re,sys
R=Path(__file__).resolve().parents[1];E=R/'artifacts/admin-mobile-social-20261112';B=R/'artifacts/cpanel-release-social-engine-20261112-r6';O=R/'artifacts/cpanel-release-admin-mobile-social-20261112-r1'
def patch_admin(body):
 s=body.decode();s=s.replace("function menu(open){","function menu(open){document.body.classList.toggle('menu-open',open);",1).replace("function clearAdministration(view){","function clearAdministration(view){document.body.classList.remove('menu-open');",1)
 old="async function enter(){schema=await api('schema');resources=schema.resources;route=location.hash.slice(1)||'dashboard';shell();await loadRoute();}";assert s.count(old)==1
 s=s.replace(old,"function resetAdminScroll(){document.activeElement?.blur();window.scrollTo({top:0,left:0,behavior:'instant'});}\nasync function enter(){schema=await api('schema');resources=schema.resources;route=location.hash.slice(1)||'dashboard';shell();await loadRoute();resetAdminScroll();}")
 old="window.addEventListener('hashchange',()=>{if(session.user){$('#editor').close();loadRoute();}});";assert s.count(old)==1
 s=s.replace(old,"window.addEventListener('hashchange',async()=>{if(session.user){const destination=location.hash;$('#editor').close();await loadRoute();if(location.hash===destination)resetAdminScroll();}});")
 s=s.replace('20261112-social-r4','20261112-home-social-r1')
 s+="\nwindow.matchMedia('(max-width:760px)').addEventListener('change',()=>menu(false));\nwindow.addEventListener('keydown',e=>{if(e.key==='Escape'&&document.body.classList.contains('menu-open')){menu(false);$('[data-menu]')?.focus({preventScroll:true});}});\n"
 return s.encode()
def main():
 spec=importlib.util.spec_from_file_location('mobile_home_deploy',R/'scripts/deploy-cpanel.py');d=importlib.util.module_from_spec(spec);sys.modules[spec.name]=d;spec.loader.exec_module(d)
 base=d.load_release(B);expected='3f8a299cb0e28aaa4c99c206a2d7ab31eaab7635d38fb343f3e1cae448dfc73f';assert base['manifest']['releaseHash']==expected and d.CpanelBackend(allow_writes=False).public_health()['releaseHash']==expected;assert not O.exists(),'immutable candidate already exists';E.mkdir(exist_ok=True)
 changes={'private/'+name:(R/'hosting'/name).read_bytes()for name in ['social-campaigns.php','social-engine.php','social-media.php','social-worker.php','social-admin.php']}
 changes.update({'public/'+name:(R/'web'/name).read_bytes()for name in ['admin.css','admin-social.js']});changes['public/admin.js']=patch_admin(base['all_bytes']['public/admin.js'])
 html=re.sub(r'((?:admin\.css|admin\.js|admin-social\.css)\?v=)[^"\s]+',r'\g<1>20261112-home-social-r1',base['all_bytes']['public/admin.html'].decode()).replace('width=device-width, initial-scale=1','width=device-width, initial-scale=1, viewport-fit=cover');changes['public/admin.html']=html.encode()
 for path in (R/'web/assets/social-headlines').glob('headline-*.png'):changes['public/assets/social-headlines/'+path.name]=path.read_bytes()
 assert len([n for n in changes if n.startswith('public/assets/social-headlines/')])==56
 for name in sorted(set(base['manifest']['files'])|set(changes)):
  target=O/name;target.parent.mkdir(parents=True,exist_ok=True)
  if name in changes:target.write_bytes(changes[name])
  else:os.link(B/name,target)
 hashes={n:d.sha256((O/n).read_bytes())for n in sorted(set(base['manifest']['files'])|set(changes))};fp=hashlib.sha256()
 for n,digest in hashes.items():fp.update((n+'\0'+digest+'\0').encode())
 manifest={**base['manifest'],'files':hashes,'releaseHash':fp.hexdigest()};(O/'private/release.json').write_text(json.dumps(manifest,indent=2)+'\n');d.load_release(O)
 for name,body in base['all_bytes'].items():
  if name not in changes and name!='private/release.json':assert (O/name).read_bytes()==body
 proof={'prepared':True,'base':B.relative_to(R).as_posix(),'release':O.relative_to(R).as_posix(),'baseReleaseHash':expected,'releaseHash':manifest['releaseHash'],'changedFiles':sorted(changes),'products':3602,'commerceAndMediaPreserved':True,'paidEnabled':False}
 (E/'release.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps({'prepared':True,'releaseHash':proof['releaseHash'],'changedFiles':len(changes)}))
 W=R/'artifacts/social-engine-20261112/preview';P=W/'public'
 for n,body in changes.items():
  if n.startswith('public/'):
   target=P/n[7:];target.parent.mkdir(parents=True,exist_ok=True)
   if target.exists():target.unlink()
   os.link(O/n,target)
 q=lambda p:"'"+str(p).replace('\\','/').replace("'","\\'")+"'"
 (W/'nodeno-runtime.php').write_text("<?php return ['privateRoot'=>"+q(O/'private')+",'storageRoot'=>"+q(W/'storage')+",'mediaRoot'=>"+q(W/'media')+"];",encoding='utf8')
if __name__=='__main__':main()
