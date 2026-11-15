"""Separate residual-ink candidates for frozen37fb outputs; no master writes."""
from pathlib import Path
import argparse
from concurrent.futures import ThreadPoolExecutor
import importlib.util
import json
import math
import shutil
import sys

import cv2
import numpy as np
from PIL import Image,ImageDraw,ImageOps

ROOT=Path(__file__).resolve().parents[1]
FROZEN_PIPELINE='37fbdbdb594cb9d366fec3cb7f2662a694d4497ea7545607d471d23c3a9ecbd9'
spec=importlib.util.spec_from_file_location('media_clean_margin',ROOT/'scripts/media-clean.py');media=importlib.util.module_from_spec(spec);spec.loader.exec_module(media)
DEST=ROOT/'artifacts/media-ink-margin'
cv2.setNumThreads(1)


def shifted_any(binary,dx=0,dy=0,distance=3):
    result=np.zeros_like(binary)
    for step in range(1,distance+1):
        transform=np.array([[1,0,dx*step],[0,1,dy*step]],np.float32)
        result|=cv2.warpAffine(binary.astype(np.uint8),transform,(binary.shape[1],binary.shape[0]),flags=cv2.INTER_NEAREST,borderMode=cv2.BORDER_CONSTANT).astype(bool)
    return result


def remove_margin_ink(source,current,original_mask,detections,tones):
    output=current.copy();incremental=np.zeros(original_mask.shape,np.uint8);audit=[]
    gray=cv2.cvtColor(current,cv2.COLOR_RGB2GRAY);hsv=cv2.cvtColor(current,cv2.COLOR_RGB2HSV)
    for index,detection in enumerate(detections):
        x0,y0,x1,y1=detection['box'];height=max(1,y1-y0)
        radius=max(3,min(8,round(height*.40)))
        gate=np.zeros_like(original_mask)
        polygon=np.array(detection.get('polygon',[[x0,y0],[x1,y0],[x1,y1],[x0,y1]]),np.int32)
        cv2.fillConvexPoly(gate,polygon,255)
        gate=cv2.dilate(gate,np.ones((3,3),np.uint8))
        gate=cv2.bitwise_and(gate,cv2.dilate(original_mask,np.ones((radius*2+1,radius*2+1),np.uint8)))
        gate[original_mask!=0]=0
        tone=np.array(tones[min(index,len(tones)-1)],float)
        bg_distance=np.linalg.norm(current.astype(float)-tone,axis=2)
        near_background=bg_distance<30
        left=shifted_any(near_background,dx=1);right=shifted_any(near_background,dx=-1)
        above=shifted_any(near_background,dy=1);below=shifted_any(near_background,dy=-1)
        bounded=(left&right)|(above&below)
        white=(gray>max(85,float(np.mean(tone))+25))&(hsv[:,:,1]<150)
        data=current.astype(float)
        colored=(data[:,:,0]>data[:,:,1]*1.35+8)&(data[:,:,0]>data[:,:,2]*1.2+8)&(data[:,:,0]>max(35,tone[0]+8))
        ink=(white|colored)&(gate!=0)&(bg_distance>18)
        # Preserve long, straight physical silver/white frame edges, including
        # the case where an equally dark furniture opening lies behind them.
        frame_protection=np.zeros_like(original_mask)
        a,b,c,d=max(0,x0-2),max(0,y0-2),min(gray.shape[1],x1+2),min(gray.shape[0],y1+2)
        white_roi=(white[b:d,a:c]&(gate[b:d,a:c]!=0)).astype(np.uint8)*255
        width=max(1,x1-x0)
        lines=cv2.HoughLinesP(white_roi,1,np.pi/180,threshold=max(5,round(min(width,height)*.45)),minLineLength=max(5,round(min(width*.65,height*.75))),maxLineGap=1)
        for line in np.asarray(lines).reshape(-1,4) if lines is not None else []:
            sx,sy,ex,ey=map(int,line);dx,dy=abs(ex-sx),abs(ey-sy);length=math.hypot(dx,dy)
            if (dy<=dx*.5 and length>=width*.65) or (dx<=dy*.35 and length>=height*.75):
                cv2.line(frame_protection,(a+sx,b+sy),(a+ex,b+ey),255,1)
        frame_protection=(cv2.dilate(frame_protection,np.ones((3,3),np.uint8))!=0)&white&~colored
        confirmed=ink&bounded&~frame_protection
        # One antialias pixel may neighbor the confirmed real ink, but the mask
        # cannot expand across arbitrary furniture colors or frame highlights.
        extended=(cv2.dilate(confirmed.astype(np.uint8),np.ones((3,3),np.uint8))!=0)&ink&~frame_protection
        part=extended.astype(np.uint8)*255
        output[part!=0]=np.round(tone).astype(np.uint8)
        incremental=cv2.bitwise_or(incremental,part)
        audit.append({'box':detection['box'],'tone':tone.tolist(),'searchRadius':radius,'candidateInkPixels':int(np.count_nonzero(ink)),'protectedPhysicalFramePixels':int(np.count_nonzero(frame_protection&(gate!=0))),'oppositeSubstrateConfirmedPixels':int(np.count_nonzero(confirmed)),'removedInkPixels':int(np.count_nonzero(part)),'unresolvedCandidateInkPixels':int(np.count_nonzero(ink&~extended&~frame_protection))})
    output[incremental==0]=current[incremental==0]
    return output,incremental,audit


def one(task):
    key,item=task;report=json.loads(media.safe_path(ROOT,item['report']).read_text('utf-8'))
    source_path=media.safe_path(ROOT,item['sourcePath']);current_path=media.safe_path(ROOT,item['path'])
    if media.sha(source_path.read_bytes())!=item['sourceSha'] or media.sha(current_path.read_bytes())!=item['outputSha']:raise ValueError('Frozen bytes changed')
    source=np.array(Image.open(source_path).convert('RGB'));current=np.array(Image.open(current_path).convert('RGB'))
    original_mask=np.array(Image.open(media.safe_path(ROOT,report['maskPath'])).convert('L'))
    original_validation=media.image_delta(source,current,original_mask)
    if original_validation['outsideMaskMaxDelta']!=0:raise ValueError('Original output outside-mask invariant failed')
    regions=report.get('plaqueAudit',{}).get('regions',[])
    tones=[region['tone'] for region in regions if region.get('tone')]
    if not tones:
        samples=current[original_mask!=0];tones=[np.median(samples,axis=0).tolist()]
    output,extra,audit=remove_margin_ink(source,current,original_mask,report['detections'],tones)
    combined=cv2.bitwise_or(original_mask,extra)
    folder=DEST/'candidates';folder.mkdir(parents=True,exist_ok=True)
    target=folder/(key+'.webp');mask_path=folder/(key+'-mask.png');extra_path=folder/(key+'-incremental-mask.png')
    if np.any(extra):validation=media.save_lossless_validated(output,source,combined,target)
    else:shutil.copyfile(current_path,target);validation=media.image_delta(source,output,combined)
    Image.fromarray(combined).save(mask_path);Image.fromarray(extra).save(extra_path)
    found,scan=media.get_engines(ROOT/'artifacts/media-cleanup/templates').scan(output)
    result={'urlSha':key,'pipelineVersion':FROZEN_PIPELINE,'operation':'ink_margin_correction' if np.any(extra) else 'existing_output_margin_review','sourceSha':item['sourceSha'],'sourcePath':item['sourcePath'],'original37fbReport':item['report'],'previousOutputSha':item['outputSha'],'previousOutputPath':item['path'],'path':media.relative(ROOT,target),'outputSha':media.sha(target.read_bytes()),'maskPath':media.relative(ROOT,mask_path),'maskSha':media.sha(mask_path.read_bytes()),'incrementalMaskPath':media.relative(ROOT,extra_path),'incrementalMaskSha':media.sha(extra_path.read_bytes()),'width':source.shape[1],'height':source.shape[0],'bytes':target.stat().st_size,'mime':'image/webp','validation':validation,'incrementalChangedPixels':int(np.count_nonzero(extra)),'marginAudit':audit,'postDetections':found,'postScan':scan,'state':'candidate_ready' if not found else 'rejected_residual_brand','visualAccepted':False,'publicationReady':False,'globalIconPassRequired':True}
    if media.sha(source_path.read_bytes())!=item['sourceSha'] or media.sha(current_path.read_bytes())!=item['outputSha']:raise ValueError('Frozen input changed while checking margin')
    media.atomic_json(folder/(key+'.json'),result)
    return result


def sheets(records):
    paths=[]
    for start in range(0,len(records),24):
        group=records[start:start+24];sheet=Image.new('RGB',(1800,math.ceil(len(group)/2)*205),'white');draw=ImageDraw.Draw(sheet)
        for i,record in enumerate(group):
            report=json.loads(media.safe_path(ROOT,record['original37fbReport']).read_text('utf-8'));boxes=[d['box'] for d in report['detections']]
            crop=(max(0,min(b[0] for b in boxes)-16),max(0,min(b[1] for b in boxes)-15),min(record['width'],max(b[2] for b in boxes)+16),min(record['height'],max(b[3] for b in boxes)+16))
            x,y=i%2*900,i//2*205
            for col,(name,path) in enumerate([('source',record['sourcePath']),('previous',record['previousOutputPath']),('margin candidate',record['path'])]):
                image=Image.open(media.safe_path(ROOT,path)).convert('RGB');tile=ImageOps.contain(image.crop(crop),(290,160));sheet.paste(tile,(x+col*300+5,y+20));draw.text((x+col*300+5,y+2),name,fill='black');draw.text((x+col*300+5,y+183),record['urlSha'][:24],fill='black')
        path=DEST/f'final-comparison-{start//24+1:03d}.png';sheet.save(path);paths.append(media.relative(ROOT,path))
    return paths


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--workers',type=int,default=4,choices=range(1,9));args=parser.parse_args()
    manifest=json.loads((ROOT/'artifacts/media-cleanup.json').read_text('utf-8'))
    if manifest['pipelineVersion']!=FROZEN_PIPELINE or media.pipeline_version(ROOT/'artifacts/media-cleanup/templates')!=FROZEN_PIPELINE:raise ValueError('Frozen pipeline changed')
    tasks=[(key,item) for key,item in manifest['images'].items() if item['state']=='approved_cleaned']
    with ThreadPoolExecutor(max_workers=args.workers) as pool:records=list(pool.map(one,tasks))
    receipt={'pipelineVersion':FROZEN_PIPELINE,'passVersion':media.sha(Path(__file__).read_bytes()),'publicationReady':False,'mainManifestModified':False,'images':records,'sheets':sheets(records),'reviewedOutputs':len(records),'changedOutputs':sum(r['incrementalChangedPixels']>0 for r in records)}
    media.atomic_json(DEST/'candidates.json',receipt);print(json.dumps({k:v for k,v in receipt.items() if k not in ['images']},ensure_ascii=False),flush=True)


if __name__=='__main__':sys.stdout.reconfigure(encoding='utf-8');main()
