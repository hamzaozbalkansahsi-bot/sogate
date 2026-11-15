"""Fetch official Argos model archives into an isolated task directory; verify and record hashes."""
from pathlib import Path,PurePosixPath
import requests,zipfile,concurrent.futures,json,hashlib
R=Path(__file__).resolve().parents[1];O=R/'artifacts/supplier-expansion/publication/local-models';O.mkdir(exist_ok=True)
index=requests.get('https://raw.githubusercontent.com/argosopentech/argospm-index/main/index.json',timeout=30);index.raise_for_status();data=index.json()
pairs=[('tr','en'),('en','ru'),('en','ar')]
def one(pair):
 row=next(x for x in data if(x.get('from_code'),x.get('to_code'))==pair);url=row['links'][0];target=O/(row['code']+'.argosmodel')
 if not target.exists():
  response=requests.get(url,stream=True,timeout=(15,120));response.raise_for_status();tmp=target.with_suffix('.download')
  with tmp.open('wb')as f:
   for chunk in response.iter_content(1024*1024):f.write(chunk)
  tmp.replace(target)
 folder=O/row['code'];folder.mkdir(exist_ok=True)
 with zipfile.ZipFile(target)as z:
  for name in z.namelist():
   p=PurePosixPath(name);assert not p.is_absolute()and'..'not in p.parts and'\\'not in name
  z.extractall(folder)
 proof={**row,'archiveSha256':hashlib.sha256(target.read_bytes()).hexdigest(),'folder':folder.relative_to(R).as_posix(),'indexSha256':hashlib.sha256(index.content).hexdigest()};(folder/'download-proof.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps({'model':row['code'],'bytes':target.stat().st_size}),flush=True);return proof
with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:proofs=list(pool.map(one,pairs))
(O/'models.json').write_text(json.dumps(proofs,indent=2)+'\n')
