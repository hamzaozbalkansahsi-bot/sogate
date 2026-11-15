"""Remove residual stamp footprints while protecting product boundaries and dimensions.

Candidate outputs only. Publication still requires inspection of the saved review sheets.
"""
from pathlib import Path
import cv2,numpy as np,json,hashlib
R=Path(__file__).resolve().parents[1];D=R/'artifacts/supplier-expansion';O=D/'watermark-refined';O.mkdir(exist_ok=True)
rows=json.loads((D/'watermark-aligned/receipt.json').read_bytes())['products'];out=[]
for row in rows:
 if row.get('status')!='candidate_ready':continue
 file=R/row['outputPath'];a=cv2.imdecode(np.fromfile(str(file),dtype=np.uint8),cv2.IMREAD_COLOR)
 mask=cv2.imdecode(np.fromfile(str(R/row.get('maskPath','artifacts/supplier-expansion/watermark-candidates/candidate-footprint.png')),dtype=np.uint8),cv2.IMREAD_GRAYSCALE)
 mask=(mask>0).astype(np.uint8)*255
 # Strong structural edges and their neighbourhood remain byte-exact.
 gray=cv2.cvtColor(a,cv2.COLOR_BGR2GRAY);edges=cv2.Canny(gray,70,160);protected=cv2.dilate(edges,np.ones((5,5),np.uint8))>0
 bgr=a.astype(np.int16);warm=(bgr[:,:,2]-bgr[:,:,0]>14)&(bgr[:,:,1]-bgr[:,:,0]>4)
 warm=cv2.morphologyEx(warm.astype(np.uint8)*255,cv2.MORPH_CLOSE,np.ones((7,7),np.uint8))
 interior=cv2.erode(warm,np.ones((7,7),np.uint8))>0
 repair=(mask>0)&interior&~protected
 repaired=cv2.inpaint(a,repair.astype(np.uint8)*255,4,cv2.INPAINT_TELEA)
 # Neutral light pixels are background. Protect a margin around the actual warm product.
 margin=cv2.dilate(warm,np.ones((11,11),np.uint8))>0
 neutral=(a.min(axis=2)>=210)&(np.ptp(a.astype(np.int16),axis=2)<=12)
 background=neutral&~margin
 mask[background]=255
 repaired[background]=255
 change=np.any(repaired!=a,axis=2);assert not np.any(change&(mask==0));assert not np.any(repair&protected)
 dest=O/(row['sourceSha256']+'.png');ok,buf=cv2.imencode('.png',repaired);assert ok;dest.write_bytes(buf.tobytes())
 out.append({**row,'outputPath':dest.relative_to(R).as_posix(),'outputSha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'previousOutputSha256':row['outputSha256'],'method':'measured_inverse_then_masked_texture_repair','structuralEdgesProtected':True,'outsideStampFootprintUnchanged':True,'changedPixels':int(change.sum()),'reviewRequired':True,'publicationReady':False})
print(json.dumps({'candidates':len(out),'publicationReady':False}));(O/'receipt.json').write_text(json.dumps({'images':out,'publicationReady':False},indent=2)+'\n')
