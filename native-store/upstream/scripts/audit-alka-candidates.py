"""Scan only completed cleaning candidates; retain hash-bound residual evidence."""
from pathlib import Path
import concurrent.futures,hashlib,importlib.util,json,re,os
R=Path(__file__).resolve().parents[1];O=R/'artifacts/supplier-expansion'
s=importlib.util.spec_from_file_location('brand_ocr',R/'scripts/audit-supplier-branding.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
group=os.environ.get('NODENO_WATERMARK_AUDIT_GROUP','watermark-aligned');source=O/group/'receipt.json';data=json.loads(source.read_bytes());rows=data.get('products',data.get('images'));out=O/group/'ocr';out.mkdir(exist_ok=True)
def one(row):
 if row['status']!='candidate_ready':return None
 file=R/row['outputPath'];digest=hashlib.sha256(file.read_bytes()).hexdigest();assert digest==row['outputSha256'];cache=out/(digest+'.json')
 if cache.exists():return json.loads(cache.read_bytes())
 scan=m.scan(file);extra=[x for x in scan['words']if re.search(r'AH[ŞS]AP',x['text'],re.I)];d={'sourceSha256':row['sourceSha256'],'outputSha256':digest,'outputPath':row['outputPath'],'scan':scan,'possibleResidualWoodBrand':extra,'publicationReady':False};cache.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8');return d
result=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=2)as pool:
 for d in pool.map(one,rows):
  if d:result.append(d)
  if len(result)%25==0:print(json.dumps({'completed':len(result)}),flush=True)
(O/group/'candidate-ocr.json').write_text(json.dumps({'products':result,'sourceReceiptSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'publicationReady':False},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'candidates':len(result),'residual':sum(bool(r['scan']['brandMatches']or r['possibleResidualWoodBrand'])for r in result)}),flush=True)
