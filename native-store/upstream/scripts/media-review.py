"""Independent review candidates and symbol audit; never writes the main manifest."""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor
import importlib.util
import json
import math
from pathlib import Path
import sys

import cv2
import numpy as np
from PIL import Image,ImageDraw,ImageOps

ROOT=Path(__file__).resolve().parents[1]
FROZEN_PIPELINE="37fbdbdb594cb9d366fec3cb7f2662a694d4497ea7545607d471d23c3a9ecbd9"
spec=importlib.util.spec_from_file_location("media_clean_review_import",ROOT/"scripts/media-clean.py")
media=importlib.util.module_from_spec(spec);spec.loader.exec_module(media)
cv2.setNumThreads(1)
DEST=ROOT/"artifacts/media-review"


def ordered_quad(points):
    points=np.array(points,dtype=np.float32).reshape(-1,2)
    center=points.mean(axis=0)
    angles=np.arctan2(points[:,1]-center[1],points[:,0]-center[0])
    points=points[np.argsort(angles)]
    return np.roll(points,-int(np.argmin(points.sum(axis=1))),axis=0)


def component_quad(rgb,detection):
    """A diagnostic quad from isolated real dark substrate; requires visual review."""
    x0,y0,x1,y1=detection["box"];width,height=x1-x0,y1-y0
    left=max(0,x0-max(5,round(width*.12)));right=min(rgb.shape[1],x1+max(5,round(width*.12)))
    top=max(0,y0-max(5,round(height*.4)));bottom=min(rgb.shape[0],y1+max(5,round(height*.4)))
    patch=rgb[top:bottom,left:right]
    gray=cv2.cvtColor(patch,cv2.COLOR_RGB2GRAY)
    gate=np.zeros(gray.shape,np.uint8)
    polygon=np.array(detection.get("polygon",[[x0,y0],[x1,y0],[x1,y1],[x0,y1]]),np.int32)-[left,top]
    cv2.fillConvexPoly(gate,polygon,255)
    samples=patch[(gate!=0)&(gray<110)]
    if len(samples)<3:
        return None,{"reason":"no_dark_substrate_samples"}
    levels=np.mean(samples,axis=1)
    tone=np.median(samples[levels<=np.percentile(levels,25)],axis=0)
    near=(np.linalg.norm(patch.astype(float)-tone,axis=2)<60)&(gray<115)
    contours,_=cv2.findContours(near.astype(np.uint8),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    choices=[]
    for contour in contours:
        area=cv2.contourArea(contour)
        if area<max(2,width*height*.05) or area>width*height*2.2:
            continue
        component=np.zeros_like(gate);cv2.drawContours(component,[contour],-1,255,-1)
        overlap=int(np.count_nonzero((component!=0)&(gate!=0)))
        if overlap<max(3,width*height*.08):
            continue
        cx,cy,cw,ch=cv2.boundingRect(contour)
        if cw<width*.40 or ch<height*.25:
            continue
        hull=cv2.convexHull(contour)
        perimeter=cv2.arcLength(hull,True)
        quad=None
        for epsilon in [.015,.025,.04,.06,.08]:
            approximation=cv2.approxPolyDP(hull,perimeter*epsilon,True)
            if len(approximation)==4:
                quad=ordered_quad(approximation.reshape(-1,2)+[left,top])
                break
        if quad is None:
            quad=ordered_quad(cv2.boxPoints(cv2.minAreaRect(contour))+[left,top])
        choices.append((overlap+area*.05,quad,{"componentArea":area,"ocrOverlapPixels":overlap,"baseTone":tone.tolist(),"candidateNotApproved":True}))
    if not choices:
        return None,{"reason":"no_isolated_plaque_component"}
    _,quad,info=max(choices,key=lambda row:row[0])
    return quad.tolist(),info


def fill_quad(rgb,quad):
    quad=ordered_quad(quad)
    mask=np.zeros(rgb.shape[:2],np.uint8)
    cv2.fillConvexPoly(mask,np.round(quad).astype(np.int32),255)
    if not np.any(mask) or np.mean(mask!=0)>.15:
        raise ValueError("Invalid or excessive review mask")
    gray=cv2.cvtColor(rgb,cv2.COLOR_RGB2GRAY)
    values=rgb[(mask!=0)&(gray<200)]
    if len(values)<3:
        raise ValueError("No real dark plaque tone")
    levels=np.mean(values,axis=1)
    values=values[levels<=np.percentile(levels,40)]
    tone=np.round(np.median(values,axis=0)).astype(np.uint8)
    output=rgb.copy();output[mask!=0]=tone
    return output,mask,tone.tolist()


def ink_only(rgb,quad,extra_quads=()):
    gate=np.zeros(rgb.shape[:2],np.uint8)
    for points in [quad,*extra_quads]:
        cv2.fillConvexPoly(gate,np.round(np.array(points)).astype(np.int32),255)
    gray=cv2.cvtColor(rgb,cv2.COLOR_RGB2GRAY)
    hsv=cv2.cvtColor(rgb,cv2.COLOR_RGB2HSV)
    data=rgb.astype(float)
    white=(gray>80)&(hsv[:,:,1]<145)
    colored=(data[:,:,0]>data[:,:,1]*1.35+8)&(data[:,:,0]>data[:,:,2]*1.2+8)&(data[:,:,0]>45)
    core=(white|colored)&(gate!=0)
    mask=cv2.dilate(core.astype(np.uint8)*255,np.ones((5,5),np.uint8))
    mask[gate==0]=0
    if not np.any(mask):
        raise ValueError("No brand ink inside the reviewed field")
    output=cv2.cvtColor(cv2.inpaint(cv2.cvtColor(rgb,cv2.COLOR_RGB2BGR),mask,2,cv2.INPAINT_TELEA),cv2.COLOR_BGR2RGB)
    output[mask==0]=rgb[mask==0]
    return output,mask,None


def snapshot():
    manifest=json.loads((ROOT/"artifacts/media-cleanup.json").read_text("utf-8"))
    if manifest.get("pipelineVersion")!=FROZEN_PIPELINE:
        raise ValueError("Main pipeline changed; review must be explicitly rebased")
    if media.pipeline_version(ROOT/"artifacts/media-cleanup/templates")!=FROZEN_PIPELINE:
        raise ValueError("Frozen code or templates changed")
    rows=[]
    for key,item in manifest["images"].items():
        if item.get("state")!="review_required" or not item.get("sourcePath","").lower().endswith((".jpg",".jpeg")):
            continue
        report=json.loads(media.safe_path(ROOT,item["report"]).read_text("utf-8"))
        rows.append((key,item,report))
    return manifest,rows


def make_candidate(task):
    key,item,report,method,manual=task
    source=media.safe_path(ROOT,item["sourcePath"])
    source_bytes=source.read_bytes()
    if media.sha(source_bytes)!=item["sourceSha"]:
        raise ValueError("Source hash mismatch")
    rgb=np.array(Image.open(source).convert("RGB"))
    detections=report.get("detections",[])
    if not detections:
        return {"urlSha":key,"method":method,"state":"unresolved","reason":"missing_detection"}
    detection=next((d for d in detections if d["source"]=="ocr"),detections[0])
    if method=="component":
        quad,geometry=component_quad(rgb,detection)
    elif method=="core-fit":
        geometry=media.fit_badge_quad(rgb,detection,media.get_engines(ROOT/"artifacts/media-cleanup/templates").matcher)
        quad=geometry.get("quad") if geometry else None
    elif method=="ocr":
        quad=detection.get("polygon")
        if not quad:
            x0,y0,x1,y1=detection["box"];quad=[[x0,y0],[x1,y0],[x1,y1],[x0,y1]]
        geometry={"source":"original_ocr_quad_requires_visual_acceptance"}
    else:
        manual_value=manual.get(key)
        quad=manual_value.get("quad") if isinstance(manual_value,dict) else manual_value
        geometry={"source":"explicit_visually_selected_quad"}
    if quad is None:
        return {"urlSha":key,"method":method,"state":"unresolved","geometry":geometry}
    try:
        if method=="manual" and isinstance(manual.get(key),dict) and manual[key].get("mode")=="ink":
            output,mask,tone=ink_only(rgb,quad,manual[key].get("extraInkQuads",[]))
            geometry["method"]="ink_strokes_only_preserve_woven_label_texture"
        else:
            output,mask,tone=fill_quad(rgb,quad)
    except ValueError as error:
        return {"urlSha":key,"method":method,"state":"unresolved","reason":str(error),"quad":quad,"geometry":geometry}
    folder=DEST/"candidates";folder.mkdir(parents=True,exist_ok=True)
    path=folder/(key+"-"+method+".webp")
    maskpath=folder/(key+"-"+method+"-mask.png")
    validation=media.save_lossless_validated(output,rgb,mask,path)
    Image.fromarray(mask).save(maskpath)
    found,scan=media.get_engines(ROOT/"artifacts/media-cleanup/templates").scan(output)
    record={"urlSha":key,"method":method,"pipelineVersion":FROZEN_PIPELINE,"sourceSha":item["sourceSha"],"sourcePath":item["sourcePath"],"outputSha":media.sha(path.read_bytes()),"path":media.relative(ROOT,path),"maskPath":media.relative(ROOT,maskpath),"maskSha":media.sha(maskpath.read_bytes()),"width":rgb.shape[1],"height":rgb.shape[0],"bytes":path.stat().st_size,"mime":"image/webp","quad":quad,"geometry":geometry,"tone":tone,"validation":validation,"postDetections":found,"postScan":scan,"state":"candidate_ready" if not found else "rejected_residual_brand","visualAccepted":False,"publicationReady":False}
    if media.sha(source.read_bytes())!=item["sourceSha"]:
        raise ValueError("Source changed during review")
    media.atomic_json(folder/(key+"-"+method+".json"),record)
    cropbox=tuple([max(0,min(p[0] for p in quad)-25),max(0,min(p[1] for p in quad)-22),min(rgb.shape[1],max(p[0] for p in quad)+25),min(rgb.shape[0],max(p[1] for p in quad)+22)])
    pair=Image.new("RGB",(1000,280),"white");draw=ImageDraw.Draw(pair)
    for x,image,name in [(0,Image.fromarray(rgb),"source"),(500,Image.fromarray(output),method+" | "+record["state"])]:
        tile=ImageOps.contain(image.crop(cropbox),(490,235));pair.paste(tile,(x+5,22));draw.text((x+5,3),name,fill="black");draw.text((x+5,261),key[:24],fill="black")
    pair.save(folder/(key+"-"+method+"-close.png"))
    full=Image.new("RGB",(rgb.shape[1]*2,rgb.shape[0]),"white");full.paste(Image.fromarray(rgb),(0,0));full.paste(Image.fromarray(output),(rgb.shape[1],0));full.thumbnail((1760,1000));full.save(folder/(key+"-"+method+"-full.jpg"),quality=95)
    return record


def candidate_sheets(rows,records):
    by_key={}
    for record in records:
        by_key.setdefault(record["urlSha"],{})[record["method"]]=record
    methods=sorted(set(record["method"] for record in records))
    paths=[]
    for start in range(0,len(rows),8):
        group=rows[start:start+8]
        sheet=Image.new("RGB",(300*(len(methods)+1),len(group)*205),"white");draw=ImageDraw.Draw(sheet)
        for i,(key,item,report) in enumerate(group):
            source=Image.open(media.safe_path(ROOT,item["sourcePath"])).convert("RGB")
            boxes=[d["box"] for d in report.get("detections",[])]
            crop=(max(0,min(b[0] for b in boxes)-25),max(0,min(b[1] for b in boxes)-20),min(source.width,max(b[2] for b in boxes)+25),min(source.height,max(b[3] for b in boxes)+25))
            for column,method in enumerate(["source",*methods]):
                image=source.copy();label=method
                if method!="source":
                    entry=by_key.get(key,{}).get(method,{})
                    label+=" | "+entry.get("state","missing")
                    if entry.get("path"):
                        image=Image.open(media.safe_path(ROOT,entry["path"])).convert("RGB")
                tile=ImageOps.contain(image.crop(crop),(290,160));sheet.paste(tile,(column*300+5,i*205+20));draw.text((column*300+5,i*205+2),label[:40],fill="black");draw.text((column*300+5,i*205+183),key[:24],fill="black")
        path=DEST/f"candidate-comparison-{start//8+1:02d}.png";sheet.save(path);paths.append(media.relative(ROOT,path))
    return paths


def static_candidates(args):
    manifest,rows=snapshot()
    manual=json.loads(args.quads.read_text("utf-8")) if args.quads else {}
    methods=["manual"] if manual else args.methods
    if args.limit:rows=rows[:args.limit]
    if manual:rows=[row for row in rows if row[0] in manual]
    tasks=[(key,item,report,method,manual) for key,item,report in rows for method in methods]
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        results=list(pool.map(make_candidate,tasks))
    receipt={"pipelineVersion":FROZEN_PIPELINE,"reviewScriptSha":media.sha(Path(__file__).read_bytes()),"publicationReady":False,"sourceManifestUpdatedAt":manifest.get("updatedAt"),"images":results,"sheets":candidate_sheets(rows,results)}
    media.atomic_json(DEST/"candidates.json",receipt)
    print(json.dumps({"images":len(rows),"candidates":len(results),"postScanPassed":sum(r.get("state")=="candidate_ready" for r in results),"sheets":receipt["sheets"]}),flush=True)


def emit_overrides(args):
    selection=json.loads(args.selection.read_text("utf-8"));candidates=json.loads((DEST/"candidates.json").read_text("utf-8"))
    by_id={(r["urlSha"],r["method"]):r for r in candidates["images"]}
    output=[]
    for key,choice in selection.items():
        row=by_id[(key,choice["method"])]
        if row["state"]!="candidate_ready" or choice.get("structureReview") is not True or not choice.get("reviewer") or not choice.get("notes"):
            raise ValueError("Explicit successful visual review and notes required")
        if media.sha(media.safe_path(ROOT,row["sourcePath"]).read_bytes())!=row["sourceSha"] or media.sha(media.safe_path(ROOT,row["path"]).read_bytes())!=row["outputSha"] or media.sha(media.safe_path(ROOT,row["maskPath"]).read_bytes())!=row["maskSha"]:
            raise ValueError("Reviewed candidate bytes changed")
        output.append({**row,"visualAccepted":True,"visualReview":choice,"proposedState":"approved_cleaned"})
    receipt={"pipelineVersion":FROZEN_PIPELINE,"publicationReady":False,"mainManifestModified":False,"images":output}
    media.atomic_json(DEST/"overrides.json",receipt)
    print(json.dumps({"overrides":len(output),"path":str(DEST/"overrides.json")}),flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest="command",required=True)
    candidates=sub.add_parser("static-candidates")
    candidates.add_argument("--methods",nargs="+",choices=["component","core-fit","ocr"],default=["component","core-fit","ocr"])
    candidates.add_argument("--quads",type=Path)
    candidates.add_argument("--workers",type=int,default=4,choices=range(1,9))
    candidates.add_argument("--limit",type=int,default=0)
    candidates.set_defaults(func=static_candidates)
    overrides=sub.add_parser("emit-overrides")
    overrides.add_argument("--selection",type=Path,required=True)
    overrides.set_defaults(func=emit_overrides)
    args=parser.parse_args();DEST.mkdir(parents=True,exist_ok=True);args.func(args)


if __name__=="__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
