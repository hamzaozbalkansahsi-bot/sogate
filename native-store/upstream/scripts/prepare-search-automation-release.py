"""Prepare a current-base search worker and approved-only blog launch. No remote writes."""
from pathlib import Path
import hashlib,importlib.util,json,os,sys,re
R=Path(__file__).resolve().parents[1];E=R/'artifacts/search-automation-20261112';E.mkdir(exist_ok=True)
def module(name,path):
 s=importlib.util.spec_from_file_location(name,R/path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
def once(body,before,after):
 if after in body:return body
 if body.count(before)!=1:raise RuntimeError('search_hook_base_changed')
 return body.replace(before,after)
def changes_for(base):
 bankBytes=(R/'data/blog-bank.json').read_bytes();bank=json.loads(bankBytes);quality=json.loads((R/'artifacts/blog-20261112/content-quality.json').read_bytes());assert quality['bankSha256']==hashlib.sha256(bankBytes).hexdigest(),'editorial_review_stale'
 compiler=module('search_editorial_checks','scripts/compile-blog.py');approved=[];held=[];slugs=set()
 for a in bank['articles']:
  if set(a.get('locales',{}))>={'en','ru','ar'} and all(compiler.translation_approved(json.loads((R/'data/blog-translations'/lang/(a['id']+'.json')).read_bytes()),compiler.translation_hash(a))for lang in ['en','ru','ar']):approved.append(a);slugs.add(a['slug'])
  else:held.append(a['id'])
 assert approved,'no_complete_reviewed_articles'
 index={'schema':1,'files':{}};blob=bytearray()
 for a in approved:
  a['related']=[s for s in a.get('related',[])if s in slugs]
  for image in [a['image'],*[x['image']for x in a['locales'].values()]]:
   body=(R/'web'/image['url'].lstrip('/')).read_bytes();assert hashlib.sha256(body).hexdigest()==image['sha256'];assert not image.get('testOnly')
   if image['url']not in index['files']:index['files'][image['url']]={'offset':len(blob),'length':len(body),'sha256':image['sha256']};blob.extend(body)
 scoped={**bank,'publicationReady':True,'publicationScope':'reviewed-four-language-bank' if not held else 'reviewed-four-language-subset','articles':approved}
 changes={'private/'+n:(R/'hosting'/n).read_bytes()for n in ['search-notifications.php','control-indexnow.php','blog-store.php','blog-worker.php','blog-admin.php','blog-http.php','blog.php','blog-i18n.php','blog-admin.html','date-time.php']}
 changes.update({'private/blog-bank.json':(json.dumps(scoped,ensure_ascii=False,separators=(',',':'))+'\n').encode(),'private/blog-images.json':json.dumps(index,separators=(',',':')).encode(),'private/blog-images.bin':bytes(blob)})
 for n in ['blog.css','blog-tools.js','blog-admin.js','blog-entry.js']:changes['public/'+n]=(R/'web'/n).read_bytes()
 seo=base['all_bytes']['private/seo.php'];needle=b"return $prefix.'<sitemapindex xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">'.$body.'</sitemapindex>';";seo=once(seo,needle,b"if(is_file(__DIR__.'/blog-bank.json'))$body.='<sitemap><loc>'.NODENO_SEO_ORIGIN.'/sitemap-blog.xml</loc></sitemap>';"+needle)
 needle=b"if(!empty($config['parentCompany']['name']))";seo=once(seo,needle,b"$organization['sameAs']=array_values(array_unique(array_column($config['socials']??[],'url')));"+needle);changes['private/seo.php']=seo
 html=base['all_bytes']['private/index.html'];changes['private/index.html']=re.sub(rb'(/blog-entry\.js\?v=)[^"\']+',rb'\g<1>20261112-search-1',html)if b'/blog-entry.js?v='in html else once(html,b'</head>',b'<script type="module" src="/blog-entry.js?v=20261112-search-1"></script></head>')
 changes['private/index.html']=re.sub(rb'(src="/app\.js\?v=)[^"]+',rb'\g<1>search-automation-20261112-r1',changes['private/index.html'])
 js=base['all_bytes']['public/seo-core.js'];needle=b"logo:SEO_ORIGIN+'/assets/brand/logo-horizontal.svg',";changes['public/seo-core.js']=once(js,needle,needle+b"sameAs:[...new Set((config.socials||[]).map(s=>s.url).filter(Boolean))],")
 for name,dependency in [('seo-ui.js','seo-core.js'),('app.js','seo-ui.js')]:
  value=base['all_bytes']['public/'+name];changes['public/'+name]=re.sub(('('+re.escape(dependency)+r'\?v=)[^\'\"]+').encode(),rb'\g<1>search-automation-20261112-r1',value)
 indexPhp=base['all_bytes']['public/index.php'];needle=b'$private = nodenoPrivateRoot();';indexPhp=once(indexPhp,needle,needle+b"\n        if(is_file($private.'/blog-http.php')){require_once $private.'/blog-http.php';if(nodenoBlogHttp($path,$method,$private,__DIR__))return;}")
 needle=b"nodenoRespond((string)file_get_contents(__DIR__.'/admin.html'),200";replacement=b"nodenoRespond(str_replace('</head>','<script type=\"module\" src=\"/blog-entry.js?v=20261112-search-1\"></script></head>',(string)file_get_contents(__DIR__.'/admin.html')),200";changes['public/index.php']=re.sub(rb'(/blog-entry\.js\?v=)[^"\']+',rb'\g<1>20261112-search-1',indexPhp)if b'/blog-entry.js?v='in indexPhp else once(indexPhp,needle,replacement)
 ht=base['all_bytes']['public/.htaccess'];needle=b'# Keep source, configuration and caches unreachable';changes['public/.htaccess']=once(ht,needle,b'RewriteRule ^assets/blog/ index.php [END]\n\n'+needle)
 config=json.loads(base['all_bytes']['private/config.json']);socials=json.loads((R/'data/brand.json').read_bytes())['socials'];assert len(socials)==7;config['socials']=socials;changes['private/config.json']=(json.dumps(config,ensure_ascii=False,separators=(',',':'))+'\n').encode()
 return {k:v for k,v in changes.items()if base['all_bytes'].get(k)!=v},{'approvedArticles':len(approved),'heldArticles':len(held),'heldIds':held,'sourceBankSha256':quality['bankSha256'],'sourceBankPreserved':True}
def main():
 d=module('search_release_backend','scripts/deploy-cpanel.py');health=d.CpanelBackend().public_health();live=health['releaseHash'];B=None
 for p in(R/'artifacts').glob('cpanel-release*/private/release.json'):
  if json.loads(p.read_bytes()).get('releaseHash')==live:B=p.parent.parent;break
 assert B is not None,'current_live_base_unavailable';base=d.load_release(B);changes,editorial=changes_for(base);identity=hashlib.sha256(b''.join(k.encode()+hashlib.sha256(v).digest()for k,v in sorted(changes.items()))).hexdigest()[:12];O=R/('artifacts/cpanel-release-search-automation-20261112-'+identity)
 if O.exists():raise RuntimeError('candidate_already_exists')
 for n in sorted(set(base['manifest']['files'])|set(changes)):
  p=O/n;p.parent.mkdir(parents=True,exist_ok=True)
  if n in changes:p.write_bytes(changes[n])
  else:os.link(B/n,p)
 files={n:hashlib.sha256((O/n).read_bytes()).hexdigest()for n in sorted(set(base['manifest']['files'])|set(changes))};fingerprint=hashlib.sha256()
 for n,h in files.items():fingerprint.update((n+'\0'+h+'\0').encode())
 manifest={**base['manifest'],'files':files,'releaseHash':fingerprint.hexdigest()};(O/'private/release.json').write_text(json.dumps(manifest,indent=2)+'\n');d.load_release(O)
 assert all((O/n).read_bytes()==b for n,b in base['all_bytes'].items()if n not in changes and n!='private/release.json')
 proof={'prepared':True,'base':B.relative_to(R).as_posix(),'release':O.relative_to(R).as_posix(),'baseReleaseHash':live,'releaseHash':manifest['releaseHash'],'changedFiles':sorted(changes),'publicProducts':health['products'],'expectedCheckoutEnabled':health['checkoutEnabled'],'editorial':editorial,'catalogueMediaCustomerDataPreserved':True};(E/'release.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps({k:v for k,v in proof.items()if k!='editorial'}));print(json.dumps(editorial))
if __name__=='__main__':main()
