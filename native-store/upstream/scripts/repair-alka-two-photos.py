"""Register the measured repeating stamp for the two pale wood photos.

Conservative hand-inspected foreground envelopes protect the pale product from background whitening.
"""
from pathlib import Path
import cv2,numpy as np,json,hashlib
from PIL import Image
R=Path(__file__).resolve().parents[1];D=R/'artifacts/supplier-expansion';O=D/'watermark-two';O.mkdir(exist_ok=True)
rows=json.loads((D/'publication/media-review/alka-remaining-source.json').read_bytes());reference=np.array(Image.open(D/'watermark-candidates/measured-background.png').convert('RGB'));out=[]
polygons={
 'ad05':[(500,65),(815,65),(855,330),(804,376),(870,455),(854,530),(815,565),(890,625),(890,700),(850,750),(925,790),(930,860),(884,920),(946,1005),(955,1080),(895,1150),(800,1190),(565,1190),(450,1160),(350,1090),(350,1000),(440,925),(390,850),(390,785),(455,735),(425,680),(425,610),(490,555),(440,505),(440,445),(495,382),(450,335)],
 'f249':[(260,120),(430,50),(1000,55),(1000,140),(950,185),(950,1000),(930,1100),(835,1150),(700,1180),(510,1170),(380,1140),(340,1090),(315,1000),(315,195),(255,180)]}
for row in rows:
 prefix=row['sourceSha256'][:4]
 if prefix not in polygons:continue
 source=np.array(Image.open(R/row['sourceFile']).convert('RGB'));height,width=source.shape[:2]
 bg=np.zeros((height,width),np.uint8);bg[:,:230]=255;bg[:,1100:]=255
 patch=cv2.cvtColor(reference[20:300,40:220],cv2.COLOR_RGB2GRAY);search=cv2.cvtColor(source[:500,:250],cv2.COLOR_RGB2GRAY);best=(-1,None,None)
 for scale in np.arange(.85,1.151,.01):
  resized=cv2.resize(patch,None,fx=scale,fy=scale);matches=cv2.matchTemplate(search,resized,cv2.TM_CCOEFF_NORMED);_,correlation,_,pos=cv2.minMaxLoc(matches)
  if correlation>best[0]:best=(correlation,float(scale),pos)
 assert best[0]>.8,best
 scale=best[1];tx=best[2][0]-40*scale;ty=best[2][1]-20*scale;warp=np.float32([[1/scale,0,-tx/scale],[0,1/scale,-ty/scale]])
 score,warp=cv2.findTransformECC(cv2.cvtColor(source,cv2.COLOR_RGB2GRAY).astype(np.float32)/255,cv2.cvtColor(reference,cv2.COLOR_RGB2GRAY).astype(np.float32)/255,warp,cv2.MOTION_AFFINE,(cv2.TERM_CRITERIA_COUNT|cv2.TERM_CRITERIA_EPS,500,1e-7),bg,5)
 assert score>.80,(prefix,score)
 overlay=cv2.warpAffine(reference,warp,(width,height),flags=cv2.INTER_LINEAR|cv2.WARP_INVERSE_MAP,borderValue=(255,255,255)).astype(np.float32)
 valid=(bg>0)&(overlay.mean(2)<253)&(source.min(2)>210);x=255-overlay[valid].mean(1);y=255-source[valid].mean(1);gain=float(np.dot(x,y)/np.dot(x,x));assert .5<gain<1.8
 field=1-(1-overlay/255)*gain;mask=(overlay.mean(2)<254)&(field.min(2)>.8);corrected=source.copy();corrected[mask]=np.clip(np.rint(source[mask]/field[mask]),0,255).astype(np.uint8)
 envelope=np.zeros((height,width),np.uint8);cv2.fillPoly(envelope,[np.array(polygons[prefix],np.int32)],255)
 Image.fromarray(corrected).save(O/(prefix+'-inverse.png'))
 edges=cv2.dilate(cv2.Canny(cv2.cvtColor(source,cv2.COLOR_RGB2GRAY),35,90),np.ones((7,7),np.uint8))>0
 ink=(1-field)*255;signal=ink-cv2.GaussianBlur(ink,(31,31),0)
 sample=(cv2.erode(envelope,np.ones((21,21),np.uint8))>0)&~edges&(source.mean(2)<240)&(source.mean(2)>100)
 chosen=[];result=source.astype(np.float32).copy()
 for channel in range(3):
  scores=[]
  for colour in range(0,226,5):
   alpha=ink[:,:,channel]/(255-colour);valid=sample&(alpha<.6)
   candidate=(source[:,:,channel]-alpha*colour)/np.maximum(1-alpha,.1)
   residual=candidate-cv2.GaussianBlur(candidate,(31,31),0);beta=float(np.sum(residual[valid]*signal[:,:,channel][valid])/max(.001,np.sum(signal[:,:,channel][valid]**2)))
   scores.append((abs(beta),colour,beta))
  _,colour,beta=min(scores);chosen.append({'inkColour':colour,'residualCorrelation':beta});alpha=ink[:,:,channel]/(255-colour);candidate=(source[:,:,channel]-alpha*colour)/np.maximum(1-alpha,.1);result[:,:,channel][mask]=candidate[mask]
 result=np.clip(np.rint(result),0,255).astype(np.uint8)
 light=(result.min(2)>=210)&(np.ptp(result.astype(np.int16),axis=2)<=18);result[light&(envelope==0)]=255
 print(json.dumps({'source':prefix,'physicalAlphaFit':chosen}),flush=True)
 file=O/(row['sourceSha256']+'.png');Image.fromarray(result).save(file);out.append({'sourceSha256':row['sourceSha256'],'sourcePath':row['sourceFile'],'outputPath':file.relative_to(R).as_posix(),'outputSha256':hashlib.sha256(file.read_bytes()).hexdigest(),'status':'candidate_ready','registrationCorrelation':score,'warp':warp.tolist(),'gain':gain,'method':'measured_stamp_ECC_physical_alpha_inverse','inkChannelFit':chosen,'reviewRequired':True,'publicationReady':False})
(O/'receipt.json').write_text(json.dumps({'images':out,'publicationReady':False},indent=2)+'\n');print(json.dumps([{'source':r['sourceSha256'][:4],'correlation':r['registrationCorrelation']}for r in out]))

