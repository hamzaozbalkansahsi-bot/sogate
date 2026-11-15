"""Independent stylized AdoreGaming gallery audit and review candidates.

Writes only artifacts/media-gaming-review; source/frozen reports/main stay intact.
"""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import importlib.util
import json
from pathlib import Path
import threading

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageOps, ImageSequence

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "artifacts/media-gaming-review"
FROZEN = "37fbdbdb594cb9d366fec3cb7f2662a694d4497ea7545607d471d23c3a9ecbd9"
spec = importlib.util.spec_from_file_location("gaming_frozen_core", ROOT / "scripts/media-clean.py")
core = importlib.util.module_from_spec(spec); spec.loader.exec_module(core)
spec = importlib.util.spec_from_file_location("gaming_finalizer", ROOT / "scripts/finalize-media.py")
final = importlib.util.module_from_spec(spec); spec.loader.exec_module(final)
cv2.setNumThreads(1)
LOCAL = threading.local()
MATCH_CACHE = {}
MATCH_LOCKS = {}
CACHE_GUARD = threading.Lock()
SPECIAL_HELPERS = None
REFERENCE_PLANS = [
    {"reference": "4583:14", "name": "stylized-pad-word.png", "quad": [[282,391],[521,34],[574,72],[335,429]], "size": [430,66]},
    {"reference": "4583:4", "name": "stylized-leg-word.png", "quad": [[367,531],[387,532],[382,648],[361,647]], "size": [22,118], "rotate": 90},
    {"reference": "4934:0", "name": "stylized-head-word.png", "quad": [[338,112],[412,112],[412,127],[338,127]], "size": [75,16], "scope":"chair"},
    {"reference": "4934:12", "name": "stylized-drawing-word.png", "quad": [[346,180],[428,184],[428,198],[346,194]], "size": [83,15], "scope":"chair"},
]


def relative(path):
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def family_products(catalog):
    return [product for product in catalog["products"] if str(product.get("id")) in {"4934","4935","4936"} or "oyuncu-masalari" in product.get("categoryIds", []) or (any(word in product.get("title", "").casefold() for word in ("oyuncu", "gaming")) and "masa" in product.get("title", "").casefold())]


def ocr_rows(scan, inherited_frame=0):
    result = []
    if isinstance(scan, dict):
        frame = scan.get("frame", inherited_frame)
        if isinstance(scan.get("text"), str) and final.joined_brand_hits(scan):
            result.append({**scan, "frame": frame})
        for value in scan.values():
            result.extend(ocr_rows(value, frame))
    elif isinstance(scan, list):
        for value in scan:
            result.extend(ocr_rows(value, inherited_frame))
    return result


def references():
    download = json.loads((ROOT / "artifacts/media-download.json").read_text("utf-8"))
    reverse = {}
    for reference, key in download["references"].items():
        reverse.setdefault(key, []).append(reference)
    return download, reverse


def generate_templates(download):
    folder = DEST / "templates"; folder.mkdir(parents=True, exist_ok=True)
    provenance = []
    for plan in REFERENCE_PLANS:
        key = download["references"][plan["reference"]]; entry = download["images"][key]
        source = ROOT / entry["path"]
        if core.sha(source.read_bytes()) != entry["sha256"]:
            raise ValueError("Original reference bytes changed")
        rgb = np.array(Image.open(source).convert("RGB")); width, height = plan["size"]
        transform = cv2.getPerspectiveTransform(np.float32(plan["quad"]), np.float32([[0,0],[width-1,0],[width-1,height-1],[0,height-1]]))
        template = cv2.warpPerspective(rgb, transform, (width,height), flags=cv2.INTER_CUBIC)
        if plan.get("rotate"):
            template = np.rot90(template, plan["rotate"] // 90).copy()
        target = folder / plan["name"]; Image.fromarray(template).save(target)
        provenance.append({**plan,"urlSha":key,"sourcePath":entry["path"],"sourceSha":entry["sha256"],"path":relative(target),"sha256":core.sha(target.read_bytes()),"actualSourceCrop":True})
    core.atomic_json(folder / "provenance.json", {"pipelineVersion":FROZEN,"publicationReady":False,"references":provenance})
    return provenance


def inventory():
    download, reverse = references(); catalog = json.loads((ROOT / "data/catalog-source.json").read_text("utf-8"))
    hits = []
    for key, source in download["images"].items():
        report_path = ROOT / "artifacts/media-cleanup/reports" / (key + ".json")
        report = json.loads(report_path.read_text("utf-8")); found = ocr_rows(report.get("scan", {}))
        if found:
            hits.append({"urlSha":key,"sourceSha":source["sha256"],"sourcePath":source["path"],"references":reverse[key],"hits":found,"originalReportSha":core.sha(report_path.read_bytes())})
    products = family_products(catalog)
    keys = {download["references"][str(product["id"])+":"+str(index)] for product in products for index in range(len(product.get("images",[])))}
    receipt = {"schemaVersion":1,"pipelineVersion":FROZEN,"mainManifestModified":False,"publicationReady":False,"allSavedSourceReportsScanned":len(download["images"]),"joinedBrandFindings":hits,"gamingDeskFamilies":[{"id":str(p["id"]),"code":p.get("code"),"title":p.get("title"),"galleryReferences":len(p.get("images",[]))} for p in products],"familyUrlShas":sorted(keys),"references":generate_templates(download)}
    core.atomic_json(DEST / "inventory.json", receipt)
    sheets = []
    for product in products:
        tiles=[]
        for index in range(len(product.get("images",[]))):
            key=download["references"][str(product["id"])+":"+str(index)];source=download["images"][key]
            with Image.open(ROOT/source["path"]) as image:
                sample_indices=sorted({0,max(0,getattr(image,"n_frames",1)//2),getattr(image,"n_frames",1)-1})
                for frame in sample_indices:
                    image.seek(frame);thumb=ImageOps.contain(image.convert("RGB"),(315,250))
                    tile=Image.new("RGB",(325,280),"white");tile.paste(thumb,((325-thumb.width)//2,22));ImageDraw.Draw(tile).text((3,3),str(product["id"])+":"+str(index)+" frame"+str(frame)+" "+key[:10],fill="black");tiles.append(tile)
        for start in range(0,len(tiles),12):
            sheet=Image.new("RGB",(325*4,280*3),"white")
            for number,tile in enumerate(tiles[start:start+12]):sheet.paste(tile,((number%4)*325,(number//4)*280))
            target=DEST/("family-"+str(product["id"])+"-"+str(start//12+1)+".jpg");sheet.save(target,quality=95);sheets.append(relative(target))
    receipt["gallerySheets"]=sheets;core.atomic_json(DEST/"inventory.json",receipt)
    return receipt


class StylizedMatcher:
    def __init__(self,scope="desk"):
        self.scope=scope
        self.variants=[]
        for path in (DEST/"templates").glob("stylized-*.png"):
            is_chair="head-"in path.name or"drawing-"in path.name
            if is_chair!=(scope=="chair"):continue
            source=np.array(Image.open(path).convert("RGB"))
            for width in [28,40,55,80,110,160,230,320,430]:
                for flatten in [.55,1.]:
                    height=max(3,round(width*source.shape[0]/source.shape[1]*flatten))
                    sample=cv2.resize(source,(width,height),interpolation=cv2.INTER_AREA if width<source.shape[1] else cv2.INTER_CUBIC)
                    for rotation in [0,90,180,270]:
                        color=np.ascontiguousarray(np.rot90(sample,rotation//90));gray=cv2.cvtColor(color,cv2.COLOR_RGB2GRAY)
                        if gray.std()>12:self.variants.append((path.name,width,flatten,rotation,color,gray))

    def detect(self,rgb):
        gray=cv2.cvtColor(rgb,cv2.COLOR_RGB2GRAY);hits=[]
        for name,width,flatten,rotation,color,template in self.variants:
            h,w=template.shape
            if h>=gray.shape[0] or w>=gray.shape[1]:continue
            scores=cv2.matchTemplate(gray,template,cv2.TM_CCOEFF_NORMED)
            _,score,_,point=cv2.minMaxLoc(scores)
            if score<.76:continue
            x,y=point;crop=rgb[y:y+h,x:x+w]
            color_score=float(cv2.matchTemplate(crop,color,cv2.TM_CCOEFF_NORMED)[0,0]);combined=float(.65*score+.35*color_score)
            dark=float(np.mean(crop.max(axis=2)<110));ink=float(np.mean((crop.max(axis=2)>120)|(crop[:,:,0].astype(int)>crop[:,:,1].astype(int)*1.5+15)))
            orange=float(np.mean((crop[:,:,0].astype(int)>crop[:,:,1].astype(int)*1.25+10)&(crop[:,:,0].astype(int)>crop[:,:,2].astype(int)*1.2+10)&(crop[:,:,0]>65)))
            white=float(np.mean((cv2.cvtColor(crop,cv2.COLOR_RGB2GRAY)>80)&((crop.max(axis=2).astype(int)-crop.min(axis=2))<45)))
            material_ok=(orange>.015 and white>.02) if self.scope=="desk" else True
            if combined>=.82 and (dark>.35 if "drawing"not in name else white>.5) and .025<ink<.8 and material_ok:
                hits.append({"box":[x,y,x+w,y+h],"confidence":round(combined,6),"template":name,"scaleWidth":width,"flatten":flatten,"rotation":rotation,"kind":"stylized_joined_brand_candidate"})
        kept=[]
        for hit in sorted(hits,key=lambda row:row["confidence"],reverse=True):
            if not any(core.box_iou(hit["box"],other["box"])>.25 for other in kept):kept.append(hit)
        return kept


def matcher(scope="desk"):
    if not hasattr(LOCAL,"matchers"):LOCAL.matchers={}
    if scope not in LOCAL.matchers:LOCAL.matchers[scope]=StylizedMatcher(scope)
    return LOCAL.matchers[scope]


def cached_detect(rgb,scope="desk"):
    key=(scope,core.sha(str((rgb.shape,str(rgb.dtype))).encode()+rgb.tobytes()))
    with CACHE_GUARD:lock=MATCH_LOCKS.setdefault(key,threading.Lock())
    with lock:
        with CACHE_GUARD:cached=MATCH_CACHE.get(key)
        if cached is not None:return cached
        hits=matcher(scope).detect(rgb)
        with CACHE_GUARD:MATCH_CACHE[key]=hits
        return hits


def audit_one(key,entry,scope="desk"):
    source=ROOT/entry["path"]
    if core.sha(source.read_bytes())!=entry["sha256"]:raise ValueError("Original changed")
    report=json.loads((ROOT/"artifacts/media-cleanup/reports"/(key+".json")).read_text("utf-8"))
    saved=ocr_rows(report.get("scan",{}));frames=[]
    with Image.open(source) as image:
        for frame in range(getattr(image,"n_frames",1)):
            image.seek(frame);rgba=image.convert("RGBA");backgrounds=["white","black"] if rgba.getchannel("A").getextrema()!=(255,255) else ["white"]
            for background in backgrounds:
                canvas=Image.new("RGBA",rgba.size,background);canvas.alpha_composite(rgba);rgb=np.array(canvas.convert("RGB"))
                hits=cached_detect(rgb,scope)
                frames.append({"frame":frame,"background":background,"rgbSha":core.sha(str((rgb.shape,str(rgb.dtype))).encode()+rgb.tobytes()),"templateHits":hits,"savedJoinedOcr":[row for row in saved if row.get("frame",0)==frame]})
    if core.sha(source.read_bytes())!=entry["sha256"]:raise ValueError("Original changed during scan")
    return {"urlSha":key,"sourceSha":entry["sha256"],"sourcePath":entry["path"],"scope":scope,"frames":frames,"candidateHits":sum(len(row["templateHits"])+len(row["savedJoinedOcr"]) for row in frames),"publicationReady":False}


def audit(workers):
    receipt=inventory();download,reverse=references();records=[]
    keys=sorted(set(receipt["familyUrlShas"])|{row["urlSha"] for row in receipt["joinedBrandFindings"]})
    folder=DEST/"reports";folder.mkdir(parents=True,exist_ok=True)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for future in as_completed([pool.submit(audit_one,key,download["images"][key],"chair" if any(r.split(':')[0]in{"4934","4935","4936","4741"}for r in reverse[key])else"desk") for key in keys]):
            record=future.result();core.atomic_json(folder/(record["urlSha"]+".json"),record);records.append(record)
            if len(records)%20==0:print(json.dumps({"event":"style_audit_progress","completed":len(records),"total":len(keys)}),flush=True)
    summary={"schemaVersion":1,"pipelineVersion":FROZEN,"mainManifestModified":False,"publicationReady":False,"sourceImagesScanned":len(records),"allGamingDeskGalleryUrlsScanned":set(receipt["familyUrlShas"])<={r["urlSha"] for r in records},"allSavedSourceReportsScanned":receipt["allSavedSourceReportsScanned"],"reports":[{"urlSha":r["urlSha"],"sourceSha":r["sourceSha"],"path":relative(folder/(r["urlSha"]+".json")),"candidateHits":r["candidateHits"]} for r in records]}
    core.atomic_json(DEST/"audit.json",summary);return summary


def ink_mask(rgba,quad,light_material=False):
    gate=np.zeros(rgba.shape[:2],np.uint8);cv2.fillConvexPoly(gate,np.round(quad).astype(np.int32),255)
    rgb=rgba[:,:,:3].astype(np.int16);gray=cv2.cvtColor(rgba[:,:,:3],cv2.COLOR_RGB2GRAY)
    orange=(rgb[:,:,0]>rgb[:,:,1]+8)&(rgb[:,:,0]>rgb[:,:,2]+12)&(rgb[:,:,0]>35)
    # A gray tabletop can be brighter than the old absolute ink threshold.
    # Actual lettering is locally brighter than its material; broad smooth
    # surface illumination must stay outside the edit mask.
    material_floor=cv2.morphologyEx(gray,cv2.MORPH_OPEN,np.ones((31,31),np.uint8))
    light=(gray>90)&((gray.astype(np.int16)-material_floor.astype(np.int16))>10)&((rgb.max(axis=2)-rgb.min(axis=2))<100)
    if light_material:light&=gray>180
    # Printed strokes must have dark product material on both sides of the
    # text's short axis; white exterior/product edges are never donor ink.
    points=np.array(quad,float);a,b=points[1]-points[0],points[3]-points[0];long=a if np.linalg.norm(a)>=np.linalg.norm(b)else b
    normal=np.array([-long[1],long[0]])/max(np.linalg.norm(long),1)
    ys,xs=np.where(gate!=0);left=np.zeros(len(xs),bool);right=left.copy()
    short_axis=min(np.linalg.norm(a),np.linalg.norm(b))
    for distance in range(1,min(100,int(np.ceil(short_axis))+5)+1):
        for direction,found in [(-1,left),(1,right)]:
            xx=np.round(xs+normal[0]*distance*direction).astype(int);yy=np.round(ys+normal[1]*distance*direction).astype(int);valid=(xx>=0)&(yy>=0)&(xx<gray.shape[1])&(yy<gray.shape[0]);found[valid]|=gray[yy[valid],xx[valid]]<90
    material=np.zeros_like(gate);material[ys[left&right],xs[left&right]]=255
    if light_material:material[gate!=0]=255
    if not np.any((orange|light)&(gate!=0)&(material!=0)):
        # A reviewed far-edge print can have white exterior on one side.
        # Keep exterior whites outside the edit, including their antialias.
        material[((gate!=0)&(gray<180))]=255
    mask=cv2.dilate(((orange|(light&(material!=0)))&(gate!=0)).astype(np.uint8)*255,np.ones((3,3),np.uint8));mask[gate==0]=0
    if not np.any(mask):raise ValueError("Reviewed brand field produced no safe ink pixels")
    if np.any((mask!=0)&(rgba[:,:,3]!=255)) or np.mean(mask!=0)>.05:raise ValueError("Unsafe ink mask")
    return mask


def texture_shift(rgba,mask,offset,max_brightness=130):
    dx,dy=[int(value) for value in offset];ys,xs=np.where(mask!=0);xx,yy=xs+dx,ys+dy
    if len(xs)==0 or np.any(xx<0)or np.any(yy<0)or np.any(xx>=rgba.shape[1])or np.any(yy>=rgba.shape[0]):raise ValueError("Invalid source texture donor")
    if np.any(mask[yy,xx]!=0)or np.any(rgba[yy,xx,3]!=255):raise ValueError("Donor overlaps brand or transparency")
    donor=rgba[yy,xx,:3]
    if np.percentile(donor.max(axis=1),95)>max_brightness:raise ValueError("Texture donor does not stay on reviewed source material")
    output=rgba.copy();output[ys,xs,:3]=donor;return output


def special_helpers():
    global SPECIAL_HELPERS
    if SPECIAL_HELPERS is None:
        spec=importlib.util.spec_from_file_location("gaming_surface_helpers",ROOT/"scripts/media-review-special.py")
        SPECIAL_HELPERS=importlib.util.module_from_spec(spec);spec.loader.exec_module(SPECIAL_HELPERS)
    return SPECIAL_HELPERS


def source_row_retouch(rgb,mask,light_material=False):
    output=rgb.copy();gray=cv2.cvtColor(rgb,cv2.COLOR_RGB2GRAY)
    material=(gray<(245 if light_material else 150))&(mask==0)
    if light_material:material&=gray>150
    ring=(cv2.dilate(mask,np.ones((11,11),np.uint8))!=0)&material
    if np.count_nonzero(ring)<5:raise ValueError("No original material around reviewed print")
    ring_values=rgb[ring];ring_gray=gray[ring]
    fallback=np.median(ring_values[ring_gray>=np.quantile(ring_gray,.5)],axis=0)
    for y in np.where(np.any(mask!=0,axis=1))[0]:
        xs=np.where(mask[y]!=0)[0];left=max(0,int(xs.min())-8);right=min(rgb.shape[1],int(xs.max())+9)
        values=rgb[y,left:right][material[y,left:right]]
        if len(values)>=4:
            tones=cv2.cvtColor(values[np.newaxis,:,:],cv2.COLOR_RGB2GRAY)[0]
            values=values[tones>=np.quantile(tones,.5)]
        tone=np.median(values,axis=0)if len(values)>=2 else fallback
        output[y,mask[y]!=0]=np.round(tone).astype(np.uint8)
    return output


def apply_region(rgba,region):
    mode=region.get("mode","inpaint_ink");output=rgba.copy();audit={"mode":mode}
    if mode in {"surface_texture","surface_texture_ink"}:
        helper=special_helpers()
        rgb,field,audit=helper.source_surface_print_retouch(rgba[:,:,:3],region["quad"],donor_offset=region.get("donorOffset",20),ring_radius=region.get("ringRadius",7),colored_print=True,donor_translation=region.get("offset"))
        if mode=="surface_texture_ink":
            ink=ink_mask(rgba,region["quad"]);mask=None
            for radius in [region.get("maskGrow",6),4,2,0]:
                trial=cv2.dilate(ink,np.ones((radius*2+1,radius*2+1),np.uint8));trial[field==0]=0
                if np.mean(trial!=0)<=.05:mask=trial;break
            if mask is None:raise ValueError("Expanded print mask exceeds five percent")
        else:mask=field
        output[mask!=0,:3]=rgb[mask!=0]
    elif mode=="inpaint_field":
        mask=np.zeros(rgba.shape[:2],np.uint8);cv2.fillConvexPoly(mask,np.round(region["quad"]).astype(np.int32),255)
        rgb,audit=core.inpaint_preserving(rgba[:,:,:3],mask);output[mask!=0,:3]=rgb[mask!=0]
    elif mode in {"white_fill","inpaint_white_only"}:
        gray=cv2.cvtColor(rgba[:,:,:3],cv2.COLOR_RGB2GRAY);data=rgba[:,:,:3].astype(np.int16)
        gate=np.zeros(rgba.shape[:2],np.uint8);cv2.fillConvexPoly(gate,np.round(region["quad"]).astype(np.int32),255)
        if mode=="white_fill":
            mask=cv2.dilate(((gray<180)&(gate!=0)).astype(np.uint8)*255,np.ones((3,3),np.uint8));mask[gate==0]=0
            ys,xs=np.where(mask!=0);dx,dy=region.get("offset",[0,-20]);xx,yy=xs+dx,ys+dy
            if np.any(xx<0)or np.any(yy<0)or np.any(xx>=rgba.shape[1])or np.any(yy>=rgba.shape[0])or np.any(rgba[yy,xx,:3].min(axis=1)<235):raise ValueError("Drawing fill donor must be actual blank source paper")
            output[ys,xs,:3]=rgba[yy,xx,:3]
        else:
            red=(data[:,:,0]>data[:,:,1]*1.15+5)&(data[:,:,0]>data[:,:,2]*1.15+5)
            protected=cv2.dilate(red.astype(np.uint8),np.ones((3,3),np.uint8))!=0
            mask=ink_mask(rgba,region["quad"]);mask[protected]=0
            rgb=source_row_retouch(rgba[:,:,:3],mask);output[mask!=0,:3]=rgb[mask!=0]
            if not np.array_equal(output[protected],rgba[protected]):raise ValueError("Technical red annotation changed")
            audit["redAnnotationPixelsProtected"]=int(np.count_nonzero(protected))
    else:
        mask=ink_mask(rgba,region["quad"],region.get("allowLightMaterial",False))
        if mode=="texture_shift":output=texture_shift(rgba,mask,region["offset"],region.get("donorMaxBrightness",130))
        elif mode=="inpaint_ink":
            mask=cv2.morphologyEx(mask,cv2.MORPH_CLOSE,np.ones((3,3),np.uint8))
            rgb=source_row_retouch(rgba[:,:,:3],mask,region.get("allowLightMaterial",False));output[mask!=0,:3]=rgb[mask!=0]
            audit={"method":"reviewed_print_only_actual_neighboring_source_row_tones","sourcePixelsOnly":True}
        else:raise ValueError("Unknown reviewed gaming region method")
    if not np.any(mask)or np.mean(mask!=0)>.05:raise ValueError("Empty or excessive reviewed gaming mask")
    final.compare_frame(rgba,output,mask!=0)
    return output,mask,audit


def apply_frame_regions(rgba,regions):
    output=rgba.copy();combined=np.zeros(rgba.shape[:2],np.uint8);audits=[]
    for region in regions:
        edited,mask,audit=apply_region(rgba,region);output[mask!=0]=edited[mask!=0];combined=cv2.bitwise_or(combined,mask);audits.append(audit)
    if np.mean(combined!=0)>.05:raise ValueError("Combined source mask exceeds five percent")
    final.compare_frame(rgba,output,combined!=0)
    return output,combined,audits


def apply_plans(path,receipt_name="candidates.json"):
    if Path(receipt_name).name!=receipt_name or not receipt_name.endswith(".json"):raise ValueError("Receipt must remain in owned review directory")
    download,reverse=references();plans=json.loads(path.read_text("utf-8"));old=DEST/receipt_name;previous=json.loads(old.read_text("utf-8"))if old.exists()else{};records=previous.get("images",{});unmodified=previous.get("reviewedUnmodified",{})
    for key,plan in plans["images"].items():
        print(json.dumps({"event":"gaming_candidate_start","urlSha":key}),flush=True)
        entry=download["images"][key]
        if plan["sourceSha"]!=entry["sha256"]:raise ValueError("Plan source SHA mismatch")
        source=ROOT/entry["path"]
        if core.sha(source.read_bytes())!=entry["sha256"]:raise ValueError("Original changed")
        if not plan.get("regions")and not plan.get("frameRegions"):
            if plan.get("reuseRequired"):
                reuse=plan["reuseExisting"];target=ROOT/reuse["path"]
                if core.sha(target.read_bytes())!=reuse["outputSha"]or reuse["sourceSha"]!=entry["sha256"]:raise ValueError("Required existing combined retouch changed")
                continue
            unmodified[key]={"sourceSha":entry["sha256"],"sourcePath":entry["path"],"notes":plan.get("reviewNotes"),"publicationReady":False};continue
        with Image.open(source) as image:
            if getattr(image,"n_frames",1)!=1:
                record=apply_animation(key,entry,plan,reverse[key]);records[key]=record
                core.atomic_json(old,{"schemaVersion":1,"pipelineVersion":FROZEN,"mainManifestModified":False,"publicationReady":False,"images":records,"reviewedUnmodified":unmodified});continue
            info=image.info.copy()
            rgba=np.array(image.convert("RGBA"))
        output,combined,region_audits=apply_frame_regions(rgba,plan["regions"])
        folder=DEST/"candidates"/key;folder.mkdir(parents=True,exist_ok=True)
        target=folder/"candidate.webp";Image.fromarray(output).save(target,"WEBP",lossless=True,quality=100,method=4,exact=True,**({"icc_profile":info["icc_profile"]}if info.get("icc_profile")else{}),**({"exif":info["exif"]}if info.get("exif")else{}))
        decoded=np.array(Image.open(target).convert("RGBA"));final.compare_frame(rgba,decoded,combined!=0)
        mask_path=folder/"mask.png";Image.fromarray(combined).save(mask_path)
        detections,scan=core.get_engines(ROOT/"artifacts/media-cleanup/templates").scan(decoded[:,:,:3]);joined=final.joined_brand_hits(scan);scope="chair"if any(r.split(':')[0]in{"4934","4935","4936","4741"}for r in reverse[key])else"desk";style=cached_detect(decoded[:,:,:3],scope)
        ready=not detections and not joined and not style
        record={"urlSha":key,"sourceSha":entry["sha256"],"sourcePath":entry["path"],"sourceBytes":entry["bytes"],"pipelineVersion":FROZEN,"publicationReady":False,"visualAccepted":False,"state":"candidate_ready"if ready else"rejected_residual_brand","path":relative(target),"outputSha":core.sha(target.read_bytes()),"bytes":target.stat().st_size,"mime":"image/webp","width":rgba.shape[1],"height":rgba.shape[0],"maskPath":relative(mask_path),"maskSha":core.sha(mask_path.read_bytes()),"validation":{"outsideMaskRgbMaxDelta":0,"alphaMaxDelta":0,"maskCoverage":float(np.mean(combined!=0))},"postDetections":detections,"postScan":scan,"postJoinedBrand":joined,"postGamingTemplates":style,"plan":plan,"regionAudits":region_audits}
        core.atomic_json(folder/"audit.json",record);record["report"]=relative(folder/"audit.json");records[key]=record
        pair=Image.new("RGB",(rgba.shape[1]*2,rgba.shape[0]),"white");pair.paste(Image.fromarray(rgba).convert("RGB"),(0,0));pair.paste(Image.fromarray(decoded).convert("RGB"),(rgba.shape[1],0));pair.thumbnail((1760,1100));pair.save(folder/"full-comparison.jpg",quality=96)
        for index,region in enumerate(plan["regions"]):
            points=np.array(region["quad"]);x0,y0=points.min(axis=0).astype(int)-12;x1,y1=points.max(axis=0).astype(int)+13;box=(max(0,x0),max(0,y0),min(rgba.shape[1],x1),min(rgba.shape[0],y1));a=Image.fromarray(rgba).convert("RGB").crop(box);b=Image.fromarray(decoded).convert("RGB").crop(box);close=Image.new("RGB",(a.width*2,a.height));close.paste(a,(0,0));close.paste(b,(a.width,0));close.save(folder/("close-"+str(index)+".png"))
        if core.sha(source.read_bytes())!=entry["sha256"]:raise ValueError("Original changed")
        core.atomic_json(old,{"schemaVersion":1,"pipelineVersion":FROZEN,"mainManifestModified":False,"publicationReady":False,"images":records,"reviewedUnmodified":unmodified})
    core.atomic_json(old,{"schemaVersion":1,"pipelineVersion":FROZEN,"mainManifestModified":False,"publicationReady":False,"images":records,"reviewedUnmodified":unmodified})
    return {"candidates":len(records),"ready":sum(r["state"]=="candidate_ready"for r in records.values()),"publicationReady":False}


def prepare_animation_frame(index,rgba,duration,regions,scope,stages,mask_folder):
    output,combined,region_audits=apply_frame_regions(rgba,regions)
    stage=stages/(str(index).zfill(3)+".png");Image.fromarray(output).save(stage)
    mask_path=mask_folder/(str(index).zfill(3)+".png");Image.fromarray(combined).save(mask_path)
    detections,scan=core.get_engines(ROOT/"artifacts/media-cleanup/templates").scan(output[:,:,:3]);joined=final.joined_brand_hits(scan);style=cached_detect(output[:,:,:3],scope)
    return {"frame":index,"durationMs":duration,"maskPath":relative(mask_path),"maskSha":core.sha(mask_path.read_bytes()),"validation":{"outsideMaskRgbMaxDelta":0,"alphaMaxDelta":0},"postDetections":detections,"postScan":scan,"postJoinedBrand":joined,"postGamingTemplates":style,"regionAudits":region_audits}


def apply_animation(key,entry,plan,source_references):
    spec=importlib.util.spec_from_file_location("gaming_review_animation_helpers",ROOT/"scripts/media-review-special.py");special=importlib.util.module_from_spec(spec);spec.loader.exec_module(special)
    folder=DEST/"candidates"/key;folder.mkdir(parents=True,exist_ok=True);stages=folder/"frames";stages.mkdir(exist_ok=True);mask_folder=folder/"masks";mask_folder.mkdir(exist_ok=True)
    frame_paths=[];durations=[];audits=[];scope="chair"if any(r.split(':')[0]in{"4934","4935","4936","4741"}for r in source_references)else"desk"
    with Image.open(ROOT/entry["path"])as source,ThreadPoolExecutor(max_workers=8)as pool:
        loop=source.info.get("loop",0);count=source.n_frames
        pending=[]
        for index in range(count):
            source.seek(index);rgba=np.array(source.convert("RGBA"));duration=int(source.info.get("duration",0));frame_paths.append(stages/(str(index).zfill(3)+".png"));durations.append(duration)
            pending.append(pool.submit(prepare_animation_frame,index,rgba,duration,plan.get("frameRegions",{}).get(str(index),plan.get("regions",[])),scope,stages,mask_folder))
            if len(pending)>=8:audits.append(pending.pop(0).result())
            if index%20==0:print(json.dumps({"event":"gaming_candidate_frame","urlSha":key,"frame":index,"frames":count}),flush=True)
        audits.extend(future.result()for future in pending)
    target=folder/"candidate.webp";special.encode_staged_animation(frame_paths,durations,loop,target);timeline=special.validate_staged_animation(frame_paths,durations,loop,target)
    clear=all(not row["postDetections"]and not row["postJoinedBrand"]and not row["postGamingTemplates"]for row in audits)
    record={"urlSha":key,"sourceSha":entry["sha256"],"sourcePath":entry["path"],"sourceBytes":entry["bytes"],"pipelineVersion":FROZEN,"publicationReady":False,"visualAccepted":False,"candidateState":"validated_candidate"if clear else"rejected_residual_brand","state":"candidate_ready"if clear else"rejected_residual_brand","path":relative(target),"outputSha":core.sha(target.read_bytes()),"bytes":target.stat().st_size,"mime":"image/webp","width":entry["width"],"height":entry["height"],"frames":timeline["outputFrameCount"],"sourceFrames":count,"timeline":timeline,"frameAudits":audits,"postDetectionCount":sum(len(r["postDetections"])+len(r["postJoinedBrand"])for r in audits),"postGamingHitCount":sum(len(r["postGamingTemplates"])for r in audits),"plan":plan}
    if core.sha((ROOT/entry["path"]).read_bytes())!=entry["sha256"]:raise ValueError("Original changed during animation cleanup")
    core.atomic_json(folder/"audit.json",record);record["report"]=relative(folder/"audit.json");return record


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--audit",action="store_true");parser.add_argument("--apply-plans",type=Path);parser.add_argument("--workers",type=int,default=8,choices=range(1,17));args=parser.parse_args();DEST.mkdir(parents=True,exist_ok=True)
    if args.apply_plans:result=apply_plans(args.apply_plans)
    elif args.audit:result=audit(args.workers)
    else:
        data=inventory();result={"families":len(data["gamingDeskFamilies"]),"galleryUrls":len(data["familyUrlShas"]),"sourceJoinedFindings":len(data["joinedBrandFindings"]),"publicationReady":False}
    print(json.dumps(result),flush=True)


if __name__=="__main__":main()
