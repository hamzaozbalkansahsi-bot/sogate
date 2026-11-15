"""Bounded original-source chair word repair; derivative receipts stay unapproved."""
import importlib.util,json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
import cv2
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('gaming_chair_base',ROOT/'scripts/media-gaming-review.py');base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
DEST=base.DEST/'chair-repair'


def bounded_surface(rgba,quad,protect_red=False,infer_edge=False,pad_field=False):
    rgb=rgba[:,:,:3];gray=cv2.cvtColor(rgb,cv2.COLOR_RGB2GRAY)
    mask=np.zeros(gray.shape,np.uint8);cv2.fillConvexPoly(mask,np.round(quad).astype(np.int32),255)
    white=(rgb.min(2)>242).astype(np.uint8)
    _,labels=cv2.connectedComponents(white)
    exterior=np.unique(np.r_[labels[0],labels[-1],labels[:,0],labels[:,-1]])
    exterior=exterior[exterior!=0]
    background=np.isin(labels,exterior)
    protected=cv2.dilate(background.astype(np.uint8),np.ones((3,3),np.uint8))!=0
    if pad_field:
        protected=background|(protected&(gray>205))
        samples=gray[(mask!=0)&(gray>25)&(gray<150)]
        if len(samples)<8:raise ValueError('Original pad material is not established')
        cutoff=float(np.quantile(samples,.6))*.60
        dark=gray<cutoff;_,dark_labels=cv2.connectedComponents(dark.astype(np.uint8))
        structural=np.unique(dark_labels[dark&(mask==0)]);structural=structural[structural!=0]
        edge=np.isin(dark_labels,structural)
        edge|=(cv2.dilate(edge.astype(np.uint8),np.ones((3,3),np.uint8))!=0)&(gray<cutoff*1.4)
        protected|=edge
        bright=gray>150;_,bright_labels=cv2.connectedComponents(bright.astype(np.uint8))
        adjoining=np.unique(bright_labels[bright&(mask==0)]);adjoining=adjoining[adjoining!=0]
        protected|=np.isin(bright_labels,adjoining)
        pigment=(rgb[:,:,0].astype(int)>rgb[:,:,1].astype(int)+5)&(rgb[:,:,0].astype(int)>rgb[:,:,2].astype(int)+5)
        protected[pigment&(mask!=0)&(gray<200)]=False
    if infer_edge:
        q=np.round(quad).astype(int);left=max(0,int(q[:,0].min())-14);right=min(rgb.shape[1],int(q[:,0].max())+15);top=int(q[:,1].min());bottom=int(q[:,1].max())
        rows=[];lo=[];hi=[]
        for y in list(range(max(0,top-12),top))+list(range(bottom+1,min(rgb.shape[0],bottom+13))):
            xs=np.where(gray[y,left:right]<210)[0]
            if len(xs)>=4:rows.append(y);lo.append(left+int(xs.min()));hi.append(left+int(xs.max()))
        if len(rows)<8:raise ValueError('Insufficient original clean silhouette rows')
        low=np.polyfit(rows,lo,2);high=np.polyfit(rows,hi,2)
        for y in range(max(0,top),min(rgb.shape[0],bottom+1)):
            a=max(left,int(np.ceil(np.polyval(low,y)))+1);b=min(right,int(np.floor(np.polyval(high,y))))
            if b>a:protected[y,a:b]=False
        pigment=(rgb[:,:,0].astype(int)>rgb[:,:,1].astype(int)+8)&(rgb[:,:,0].astype(int)>rgb[:,:,2].astype(int)+8)
        protected[pigment&(mask!=0)]=False
    data=rgb.astype(np.int16)
    solve_mask=mask.copy();solve_mask[protected]=0
    working=rgb
    if infer_edge or pad_field:
        ring=(cv2.dilate(mask,np.ones((19,19),np.uint8))!=0)&(mask==0)&(gray>80)&(gray<205)
        if pad_field:ring=(cv2.dilate(mask,np.ones((19,19),np.uint8))!=0)&(mask==0)&(gray>cutoff*1.4)&(gray<150)
        if np.count_nonzero(ring)<8:raise ValueError('No original interior gray near oblique word')
        tone=np.median(rgb[ring],axis=0).astype(np.uint8)
        working=rgb.copy();working[background]=tone
        if pad_field:working[protected]=tone
    if protect_red:
        red=(data[:,:,0]>data[:,:,1]*1.15+5)&(data[:,:,0]>data[:,:,2]*1.15+5)
        red_mask=cv2.dilate(red.astype(np.uint8)*255,np.ones((3,3),np.uint8))
        protected|=red_mask!=0
        # Recover the material under the measurement overlay for interpolation;
        # original red annotation bytes are restored outside the output mask.
        working=cv2.inpaint(rgb,red_mask,3,cv2.INPAINT_NS)
    mask[protected]=0
    if not np.any(mask)or np.mean(mask!=0)>.05:raise ValueError('Unsafe full-word source field')
    ys,xs=np.where(mask!=0);x0,x1=max(0,int(xs.min())-2),min(rgb.shape[1],int(xs.max())+3);y0,y1=max(0,int(ys.min())-2),min(rgb.shape[0],int(ys.max())+3)
    local=solve_mask[y0:y1,x0:x1]!=0
    seed=cv2.inpaint(working,solve_mask,3,cv2.INPAINT_NS)[y0:y1,x0:x1].astype(np.float32)
    original=working[y0:y1,x0:x1].astype(np.float32);seed[~local]=original[~local]
    for iteration in range(3000):
        smooth=cv2.blur(seed,(3,3));delta=float(np.max(np.abs(seed[local]-smooth[local])));seed[local]=smooth[local]
        if delta<.0005:break
    output=rgba.copy();patch=output[y0:y1,x0:x1,:3];local_output=mask[y0:y1,x0:x1]!=0;patch[local_output]=np.round(np.clip(seed[local_output],0,255)).astype(np.uint8)
    base.final.compare_frame(rgba,output,mask!=0)
    if not np.array_equal(output[protected],rgba[protected]):raise ValueError('Protected original silhouette/annotation changed')
    return output,mask,{'method':'original_boundary_harmonic_full_word_no_external_donor','harmonicIterations':iteration+1,'protectedOriginalSilhouette':True,'originalCleanRowsBoundObliqueSilhouette':infer_edge,'protectedOriginalRedAnnotations':protect_red,'outsideMaskRgbMaxDelta':0,'alphaMaxDelta':0}


def drawing_word(rgba,quad):
    rgb=rgba[:,:,:3];gray=cv2.cvtColor(rgb,cv2.COLOR_RGB2GRAY);gate=np.zeros(gray.shape,np.uint8);cv2.fillConvexPoly(gate,np.round(quad).astype(np.int32),255)
    dark=gray<180;_,labels=cv2.connectedComponents(dark.astype(np.uint8))
    structural=np.unique(labels[dark&(gate==0)]);structural=structural[structural!=0]
    protected=cv2.dilate(np.isin(labels,structural).astype(np.uint8),np.ones((3,3),np.uint8))!=0
    mask=cv2.dilate((dark&(gate!=0)).astype(np.uint8)*255,np.ones((3,3),np.uint8));mask[(gate==0)|protected]=0
    yy,xx=np.where(mask!=0);donor_x,donor_y=xx-300,yy-160
    if not len(xx)or np.any(rgb[donor_y,donor_x].min(1)<235):raise ValueError('Verified blank original paper donor missing')
    output=rgba.copy();output[yy,xx,:3]=rgb[donor_y,donor_x]
    base.final.compare_frame(rgba,output,mask!=0)
    return output,mask,{'method':'original_blank_paper_print_only_structural_components_protected','sourceDonorTranslation':[-300,-160],'originalCurvesAndArrowsPreserved':True,'outsideMaskRgbMaxDelta':0,'alphaMaxDelta':0}


def repair(key,old,plan):
    source=ROOT/old['sourcePath']
    if base.core.sha(source.read_bytes())!=old['sourceSha']:raise ValueError('Immutable source changed')
    with Image.open(source)as image:rgba=np.array(image.convert('RGBA'));info=image.info.copy()
    output=rgba.copy();combined=np.zeros(rgba.shape[:2],np.uint8);audits=[]
    for region in plan['regions']:
        if region['mode']=='white_fill':edited,mask,audit=drawing_word(rgba,region['quad'])
        else:edited,mask,audit=bounded_surface(rgba,region['quad'],region['mode']=='inpaint_white_only',region.get('perspectiveReviewRequired',False))
        output[mask!=0]=edited[mask!=0];combined|=mask;audits.append(audit)
    folder=DEST/key;folder.mkdir(parents=True,exist_ok=True);target=folder/'candidate.webp'
    Image.fromarray(output).save(target,'WEBP',lossless=True,quality=100,method=4,exact=True,**{field:info[field]for field in ['icc_profile','exif']if info.get(field)})
    with Image.open(target)as image:decoded=np.array(image.convert('RGBA'))
    base.final.compare_frame(rgba,decoded,combined!=0);mask_path=folder/'mask.png';Image.fromarray(combined).save(mask_path)
    detections,scan=base.core.get_engines(ROOT/'artifacts/media-cleanup/templates').scan(decoded[:,:,:3]);joined=base.final.joined_brand_hits(scan);style=base.cached_detect(decoded[:,:,:3],'chair')
    record={**old,'path':base.relative(target),'outputSha':base.core.sha(target.read_bytes()),'bytes':target.stat().st_size,'state':'candidate_ready'if not detections and not joined else'rejected_residual_brand','publicationReady':False,'visualAccepted':False,'maskPath':base.relative(mask_path),'maskSha':base.core.sha(mask_path.read_bytes()),'postDetections':detections,'postScan':scan,'postJoinedBrand':joined,'postGamingTemplates':style,'postGamingHitCount':len(style),'styleReviewRequired':bool(style),'regionAudits':audits,'validation':{'outsideMaskRgbMaxDelta':0,'alphaMaxDelta':0,'maskCoverage':float(np.mean(combined!=0))},'derivedFromCandidateSha':old['outputSha'],'plan':plan}
    record.pop('postGamingTemplateReview',None)
    previous=old.get('postGamingTemplateReview')
    if style and previous and style==old.get('postGamingTemplates'):
        with Image.open(ROOT/old['path'])as image:previous_rgb=np.array(image.convert('RGB'))
        for hit in style:
            x0,y0,x1,y1=hit['box']
            if not np.array_equal(previous_rgb[y0:y1,x0:x1],decoded[y0:y1,x0:x1,:3]):raise ValueError('Reviewed false-positive ROI changed')
        record['postGamingTemplateReview']={**previous,'candidateSha':record['outputSha'],'derivedFromCandidateSha':old['outputSha'],'exactReviewedRoiPixelsUnchanged':True}
    base.core.atomic_json(folder/'audit.json',record);record['report']=base.relative(folder/'audit.json')
    for index,region in enumerate(plan['regions']):
        q=np.array(region['quad']);lo=np.maximum(0,q.min(0).astype(int)-12);hi=np.minimum([rgba.shape[1],rgba.shape[0]],q.max(0).astype(int)+13);box=tuple([*lo,*hi]);a=Image.fromarray(rgba).convert('RGB').crop(box);b=Image.fromarray(decoded).convert('RGB').crop(box);im=Image.new('RGB',(a.width*2,a.height));im.paste(a,(0,0));im.paste(b,(a.width,0));im.save(folder/('close-'+str(index)+'.png'))
    return key,record


def main():
    old=json.loads((base.DEST/'nonadvent-final-candidates.json').read_text('utf-8'))
    plans=json.loads((base.DEST/'review-plans-prox.json').read_text('utf-8'))['images']
    refs={'4934:1','4934:2','4934:4','4934:9','4934:10','4934:11','4934:12','4934:13','4935:2','4935:10','4935:11','4935:12','4936:2','4936:5','4936:11','4936:12'}
    records={};errors=[]
    with ThreadPoolExecutor(max_workers=4)as pool:
        for plan in plans.values():
            if plan['reference']=='4934:13':plan['regions'][0]['quad']=[[760,276],[809,276],[809,295],[760,295]]
        tasks=[pool.submit(repair,key,old['images'][key],plan)for key,plan in plans.items()if plan['reference']in refs]
        for future in as_completed(tasks):
            try:key,record=future.result();records[key]=record;print(json.dumps({'reference':record['plan']['reference'],'outputSha':record['outputSha'],'state':record['state']}),flush=True)
            except Exception as error:errors.append(str(error));print(json.dumps({'error':str(error)}),flush=True)
    base.core.atomic_json(DEST/'candidates.json',{'schemaVersion':1,'pipelineVersion':base.FROZEN,'publicationReady':False,'images':records});base.core.atomic_json(DEST/'errors.json',errors)
    print(json.dumps({'images':len(records),'errors':errors,'publicationReady':False}),flush=True)

if __name__=='__main__':main()
