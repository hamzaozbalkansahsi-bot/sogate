"""Six reviewed TCross pad prints: actual ink/AA only, original local pad grain."""
from pathlib import Path
import importlib.util,json
import cv2,numpy as np
from PIL import Image,ImageDraw,ImageOps
ROOT=Path(__file__).resolve().parents[1];DEST=ROOT/'artifacts/media-tcross-final'
spec=importlib.util.spec_from_file_location('tcross_frozen_core',ROOT/'scripts/media-clean.py');core=importlib.util.module_from_spec(spec);spec.loader.exec_module(core)
spec=importlib.util.spec_from_file_location('tcross_style',ROOT/'scripts/media-gaming-review.py');style=importlib.util.module_from_spec(spec);spec.loader.exec_module(style)
cv2.setNumThreads(1)

def ink_retouch(rgba,quad,offset):
 rgb=rgba[:,:,:3];gray=cv2.cvtColor(rgb,cv2.COLOR_RGB2GRAY).astype(float);data=rgb.astype(float)
 gate=np.zeros(gray.shape,np.uint8);cv2.fillConvexPoly(gate,np.array(quad,np.int32),255)
 ys,xs=np.where(gate!=0);dx,dy=offset;xx,yy=xs+dx,ys+dy
 if np.any(xx<0)|np.any(xx>=rgb.shape[1])|np.any(yy<0)|np.any(yy>=rgb.shape[0]):raise ValueError('Donor leaves source')
 donor=data[yy,xx];donor_gray=gray[yy,xx];material=(donor_gray>40)&(donor_gray<175)&((donor.max(axis=1)-donor.min(axis=1))<24)&(rgba[yy,xx,3]==255)
 if np.count_nonzero(material)<8:raise ValueError('Too few actual unprinted pad samples')
 center=np.array([xs.mean(),ys.mean()]);design=np.c_[np.ones(len(xs)),xx-center[0],yy-center[1]]
 kept=material.copy()
 for iteration in range(4):
  coeff=np.linalg.lstsq(design[kept],donor[kept],rcond=None)[0];residual=np.linalg.norm(donor-design@coeff,axis=1);kept=material&(residual<=max(5,float(np.percentile(residual[material],75))))
  if np.count_nonzero(kept)<8:raise ValueError('Unstable source pad samples')
 target_design=np.c_[np.ones(len(xs)),xs-center[0],ys-center[1]];plane=target_design@coeff;actual=data[ys,xs];source_gray=gray[ys,xs];plane_gray=plane@np.array([.299,.587,.114]);excess=source_gray-plane_gray;red=(actual[:,0]-actual[:,1])-(plane[:,0]-plane[:,1])
 # Wood/warm exterior is not font, nor is the original dark rubber/piping edge.
 wood=((actual[:,0]-actual[:,2])>20)&((actual[:,1]-actual[:,2])>8)
 support=(~wood)&(source_gray>plane_gray-8)&(source_gray<np.maximum(205,plane_gray+85))&(rgba[ys,xs,3]==255)
 strong=support&((excess>8)|(red>7));weak=support&((excess>1.5)|(red>2))
 seed=np.zeros(gray.shape,np.uint8);seed[ys[strong],xs[strong]]=255;near=cv2.dilate(seed,np.ones((3,3),np.uint8))!=0
 chosen=weak&near[ys,xs];mask=np.zeros(gray.shape,np.uint8);mask[ys[chosen],xs[chosen]]=255
 if np.count_nonzero(mask)<3:raise ValueError('No confirmed ink')
 if np.any(mask[yy[chosen],xx[chosen]]!=0):raise ValueError('Source grain donor overlaps print')
 # Copy only authentic donor grain; the same source pad plane supplies lighting.
 donor_plane=design@coeff;grain=donor-donor_plane;fill=np.clip(plane+grain,0,255)
 output=rgba.copy();output[ys[chosen],xs[chosen],:3]=np.round(fill[chosen]).astype(np.uint8)
 if not np.array_equal(output[mask==0],rgba[mask==0]) or not np.array_equal(output[:,:,3],rgba[:,:,3]):raise ValueError('Outside/alpha changed')
 # These explicit classified edge/wood pixels must survive even inside the ROI.
 protected=wood|(source_gray<plane_gray-8)
 if not np.array_equal(output[ys[protected],xs[protected]],rgba[ys[protected],xs[protected]]):raise ValueError('Wood or dark border changed')
 return output,mask,{'method':'reviewed_true_ink_and_one_pixel_aa_only_source_pad_plane_and_authentic_grain','sourceDonorTranslation':offset,'originalQuad':quad,'inkPixels':int(np.count_nonzero(mask)),'protectedWoodAndBorderPixels':int(np.count_nonzero(protected)),'protectedWoodAndBorderChangedValues':0,'sourceSampleCount':int(np.count_nonzero(kept)),'sourcePadPlaneCoefficients':coeff.tolist(),'maskOutsideRgbaChangedValues':0}

def main():
 DEST.mkdir(parents=True,exist_ok=True);plans=json.loads((ROOT/'artifacts/media-review/review-plans-tcross4967.json').read_text('utf8'));records={};tiles=[]
 for key,plan in plans['images'].items():
  source=ROOT/plan['sourcePath'];raw=source.read_bytes()
  if core.sha(raw)!=plan['sourceSha']:raise ValueError('Source SHA changed')
  with Image.open(source) as im:rgba=np.array(im.convert('RGBA'));icc=im.info.get('icc_profile',b'');orientation=im.getexif().get(274,1)or 1
  region=plan['regions'][0];out,mask,method=ink_retouch(rgba,region['quad'],region['suggestedDonorTranslation'])
  folder=DEST/key;folder.mkdir(exist_ok=True);path=folder/'candidate.webp';maskpath=folder/'mask.png';exif=Image.Exif();exif[274]=orientation
  Image.fromarray(out).save(path,'WEBP',lossless=True,quality=100,method=6,exact=True,icc_profile=icc,exif=exif)
  decoded=np.array(Image.open(path).convert('RGBA'));assert np.array_equal(decoded,out);assert Image.open(path).info.get('icc_profile',b'')==icc;Image.fromarray(mask).save(maskpath)
  detected,scan=core.get_engines(ROOT/'artifacts/media-cleanup/templates').scan(decoded[:,:,:3]);joined=style.final.joined_brand_hits(scan);gaming=style.matcher('desk').detect(decoded[:,:,:3]);ready=not detected and not joined and not gaming
  row={'urlSha':key,'sourceSha':plan['sourceSha'],'sourcePath':plan['sourcePath'],'sourceBytes':len(raw),'pipelineVersion':style.FROZEN,'publicationReady':False,'visualAccepted':False,'state':'candidate_ready'if ready else'rejected_residual_brand','path':core.relative(ROOT,path),'outputSha':core.sha(path.read_bytes()),'bytes':path.stat().st_size,'mime':'image/webp','width':out.shape[1],'height':out.shape[0],'maskPath':core.relative(ROOT,maskpath),'maskSha':core.sha(maskpath.read_bytes()),'validation':{'outsideMaskRgbMaxDelta':0,'alphaMaxDelta':0,'protectedWoodAndBorderChangedValues':0},'postDetections':detected,'postScan':scan,'postJoinedBrand':joined,'postGamingTemplates':gaming,'method':method,'reference':plan['reference'],'iccSha256':core.sha(icc)if icc else None,'orientation':orientation}
  core.atomic_json(folder/'audit.json',row);records[key]=row
  q=np.array(region['quad']);x0,y0=q.min(axis=0)-[10,9];x1,y1=q.max(axis=0)+[11,10];box=(max(0,int(x0)),max(0,int(y0)),min(out.shape[1],int(x1)),min(out.shape[0],int(y1)))
  tile=Image.new('RGB',(1500,260),'white');draw=ImageDraw.Draw(tile)
  for col,(array,label) in enumerate([(rgba[:,:,:3],'source'),(decoded[:,:,:3],'candidate'),(np.repeat(mask[:,:,None],3,axis=2),'mask')]):
   crop=Image.fromarray(array).crop(box);close=ImageOps.contain(crop,(490,220));tile.paste(close,(col*500+5,25));draw.text((col*500+5,4),plan['reference']+' '+label+' '+row['outputSha'][:12],fill='black')
  tiles.append(tile);pair=Image.new('RGB',(rgba.shape[1]*2,rgba.shape[0]),'white');pair.paste(Image.fromarray(rgba).convert('RGB'));pair.paste(Image.fromarray(decoded).convert('RGB'),(rgba.shape[1],0));pair.thumbnail((1760,1000));pair.save(folder/'full-comparison.jpg',quality=97)
  if core.sha(source.read_bytes())!=plan['sourceSha']:raise ValueError('Source changed during processing')
  core.atomic_json(DEST/'candidates.json',{'pipelineVersion':style.FROZEN,'publicationReady':False,'mainManifestModified':False,'images':records})
 sheet=Image.new('RGB',(1500,len(tiles)*260),'white')
 for i,tile in enumerate(tiles):sheet.paste(tile,(0,i*260))
 sheet.save(DEST/'comparison.png');print(json.dumps({'candidates':len(records),'ready':sum(r['state']=='candidate_ready'for r in records.values()),'shas':{k:r['outputSha']for k,r in records.items()}}),flush=True)
if __name__=='__main__':main()
