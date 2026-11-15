"""Create final review candidates from same-layout measured background stamps."""
from pathlib import Path
import json,hashlib,cv2,numpy as np,importlib.util
from PIL import Image
R=Path(__file__).resolve().parents[1];D=R/'artifacts/supplier-expansion';O=D/'watermark-last';O.mkdir(exist_ok=True)
rows=json.loads((D/'publication/media-review/alka-remaining-source.json').read_bytes());groups={}
for r in rows:
 if not r['source']['brandMatches']:continue
 a=np.array(Image.open(R/r['sourceFile']).convert('RGB'));key='old700'if a.shape[0]==700 else'old1254'if r['sourceSha256'][:4]not in ['ad05','f249']else'new1254';groups.setdefault(key,[]).append((r,a))
out=[]
for group,items in groups.items():
 ref=np.maximum.reduce([a for _,a in items]);neutral=(ref.min(2)>=210)&(np.ptp(ref.astype(np.int16),axis=2)<=18)
 # Repeating background offsets measured from the old 700 px artwork.
 if group=='old700':
  candidates=[]
  for u in range(-3,4):
   for v in range(-2,3):
    if not(u or v):continue
    dx,dy=u*265+v*145,u*27+v*495
    shifted=cv2.warpAffine(ref,np.float32([[1,0,dx],[0,1,dy]]),(700,700),borderValue=(0,0,0));known=cv2.warpAffine(neutral.astype(np.uint8),np.float32([[1,0,dx],[0,1,dy]]),(700,700))>0
    use=~neutral&known
    ref[use]=shifted[use];neutral|=known
 ref[~neutral]=255;Image.fromarray(ref).save(O/(group+'-background.png'))
 field=ref.astype(np.float32)/255;mask=(ref.mean(2)<254)&neutral
 for row,a in items:
  if group=='new1254':
   # The sparse two-image group is handled conservatively using the actual detected text regions.
   mask=np.zeros(a.shape[:2],bool)
   for word in row['source']['words']:
    text=word['text'].upper()
    if ('ALKA'in text and'HALKA'not in text)or'AHSAP'in text or'AHŞAP'in text:
     box=np.array(word['box']);x0,y0=np.maximum(0,np.floor(box.min(0)-[8,35])).astype(int);x1,y1=np.minimum([a.shape[1],a.shape[0]],np.ceil(box.max(0)+[8,5])).astype(int);mask[y0:y1,x0:x1]=True
   corrected=a.copy()
  else:corrected=np.clip(np.rint(a/np.maximum(field,.8)),0,255).astype(np.uint8)
  gray=cv2.cvtColor(corrected,cv2.COLOR_RGB2GRAY);edge=cv2.dilate(cv2.Canny(gray,70,160),np.ones((3,3),np.uint8))>0
  rgb=corrected.astype(np.int16);warm=(rgb[:,:,0]-rgb[:,:,2]>10)&(rgb[:,:,1]-rgb[:,:,2]>3);warm=cv2.morphologyEx(warm.astype(np.uint8)*255,cv2.MORPH_CLOSE,np.ones((5,5),np.uint8));inside=cv2.erode(warm,np.ones((5,5),np.uint8))>0
  footprint=cv2.dilate(mask.astype(np.uint8),np.ones((3,3),np.uint8))>0;repair=footprint&inside&~edge;result=cv2.inpaint(corrected,repair.astype(np.uint8)*255,3,cv2.INPAINT_TELEA)
  margin=cv2.dilate(warm,np.ones((9,9),np.uint8))>0;light=(result.min(2)>=210)&(np.ptp(result.astype(np.int16),axis=2)<=15);result[light&~margin]=255
  file=O/(row['sourceSha256']+'.png');Image.fromarray(result).save(file)
  out.append({'sourceSha256':row['sourceSha256'],'sourcePath':row['sourceFile'],'outputPath':file.relative_to(R).as_posix(),'outputSha256':hashlib.sha256(file.read_bytes()).hexdigest(),'width':a.shape[1],'height':a.shape[0],'status':'candidate_ready','method':'layout_measured_inverse_masked_repair','structuralEdgesProtected':True,'reviewRequired':True,'publicationReady':False})
(O/'receipt.json').write_text(json.dumps({'images':out,'publicationReady':False},indent=2)+'\n');print(json.dumps({'candidates':len(out)}))
