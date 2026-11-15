"""Isolated PHP/browser draft; its explicit testOnly manifest is not deployable."""
from pathlib import Path
import hashlib,json,os
R=Path(__file__).resolve().parents[1];E=R/'artifacts/target-locales-20261111';B=R/'artifacts/cpanel-release-vitrine-20261111';O=R/'artifacts/cpanel-release-native-draft-20261111';revision=1
while O.exists():
 revision+=1;O=R/('artifacts/cpanel-release-native-draft-20261111-r'+str(revision))
base=json.loads((B/'private/release.json').read_bytes());changes={}
for path in (R/'web').rglob('*'):
 if path.is_file()and path.suffix in {'.js','.css','.json','.html'}:
  name=path.relative_to(R/'web').as_posix();changes['private/index.html'if name=='index.html'else'public/'+name]=path.read_bytes()
for path in (R/'hosting').glob('*.php'):
 if path.name=='dev-router.php':continue
 changes[('public/'if path.name=='index.php'else'private/')+path.name]=path.read_bytes()
changes['public/.htaccess']=(R/'hosting/.htaccess').read_bytes()
for path in (R/'web/locales').glob('*.json'):changes['private/locale.'+path.name]=path.read_bytes()
for path in (R/'data/legal').glob('site-documents.*.json'):changes['private/'+path.name]=path.read_bytes()
# No hard-linked file is ever opened for writing.
for name in sorted(set(base['files'])|set(changes)):
 target=O/name;target.parent.mkdir(parents=True,exist_ok=True)
 if name in changes:target.write_bytes(changes[name])
 else:os.link(B/name,target)
files={p.relative_to(O).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()for p in O.rglob('*')if p.is_file()};fingerprint=hashlib.sha256()
for name,digest in sorted(files.items()):fingerprint.update((name+'\0'+digest+'\0').encode())
manifest={**base,'testOnly':True,'releaseHash':fingerprint.hexdigest(),'files':dict(sorted(files.items()))};(O/'private/release.json').write_text(json.dumps(manifest,indent=2)+'\n')
translations={lang:{key:value for suffix in ['', '.catalogue']for key,value in json.loads((O/('public/locales/'+lang+suffix+'.json')).read_bytes())['translations'].items()}for lang in ['de','az','kk','tk','uz','ky','fa']}
index=json.loads((O/'private/supplier-details.json').read_bytes());blob=(O/'private/supplier-details.bin').read_bytes();candidates=[]
for pid,row in index.get('entries',index.get('products',index)).items():
 if not isinstance(row,dict)or not isinstance(row.get('offset'),int):continue
 value=json.loads(blob[row['offset']:row['offset']+row['bytes']]);source=value['description']['en']
 if len(source)>150 and all(source in values for values in translations.values()):candidates.append(pid)
assert candidates,'no_complete_supplier_for_draft'
proof={'testOnly':True,'productionAcceptance':False,'release':O.relative_to(R).as_posix(),'releaseHash':manifest['releaseHash'],'supplierProduct':candidates[0]};(E/'draft-php-proof.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof))
