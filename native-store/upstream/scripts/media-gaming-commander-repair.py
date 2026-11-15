"""Original-boundary full-field Commander word derivatives; no publication writes."""
import importlib.util,json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('commander_surface',ROOT/'scripts/media-gaming-chair-repair.py');chair=importlib.util.module_from_spec(spec);spec.loader.exec_module(chair)
base=chair.base;DEST=base.DEST/'commander-repair'


def repair(key,old,plan):
    source=ROOT/old['sourcePath']
    if base.core.sha(source.read_bytes())!=old['sourceSha']:raise ValueError('Original changed')
    with Image.open(source)as image:rgba=np.array(image.convert('RGBA'));info=image.info.copy()
    output=rgba.copy();combined=np.zeros(rgba.shape[:2],np.uint8);audits=[]
    for region in plan['regions']:
        edited,mask,audit=chair.bounded_surface(rgba,region['quad'],pad_field=True)
        output[mask!=0]=edited[mask!=0];combined|=mask;audits.append(audit)
    folder=DEST/key;folder.mkdir(parents=True,exist_ok=True);target=folder/'candidate.webp';Image.fromarray(output).save(target,'WEBP',lossless=True,quality=100,method=4,exact=True,**{field:info[field]for field in ['icc_profile','exif']if info.get(field)})
    with Image.open(target)as image:decoded=np.array(image.convert('RGBA'))
    base.final.compare_frame(rgba,decoded,combined!=0);mask_path=folder/'mask.png';Image.fromarray(combined).save(mask_path)
    detections,scan=base.core.get_engines(ROOT/'artifacts/media-cleanup/templates').scan(decoded[:,:,:3]);joined=base.final.joined_brand_hits(scan);style=base.cached_detect(decoded[:,:,:3],'desk')
    record={**old,'path':base.relative(target),'outputSha':base.core.sha(target.read_bytes()),'bytes':target.stat().st_size,'maskPath':base.relative(mask_path),'maskSha':base.core.sha(mask_path.read_bytes()),'state':'candidate_ready'if not detections and not joined else'rejected_residual_brand','postDetections':detections,'postScan':scan,'postJoinedBrand':joined,'postGamingTemplates':style,'postGamingHitCount':len(style),'styleReviewRequired':bool(style),'regionAudits':audits,'publicationReady':False,'visualAccepted':False,'validation':{'outsideMaskRgbMaxDelta':0,'alphaMaxDelta':0,'maskCoverage':float(np.mean(combined!=0))},'derivedFromCandidateSha':old['outputSha'],'plan':plan}
    record.pop('postGamingTemplateReview',None);base.core.atomic_json(folder/'audit.json',record);record['report']=base.relative(folder/'audit.json')
    q=np.array(plan['regions'][0]['quad']);lo=np.maximum(0,q.min(0).astype(int)-12);hi=np.minimum([rgba.shape[1],rgba.shape[0]],q.max(0).astype(int)+13);box=tuple([*lo,*hi]);a=Image.fromarray(rgba).convert('RGB').crop(box);b=Image.fromarray(decoded).convert('RGB').crop(box);im=Image.new('RGB',(a.width*2,a.height));im.paste(a,(0,0));im.paste(b,(a.width,0));im.save(folder/'close-0.png')
    return key,record


def main():
    old=json.loads((base.DEST/'nonadvent-final-candidates.json').read_text('utf-8'))['images'];plans=json.loads((base.DEST/'review-plans-remaining-desks.json').read_text('utf-8'))['images'];records={};errors=[]
    targets={key:plan for key,plan in plans.items()if plan['references'][0].startswith('4687:')and plan['references'][0]not in {'4687:1','4687:17'}}
    with ThreadPoolExecutor(max_workers=4)as pool:
        tasks=[pool.submit(repair,key,old[key],plan)for key,plan in targets.items()]
        for future in as_completed(tasks):
            try:key,row=future.result();records[key]=row;print(json.dumps({'reference':row['plan']['references'],'outputSha':row['outputSha'],'state':row['state']}),flush=True)
            except Exception as error:errors.append(str(error));print(json.dumps({'error':str(error)}),flush=True)
    base.core.atomic_json(DEST/'candidates.json',{'schemaVersion':1,'pipelineVersion':base.FROZEN,'publicationReady':False,'images':records});base.core.atomic_json(DEST/'errors.json',errors)
    print(json.dumps({'images':len(records),'errors':errors,'publicationReady':False}),flush=True)

if __name__=='__main__':main()
