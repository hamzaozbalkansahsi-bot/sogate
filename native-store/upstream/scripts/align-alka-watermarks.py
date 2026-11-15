"""Prepare aligned, native-pixel watermark inverses for OCR-confirmed Alka images."""
from pathlib import Path
import cv2,hashlib,importlib.util,json
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[1];O=R/'artifacts/supplier-expansion';OUT=O/'watermark-aligned';OUT.mkdir(exist_ok=True)
s=importlib.util.spec_from_file_location('supplier_wm',R/'lib/supplier_watermarks.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
audit=json.loads((O/'alka-branding-audit.json').read_bytes());known=json.loads((O/'watermark-candidates/receipt.json').read_bytes());knownBySha={x['sourceSha256']:x for x in known['products']};reference=np.asarray(Image.open(O/'watermark-candidates/measured-background.png').convert('RGB'));rows=[]
previous={x['sourceSha256']:x for x in json.loads((OUT/'receipt.json').read_bytes())['products']}if(OUT/'receipt.json').exists()else {}
for i,item in enumerate(audit['images'],1):
 if not item.get('source',{}).get('brandMatches'):continue
 digest=item['sourceSha256'];file=R/item['sourceFile'];source=np.asarray(Image.open(file).convert('RGB'));record={'sourceSha256':digest,'sourcePath':item['sourceFile'],'width':source.shape[1],'height':source.shape[0],'reviewRequired':True,'publicationReady':False}
 old=previous.get(digest)
 if old and old['status']=='candidate_ready'and hashlib.sha256((R/old['outputPath']).read_bytes()).hexdigest()==old['outputSha256']:
  rows.append(old);continue
 existing=knownBySha.get(digest)
 if existing and not item.get('result',{}).get('brandMatches'):
  rows.append({**record,'status':'candidate_ready','outputPath':existing['outputPath'],'outputSha256':existing['outputSha256'],'method':'measured_native_overlay','outsidePixelsUnchanged':True});continue
 try:
  fitted=m.align_overlay(source,reference);referenceScale=1
  if fitted is None:
   for factor in [.5,.3]:
    fitted=m.align_overlay(source,cv2.resize(reference,None,fx=factor,fy=factor,interpolation=cv2.INTER_AREA))
    if fitted is not None:referenceScale=factor;break
  if fitted is None:rows.append({**record,'status':'alignment_review_required'});continue
  footprint=cv2.dilate(fitted['mask'].astype(np.uint8),np.ones((3,3),np.uint8)).astype(bool)
  output=m.reverse_multiply(source,fitted['transmission'],fitted['mask']);output=m.clear_background_residual(output,footprint)
  assert np.array_equal(source[~footprint],output[~footprint]);out=OUT/(digest+'.png');mask=OUT/(digest+'-mask.png');Image.fromarray(output).save(out);Image.fromarray(footprint.astype(np.uint8)*255).save(mask)
  rows.append({**record,'status':'candidate_ready','outputPath':out.relative_to(R).as_posix(),'outputSha256':hashlib.sha256(out.read_bytes()).hexdigest(),'maskPath':mask.relative_to(R).as_posix(),'maskSha256':hashlib.sha256(mask.read_bytes()).hexdigest(),'maskPixels':int(footprint.sum()),'outsidePixelsUnchanged':True,'geometryGenerated':False,'method':'aligned_measured_overlay','referenceScale':referenceScale,'models':fitted['models']})
 except Exception as e:rows.append({**record,'status':'repair_review_required','error':type(e).__name__})
 if len(rows)%10==0:print(json.dumps({'processedBranded':len(rows),'candidates':sum(x['status']=='candidate_ready'for x in rows)}),flush=True)
(OUT/'receipt.json').write_text(json.dumps({'products':rows,'publicationReady':False,'sourceBrandImages':len(rows)},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
from collections import Counter
print(json.dumps(dict(Counter(x['status']for x in rows))),flush=True)
