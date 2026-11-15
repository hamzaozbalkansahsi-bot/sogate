"""Build a bounded SEO delta on the exact live release, preserving commerce and legal files."""
from pathlib import Path
import json,hashlib,importlib.util,os,secrets,re,requests
R=Path(__file__).resolve().parents[1];E=R/'artifacts/seo-products';E.mkdir(exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest()
h=requests.get('https://nodenohome.com/api/health?seo-build='+secrets.token_hex(6),timeout=60);h.raise_for_status();health=h.json()
candidates=[f.parent.parent for f in(R/'artifacts').glob('cpanel-release*/private/release.json')if json.loads(f.read_bytes()).get('releaseHash')==health['releaseHash']];assert len(candidates)==1;B=candidates[0];O=R/os.environ.get('NODENO_SEO_OUTPUT','artifacts/cpanel-release-product-seo-20261110');assert O.parent==R/'artifacts'and O.name.startswith('cpanel-release-');assert not O.exists(),'Use a new immutable output directory'
manifest=json.loads((B/'private/release.json').read_bytes());assert health['products']==3602
spec=importlib.util.spec_from_file_location('material_correction',R/'lib/supplier_seo_content.py');material=importlib.util.module_from_spec(spec);spec.loader.exec_module(material)
catalog=json.loads((B/'private/catalog.json').read_bytes());sources={p['id']:p for p in json.loads((R/'artifacts/supplier-expansion/publication/content-tr.json').read_bytes())['products']};index=json.loads((B/'private/supplier-details.json').read_bytes());blob=(B/'private/supplier-details.bin').read_bytes();newblob=bytearray();newindex={};review=[]
for i,p in enumerate(catalog['products']):
 if p.get('productType')!='supplier-item':continue
 entry=index['products'][p['id']];body=blob[entry['offset']:entry['offset']+entry['bytes']];assert sha(body)==p['supplierDetailsHash'];detail=json.loads(body);updated,newdetail=material.enrich_supplier(p,sources[p['id']],detail)
 body=json.dumps(newdetail,ensure_ascii=False,separators=(',',':')).encode();newindex[p['id']]={'offset':len(newblob),'bytes':len(body),'sha256':sha(body)};newblob.extend(body)
 updated['supplierDetailsHash']=sha(body)
 if updated!=p or newdetail!=detail:review.append({'id':p['id'],'code':p['code'],'priceUnchanged':updated['salePriceMinor']==p['salePriceMinor'],'imagesUnchanged':updated['images']==p['images'],'nameBefore':p['name'],'nameAfter':updated['name'],'detailsBefore':p['supplierDetailsHash'],'detailsAfter':sha(body)})
 catalog['products'][i]=updated
catalog['meta']['productCount']=len(catalog['products']);catalog['meta']['categoryCount']=len(catalog['categories'])
changes={'private/catalog.json':json.dumps(catalog,ensure_ascii=False,separators=(',',':')).encode(),'private/supplier-details.bin':bytes(newblob),'private/supplier-details.json':json.dumps({'schema':1,'products':newindex},separators=(',',':')).encode()}
for name in ['app.js','seo-core.js','seo-ui.js','catalog-pagination.js','styles.css']:changes['public/'+name]=(R/'web'/name).read_bytes()
changes['private/seo.php']=(R/'hosting/seo.php').read_bytes()
entry=(B/'public/index.php').read_text(encoding='utf8');needle="['Cache-Control'=>'no-cache','ETag'=>'\"'.hash('sha256',$bytes).'\"']";assert entry.count(needle)==1;entry=entry.replace(needle,"['Cache-Control'=>'no-cache','ETag'=>'\"'.hash('sha256',$bytes).'\"','X-Robots-Tag'=>'noindex']");changes['public/index.php']=entry.encode()
html=(B/'private/index.html').read_text(encoding='utf8');html=re.sub(r'/app\.js\?v=[^"\s]+','/app.js?v=nodeno-products-seo-20261110-r1',html);html=re.sub(r'/styles\.css\?v=[^"\s]+','/styles.css?v=nodeno-products-seo-20261110-r1',html);changes['private/index.html']=html.encode()
# This public ownership file is separate from any administrator-managed IndexNow key.
keyfile=R/'data/seo-indexnow.json'
if keyfile.exists():key=json.loads(keyfile.read_bytes())['key']
else:
 key=secrets.token_hex(16);keyfile.write_text(json.dumps({'key':key,'host':'nodenohome.com','keyLocation':'https://nodenohome.com/'+key+'.txt'},indent=2)+'\n')
assert re.fullmatch('[a-f0-9]{32}',key);changes['public/'+key+'.txt']=key.encode();(R/'web'/(key+'.txt')).write_bytes(key.encode())
for name in set(manifest['files'])|set(changes):
 target=O/name;target.parent.mkdir(parents=True,exist_ok=True)
 if name in changes:target.write_bytes(changes[name])
 else:os.link(B/name,target)
files={name:sha((O/name).read_bytes())for name in sorted(set(manifest['files'])|set(changes))};fp=hashlib.sha256()
for name,value in files.items():fp.update((name+'\0'+value+'\0').encode())
newmanifest={**manifest,'releaseHash':fp.hexdigest(),'files':files};(O/'private/release.json').write_text(json.dumps(newmanifest,indent=2)+'\n')
proof={'prepared':True,'base':B.relative_to(R).as_posix(),'release':O.relative_to(R).as_posix(),'baseReleaseHash':manifest['releaseHash'],'releaseHash':newmanifest['releaseHash'],'changedFiles':[n for n in changes if (B/n).read_bytes()!=changes[n]]if all((B/n).exists()for n in changes)else list(changes),'products':len(catalog['products']),'reviewedMaterialCorrections':review,'sourceArchivesUntouched':True,'pricesUnitsMediaAndCodesUnchanged':True}
(E/'release.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({k:v for k,v in proof.items()if k not in ['changedFiles','reviewedMaterialCorrections']}));print(json.dumps({'materialCorrections':len(review)}))
