"""Build a narrow blog overlay on the freshly verified live release; preserve all other work."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,os,sys,re
R=Path(__file__).resolve().parents[1];E=R/'artifacts/blog-20261112'
sys.path.insert(0,str(R))
from lib.blog_bundle import merge_bundles
def module():
 s=importlib.util.spec_from_file_location('blog_release_deploy',R/'scripts/deploy-cpanel.py');m=importlib.util.module_from_spec(s);sys.modules[s.name]=m;s.loader.exec_module(m);return m
def patch_once(body,before,after):
 if after in body:return body
 if body.count(before)!=1:raise RuntimeError('blog_hook_base_mismatch')
 return body.replace(before,after)
def changes_for(base,bank):
 date_spec=importlib.util.spec_from_file_location('blog_date_overlay',R/'scripts/prepare-date-time-release.py');date_module=importlib.util.module_from_spec(date_spec);date_spec.loader.exec_module(date_module);changes=date_module.changes_for(base)
 changes.update({'private/'+n:(R/'hosting'/n).read_bytes()for n in ['blog-store.php','blog-worker.php','blog-admin.php','blog-http.php','blog.php','blog-i18n.php','blog-surface.php','blog-admin.html','date-time.php']});changes['private/blog-bank.json']=(R/'data/blog-bank.json').read_bytes()
 for name in ['blog-images.json','blog-images.bin']:changes['private/'+name]=(R/'data'/name).read_bytes()
 old_index=base['all_bytes'].get('private/blog-images.json');old_blob=base['all_bytes'].get('private/blog-images.bin',b'');index,blob=merge_bundles(json.loads(old_index)if old_index else None,old_blob,json.loads(changes['private/blog-images.json']),changes['private/blog-images.bin']);changes['private/blog-images.json']=(json.dumps(index,separators=(',',':'))+'\n').encode();changes['private/blog-images.bin']=blob
 for name in ['blog.css','blog-tools.js','blog-surface.js','blog-admin.js','blog-entry.js','date-time.js']:changes['public/'+name]=(R/'web'/name).read_bytes()
 for a in bank['articles']:
  name='public'+a['image']['url'];body=(R/'web'/a['image']['url'].lstrip('/')).read_bytes()
  if hashlib.sha256(body).hexdigest()!=a['image']['sha256']:raise RuntimeError('blog_illustration_changed')
  for translation in a.get('locales',{}).values():
   image=translation['image'];name='public'+image['url'];body=(R/'web'/image['url'].lstrip('/')).read_bytes()
   if hashlib.sha256(body).hexdigest()!=image['sha256']:raise RuntimeError('translated_illustration_changed')
 index=base['all_bytes']['public/index.php'];needle=b'$private = nodenoPrivateRoot();';hook=b"\n        if(is_file($private.'/blog-http.php')){require_once $private.'/blog-http.php';if(nodenoBlogHttp($path,$method,$private,__DIR__))return;}"
 index=patch_once(index,needle,needle+hook)
 index=patch_once(index,b"$supplierHealth=[];",b"$blogHealth=[];if(is_file($private.'/blog-bank.json')){require_once $private.'/blog-worker.php';$storage=nodenoRuntimeConfiguration()['storageRoot']??dirname(__DIR__).'/nodeno-data';if(!is_string($storage))throw new RuntimeException('Invalid blog storage');$blogHealth=nodenoBlogMediaHealth($storage,$private,__DIR__);}$supplierHealth=[];")
 index=patch_once(index,b"...$supplierHealth,",b"...$supplierHealth,...$blogHealth,")
 old=b"nodenoRespond((string)file_get_contents(__DIR__.'/admin.html'),200"
 new=b"nodenoRespond(str_replace('</head>','<script type=\"module\" src=\"/blog-entry.js?v=20261112-r1\"></script></head>',(string)file_get_contents(__DIR__.'/admin.html')),200"
 if b'/blog-entry.js?v='not in index:index=patch_once(index,old,new)
 changes['public/index.php']=re.sub(rb'(/blog-entry\.js\?v=)[^"\']+',rb'\g<1>20261113-r2',index)
 html=changes.get('private/index.html',base['all_bytes']['private/index.html'])
 if b'/blog-entry.js?v='not in html:html=patch_once(html,b'</head>',b'<script type="module" src="/blog-entry.js?v=20261113-r2"></script></head>')
 changes['private/index.html']=re.sub(rb'(/blog-entry\.js\?v=)[^"\']+',rb'\g<1>20261113-r2',html)
 seo=base['all_bytes']['private/seo.php'];needle=b"return $prefix.'<sitemapindex xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">'.$body.'</sitemapindex>';"
 changes['private/seo.php']=patch_once(seo,needle,b"if(is_file(__DIR__.'/blog-bank.json'))$body.='<sitemap><loc>'.NODENO_SEO_ORIGIN.'/sitemap-blog.xml</loc></sitemap>';"+needle)
 htaccess=base['all_bytes']['public/.htaccess'];needle=b'# Keep source, configuration and caches unreachable';changes['public/.htaccess']=patch_once(htaccess,needle,b'RewriteRule ^assets/blog/ index.php [END]\n\n'+needle)
 return {name:body for name,body in changes.items()if base['all_bytes'].get(name)!=body}
def main():
 p=argparse.ArgumentParser();p.add_argument('--preview',action='store_true');args=p.parse_args();d=module();health=d.CpanelBackend().public_health();live=health['releaseHash'];candidates=[]
 for path in(R/'artifacts').glob('cpanel-release*/private/release.json'):
  try:
   if json.loads(path.read_bytes()).get('releaseHash')==live:candidates.append(path.parent.parent)
  except (OSError,json.JSONDecodeError):continue
 if not candidates:raise RuntimeError('current_live_base_not_available')
 B=candidates[0];base=d.load_release(B);bank=json.loads((R/'data/blog-bank.json').read_bytes());quality=json.loads((E/'content-quality.json').read_bytes())
 if not args.preview:
  if bank.get('publicationReady')is not True or len(bank['articles'])<250 or any(len(a.get('locales',{}))<3 for a in bank['articles']):raise RuntimeError('complete_editorial_bank_required')
  if quality['bankSha256']!=hashlib.sha256((R/'data/blog-bank.json').read_bytes()).hexdigest():raise RuntimeError('content_quality_stale')
 if json.loads((R/'artifacts/media-cleanup.json').read_bytes()).get('publicationReady')is not True:raise RuntimeError('media_publication_gate_not_ready')
 changes=changes_for(base,bank);dig=hashlib.sha256(b''.join(k.encode()+hashlib.sha256(v).digest()for k,v in sorted(changes.items()))).hexdigest()[:12];O=R/('artifacts/cpanel-release-blog-20261112-'+('preview-'if args.preview else'')+dig)
 if O.exists():raise RuntimeError('blog_candidate_already_exists')
 for name in sorted(set(base['manifest']['files'])|set(changes)):
  target=O/name;target.parent.mkdir(parents=True,exist_ok=True)
  if name in changes:target.write_bytes(changes[name])
  else:os.link(B/name,target)
 files={n:hashlib.sha256((O/n).read_bytes()).hexdigest()for n in sorted(set(base['manifest']['files'])|set(changes))};fp=hashlib.sha256()
 for name,digest in files.items():fp.update((name+'\0'+digest+'\0').encode())
 manifest={**base['manifest'],'files':files,'releaseHash':fp.hexdigest(),'testOnly':bool(args.preview)};(O/'private/release.json').write_text(json.dumps(manifest,indent=2)+'\n')
 if not args.preview:d.load_release(O)
 if not all((O/name).read_bytes()==body for name,body in base['all_bytes'].items()if name not in changes and name!='private/release.json'):raise RuntimeError('unrelated_release_bytes_changed')
 proof={'prepared':True,'preview':args.preview,'base':B.relative_to(R).as_posix(),'release':O.relative_to(R).as_posix(),'baseReleaseHash':live,'releaseHash':manifest['releaseHash'],'changedFiles':sorted(changes),'articles':len(bank['articles']),'publicProducts':health['products'],'expectedCheckoutEnabled':health['checkoutEnabled'],'mediaUnchanged':True,'catalogueAndPriceBytesPreserved':True,'otherChatEditorBytesPreserved':True}
 (E/('preview-release.json'if args.preview else'release.json')).write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps({k:v for k,v in proof.items()if k!='changedFiles'}))
if __name__=='__main__':main()
