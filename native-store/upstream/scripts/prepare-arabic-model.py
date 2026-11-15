"""Download a pinned official Helsinki-NLP model without credentials or remote executable code."""
from pathlib import Path
import requests,json,hashlib,concurrent.futures
R=Path(__file__).resolve().parents[1];O=R/'artifacts/supplier-expansion/publication/local-models/opus-tc-big-en-ar';O.mkdir(exist_ok=True)
repository='Helsinki-NLP/opus-mt-tc-big-en-ar';meta=requests.get('https://huggingface.co/api/models/'+repository,params={'blobs':'true'},timeout=30);meta.raise_for_status();data=meta.json();commit=data['sha'];files={x['rfilename']:x for x in data['siblings']};wanted=[n for n in ['config.json','generation_config.json','model.safetensors','source.spm','target.spm','tokenizer_config.json','vocab.json','README.md','special_tokens_map.json']if n in files]
def one(name):
 target=O/name;expected=files[name].get('lfs',{}).get('sha256')
 if not target.exists():
  response=requests.get(f'https://huggingface.co/{repository}/resolve/{commit}/{name}',stream=True,timeout=(20,180));response.raise_for_status();temp=target.with_suffix(target.suffix+'.download')
  with temp.open('wb')as f:
   for chunk in response.iter_content(1024*1024):f.write(chunk)
  temp.replace(target)
 digest=hashlib.sha256(target.read_bytes()).hexdigest()
 if expected:assert expected==digest
 print(json.dumps({'downloadedModelFile':name,'bytes':target.stat().st_size}),flush=True);return(name,digest)
with concurrent.futures.ThreadPoolExecutor(max_workers=4)as pool:hashes=dict(pool.map(one,wanted))
(O/'download-proof.json').write_text(json.dumps({'repository':repository,'commit':commit,'license':data.get('cardData',{}).get('license'),'files':hashes,'weightsHashVerified':True,'trustRemoteCode':False},indent=2)+'\n')
