"""Independent full-image Adore gaming-symbol audit, tied to frozen media hashes.

This creates evidence and candidate hits, never approvals or main-manifest edits.
"""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor,as_completed
import importlib.util
import json
import math
from pathlib import Path
import sys
import threading
import time
import unicodedata

import cv2
import numpy as np
from PIL import Image,ImageDraw,ImageOps

ROOT=Path(__file__).resolve().parents[1]
FROZEN_PIPELINE="37fbdbdb594cb9d366fec3cb7f2662a694d4497ea7545607d471d23c3a9ecbd9"
spec=importlib.util.spec_from_file_location('media_clean_symbol_import',ROOT/'scripts/media-clean.py')
media=importlib.util.module_from_spec(spec);spec.loader.exec_module(media)
cv2.setNumThreads(1)
DEST=ROOT/'artifacts/media-symbol-audit'
REFERENCE_FOLDER=ROOT/'artifacts/media-review-special/templates'
CONFIG={'widths':[8,10,12,15,18,22,24,27,34,42,52,64], 'rotations':[0,90,180,270], 'globalScore':.90, 'gamingScore':.80, 'minDarkRatio':.45, 'minWhiteRatio':.035, 'maxPeaksPerVariant':3}
CACHE={}
LOCKS={}
GUARD=threading.Lock()
LOCAL=threading.local()


class SymbolMatcher:
    def __init__(self,folder=REFERENCE_FOLDER):
        paths=[Path(folder)/name for name in ['adore-gaming-flame-frame14.png','adore-gaming-flame-gray-frame10.png']]
        self.paths=paths
        self.variants=[]
        for path in paths:
            rgb=np.array(Image.open(path).convert('RGB'))
            for width in CONFIG['widths']:
                height=max(4,round(width*rgb.shape[0]/rgb.shape[1]))
                resized=cv2.resize(rgb,(width,height),interpolation=cv2.INTER_AREA if width<rgb.shape[1] else cv2.INTER_CUBIC)
                for angle in CONFIG['rotations']:
                    variant=np.ascontiguousarray(np.rot90(resized,angle//90))
                    gray=cv2.cvtColor(variant,cv2.COLOR_RGB2GRAY)
                    if gray.std()<12:continue
                    self.variants.append((path.name,width,angle,variant,gray))

    def detect(self,rgb,targeted=False):
        gray=cv2.cvtColor(rgb,cv2.COLOR_RGB2GRAY)
        if int(gray.max())-int(gray.min())<8:
            return []
        threshold=CONFIG['gamingScore'] if targeted else CONFIG['globalScore']
        found=[]
        for name,width,angle,template,template_gray in self.variants:
            height,tw=template_gray.shape
            if height>=gray.shape[0] or tw>=gray.shape[1]:continue
            if not targeted and min(height,tw)<6:continue
            scores=cv2.matchTemplate(gray,template_gray,cv2.TM_CCOEFF_NORMED)
            for _ in range(CONFIG['maxPeaksPerVariant']):
                _,score,_,point=cv2.minMaxLoc(scores)
                if not math.isfinite(score) or score<threshold-.10:break
                x,y=point;crop=rgb[y:y+height,x:x+tw];cropgray=gray[y:y+height,x:x+tw]
                dark=float(np.mean(cropgray<95));white=float(np.mean((crop.min(axis=2)>125)&((crop.max(axis=2).astype(int)-crop.min(axis=2))<85)))
                color=float(cv2.matchTemplate(crop,template,cv2.TM_CCOEFF_NORMED)[0,0])
                combined=float(score*.6+color*.4)
                data=crop.astype(float)
                orange=float(np.mean((data[:,:,0]>data[:,:,1]*1.4+15)&(data[:,:,0]>data[:,:,2]*1.4+15)&(data[:,:,0]>100)))
                if combined>=threshold and dark>=CONFIG['minDarkRatio'] and white>=CONFIG['minWhiteRatio'] and ('gray' in name or orange>=.01):
                    found.append({'box':[x,y,x+tw,y+height],'confidence':round(combined,6),'grayConfidence':round(float(score),6),'colorConfidence':round(color,6),'template':name,'scaleWidth':width,'rotation':angle,'darkRatio':round(dark,5),'whiteRatio':round(white,5),'orangeRatio':round(orange,5),'visualAccepted':False})
                scores[max(0,y-height//2):min(scores.shape[0],y+height//2+1),max(0,x-tw//2):min(scores.shape[1],x+tw//2+1)]=-1
        kept=[]
        for hit in sorted(found,key=lambda h:h['confidence'],reverse=True):
            if not any(media.box_iou(hit['box'],old['box'])>.20 for old in kept):kept.append(hit)
        return kept


def matcher():
    if not hasattr(LOCAL,'matcher'):LOCAL.matcher=SymbolMatcher()
    return LOCAL.matcher


def scan_frame(rgb,targeted):
    rgb_sha=media.sha(str((rgb.shape,str(rgb.dtype))).encode()+rgb.tobytes())
    key=(rgb_sha,bool(targeted))
    with GUARD:lock=LOCKS.setdefault(key,threading.Lock())
    with lock:
        with GUARD:cached=CACHE.get(key)
        if cached is not None:return cached,rgb_sha,True
        hits=matcher().detect(rgb,targeted)
        with GUARD:CACHE[key]=hits
        return hits,rgb_sha,False


def scan_file(job):
    expected,path,targeted,roles=job
    started=time.monotonic()
    actual=media.sha(path.read_bytes())
    if actual!=expected:raise ValueError('Input file SHA mismatch: '+path.name)
    hits=[];frames=[]
    with Image.open(path) as image:
        count=getattr(image,'n_frames',1);width,height=image.size
        for frame_index in range(count):
            image.seek(frame_index);rgba=image.convert('RGBA');has_alpha=rgba.getchannel('A').getextrema()!=(255,255)
            for background in (['white','black'] if has_alpha else ['white']):
                canvas=Image.new('RGBA',image.size,background);canvas.alpha_composite(rgba);rgb=np.array(canvas.convert('RGB'))
                found,rgb_sha,reused=scan_frame(rgb,targeted)
                frames.append({'frame':frame_index,'background':background,'rgbSha256':rgb_sha,'scanReuse':reused,'hits':len(found)})
                hits.extend({**hit,'frame':frame_index,'background':background} for hit in found)
    if media.sha(path.read_bytes())!=expected:raise ValueError('Input changed while scanning')
    for hit in hits:
        identity={'fileSha256':expected,**{name:hit[name] for name in ['frame','background','box','template','scaleWidth','rotation']}}
        hit['id']=media.sha(json.dumps(identity,sort_keys=True).encode())
    report={'fileSha256':expected,'path':media.relative(ROOT,path),'roles':roles,'targetedGamingFamily':targeted,'width':width,'height':height,'frameCount':count,'compositesScanned':len(frames),'frames':frames,'hits':hits,'candidateHits':len(hits),'elapsedSeconds':round(time.monotonic()-started,3),'visualAccepted':False}
    return report


def normalized(value):
    return ''.join(c for c in unicodedata.normalize('NFKD',value.lower().replace('ı','i')) if not unicodedata.combining(c))


def gaming_keys(download):
    catalog=json.loads((ROOT/'data/catalog-source.json').read_text('utf-8'))
    ids=set()
    for product in catalog['products']:
        text=normalized(json.dumps(product,ensure_ascii=False))
        if any(word in text for word in ['oyuncu','gaming','oyun','koltuk']):ids.add(str(product['id']))
    return {key for ref,key in download['references'].items() if ref.split(':',1)[0] in ids},ids


def jobs_from_manifests(candidate_manifests=()):
    manifest=json.loads((ROOT/'artifacts/media-cleanup.json').read_text('utf-8'))
    download=json.loads((ROOT/'artifacts/media-download.json').read_text('utf-8'))
    if manifest.get('pipelineVersion')!=FROZEN_PIPELINE:raise ValueError('Unexpected main pipeline')
    targets,product_ids=gaming_keys(download)
    jobs={}
    def add(key,role,path,expected):
        if not path or not expected:return
        resolved=media.safe_path(ROOT,path)
        entry=jobs.setdefault(expected,{'path':resolved,'targeted':False,'roles':[]})
        entry['targeted']|=key in targets
        entry['roles'].append({'urlSha':key,'role':role,'path':path})
    for key,entry in download['images'].items():
        if entry.get('status')!='verified':raise ValueError('Original file not verified: '+key)
        add(key,'source',entry['path'],entry['sha256'])
    for key,entry in manifest['images'].items():
        if entry.get('state') in {'approved_unmodified','approved_cleaned'}:add(key,'current_output',entry.get('path'),entry.get('outputSha'))
    for candidate_path in candidate_manifests:
        data=json.loads(candidate_path.read_text('utf-8'));rows=data.get('images',data.get('candidates',[]))
        if isinstance(rows,dict):rows=[{'urlSha':key,**value} for key,value in rows.items()]
        for entry in rows:
            key=entry.get('urlSha',entry.get('key'))
            add(key,'review_candidate',entry.get('path',entry.get('outputPath')),entry.get('outputSha',entry.get('candidateSha')))
    return [(expected,item['path'],item['targeted'],item['roles']) for expected,item in jobs.items()],manifest,download,targets,product_ids


def generate_gaming_sheets(download,targets):
    folder=DEST/'gaming-gallery';folder.mkdir(parents=True,exist_ok=True)
    refs=[(ref,key) for ref,key in download['references'].items() if key in targets]
    paths=[]
    for start in range(0,len(refs),36):
        group=refs[start:start+36];sheet=Image.new('RGB',(1800,math.ceil(len(group)/6)*320),'white');draw=ImageDraw.Draw(sheet)
        for i,(ref,key) in enumerate(group):
            entry=download['images'][key]
            with Image.open(media.safe_path(ROOT,entry['path'])) as image:
                image.seek(0);tile=ImageOps.contain(image.convert('RGB'),(290,285))
                x,y=i%6*300,i//6*320;sheet.paste(tile,(x+5,y+20));draw.text((x+5,y+2),ref+' | '+key[:15],fill='black');draw.text((x+5,y+305),entry['format']+' '+str(entry.get('frames',1))+' frames',fill='black')
        path=folder/f'gallery-{start//36+1:03d}.jpg';sheet.save(path,quality=94);paths.append(media.relative(ROOT,path))
    return paths


def hit_sheets(reports):
    folder=DEST/'hits';folder.mkdir(parents=True,exist_ok=True)
    tiles=[];paths=[];sheet_index=0
    def flush():
        nonlocal sheet_index
        if not tiles:return
        sheet=Image.new('RGB',(1800,math.ceil(len(tiles)/6)*220),'white')
        for i,tile in enumerate(tiles):sheet.paste(tile,((i%6)*300,(i//6)*220))
        sheet_index+=1;path=folder/f'contact-{sheet_index:03d}.jpg';sheet.save(path,quality=94);paths.append(media.relative(ROOT,path));tiles.clear()
    for report in reports:
        unique=[]
        for hit in report['hits']:
            if any(hit['frame']==old['frame'] and media.box_iou(hit['box'],old['box'])>.2 for old in unique):continue
            unique.append(hit)
        if not unique:continue
        with Image.open(media.safe_path(ROOT,report['path'])) as image:
            for index,hit in enumerate(unique):
                image.seek(hit['frame']);rgb=image.convert('RGB');x0,y0,x1,y1=hit['box'];pad=max(15,y1-y0)
                crop=rgb.crop((max(0,x0-pad),max(0,y0-pad),min(rgb.width,x1+pad),min(rgb.height,y1+pad)))
                tile=Image.new('RGB',(300,220),'white');draw=ImageDraw.Draw(tile);thumb=ImageOps.contain(crop,(290,165));tile.paste(thumb,(5,20));draw.text((5,2),report['fileSha256'][:18]+' frame '+str(hit['frame']),fill='black');draw.text((5,190),str(hit['confidence'])+' '+str(hit['box']),fill='black');tiles.append(tile)
                crop.save(folder/(report['fileSha256']+f'-{index:03d}.png'))
                if len(tiles)>=48:flush()
    flush()
    return paths


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workers',type=int,default=12,choices=range(1,17))
    parser.add_argument('--limit',type=int,default=0)
    parser.add_argument('--targeted-only',action='store_true',help='Calibration only; receipt will not claim all-source coverage')
    parser.add_argument('--candidate-manifests',type=Path,nargs='*',default=[])
    parser.add_argument('--gaming-sheets',action='store_true')
    args=parser.parse_args()
    DEST.mkdir(parents=True,exist_ok=True)
    reference_paths=SymbolMatcher().paths
    version=media.sha(Path(__file__).read_bytes()+json.dumps(CONFIG,sort_keys=True).encode()+b''.join(path.read_bytes() for path in reference_paths))
    jobs,manifest,download,targets,product_ids=jobs_from_manifests(args.candidate_manifests)
    if args.targeted_only:jobs=[job for job in jobs if job[2]]
    if args.limit:jobs=jobs[:args.limit]
    reports=[];todo=[]
    for job in jobs:
        path=DEST/'reports'/(job[0]+'.json')
        if path.exists():
            previous=json.loads(path.read_text('utf-8'))
            if previous.get('passVersion')==version and media.sha(job[1].read_bytes())==job[0] and previous.get('targetedGamingFamily')==job[2]:
                previous['roles']=job[3];reports.append(previous);continue
        todo.append(job)
    print(json.dumps({'event':'started','uniqueFileJobs':len(jobs),'cached':len(reports),'newJobs':len(todo),'targetGalleryReferences':len(targets),'targetProductFamilies':len(product_ids),'passVersion':version}),flush=True)
    completed=0
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures={pool.submit(scan_file,job):job for job in todo}
        for future in as_completed(futures):
            report=future.result();report['passVersion']=version
            media.atomic_json(DEST/'reports'/(report['fileSha256']+'.json'),report);reports.append(report);completed+=1
            if completed%50==0:print(json.dumps({'event':'progress','completed':len(reports),'total':len(jobs),'filesWithHits':sum(bool(r['hits']) for r in reports)}),flush=True)
    source_keys={role['urlSha'] for report in reports for role in report['roles'] if role['role']=='source'}
    output_keys={role['urlSha'] for report in reports for role in report['roles'] if role['role']=='current_output'}
    receipt={'schemaVersion':1,'basePipelineVersion':FROZEN_PIPELINE,'passVersion':version,'publicationReady':False,'mainManifestModified':False,'config':CONFIG,'referenceSha256':{path.name:media.sha(path.read_bytes()) for path in reference_paths},'mainManifestUpdatedAt':manifest.get('updatedAt'),'sourceReferences':len(download['references']),'sourceUrlsScanned':len(source_keys),'currentOutputUrlsScanned':len(output_keys),'uniqueFilesScanned':len(reports),'allSourceUrlsScanned':len(source_keys)==len(download['images']),'filesWithCandidateHits':sum(bool(r['hits']) for r in reports),'currentOutputFilesWithCandidateHits':sum(bool(r['hits']) and any(role['role']=='current_output' for role in r['roles']) for r in reports),'gamingProductIds':sorted(product_ids),'gamingGalleryUrlCount':len(targets),'hitSheets':hit_sheets(reports),'reports':[{'fileSha256':r['fileSha256'],'path':'artifacts/media-symbol-audit/reports/'+r['fileSha256']+'.json','hits':r['candidateHits'],'roles':r['roles']} for r in reports]}
    if args.gaming_sheets:receipt['gamingGallerySheets']=generate_gaming_sheets(download,targets)
    media.atomic_json(DEST/'receipt.json',receipt)
    print(json.dumps({k:v for k,v in receipt.items() if k not in ['reports','gamingProductIds','gamingGallerySheets','hitSheets','config']},ensure_ascii=False),flush=True)


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');main()
