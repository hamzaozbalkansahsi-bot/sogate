"""Read-only second pass for tiny physical word badges missed at catalogue scale."""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor,as_completed
import importlib.util
import json,math,threading
from pathlib import Path
import cv2
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('nodeno_symbol_audit',ROOT/'scripts/media-symbol-audit.py')
audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
DEST=ROOT/'artifacts/media-small-badge-audit'
CONFIG={'widths':[12,13,14,16,18,20,22,24],'rotations':[0],'score':.93,'realTinyScore':.90,'edgeScore':.38,'maxPeaks':4,'obliqueWordScore':.85,'obliqueWordMinWidth':18,'obliqueEdgeScore':.60,'obliqueContrast':60}
LOCAL=threading.local()

class SmallBadgeMatcher:
    def __init__(self):
        paths=list((ROOT/'artifacts/media-cleanup/templates').glob('*.png'))+[DEST/'templates'/name for name in ['tiny-real-badge.png','tiny-oblique-word.png','tiny-collapsed-word.png']]
        self.paths=sorted(paths)
        self.variants=[]
        for path in self.paths:
            rgb=np.array(Image.open(path).convert('RGB'))
            for width in CONFIG['widths']:
                if path.name=='tiny-oblique-word.png' and width<CONFIG['obliqueWordMinWidth']:continue
                height=max(3,round(width*rgb.shape[0]/rgb.shape[1]))
                variant=cv2.resize(rgb,(width,height),interpolation=cv2.INTER_AREA if width<=rgb.shape[1] else cv2.INTER_CUBIC)
                for angle in CONFIG['rotations']:
                    color=np.ascontiguousarray(np.rot90(variant,angle//90));gray=cv2.cvtColor(color,cv2.COLOR_RGB2GRAY)
                    if gray.std()<12:continue
                    self.variants.append((path.name,width,angle,color,gray,cv2.Canny(gray,45,135)))

    def detect(self,rgb,targeted=False):
        gray=cv2.cvtColor(rgb,cv2.COLOR_RGB2GRAY)
        if int(gray.max())-int(gray.min())<8:return []
        found=[]
        for name,width,angle,color,template,edges in self.variants:
            is_oblique=name=='tiny-oblique-word.png'
            threshold=CONFIG['obliqueWordScore'] if is_oblique else CONFIG['realTinyScore'] if name.startswith('tiny-') else CONFIG['score']
            h,w=template.shape
            if h>=gray.shape[0] or w>=gray.shape[1]:continue
            scores=cv2.matchTemplate(gray,template,cv2.TM_CCOEFF_NORMED)
            for _ in range(CONFIG['maxPeaks']):
                _,score,_,point=cv2.minMaxLoc(scores)
                if not math.isfinite(score) or score<threshold-.04:break
                x,y=point;crop=rgb[y:y+h,x:x+w];g=gray[y:y+h,x:x+w]
                color_score=float(cv2.matchTemplate(crop,color,cv2.TM_CCOEFF_NORMED)[0,0])
                combined=float(score*.7+color_score*.3)
                edge_score=float(cv2.matchTemplate(cv2.Canny(g,45,135),edges,cv2.TM_CCORR_NORMED)[0,0])
                contrast=float(np.percentile(g,90)-np.percentile(g,10))
                if combined>=threshold and edge_score>=(CONFIG['obliqueEdgeScore'] if is_oblique else CONFIG['edgeScore']) and contrast>=(CONFIG['obliqueContrast'] if is_oblique else 35):
                    found.append({'box':[x,y,x+w,y+h],'confidence':round(combined,6),'grayConfidence':round(float(score),6),'colorConfidence':round(color_score,6),'edgeConfidence':round(edge_score,6),'template':name,'scaleWidth':width,'rotation':angle,'kind':'tiny_word_badge_candidate','visualAccepted':False})
                scores[max(0,y-h//2):min(scores.shape[0],y+h//2+1),max(0,x-w//2):min(scores.shape[1],x+w//2+1)]=-1
        kept=[]
        for hit in sorted(found,key=lambda value:value['confidence'],reverse=True):
            if not any(audit.media.box_iou(hit['box'],old['box'])>.2 for old in kept):kept.append(hit)
        return kept

def matcher():
    if not hasattr(LOCAL,'matcher'):LOCAL.matcher=SmallBadgeMatcher()
    return LOCAL.matcher

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--workers',type=int,default=16,choices=range(1,33));parser.add_argument('--limit',type=int,default=0);args=parser.parse_args()
    DEST.mkdir(parents=True,exist_ok=True)
    paths=SmallBadgeMatcher().paths
    version=audit.media.sha(Path(__file__).read_bytes()+json.dumps(CONFIG,sort_keys=True).encode()+b''.join(path.read_bytes() for path in paths))
    audit.matcher=matcher
    jobs,manifest,download,targets,product_ids=audit.jobs_from_manifests()
    if args.limit:jobs=jobs[:args.limit]
    reports=[];todo=[]
    for job in jobs:
        path=DEST/'reports'/(job[0]+'.json')
        if path.exists():
            previous=json.loads(path.read_text('utf-8'))
            if previous.get('passVersion')==version and audit.media.sha(job[1].read_bytes())==job[0]:
                previous['roles']=job[3];reports.append(previous);continue
        todo.append(job)
    print(json.dumps({'event':'started','uniqueFiles':len(jobs),'cached':len(reports),'passVersion':version}),flush=True)
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for future in as_completed([pool.submit(audit.scan_file,job) for job in todo]):
            report=future.result();report['passVersion']=version
            for hit in report['hits']:hit['id']=audit.media.sha((version+report['fileSha256']+json.dumps(hit,sort_keys=True)).encode())
            audit.media.atomic_json(DEST/'reports'/(report['fileSha256']+'.json'),report);reports.append(report)
            if len(reports)%100==0:print(json.dumps({'event':'progress','completed':len(reports),'total':len(jobs),'filesWithHits':sum(bool(row['hits']) for row in reports)}),flush=True)
    source_keys={role['urlSha'] for row in reports for role in row['roles'] if role['role']=='source'}
    output_keys={role['urlSha'] for row in reports for role in row['roles'] if role['role']=='current_output'}
    audit.DEST=DEST
    receipt={'schemaVersion':1,'basePipelineVersion':audit.FROZEN_PIPELINE,'passVersion':version,'publicationReady':False,'mainManifestModified':False,'config':CONFIG,'referenceSha256':{path.name:audit.media.sha(path.read_bytes()) for path in paths},'sourceReferences':len(download['references']),'sourceUrlsScanned':len(source_keys),'currentOutputUrlsScanned':len(output_keys),'allSourceUrlsScanned':len(source_keys)==len(download['images']),'uniqueFilesScanned':len(reports),'filesWithCandidateHits':sum(bool(row['hits']) for row in reports),'hitSheets':audit.hit_sheets(reports),'reports':[{'fileSha256':row['fileSha256'],'path':'artifacts/media-small-badge-audit/reports/'+row['fileSha256']+'.json','hits':row['candidateHits'],'roles':row['roles']} for row in reports]}
    audit.media.atomic_json(DEST/'receipt.json',receipt)
    print(json.dumps({key:value for key,value in receipt.items() if key not in ['reports','hitSheets','config']}),flush=True)

if __name__=='__main__':main()
