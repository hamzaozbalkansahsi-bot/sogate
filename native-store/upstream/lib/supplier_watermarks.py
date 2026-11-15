"""Conservative inverse of a measured light multiply watermark, candidate use only.

No geometry is generated. Pixels outside the explicit measured overlay stay exact.
This does not approve a candidate for publication; visual and residual checks follow.
"""
import numpy as np
def reverse_multiply(source,transmission,mask):
 if source.dtype!=np.uint8 or source.ndim!=3 or source.shape[2]!=3 or transmission.shape!=source.shape or mask.dtype!=bool or mask.shape!=source.shape[:2]:raise ValueError('watermark_geometry_invalid')
 if not np.isfinite(transmission).all()or not mask.any()or mask.mean()>.2:raise ValueError('watermark_footprint_untrusted')
 if (transmission[mask]<.80).any()or(transmission[mask]>1).any():raise ValueError('watermark_transmission_untrusted')
 output=source.copy();output[mask]=np.clip(np.rint(source[mask].astype(np.float32)/transmission[mask]),0,255).astype(np.uint8)
 if not np.array_equal(source[~mask],output[~mask]):raise ValueError('watermark_outside_pixels_changed')
 return output
def clear_background_residual(source,mask):
 if source.dtype!=np.uint8 or source.ndim!=3 or source.shape[2]!=3 or mask.dtype!=bool or mask.shape!=source.shape[:2]:raise ValueError('watermark_geometry_invalid')
 output=source.copy();neutral=(source.min(2)>=245)&(source.max(2).astype(int)-source.min(2)<=10)&mask
 output[neutral]=255
 return output
def align_overlay(source,reference):
 """Fit measured watermark coordinates using bright neutral background evidence.

 Repeated stamps yield multiple legitimate translations. Each accepted transform
 is checked against observed background pixels before any inverse is attempted.
 """
 import cv2
 def features(a):
  valid=(a.min(2)>208)&(a.max(2).astype(int)-a.min(2)<16)
  dark=np.clip((255-a.mean(2))*8,0,255).astype(np.uint8);dark[~valid]=0
  detector=cv2.ORB_create(nfeatures=4500,fastThreshold=7,edgeThreshold=8)
  return detector.detectAndCompute(dark,None)
 kr,dr=features(reference);ks,ds=features(source)
 if dr is None or ds is None or len(kr)<20 or len(ks)<20:return None
 pairs=cv2.BFMatcher(cv2.NORM_HAMMING).knnMatch(dr,ds,k=min(6,len(ds)))
 matches=[]
 for choices in pairs:
  best=choices[0].distance
  if best>45:continue
  matches.extend(m for m in choices if m.distance<=best+3)
 if len(matches)<20:return None
 src=np.float32([kr[m.queryIdx].pt for m in matches]);dst=np.float32([ks[m.trainIdx].pt for m in matches]);remaining=np.arange(len(matches));height,width=source.shape[:2]
 field=np.ones(source.shape,np.float32);support=np.zeros((height,width),bool);accepted=0;totalInliers=0;diagnostics=[]
 for attempt in range(6):
  if len(remaining)<20:break
  matrix,inliers=cv2.estimateAffinePartial2D(src[remaining],dst[remaining],method=cv2.RANSAC,ransacReprojThreshold=2.2,maxIters=6000,confidence=.999)
  if matrix is None:break
  hit=inliers.ravel().astype(bool);points=dst[remaining[hit]];remaining=remaining[~hit];count=int(hit.sum())
  scale=float(np.hypot(matrix[0,0],matrix[0,1]));angle=abs(float(np.degrees(np.arctan2(matrix[1,0],matrix[0,0]))))
  if count<12 or not .35<scale<2.5 or angle>10:continue
  extent=np.ptp(points,axis=0)
  if extent[0]<width*.18 or extent[1]<height*.18:continue
  overlay=cv2.warpAffine(reference,matrix,(width,height),flags=cv2.INTER_LINEAR,borderValue=(255,255,255)).astype(np.float32)
  domain=(overlay.min(2)>210)&(overlay.mean(2)<253)
  valid=domain&(source.min(2)>210)&(source.max(2).astype(int)-source.min(2)<14)
  if valid.sum()<max(200,width*height*.002):continue
  x=255-overlay[valid].mean(1);y=255-source[valid].mean(1)
  if x.std()<.2 or y.std()<.2:continue
  correlation=float(np.corrcoef(x,y)[0,1]);gain=float(np.dot(x,y)/max(np.dot(x,x),.001))
  if correlation<.70 or not .5<gain<1.8:continue
  measured=1-(1-overlay/255)*gain
  usable=domain&~support
  field[usable]=measured[usable];support|=domain;accepted+=1;totalInliers+=count
  diagnostics.append({'inliers':count,'scale':scale,'angle':angle,'backgroundCorrelation':correlation,'opacityGain':gain,'matrix':matrix.tolist()})
 mask=support&(field.min(2)>=.80)
 if not accepted or not mask.any()or mask.mean()>.2:return None
 return {'transmission':field,'mask':mask,'inliers':totalInliers,'models':diagnostics}
