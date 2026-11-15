"""OCR evidence for supplier media. Detection alone never authorises publication."""
from pathlib import Path
import argparse,concurrent.futures,hashlib,json,re,threading
import cv2,numpy as np
from PIL import Image
from rapidocr_onnxruntime import RapidOCR
R=Path(__file__).resolve().parents[1];O=R/'artifacts/supplier-expansion';STATE=threading.local()
def engine():
 if not hasattr(STATE,'ocr'):STATE.ocr=RapidOCR(intra_op_num_threads=1,inter_op_num_threads=1,det_limit_side_len=960,det_limit_type='max',text_score=.25)
 return STATE.ocr
def scan(file):
 a=np.asarray(Image.open(file).convert('RGB'));grey=cv2.cvtColor(a,cv2.COLOR_RGB2GRAY)
 # Analytic contrast view only. The source and candidate files are untouched.
 contrast=np.clip((grey.astype(np.float32)-205)*255/50,0,255).astype(np.uint8)
 rows,_=engine()(contrast);words=[{'text':x[1],'confidence':float(x[2]),'box':np.asarray(x[0]).tolist()}for x in rows or []]
 brands=[x for x in words if re.search(r'ALKA|ALTIN\s*[İIıi]?[ŞS]\s*A[GĞ]|ALTINISAGAC',x['text'],re.I)]
 return {'words':words,'brandMatches':brands}
def main():
 p=argparse.ArgumentParser();p.add_argument('--supplier',choices=['alka','altinis','all'],default='alka');args=p.parse_args()
 products=json.loads((O/'all-catalog.json').read_bytes())['products'];products=[p for p in products if args.supplier=='all'or p['supplierId']==args.supplier];urls={u for p in products for u in p['images']}
 bysha={};sourcepaths={}
 for u in urls:
  file=O/'media'/(hashlib.sha256(u.encode()).hexdigest()+'.bin');digest=hashlib.sha256(file.read_bytes()).hexdigest();bysha.setdefault(digest,file);sourcepaths[u]=digest
 candidates=json.loads((O/'watermark-candidates/receipt.json').read_bytes())['products'];candidateBySha={x['sourceSha256']:x for x in candidates}
 def one(job):
  digest,file=job
  try:
   source=scan(file);candidate=candidateBySha.get(digest);result={'sourceSha256':digest,'sourceFile':file.relative_to(R).as_posix(),'source':source,'publicationReady':False,'reviewRequired':True}
   if candidate:result.update(candidate=candidate,result=scan(R/candidate['outputPath']))
   return result
  except Exception as e:return {'sourceSha256':digest,'error':type(e).__name__,'publicationReady':False,'reviewRequired':True}
 rows=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=2)as pool:
  for i,row in enumerate(pool.map(one,bysha.items()),1):
   rows.append(row)
   if i%25==0:print(json.dumps({'ocrCompleted':i,'total':len(bysha)}),flush=True)
 out={'supplier':args.supplier,'images':rows,'references':sourcepaths,'publicationReady':False,'detectionIsNotVisualQA':True}
 (O/(args.supplier+'-branding-audit.json')).write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({'images':len(rows),'sourceWithBrand':sum(bool(x.get('source',{}).get('brandMatches'))for x in rows),'candidatesWithResidualBrand':sum(bool(x.get('result',{}).get('brandMatches'))for x in rows)}),flush=True)
if __name__=='__main__':main()
