"""Separate Advent flat-pad field candidates from the hash-frozen review set."""
from __future__ import annotations
import argparse
import copy
import importlib.util
import json
from pathlib import Path
import sys

import cv2
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('gaming_review',ROOT/'scripts/media-gaming-review.py')
gaming=importlib.util.module_from_spec(spec);spec.loader.exec_module(gaming)
SOURCE=ROOT/'artifacts/media-gaming-review/advent-final-candidates.json'
SOURCE_SHA='7e498afdffdd4bf28f644346fea6dd49e358f263fbed648129e1aed0fcaed355'
DEST=ROOT/'artifacts/media-gaming-review/advent-aa'
LARGE_SHA='8564df738f2e92a74d45142e7a85e6aa55cf4350a4dec081fab147b7e72331e8'


def pad_field(source,base,old_mask,quad,padding=3,material_patch=None):
    """Restore a contiguous printed field using measured same-plane material.

    All planar pixels, including faint coloured antialias, are included. Dark
    bevels, phone occlusions, white exterior and nonopaque pixels are protected.
    The fill's colour plane and fine grain come from original unprinted pad.
    """
    rgb=source[:,:,:3];q=np.array(quad,float);center=q.mean(0)
    original_zone=np.zeros(rgb.shape[:2],np.uint8);cv2.fillConvexPoly(original_zone,np.round(q).astype(np.int32),255)
    difference=np.max(np.abs(rgb.astype(int)-base[:,:,:3].astype(int)),axis=2)
    core=(old_mask!=0)&(original_zone!=0)&(difference>12)
    cy_seed,cx_seed=np.where(core);seed_count=len(cx_seed)
    if seed_count>=8:
        points=np.c_[cx_seed,cy_seed].astype(float);cov=np.cov(points.T);_,vectors=np.linalg.eigh(cov);axis=vectors[:,-1]
        if axis[0]<0:axis=-axis
        normal=np.array([-axis[1],axis[0]])
        along=q@axis;across=points@normal
        u0,u1=float(along.min()-padding),float(along.max()+padding)
        v0,v1=np.quantile(across,[.02,.98])+[-2.0,2.0]
        expanded=np.array([axis*u0+normal*v0,axis*u1+normal*v0,axis*u1+normal*v1,axis*u0+normal*v1])
    else:
        direction=q-center;length=np.linalg.norm(direction,axis=1)[:,None]
        expanded=q+direction/np.maximum(length,1)*padding
    zone=np.zeros(rgb.shape[:2],np.uint8);cv2.fillConvexPoly(zone,np.round(expanded).astype(np.int32),255)
    gray_base=cv2.cvtColor(base[:,:,:3],cv2.COLOR_RGB2GRAY)
    initial=(zone!=0)&(base[:,:,:3].min(2)<235)&(gray_base>12)&(source[:,:,3]==255)
    values=gray_base[initial]
    if len(values)<10:raise ValueError('Pad material samples missing')
    # Mid-tone material is more reliable than the brightest quantile: faint
    # white print and exterior antialias can otherwise bias a very thin field.
    low,high=np.quantile(values,[.25,.65]);material=initial&(gray_base>=low)&(gray_base<=high)
    tone=np.median(base[:,:,:3][material],axis=0)
    if material_patch:
        ax,ay,bx,by=material_patch
        actual=rgb[ay:by,ax:bx]
        if min(actual.shape[:2])<3:raise ValueError('Reviewed original material patch too small')
        tone=np.median(actual.reshape(-1,3),axis=0)
    tone_gray=float(cv2.cvtColor(np.round(tone).astype(np.uint8)[None,None,:],cv2.COLOR_RGB2GRAY)[0,0])
    if tone_gray<20:raise ValueError('Material estimate selected a dark structural edge')
    gray=cv2.cvtColor(rgb,cv2.COLOR_RGB2GRAY)
    # Use the geometry of the already reviewed base, not ink thresholds, to
    # bound this continuous field. Low-valued antialias must not become holes.
    upper=tone_gray*(1.8 if material_patch else 1.5)+(20 if material_patch else 15)
    plane=(gray_base>=tone_gray*.40)&(gray_base<=upper)&(base[:,:,:3].min(2)<245)&(source[:,:,3]==255)
    mask=((zone!=0)&plane).astype(np.uint8)*255
    mask[((old_mask!=0)&(zone!=0)&(gray_base>=tone_gray*.45)&(base[:,:,:3].min(2)<245)&(source[:,:,3]==255))]=255
    # Fill interior holes from source grain/glyph shadows. Exterior-connected
    # black borders and occluding hardware remain outside the planar polygon.
    contours,_=cv2.findContours(mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    continuous=np.zeros_like(mask);cv2.drawContours(continuous,contours,-1,255,cv2.FILLED)
    continuous[(zone==0)|(base[:,:,:3].min(2)>=245)|(source[:,:,3]!=255)]=0
    mask=continuous
    if not np.any(mask):raise ValueError('Empty reviewed flat-pad field')
    x0,y0=np.maximum(0,np.floor(expanded.min(0)-25).astype(int))
    x1,y1=np.minimum([rgb.shape[1],rgb.shape[0]],np.ceil(expanded.max(0)+26).astype(int))
    local=rgb[y0:y1,x0:x1].astype(float);z=zone[y0:y1,x0:x1]!=0
    distance=np.max(np.abs(local-tone),axis=2)
    chroma1=np.abs((local[:,:,0]-local[:,:,1])-(tone[0]-tone[1]))
    chroma2=np.abs((local[:,:,2]-local[:,:,1])-(tone[2]-tone[1]))
    valid=(distance<=16)&(chroma1<=5)&(chroma2<=5)&~z&(source[y0:y1,x0:x1,3]==255)
    yy,xx=np.where(valid)
    if len(xx)<15:raise ValueError('No source-only unprinted material around pad field')
    cx,cy=expanded.mean(0);sx=max(5,float(np.ptp(expanded[:,0])));sy=max(5,float(np.ptp(expanded[:,1])))
    design=np.c_[np.ones(len(xx)),(xx+x0-cx)/sx,(yy+y0-cy)/sy]
    samples=local[valid]
    coefficients=np.linalg.lstsq(design,samples,rcond=None)[0]
    for _ in range(2):
        error=np.max(np.abs(design@coefficients-samples),axis=1);keep=error<=max(3,float(np.quantile(error,.85)))
        coefficients=np.linalg.lstsq(design[keep],samples[keep],rcond=None)[0]
    valid_patch=valid.astype(np.uint8);valid_patch[:2]=0;valid_patch[-2:]=0;valid_patch[:,:2]=0;valid_patch[:,-2:]=0
    dist=cv2.distanceTransform(valid_patch,cv2.DIST_L2,5);py,px=np.unravel_index(np.argmax(dist),dist.shape)
    half=max(1,int(float(dist[py,px])/1.42)-1)
    while half>1 and not np.all(valid_patch[py-half:py+half+1,px-half:px+half+1]):half-=1
    patch=local[py-half:py+half+1,px-half:px+half+1]
    if min(patch.shape[:2])<3:raise ValueError('Original pad grain donor too small')
    grain=patch-cv2.GaussianBlur(patch,(0,0),1.5)
    my,mx=np.where(mask!=0)
    field=np.c_[np.ones(len(mx)),(mx-cx)/sx,(my-cy)/sy]@coefficients
    minimum=np.quantile(samples,.02,axis=0)-6;maximum=np.quantile(samples,.98,axis=0)+6
    field=np.clip(field,minimum,maximum)
    field+=grain[(my-y0)%grain.shape[0],(mx-x0)%grain.shape[1]]
    edited=base.copy()
    # Discard the old pad-only threshold retouch, keeping every previous leg.
    edited[zone!=0]=source[zone!=0]
    edited[my,mx,:3]=np.round(np.clip(field,0,255)).astype(np.uint8)
    combined=cv2.bitwise_or(old_mask,mask)
    gaming.final.compare_frame(source,edited,combined!=0)
    protected=(zone!=0)&(mask==0)&(old_mask==0)
    if not np.array_equal(source[protected],edited[protected]):raise ValueError('Protected bevel, silhouette or phone changed')
    source_only_interior=(mask!=0)&(np.max(np.abs(rgb.astype(float)-tone),axis=2)<8)
    color_delta=np.abs(edited[:,:,:3].astype(int)-rgb.astype(int))[source_only_interior]
    audit={'method':'contiguous_flat_pad_field_original_material_colour_plane_and_grain','sourceQuad':q.tolist(),'expandedFieldQuad':expanded.tolist(),'fieldOrientationSource':'PCA_of_original_print_core_then_contiguous_full_word_field','originalPrintCorePixels':seed_count,'paddingPixels':padding,'materialTone':tone.tolist(),'reviewedSourceMaterialPatch':material_patch,'materialGray':tone_gray,'sourceUnprintedSampleCount':len(xx),'sourceGrainPatch':[int(x0+px-half),int(y0+py-half),int(x0+px+half+1),int(y0+py+half+1)],'sourceGrainOnly':True,'protectedBevelPhoneExteriorPixels':int(np.count_nonzero(protected)),'unprintedInteriorMeanAbsRgbDelta':float(color_delta.mean()) if color_delta.size else None,'sourceMaskOutsideExact':True,'previousLegEditsPreserved':True}
    return edited,combined,mask,audit


def process(key,record):
    source_path=ROOT/record['sourcePath'];base_path=ROOT/record['path'];old_mask_path=ROOT/record['maskPath']
    for p,expected in [(source_path,record['sourceSha']),(base_path,record['outputSha']),(old_mask_path,record['maskSha'])]:
        if gaming.core.sha(p.read_bytes())!=expected:raise ValueError('Frozen source, base or mask bytes changed')
    if record['outputSha']==LARGE_SHA:
        reuse=copy.deepcopy(record);reuse['padPass']='unchanged_frozen_large_pad_already_root_reviewed';return reuse
    with Image.open(source_path) as im:source=np.array(im.convert('RGBA'));info=im.info.copy()
    base=np.array(Image.open(base_path).convert('RGBA'));old_mask=np.array(Image.open(old_mask_path).convert('L'))
    gaming.final.compare_frame(source,base,old_mask!=0)
    patches={'d50a4aa680ff0e376697356ea2771b123775c1aa87988f7fac3158fe98564807':[702,335,719,340],'ef5b7d0c667c9b8eed2e4a982197c9418b769df21e9a709d8c6047de847806b6':[741,353,758,358]}
    output,combined,new_mask,audit=pad_field(source,base,old_mask,record['plan']['regions'][0]['quad'],material_patch=patches.get(key))
    folder=DEST/key;folder.mkdir(parents=True,exist_ok=True);target=folder/'candidate.webp';metadata={k:info[k] for k in ['icc_profile','exif','xmp'] if info.get(k)}
    Image.fromarray(output).save(target,'WEBP',lossless=True,quality=100,method=4,exact=True,**metadata)
    decoded=np.array(Image.open(target).convert('RGBA'));gaming.final.compare_frame(source,decoded,combined!=0)
    mp=folder/'mask.png';Image.fromarray(combined).save(mp);npad=folder/'pad-field-mask.png';Image.fromarray(new_mask).save(npad)
    if np.mean(combined!=0)>.05:raise ValueError('Combined original-source mask exceeds 5 percent')
    detections,scan=gaming.core.get_engines(ROOT/'artifacts/media-cleanup/templates').scan(decoded[:,:,:3]);joined=gaming.final.joined_brand_hits(scan);style=gaming.cached_detect(decoded[:,:,:3],'desk')
    result={**record,'publicationReady':False,'visualAccepted':False,'state':'candidate_ready' if not detections and not joined and not style else 'rejected_residual_brand','path':gaming.relative(target),'outputSha':gaming.core.sha(target.read_bytes()),'bytes':target.stat().st_size,'maskPath':gaming.relative(mp),'maskSha':gaming.core.sha(mp.read_bytes()),'validation':{'outsideMaskRgbMaxDelta':0,'alphaMaxDelta':0,'maskCoverage':float(np.mean(combined!=0))},'postDetections':detections,'postScan':scan,'postJoinedBrand':joined,'postGamingTemplates':style,'padPass':audit,'frozenParentOutputSha':record['outputSha'],'padFieldMask':gaming.relative(npad),'padFieldMaskSha':gaming.core.sha(npad.read_bytes())}
    report=folder/'audit.json';result['report']=gaming.relative(report);gaming.core.atomic_json(report,result)
    pair=Image.new('RGB',(source.shape[1]*2,source.shape[0]),'white');pair.paste(Image.fromarray(source).convert('RGB'),(0,0));pair.paste(Image.fromarray(decoded).convert('RGB'),(source.shape[1],0));pair.save(folder/'full-comparison.jpg',quality=96)
    q=np.array(record['plan']['regions'][0]['quad']);a=np.maximum(0,q.min(0).astype(int)-12);b=np.minimum([source.shape[1],source.shape[0]],q.max(0).astype(int)+13);box=[*a,*b]
    before=Image.fromarray(source).convert('RGB').crop(box);after=Image.fromarray(decoded).convert('RGB').crop(box);close=Image.new('RGB',(before.width*2,before.height));close.paste(before,(0,0));close.paste(after,(before.width,0));close.save(folder/'close-pad.png')
    if gaming.core.sha(source_path.read_bytes())!=record['sourceSha']:raise ValueError('Original changed during review')
    return result


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--key',action='append');args=parser.parse_args()
    if gaming.core.sha(SOURCE.read_bytes())!=SOURCE_SHA:raise ValueError('Frozen Advent receipt changed')
    frozen=json.loads(SOURCE.read_text('utf-8'));receipt=DEST/'candidates.json';records=json.loads(receipt.read_text('utf-8')).get('images',{}) if receipt.exists() else {}
    for key,record in frozen['images'].items():
        if args.key and key not in args.key:continue
        try:result=process(key,record)
        except Exception as error:
            result={**record,'state':'failed_candidate_generation','publicationReady':False,'visualAccepted':False,'generationError':str(error)}
        records[key]=result
        gaming.core.atomic_json(receipt,{'schemaVersion':1,'pipelineVersion':frozen['pipelineVersion'],'publicationReady':False,'frozenParentManifest':gaming.relative(SOURCE),'frozenParentManifestSha':SOURCE_SHA,'mainManifestModified':False,'images':records})
        print(json.dumps({'key':key,'references':record['plan'].get('references'),'state':result['state'],'outputSha':result['outputSha'],'maskCoverage':result['validation']['maskCoverage'],'materialTone':result.get('padPass',{}).get('materialTone') if isinstance(result.get('padPass'),dict) else None}),flush=True)


if __name__=='__main__':sys.stdout.reconfigure(encoding='utf-8');main()
