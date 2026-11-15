"""Source-bound combined candidates; never changes accepted earlier candidates."""
from __future__ import annotations
import argparse
import importlib.util
import json
from pathlib import Path
import re
import sys

import cv2
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('special_review',ROOT/'scripts/media-review-special.py')
review=importlib.util.module_from_spec(spec);spec.loader.exec_module(review)
DEST=review.DEST/'combined'
C21='c21c9627608d2a5b3cf8b3985e6b0fd4c4625611ec4321f75ae3e7a9709f957d'
EFDAA='efdaa6163e60d1c13ea64b7312d56dcbf86876c728184fb91be31777ee30c956'
SOURCE_SHAS={C21:'929e15c2add3c41e546eed3dae45a81dea43177c703d4e499c5ed129391174d7',EFDAA:'11f39f8185035d1cb755c586bab68edb62e1b80f033b883aa81e1dba6b515d5a'}
OBLIQUE={
    **{frame:[[733,198],[745,199],[745,225],[732,225]] for frame in [13,17,18,19,20]},
    14:[[397,199],[441,217],[455,254],[401,240]],
    15:[[286,248],[330,267],[342,306],[292,289]],
    16:[[397,199],[441,217],[455,254],[401,240]],
    24:[[1224,198],[1237,198],[1237,230],[1224,230]],
}


def joined_brand_rows(scan):
    found=[]
    for row in scan.get('ocr',[]):
        value=re.sub('[^a-z0-9]','',row.get('text','').lower())
        if ('gaming' in value and any(x in value for x in ['dore','dorg','dare','adore','sdore'])) or any(x in value for x in ['adoregsming','adorggsming','adorggaming','adorgaming','sdoregaming','doregame']):found.append(row)
    return found


def vertical_surface_retouch(rgb,quad,offset=45):
    """Edge-on leather: source donor follows the reviewed projected face slope."""
    allowed=np.zeros(rgb.shape[:2],np.uint8);cv2.fillConvexPoly(allowed,np.array(quad,np.int32),255)
    foreground=rgb.min(2)<252
    mask=((allowed!=0)&foreground).astype(np.uint8)*255
    yy,xx=np.where(mask!=0)
    if not len(xx):raise ValueError('Edge-on word mask is empty')
    if yy.max()+offset>=rgb.shape[0]:raise ValueError('Column donor leaves image')
    # The reviewed donor follows the sloped front face instead of crossing its
    # side seam. Original white background is excluded; native contour QA is
    # still required for each of these very narrow perspective views.
    points=np.array(quad);narrow=np.ptp(points[:,0])<20
    offset_x=(-4 if points[:,0].mean()<1000 else 4) if narrow else 18
    donor=rgb[yy+offset,xx+offset_x].astype(float)
    distance=cv2.distanceTransform((mask!=0).astype(np.uint8),cv2.DIST_L2,5)[yy,xx]
    alpha=np.ones((len(xx),1)) if narrow else np.clip(distance/2,0,1)[:,None]
    output=rgb.copy();output[yy,xx]=np.round(donor*alpha+rgb[yy,xx]*(1-alpha)).astype(np.uint8)
    return output,mask,{'method':'source_unprinted_leather_following_projected_face_slope','manualPrintQuad':quad,'donorTranslation':[offset_x,offset],'sourceWhiteBackgroundExcluded':True,'outsideMaskExact':True}


def local_scan(engines,rgb,quad):
    p=np.array(quad);a=np.maximum(0,np.floor(p.min(0)-12).astype(int));b=np.minimum([rgb.shape[1],rgb.shape[0]],np.ceil(p.max(0)+13).astype(int))
    crop=Image.fromarray(rgb).crop([*a,*b]);crop=crop.resize((crop.width*3,crop.height*3))
    detections,scan=engines.scan(np.array(crop))
    return {'cropBox':[*a.tolist(),*b.tolist()],'scale':3,'detections':detections,'scan':scan,'joinedBrandRows':joined_brand_rows(scan)}


def process_c21(entry,engines,flames,revise_obliques=False):
    source_path=ROOT/entry['path'];base_path=review.DEST/C21/'audit.json';base=json.loads(base_path.read_text('utf-8'))
    if review.sha((ROOT/base['path']).read_bytes())!=base['outputSha']:raise ValueError('Frozen accepted base changed')
    folder=DEST/C21;staged=folder/'staged';masks=folder/'masks';staged.mkdir(parents=True,exist_ok=True);masks.mkdir(parents=True,exist_ok=True)
    previous=json.loads((folder/'audit.json').read_text('utf-8')) if revise_obliques else None
    audits=[];paths=[];mask_paths=[];durations=[];post_count=0;flame_count=0;joined_count=0
    with Image.open(source_path) as source:
        loop=int(source.info.get('loop',0));count=source.n_frames
        for frame in range(count):
            source.seek(frame);original=np.array(source.convert('RGBA'));duration=int(source.info.get('duration',0));durations.append(duration)
            if previous and frame not in OBLIQUE:
                old=previous['frameAudits'][frame];mp=ROOT/old['maskPath'];path=staged/f'{frame:03d}.png'
                if review.sha(mp.read_bytes())!=old['maskSha']:raise ValueError('Unchanged combined mask changed')
                mask=np.array(Image.open(mp).convert('L'));review.validate_rgba(original,np.array(Image.open(path).convert('RGBA')),mask)
                audits.append(old);paths.append(path);mask_paths.append(mp);post_count+=len(old['postDetections']);flame_count+=len(old['postFlame']['hits']);joined_count+=len(old['joinedBrandRows'])+(len(old['headrestLocalScan']['joinedBrandRows']) if old['headrestLocalScan'] else 0)
                continue
            prior=base['frameAudits'][frame];base_mask_path=ROOT/prior['maskPath']
            if review.sha(base_mask_path.read_bytes())!=prior['maskSha']:raise ValueError('Accepted base mask changed')
            mask=np.array(Image.open(base_mask_path).convert('L'));base_rgba=np.array(Image.open(review.DEST/C21/'staged'/f'{frame:03d}.png').convert('RGBA'))
            review.validate_rgba(original,base_rgba,mask);edited=base_rgba[:,:,:3].copy();quads=list(prior['allowedLabelQuads']);head_audit=None;local=None
            if frame in list(range(13))+[25]:
                row=next(row for row in prior['postScan']['ocr'] if row['box'][1]<280 and row['box'][2]-row['box'][0]>100)
                quad=np.array(row['polygon'],float);quad=(quad-quad.mean(0))*[1.10,1.65]+quad.mean(0)
                edited,extra,head_audit=review.source_surface_print_retouch(edited,quad)
                mask=cv2.bitwise_or(mask,extra);quads.append(quad.tolist());local=local_scan(engines,edited,quad)
            elif frame in OBLIQUE:
                quad=OBLIQUE[frame];edited,extra,head_audit=vertical_surface_retouch(edited,quad)
                mask=cv2.bitwise_or(mask,extra);quads.append(quad);local=local_scan(engines,edited,quad)
            output=review.combine_opaque_mask(original,edited,mask)
            path=staged/f'{frame:03d}.png';Image.fromarray(output).save(path,'PNG',compress_level=4);paths.append(path)
            mp=masks/f'{frame:03d}.png';Image.fromarray(mask).save(mp);mask_paths.append(mp)
            validation=review.validate_rgba(original,np.array(Image.open(path).convert('RGBA')),mask)
            detections,post=engines.scan(output[:,:,:3].copy());flame=flames.detect_regions(output[:,:,:3],quads)
            joined=joined_brand_rows(post);post_count+=len(detections);flame_count+=len(flame['hits']);joined_count+=len(joined)+(len(local['joinedBrandRows']) if local else 0)
            audits.append({'frame':frame,'durationMs':duration,'maskPath':review.rel(mp),'maskSha':review.sha(mp.read_bytes()),'maskPixels':int(np.count_nonzero(mask)),'allowedLabelQuads':quads,'validation':validation,'postDetections':detections,'postScan':post,'postFlame':flame,'joinedBrandRows':joined,'headrestLocalScan':local,'headrestRetouch':head_audit,'baseMaskSha':prior['maskSha']})
            if head_audit:
                p=np.array(quads[-1]);box=[*p.min(0),*p.max(0)];review.proof_pair(Image.fromarray(original),Image.fromarray(output),box,folder/f'headrest-{frame:03d}-before-after.png',C21+f' frame{frame}')
            if frame in [0,6,14,15,21,22,23,25]:
                pair=Image.new('RGB',(2000,1000),'white')
                for j,im in enumerate([Image.fromarray(original),Image.fromarray(output)]):im=im.convert('RGB');im.thumbnail((1000,1000));pair.paste(im,(j*1000,0))
                pair.save(folder/f'full-frame-{frame:03d}.jpg',quality=95)
            print(json.dumps({'key':C21[:12],'frame':frame,'detections':len(detections),'joinedBrandRows':len(joined),'flameHits':len(flame['hits'])}),flush=True)
    output_path=folder/'candidate.webp';review.encode_staged_animation(paths,durations,loop,output_path);timeline=review.validate_staged_animation(paths,durations,loop,output_path)
    checks=[]
    with Image.open(source_path) as source,Image.open(output_path) as output:
        for frame,mapping in enumerate(timeline['sourceToOutputMapping']):
            source.seek(frame);rgba=np.array(source.convert('RGBA'));mask=np.array(Image.open(mask_paths[frame]).convert('L'));results=[]
            for segment in mapping['outputSegments']:
                output.seek(segment['outputFrame']);results.append(review.validate_rgba(rgba,np.array(output.convert('RGBA')),mask))
            checks.append({'sourceFrame':frame,'checks':results})
    receipt=review.source_receipt(C21,entry)
    return {**receipt,'candidateState':'validated_candidate' if post_count==0 and flame_count==0 and joined_count==0 else 'review_required','reason':'combined_source_side_tag_and_all_visible_headrest_print','path':review.rel(output_path),'outputSha':review.sha(output_path.read_bytes()),'bytes':output_path.stat().st_size,'mime':'image/webp','frames':timeline['outputFrameCount'],'sourceFrames':count,'timeline':timeline,'frameAudits':audits,'decodeChecks':checks,'postDetectionCount':post_count,'postFlameHitCount':flame_count,'joinedBrandCount':joined_count,'maskOutsideRgbMaxDelta':0,'alphaMaxDelta':0,'supersedesCandidate':{'path':base['path'],'outputSha':base['outputSha'],'receipt':review.rel(base_path),'receiptSha':review.sha(base_path.read_bytes())},'fullFrameInspection':{'sourceFrames':26,'headrestVisibleFrames':list(range(21))+[24,25],'headrestAbsentFrames':[21,22,23],'usbCableConnectorPreserved':True,'careTagAmbiguityDecision':'pending_root_context_confirmation'}}


def process_efdaa(entry,engines,flames):
    receipt=review.source_receipt(EFDAA,entry);folder=DEST/EFDAA;folder.mkdir(parents=True,exist_ok=True)
    original=np.array(Image.open(ROOT/entry['path']).convert('RGBA'));rgb=original[:,:,:3]
    head=np.array([[692,201],[742,203],[742,232],[692,230]],float)
    edited,mask,head_audit=review.source_surface_print_retouch(rgb,head,donor_offset=25,ring_radius=7,colored_print=True,donor_patch=[696,229,735,239])
    side=[[739,300],[750,300],[751,337],[741,337]];extra=review.lettering_mask(rgb,side);edited=review.retouch_ink(edited,extra);mask=cv2.bitwise_or(mask,extra)
    output=review.combine_opaque_mask(original,edited,mask);path=folder/'candidate.webp';Image.fromarray(output).save(path,'WEBP',lossless=True,quality=100,method=6)
    decoded=np.array(Image.open(path).convert('RGBA'));validation=review.validate_rgba(original,decoded,mask);mp=folder/'mask.png';Image.fromarray(mask).save(mp)
    detections,scan=engines.scan(decoded[:,:,:3].copy());local=local_scan(engines,decoded[:,:,:3],head);flame=flames.detect_regions(decoded[:,:,:3],[head.tolist(),side]);joined=joined_brand_rows(scan)
    review.proof_pair(Image.fromarray(original),Image.fromarray(decoded),[680,190,762,345],folder/'before-after.png',EFDAA)
    pair=Image.new('RGB',(1760,880),'white');pair.paste(Image.fromarray(original).convert('RGB'),(0,0));pair.paste(Image.fromarray(decoded).convert('RGB'),(880,0));pair.save(folder/'before-after-full.jpg',quality=95)
    review.source_receipt(EFDAA,entry)
    return {**receipt,'candidateState':'validated_candidate' if not detections and not flame['hits'] and not joined and not local['joinedBrandRows'] else 'review_required','reason':'combined_headrest_adoregaming_and_small_side_adore_tag','path':review.rel(path),'outputSha':review.sha(path.read_bytes()),'bytes':path.stat().st_size,'mime':'image/webp','frames':1,'maskPath':review.rel(mp),'maskSha':review.sha(mp.read_bytes()),'validation':validation,'postScans':[{'background':'opaque_source','detections':detections,'scan':scan}],'postFlame':flame,'headrestLocalScan':local,'joinedBrandRows':joined,'headrestRetouch':head_audit,'manualLabelQuads':[head.tolist(),side],'sourceIdentification':{'globalGroup':547,'preservedModelText':'ProX'},'closeProof':review.rel(folder/'before-after.png'),'fullProof':review.rel(folder/'before-after-full.jpg')}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--key',choices=[C21,EFDAA],required=True);parser.add_argument('--revise-obliques',action='store_true',help='Retain validated full-face stages and replace only separately reviewed oblique masks');args=parser.parse_args()
    if review.core.pipeline_version(ROOT/'artifacts/media-cleanup/templates')!=review.FROZEN_PIPELINE:raise ValueError('Frozen core changed')
    download=json.loads((ROOT/'artifacts/media-download.json').read_text('utf-8'));entry=download['images'][args.key]
    if entry['sha256']!=SOURCE_SHAS[args.key]:raise ValueError('Manual source changed')
    snapshot=review.DEST/'accepted-combined-frozen.json'
    if snapshot.exists():
        for frozen in json.loads(snapshot.read_text('utf-8'))['images']:
            if frozen['urlSha']==args.key:
                review.source_receipt(args.key,entry)
                if review.sha((ROOT/frozen['path']).read_bytes())!=frozen['outputSha']:raise ValueError('Root-reviewed combined bytes changed')
                print(json.dumps({'key':args.key,'candidateState':'frozen_root_reviewed_bytes','outputSha':frozen['outputSha']}),flush=True)
                return
    engines=review.core.Engines(ROOT/'artifacts/media-cleanup/templates');flames=review.FlameMatcher(scales=[.33,.36,.4,.45,.5,.6,.75,1.,1.25,1.5])
    result=process_c21(entry,engines,flames,args.revise_obliques) if args.key==C21 else process_efdaa(entry,engines,flames)
    report=DEST/args.key/'audit.json';result['report']=review.rel(report);review.core.atomic_json(report,result)
    cp=DEST/'candidates.json';records=json.loads(cp.read_text('utf-8')).get('images',{}) if cp.exists() else {};records[args.key]=result
    review.core.atomic_json(cp,{'schemaVersion':1,'pipelineVersion':review.FROZEN_PIPELINE,'publicationReady':False,'globalIconPassRequired':True,'images':records})
    print(json.dumps({'key':args.key,'state':result['candidateState'],'path':result['path'],'outputSha':result['outputSha']}),flush=True)


if __name__=='__main__':sys.stdout.reconfigure(encoding='utf-8');main()
