"""Conservative, auditable OCR/CV retouch of user-authorized catalog brand marks.

Never changes original downloads. Only approved outputs may be published. A zero
detection result is a measured scan result, not proof that no possible mark exists.
"""
from __future__ import annotations

import argparse
from collections import OrderedDict
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from datetime import datetime, timezone
from difflib import SequenceMatcher
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import sys
import threading
import time
import unicodedata

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageOps

cv2.setNumThreads(1)
ROOT = Path(__file__).resolve().parents[1]
CONFIG = {
    "algorithm":"nodeno-ocr-cv-retouch-2-preserve-physical-plaque", "ocrTextScore":.3,
    "ocrAutoConfidence":.65, "templateReview":.79, "templateAuto":.91,
    "maxMaskCoverage":.025, "maxRegionWidthRatio":.30,
    "maxRegionHeightRatio":.18, "maxContextDeviation":24.,
    "losslessWebp":True, "opencvThreads":1, "ocrIntraThreads":2,
    "physicalPlateFitMinScore":.57,
    "maxPhysicalPlateCoverage":.015,
}
LOCAL = threading.local()
SCAN_CACHE=OrderedDict()
SCAN_LOCKS={}
SCAN_CACHE_GUARD=threading.Lock()


def utcnow():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w",encoding="utf-8") as stream:
        stream.write(json.dumps(value,ensure_ascii=False,indent=2)+"\n")
        stream.flush()
        os.fsync(stream.fileno())
    # Windows readers can briefly deny DELETE/rename sharing on an open JSON.
    # Retry only the atomic replace, preserving the old checkpoint on failure.
    for attempt in range(10):
        try:
            os.replace(temporary,path)
            break
        except PermissionError:
            if attempt==9:
                raise
            time.sleep(min(.5,.03*(1.6**attempt)))


def safe_path(root, relative):
    result = (root / relative).resolve()
    if not result.is_relative_to(root.resolve()):
        raise ValueError("Path escapes workspace")
    return result


def relative(root, path):
    return path.resolve().relative_to(root.resolve()).as_posix()


def classify_brand_text(text, confidence):
    text = unicodedata.normalize("NFKD", text).lower()
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.replace("ı", "i").replace("0", "o").replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
    tokens = re.findall(r"[a-zа-я\u0600-\u06ff]+", text)
    compact = "".join(tokens)
    aliases = {"adore", "adoremobilya", "adoremobilyacom", "adoremobilyacomtr", "адоре", "адоремобиля", "ادور", "ادوره", "ادوري"}
    if compact in aliases or "adore" in tokens or "адоре" in tokens or any(t in aliases for t in tokens):
        return "exact"
    if "adoremobilya" in compact:
        return "exact"
    if confidence >= .3 and any(4 <= len(t) <= 8 and SequenceMatcher(None,t,"adore").ratio() >= .8 for t in tokens):
        return "uncertain"
    return None


def is_uniform(rgb):
    return int(rgb.max()) - int(rgb.min()) <= 2


def box_iou(a, b):
    x0, y0, x1, y1 = max(a[0],b[0]), max(a[1],b[1]), min(a[2],b[2]), min(a[3],b[3])
    inter = max(0,x1-x0) * max(0,y1-y0)
    area_a, area_b = (a[2]-a[0])*(a[3]-a[1]), (b[2]-b[0])*(b[3]-b[1])
    return inter / max(1,area_a+area_b-inter)


class TemplateMatcher:
    def __init__(self, folder):
        self.paths = sorted(Path(folder).glob("*.png"))
        if not self.paths:
            raise ValueError("No user-approved badge reference template found")
        self.templates = [(p.name,cv2.cvtColor(np.array(Image.open(p).convert("RGB")),cv2.COLOR_RGB2GRAY)) for p in self.paths]
        self.color_templates = {p.name:np.array(Image.open(p).convert("RGB")) for p in self.paths}

    def detect(self, rgb, extra_widths=()):
        if is_uniform(rgb):
            return []
        gray = cv2.cvtColor(rgb,cv2.COLOR_RGB2GRAY)
        height,width = gray.shape
        # Whole-image scan, including product corners and physical plaques.
        widths = set(extra_widths)
        value = 24.
        while value <= min(240,width*.33):
            widths.add(round(value))
            value *= 1.20
        hits = []
        for name,template in self.templates:
            for target_width in sorted(widths):
                target_height = round(target_width*template.shape[0]/template.shape[1])
                if target_height < 6 or target_height >= height or target_width >= width:
                    continue
                resized = cv2.resize(template,(target_width,target_height),interpolation=cv2.INTER_AREA if target_width<template.shape[1] else cv2.INTER_CUBIC)
                if resized.std() < 12:
                    continue
                result = cv2.matchTemplate(gray,resized,cv2.TM_CCOEFF_NORMED)
                # More than one physical badge can occur in a collage.
                for _ in range(4):
                    _,score,_,point = cv2.minMaxLoc(result)
                    if not math.isfinite(score) or score < CONFIG["templateReview"]:
                        break
                    x,y=point
                    crop=gray[y:y+target_height,x:x+target_width]
                    edges_a=cv2.Canny(crop,50,140)
                    edges_b=cv2.Canny(resized,50,140)
                    edge_score=float(cv2.matchTemplate(edges_a,edges_b,cv2.TM_CCORR_NORMED)[0,0])
                    if edge_score >= .28:
                        hits.append({"box":[x,y,x+target_width,y+target_height],"source":"template","text":"adore physical badge reference","confidence":round(float(score),5),"edgeConfidence":round(edge_score,5),"certainty":"exact" if score>=CONFIG["templateAuto"] else "uncertain","template":name})
                    result[max(0,y-target_height//2):min(result.shape[0],y+target_height//2+1),max(0,x-target_width//2):min(result.shape[1],x+target_width//2+1)] = -1
        kept=[]
        for hit in sorted(hits,key=lambda h:h["confidence"],reverse=True):
            if not any(box_iou(hit["box"],old["box"])>.25 for old in kept):
                kept.append(hit)
        return kept


class Engines:
    def __init__(self, template_folder):
        from rapidocr_onnxruntime import RapidOCR
        self.ocr = RapidOCR(intra_op_num_threads=2,inter_op_num_threads=1,det_limit_side_len=1280,det_limit_type="max",text_score=.3,max_side_len=2200)
        self.matcher=TemplateMatcher(template_folder)
        self.scan_config=sha(json.dumps(CONFIG,sort_keys=True).encode()+b"".join(path.read_bytes() for path in self.matcher.paths))

    def scan(self,rgb):
        # Identical decoded GIF frames/duplicate files need the same analysis,
        # without keeping RGB arrays or re-running hundreds of ONNX inferences.
        content_sha=sha(str((rgb.shape,str(rgb.dtype))).encode()+rgb.tobytes())
        key=(self.scan_config,content_sha)
        with SCAN_CACHE_GUARD:
            lock=SCAN_LOCKS.setdefault(key,threading.Lock())
        with lock:
            with SCAN_CACHE_GUARD:
                cached=SCAN_CACHE.get(key)
                if cached is not None:
                    SCAN_CACHE.move_to_end(key)
                    found,audit=deepcopy(cached)
                    audit["scanReuse"]="identical_decoded_rgb_sha256"
                    return found,audit
            found,audit=self._scan_uncached(rgb)
            audit["decodedRgbSha256"]=content_sha
            with SCAN_CACHE_GUARD:
                SCAN_CACHE[key]=deepcopy((found,audit))
                while len(SCAN_CACHE)>4096:
                    SCAN_CACHE.popitem(last=False)
            return found,audit

    def _scan_uncached(self,rgb):
        if is_uniform(rgb):
            return [],{"ocr":[],"uniform":True}
        results,_=self.ocr(rgb[...,::-1].copy(),text_score=.3)
        words=[]
        detections=[]
        for points,text,confidence,*_ in results or []:
            points=np.array(points,dtype=float)
            x0,y0=points.min(axis=0)
            x1,y1=points.max(axis=0)
            item={"box":[math.floor(x0),math.floor(y0),math.ceil(x1),math.ceil(y1)],"polygon":points.round(2).tolist(),"text":text,"confidence":round(float(confidence),5)}
            words.append(item)
            kind=classify_brand_text(text,float(confidence))
            if kind:
                item={**item,"source":"ocr","certainty":kind if confidence>=CONFIG["ocrAutoConfidence"] else "uncertain"}
                # Mixed technical content is never removed as one OCR rectangle.
                if re.search(r"\d\s*[x×]|\b(?:cm|mm|kg)\b",text,re.I):
                    item["certainty"]="uncertain"
                    item["risk"]="brand_and_technical_content_in_same_text_line"
                detections.append(item)
        template_hits=self.matcher.detect(rgb)
        for hit in template_hits:
            overlap=[d for d in detections if box_iou(d["box"],hit["box"])>.2]
            if overlap and any(d["certainty"]=="exact" for d in overlap):
                hit["certainty"]="exact"
                hit["supportedByOcr"]=True
            detections.append(hit)
        return detections,{"ocr":words,"templateHits":template_hits,"uniform":False}


def get_engines(template_folder):
    if not hasattr(LOCAL,"engines"):
        LOCAL.engines=Engines(template_folder)
    return LOCAL.engines


def residual_brand(detections):
    return bool(detections)


def fit_badge_quad(rgb,detection,matcher):
    """Fit an actual logo reference locally; never grow a dark-color hull."""
    x0,y0,x1,y1=detection["box"]
    width,height=x1-x0,y1-y0
    if width<8 or height<3:
        return None
    left=max(0,x0-round(width*.35))
    top=max(0,y0-max(12,height))
    right=min(rgb.shape[1],x1+round(width*.35))
    bottom=min(rgb.shape[0],y1+max(12,height))
    gray=cv2.cvtColor(rgb[top:bottom,left:right],cv2.COLOR_RGB2GRAY)
    def red_ink(image):
        data=image.astype(float)
        return ((data[:,:,0]>data[:,:,1]*1.35+8)&(data[:,:,0]>data[:,:,2]*1.2+8)&(data[:,:,0]>35)).astype(np.uint8)*255
    red_source=red_ink(rgb[top:bottom,left:right])
    polygon=np.array(detection.get("polygon",[[x0,y0],[x1,y0],[x1,y1],[x0,y1]]),float)
    slope=(polygon[1,1]-polygon[0,1])/max(1,polygon[1,0]-polygon[0,0])
    best=None
    for template_name,template in matcher.templates:
        for width_factor in [.85,.925,1.,1.075,1.15,1.225,1.30]:
            tw=max(12,round(width*width_factor))
            for height_factor in [.8,.9,1.,1.1,1.2]:
                th=max(7,round(tw*template.shape[0]/template.shape[1]*height_factor))
                plain=cv2.resize(template,(tw,th),interpolation=cv2.INTER_CUBIC)
                color_plain=cv2.resize(matcher.color_templates[template_name],(tw,th),interpolation=cv2.INTER_CUBIC)
                for shear in sorted(set([0.,round(slope,3),round(slope-.035,3),round(slope+.035,3)])):
                    transform=np.array([[1,0,0],[shear,1,max(0,-shear*tw)]],np.float32)
                    fitted=cv2.warpAffine(plain,transform,(tw,th+math.ceil(abs(shear)*tw)),flags=cv2.INTER_CUBIC,borderMode=cv2.BORDER_REPLICATE)
                    color_fitted=cv2.warpAffine(color_plain,transform,(tw,th+math.ceil(abs(shear)*tw)),flags=cv2.INTER_CUBIC,borderMode=cv2.BORDER_REPLICATE)
                    if fitted.shape[0]>=gray.shape[0] or fitted.shape[1]>=gray.shape[1]:
                        continue
                    gray_scores=cv2.matchTemplate(gray,fitted,cv2.TM_CCOEFF_NORMED)
                    red_template=red_ink(color_fitted)
                    if np.count_nonzero(red_template)>=max(3,tw*.15):
                        color_scores=cv2.matchTemplate(red_source,red_template,cv2.TM_CCORR_NORMED)
                        color_scores=np.nan_to_num(color_scores,nan=0,posinf=0,neginf=0)
                        scores=gray_scores*.72+color_scores*.28
                    else:
                        color_scores=np.zeros_like(gray_scores)
                        scores=gray_scores
                    _,score,_,point=cv2.minMaxLoc(scores)
                    if best is None or score>best["score"]:
                        corners=np.array([[0,0],[tw-1,0],[tw-1,th-1],[0,th-1]],np.float32)
                        corners=cv2.transform(corners[None],transform)[0]+np.array([left+point[0],top+point[1]])
                        best={"score":round(float(score),6),"grayscaleConfidence":round(float(gray_scores[point[1],point[0]]),6),"colorLineConfidence":round(float(color_scores[point[1],point[0]]),6),"quad":corners.tolist(),"width":tw,"height":th,"shear":shear,"template":template_name}
    return best


def clean_physical_plaque(rgb,detections,matcher):
    """Retain the manufactured plaque, erase its brand ink within its known quad."""
    output=rgb.copy()
    mask=np.zeros(rgb.shape[:2],np.uint8)
    gray=cv2.cvtColor(rgb,cv2.COLOR_RGB2GRAY)
    hsv=cv2.cvtColor(rgb,cv2.COLOR_RGB2HSV)
    regions=[]
    processed=[]
    for detection in sorted(detections,key=lambda d:d["source"]!="ocr"):
        if any(box_iou(detection["box"],old)>.2 for old in processed):
            continue
        fitted=fit_badge_quad(rgb,detection,matcher)
        if fitted is None or fitted["score"]<CONFIG["physicalPlateFitMinScore"]:
            return rgb.copy(),np.zeros_like(mask),{"accepted":False,"reason":"physical_plate_reference_fit_uncertain","fit":fitted}
        if detection["source"]=="ocr" and detection["confidence"]<.65:
            return rgb.copy(),np.zeros_like(mask),{"accepted":False,"reason":"physical_plate_ocr_confidence_uncertain","fit":fitted}
        quad=np.array(fitted["quad"],np.float32)
        plate=np.zeros_like(mask)
        cv2.fillConvexPoly(plate,np.round(quad).astype(np.int32),255)
        # Both supplied reference crops are the printed INNER plaque field;
        # the manufactured external frame lies outside this fitted quad.
        interior=plate.copy()
        if not np.any(interior) or np.mean(plate!=0)>CONFIG["maxPhysicalPlateCoverage"]:
            return rgb.copy(),np.zeros_like(mask),{"accepted":False,"reason":"physical_plate_area_gate","fit":fitted}
        dark=(interior!=0)&(gray<95)
        values=rgb[dark]
        if len(values)<8 or len(values)/max(1,np.count_nonzero(interior))<.30:
            return rgb.copy(),np.zeros_like(mask),{"accepted":False,"reason":"physical_dark_substrate_not_supported","fit":fitted}
        order=np.argsort(cv2.cvtColor(values[None],cv2.COLOR_RGB2GRAY)[0])
        values=values[order[:max(5,round(len(values)*.65))]]
        tone=np.round(np.median(values,axis=0)).astype(np.uint8)
        if int(tone.max())>90 or int(tone.max())-int(tone.min())>40:
            return rgb.copy(),np.zeros_like(mask),{"accepted":False,"reason":"physical_plaque_tone_not_dark_neutral","fit":fitted}
        # The colored underline and antialiased ink may occupy the inner frame.
        # Include those pixels, always clipped to the fitted original quad.
        orange=(hsv[:,:,0]<35)&(hsv[:,:,1]>80)&(hsv[:,:,2]>65)&(plate!=0)
        letter_core=(gray>130)&(interior!=0)
        connected_ink=(cv2.dilate(letter_core.astype(np.uint8),np.ones((3,3),np.uint8))!=0)&(gray>70)&(plate!=0)
        interior[orange|connected_ink]=255
        output[interior!=0]=tone
        mask=cv2.bitwise_or(mask,interior)
        processed.append(detection["box"])
        regions.append({**fitted,"tone":tone.tolist(),"maskPixels":int(np.count_nonzero(interior)),"referenceQuadIsPrintedInterior":True,"physicalPlaqueRetained":True})
    output[mask==0]=rgb[mask==0]
    return output,mask,{"accepted":bool(regions),"physicalPlaqueRetained":True,"regions":regions,"method":"brand_ink_removed_with_existing_dark_plaque_tone"}


def build_brand_mask(rgb,detections):
    height,width=rgb.shape[:2]
    mask=np.zeros((height,width),np.uint8)
    details=[]
    for det in detections:
        x0,y0,x1,y1=[int(v) for v in det["box"]]
        x0,y0,x1,y1=max(0,x0),max(0,y0),min(width,x1),min(height,y1)
        w,h=x1-x0,y1-y0
        if w<3 or h<3:
            details.append({"reason":"degenerate_box","risk":True})
            continue
        # Include the orange underline without expanding into the furniture panel.
        scan=rgb[y0:min(height,y1+max(6,round(h*.4))),x0:x1]
        hsv=cv2.cvtColor(scan,cv2.COLOR_RGB2HSV)
        orange=(hsv[:,:,0]<28)&(hsv[:,:,1]>95)&(hsv[:,:,2]>80)
        rows=np.where(orange.sum(axis=1)>=max(5,w*.35))[0]
        if len(rows):
            y1=max(y1,min(height,y0+int(rows.max())+2))
        crop=rgb[y0:y1,x0:x1]
        gray=cv2.cvtColor(crop,cv2.COLOR_RGB2GRAY)
        black_ratio=float(np.mean(gray<70))
        white_ratio=float(np.mean(gray>180))
        badge=det["source"]=="template" or (black_ratio>.20 and white_ratio>.03 and w/max(1,h)>1.8)
        pad=2 if max(width,height)<1400 else 3
        a,b,c,d=max(0,x0-pad),max(0,y0-pad),min(width,x1+pad),min(height,y1+pad)
        region_mask=np.zeros_like(mask)
        ring=np.zeros_like(mask)
        ring[max(0,b-5):min(height,d+5),max(0,a-5):min(width,c+5)]=255
        ring[b:d,a:c]=0
        context=rgb[ring!=0].astype(np.float32)
        median=np.median(context,axis=0) if len(context) else np.array([128,128,128])
        distances=np.linalg.norm(context-median,axis=1) if len(context) else np.array([999.])
        deviation=float(np.median(distances))
        context_p90=float(np.percentile(distances,90))
        if badge:
            region_mask[b:d,a:c]=255
            method="whole_physical_badge"
        else:
            # On a smooth surface, remove only high-contrast letter strokes.
            delta=np.linalg.norm(crop.astype(float)-median,axis=2)
            foreground=(delta>max(18,deviation*2.5)).astype(np.uint8)*255
            fraction=float(np.mean(foreground!=0))
            if .02<=fraction<=.70 and deviation<18:
                region_mask[y0:y1,x0:x1]=foreground
                region_mask=cv2.dilate(region_mask,np.ones((3,3),np.uint8))
                method="segmented_letter_strokes"
            else:
                region_mask[b:d,a:c]=255
                method="ocr_region_requires_smooth_context"
        risk=[]
        if w/width>CONFIG["maxRegionWidthRatio"] or h/height>CONFIG["maxRegionHeightRatio"]:
            risk.append("large_brand_region")
        if deviation>CONFIG["maxContextDeviation"]:
            risk.append("textured_or_geometry_sensitive_context")
        if context_p90>35:
            risk.append("multiple_materials_or_product_silhouette_in_context")
        if det["certainty"]!="exact":
            risk.append("uncertain_brand_detection")
        if det.get("risk"):
            risk.append(det["risk"])
        polygon=np.array(det.get("polygon",[]))
        if len(polygon)==4 and abs(float(polygon[1,1]-polygon[0,1]))>max(5,w*.12):
            risk.append("rotated_or_perspective_text")
        details.append({"box":[a,b,c,d],"method":method,"blackRatio":round(black_ratio,5),"contextDeviation":round(deviation,5),"contextDeviationP90":round(context_p90,5),"maskPixels":int(np.count_nonzero(region_mask)),"risks":risk})
        mask=cv2.bitwise_or(mask,region_mask)
    return mask,details


def image_delta(source,output,mask):
    outside=mask==0
    a,b=source[outside].astype(np.float64),output[outside].astype(np.float64)
    if not len(a):
        raise ValueError("Mask covers whole image")
    delta=np.abs(a-b)
    # SSIM over the unmasked RGB samples; exact equality is also mandatory.
    if np.array_equal(a,b):
        similarity=1.
    else:
        mu_a,mu_b=a.mean(),b.mean()
        var_a,var_b=a.var(),b.var()
        covariance=np.mean((a-mu_a)*(b-mu_b))
        similarity=float(((2*mu_a*mu_b+6.5025)*(2*covariance+58.5225))/((mu_a*mu_a+mu_b*mu_b+6.5025)*(var_a+var_b+58.5225)))
    return {"outsideMaskMaxDelta":int(delta.max()),"outsideMaskMeanDelta":round(float(delta.mean()),8),"outsideMaskChangedValues":int(np.count_nonzero(delta)),"outsideMaskSsim":round(similarity,8)}


def inpaint_preserving(rgb,mask):
    if not np.any(mask):
        return rgb.copy(),{**image_delta(rgb,rgb,mask),"method":"unchanged"}
    source=cv2.cvtColor(rgb,cv2.COLOR_RGB2BGR)
    ring=cv2.dilate(mask,np.ones((7,7),np.uint8))-mask
    context=rgb[ring!=0].astype(float)
    median=np.median(context,axis=0) if len(context) else rgb.reshape(-1,3).mean(axis=0)
    candidates=[]
    boundary=(cv2.dilate(mask,np.ones((3,3),np.uint8))!=cv2.erode(mask,np.ones((3,3),np.uint8)))
    def candidate_score(candidate):
        # Boundary curvature penalizes a visible rectangular patch or broken trim.
        gray=cv2.cvtColor(candidate,cv2.COLOR_RGB2GRAY).astype(float)
        laplacian=cv2.Laplacian(gray,cv2.CV_64F)
        return float(np.mean(np.abs(laplacian[boundary])))
    for name,flag in [("Telea",cv2.INPAINT_TELEA),("Navier-Stokes",cv2.INPAINT_NS)]:
        candidate=cv2.cvtColor(cv2.inpaint(source,mask,3,flag),cv2.COLOR_BGR2RGB)
        candidate[mask==0]=rgb[mask==0]
        colors=candidate[mask!=0].astype(float)
        context_delta=float(np.linalg.norm(colors.mean(axis=0)-median))
        score=candidate_score(candidate)+context_delta*.05
        candidates.append((score,candidate,name,context_delta))
    # A smooth horizontal furniture rail is better reconstructed from the same
    # rows on either side than by diffusing its top/bottom tones into the plaque.
    # This candidate is admitted only when both unmasked side profiles agree.
    directional=rgb.copy()
    disagreements=[]
    valid=True
    for y in np.where(np.any(mask!=0,axis=1))[0]:
        xs=np.where(mask[y]!=0)[0]
        intervals=np.split(xs,np.where(np.diff(xs)>1)[0]+1)
        for interval in intervals:
            x0,x1=int(interval[0]),int(interval[-1])+1
            if x0<4 or x1+4>rgb.shape[1]:
                valid=False
                break
            left=rgb[y,x0-4:x0][mask[y,x0-4:x0]==0]
            right=rgb[y,x1:x1+4][mask[y,x1:x1+4]==0]
            if not len(left) or not len(right):
                valid=False
                break
            a,b=np.median(left,axis=0),np.median(right,axis=0)
            disagreements.append(float(np.linalg.norm(a-b)))
            alpha=np.linspace(0,1,x1-x0+2)[1:-1,None]
            directional[y,x0:x1]=np.round(a*(1-alpha)+b*alpha).astype(np.uint8)
        if not valid:
            break
    if valid and disagreements and np.mean(disagreements)<18 and np.percentile(disagreements,90)<35:
        colors=directional[mask!=0].astype(float)
        delta=float(np.linalg.norm(colors.mean(axis=0)-median))
        candidates.append((candidate_score(directional)+delta*.05,directional,"directional-boundary-interpolation",delta))
    selection_reason="lowest_boundary_curvature"
    if valid and disagreements and np.mean(disagreements)<8 and np.percentile(disagreements,90)<15 and candidates[-1][2]=="directional-boundary-interpolation":
        score,output,name,context_delta=candidates[-1]
        selection_reason="strong_same_row_boundary_agreement"
    else:
        score,output,name,context_delta=min(candidates,key=lambda row:row[0])
    return output,{**image_delta(rgb,output,mask),"method":name,"selectionReason":selection_reason,"selectionScore":round(score,5),"inpaintContextColorDelta":round(context_delta,5),"candidateScores":[{"method":row[2],"seamScore":round(row[0],5)} for row in candidates]}


def save_lossless_validated(output,source,mask,path):
    path.parent.mkdir(parents=True,exist_ok=True)
    Image.fromarray(output).save(path,"WEBP",lossless=True,quality=100,method=4,exact=True)
    with Image.open(path) as image:
        image.load()
        decoded=np.array(image.convert("RGB"))
    if decoded.shape!=source.shape:
        raise ValueError("Output dimensions changed")
    result=image_delta(source,decoded,mask)
    if result["outsideMaskMaxDelta"]!=0 or not np.array_equal(decoded,output):
        raise ValueError("Lossless output validation failed")
    return result


def write_review(root,key,rgb,detections,candidate=None):
    folder=root/"artifacts/media-cleanup/review"
    folder.mkdir(parents=True,exist_ok=True)
    thumb=Image.fromarray(rgb)
    thumb.thumbnail((600,600))
    thumb.save(folder/(key+"-source.jpg"),quality=92)
    if candidate is not None:
        Image.fromarray(candidate).save(folder/(key+"-candidate.webp"),"WEBP",lossless=True,quality=100)
    crops=[]
    for index,det in enumerate(detections[:8]):
        x0,y0,x1,y1=det["box"]
        pad=max(12,round((y1-y0)*.8))
        crop=Image.fromarray(rgb).crop((max(0,x0-pad),max(0,y0-pad),min(rgb.shape[1],x1+pad),min(rgb.shape[0],y1+pad)))
        crop.thumbnail((500,220))
        path=folder/(key+f"-crop-{index}.png")
        crop.save(path)
        crops.append(relative(root,path))
    return crops


def process_entry(key,entry,root,output_folder,apply,engines=None):
    started=time.monotonic()
    report={"key":key,"sourceSha":entry.get("sha256"),"sourcePath":entry.get("path"),"sourceBytes":entry.get("bytes"),"url":entry.get("url"),"state":"failed","updatedAt":utcnow(),"detections":[],"outputSha":None,"path":None}
    try:
        path=safe_path(root,entry["path"])
        raw=path.read_bytes()
        if sha(raw)!=entry["sha256"]:
            report["reason"]="source_sha_mismatch"
            return report
        special_scans=[]
        special_detections=[]
        with Image.open(path) as image:
            image.load()
            report["width"],report["height"]=image.size
            frames=getattr(image,"n_frames",1)
            transparent=image.mode in {"RGBA","LA","P"} and image.convert("RGBA").getchannel("A").getextrema()!=(255,255)
            if frames!=1 or transparent:
                if engines is None:
                    engines=get_engines(root/"artifacts/media-cleanup/templates")
                for frame_index in range(frames):
                    image.seek(frame_index)
                    rgba=image.convert("RGBA")
                    has_alpha=rgba.getchannel("A").getextrema()!=(255,255)
                    for background in (["white","black"] if has_alpha else ["white"]):
                        composed=Image.new("RGBA",image.size,background)
                        composed.alpha_composite(rgba)
                        frame_rgb=np.array(composed.convert("RGB"))
                        found,frame_scan=engines.scan(frame_rgb)
                        special_detections.extend({**d,"frame":frame_index,"background":background} for d in found)
                        special_scans.append({"frame":frame_index,"background":background,**frame_scan})
                report["frames"]=frames
            rgb=np.array(image.convert("RGB"))
        if engines is None:
            engines=get_engines(root/"artifacts/media-cleanup/templates")
        if special_scans:
            detections,scan=special_detections,{"frames":special_scans,"framesScanned":frames}
        else:
            detections,scan=engines.scan(rgb)
        report["detections"],report["scan"]=detections,scan
        if not detections:
            report["maskCoverage"]=0.
            report["validation"]={"outsideMaskMaxDelta":0,"outsideMaskMeanDelta":0.,"outsideMaskChangedValues":0,"outsideMaskSsim":1.0,"unmodifiedBytes":True}
            if apply:
                output_folder.mkdir(parents=True,exist_ok=True)
                target=output_folder/(key+path.suffix.lower())
                shutil.copyfile(path,target)
                if sha(target.read_bytes())!=entry["sha256"]:
                    raise ValueError("Unmodified copy hash mismatch")
                report.update(state="approved_unmodified",path=relative(root,target),filename=target.name,mime=entry.get("mime") or Image.MIME.get(Image.open(path).format,"application/octet-stream"),outputSha=sha(target.read_bytes()),bytes=target.stat().st_size,reason="no_brand_detected_by_ocr_and_reference_templates")
            else:
                report.update(state="pending",reason="dry_run_no_brand_detected")
        elif special_scans:
            report.update(state="review_required",reason="animated_or_transparent_brand_requires_manual_retouch",reviewCrops=write_review(root,key,rgb,detections))
        else:
            matcher=getattr(engines,"matcher",None)
            plaque_result=None
            if matcher is not None and not any(d.get("risk") for d in detections):
                plaque_result=clean_physical_plaque(rgb,detections,matcher)
            if plaque_result is not None and plaque_result[2].get("accepted"):
                cleaned,mask,plaque_audit=plaque_result
                report.update(physicalPlaqueRetained=True,plaqueAudit=plaque_audit,regions=plaque_audit["regions"],maskCoverage=round(float(np.mean(mask!=0)),8),validation={**image_delta(rgb,cleaned,mask),"method":plaque_audit["method"]})
                mask_path=root/"artifacts/media-cleanup/masks"/(key+".png")
                mask_path.parent.mkdir(parents=True,exist_ok=True)
                Image.fromarray(mask).save(mask_path)
                report["maskPath"]=relative(root,mask_path)
                post_detections,post_scan=engines.scan(cleaned)
                report["postDetections"],report["postScan"]=post_detections,post_scan
                if residual_brand(post_detections):
                    report.update(state="review_required",reason="residual_brand_after_plaque_ink_cleanup",reviewCrops=write_review(root,key,rgb,detections,cleaned))
                elif apply:
                    target=output_folder/(key+".webp")
                    report["decodeValidation"]=save_lossless_validated(cleaned,rgb,mask,target)
                    report.update(state="approved_cleaned",path=relative(root,target),filename=target.name,mime="image/webp",outputSha=sha(target.read_bytes()),bytes=target.stat().st_size,reason="physical_plaque_preserved_brand_ink_removed",reviewCrops=write_review(root,key,rgb,detections,cleaned))
                else:
                    report.update(state="pending",reason="dry_run_plaque_candidate_passed",reviewCrops=write_review(root,key,rgb,detections,cleaned))
                if sha(path.read_bytes())!=entry["sha256"]:
                    report.update(state="failed",reason="source_changed_during_processing",path=None,outputSha=None)
                return report
            # Never fall back to destroying a physical plaque and reconstructing
            # the furniture corner when fitting that plaque was uncertain.
            dark_regions=[]
            for detection in detections:
                a,b,c,d=[max(0,int(v)) for v in detection["box"]]
                region=rgb[b:min(rgb.shape[0],d),a:min(rgb.shape[1],c)]
                if region.size:
                    levels=cv2.cvtColor(region,cv2.COLOR_RGB2GRAY)
                    if np.median(levels)<140 or np.mean(levels<70)>.35:
                        dark_regions.append(detection)
            if plaque_result is not None and dark_regions:
                report.update(state="review_required",reason="physical_plaque_fit_requires_visual_review",plaqueAudit=plaque_result[2],reviewCrops=write_review(root,key,rgb,detections))
                if sha(path.read_bytes())!=entry["sha256"]:
                    report.update(state="failed",reason="source_changed_during_processing")
                return report
            mask,regions=build_brand_mask(rgb,detections)
            report["regions"]=regions
            report["maskCoverage"]=round(float(np.mean(mask!=0)),8)
            risks=sorted(set(risk for item in regions for risk in item.get("risks",[])))
            if report["maskCoverage"]>CONFIG["maxMaskCoverage"]:
                risks.append("mask_area_exceeds_safety_limit")
            if not np.any(mask):
                risks.append("empty_brand_mask")
            report["risks"]=risks
            mask_path=root/"artifacts/media-cleanup/masks"/(key+".png")
            mask_path.parent.mkdir(parents=True,exist_ok=True)
            Image.fromarray(mask).save(mask_path)
            report["maskPath"]=relative(root,mask_path)
            if risks:
                report.update(state="review_required",reason="conservative_geometry_or_detection_gate",reviewCrops=write_review(root,key,rgb,detections))
            else:
                cleaned,audit=inpaint_preserving(rgb,mask)
                report["validation"]=audit
                post_detections,post_scan=engines.scan(cleaned)
                report["postDetections"],report["postScan"]=post_detections,post_scan
                if residual_brand(post_detections):
                    report.update(state="review_required",reason="residual_brand_after_inpaint",reviewCrops=write_review(root,key,rgb,detections,cleaned))
                elif audit["inpaintContextColorDelta"]>15 or audit["selectionScore"]>5:
                    report.update(state="review_required",reason="inpaint_color_coherence_gate",reviewCrops=write_review(root,key,rgb,detections,cleaned))
                elif apply:
                    target=output_folder/(key+".webp")
                    report["decodeValidation"]=save_lossless_validated(cleaned,rgb,mask,target)
                    report.update(state="approved_cleaned",path=relative(root,target),filename=target.name,mime="image/webp",outputSha=sha(target.read_bytes()),bytes=target.stat().st_size,reason="tight_mask_inpaint_and_post_scan_passed")
                else:
                    report.update(state="pending",reason="dry_run_candidate_passed",reviewCrops=write_review(root,key,rgb,detections,cleaned))
        if sha(path.read_bytes())!=entry["sha256"]:
            report.update(state="failed",reason="source_changed_during_processing",path=None,outputSha=None)
        return report
    except Exception as error:
        report.update(state="failed",reason="processing_error",error=f"{type(error).__name__}: {error}",path=None,outputSha=None)
        return report
    finally:
        report["elapsedSeconds"]=round(time.monotonic()-started,3)


def pipeline_version(template_folder):
    payload=Path(__file__).read_bytes()+json.dumps(CONFIG,sort_keys=True).encode()
    for path in sorted(template_folder.glob("*.png")):
        payload+=path.name.encode()+path.read_bytes()
    return sha(payload)


def summarize(manifest):
    counts={state:0 for state in ["pending","approved_unmodified","approved_cleaned","review_required","failed"]}
    for item in manifest["images"].values():
        counts[item["state"]]=counts.get(item["state"],0)+1
    counts["images"]=len(manifest["images"])
    counts["references"]=len(manifest.get("references",{}))
    counts["approved"]=counts["approved_unmodified"]+counts["approved_cleaned"]
    return counts


def resume_valid(record,entry,version,root):
    if record.get("pipelineVersion")!=version or record.get("sourceSha")!=entry.get("sha256"):
        return False
    if record.get("state") not in {"approved_unmodified","approved_cleaned","review_required","failed"}:
        return False
    source=safe_path(root,entry["path"])
    if not source.exists() or sha(source.read_bytes())!=entry.get("sha256"):
        return False
    if record["state"].startswith("approved_"):
        target=safe_path(root,record.get("path", ""))
        return target.is_file() and sha(target.read_bytes())==record.get("outputSha")
    return True


def contact_sheets(root,manifest):
    reviewed=[(key,item) for key,item in manifest["images"].items() if item.get("state")=="review_required"]
    folder=root/"artifacts/media-cleanup/review"
    if not reviewed:
        return []
    folder.mkdir(parents=True,exist_ok=True)
    paths=[]
    for start in range(0,len(reviewed),48):
        group=reviewed[start:start+48]
        sheet=Image.new("RGB",(1200,math.ceil(len(group)/4)*200),"white")
        draw=ImageDraw.Draw(sheet)
        for index,(key,item) in enumerate(group):
            x,y=(index%4)*300,(index//4)*200
            crops=item.get("reviewCrops",[])
            candidate=safe_path(root,crops[0]) if crops else folder/(key+"-source.jpg")
            if candidate.is_file():
                with Image.open(candidate) as image:
                    tile=ImageOps.contain(image.convert("RGB"),(280,150))
                    sheet.paste(tile,(x+10,y+5))
            draw.text((x+10,y+160),key[:20],fill="black")
            draw.text((x+10,y+176),item.get("reason","")[:36],fill="black")
        path=folder/f"contact-sheet-{start//48+1:03d}.jpg"
        sheet.save(path,quality=92)
        paths.append(relative(root,path))
    return paths


def cleaned_contact_sheets(root,manifest):
    """Before/after crops for visual acceptance of every automatically edited file."""
    items=[(key,item) for key,item in manifest["images"].items() if item.get("state")=="approved_cleaned"]
    folder=root/"artifacts/media-cleanup/edited-review"
    if not items:
        return []
    folder.mkdir(parents=True,exist_ok=True)
    paths=[]
    for start in range(0,len(items),24):
        group=items[start:start+24]
        sheet=Image.new("RGB",(1200,math.ceil(len(group)/2)*210),"white")
        draw=ImageDraw.Draw(sheet)
        for index,(key,item) in enumerate(group):
            report=json.loads(safe_path(root,item["report"]).read_text("utf-8"))
            boxes=[d["box"] for d in report.get("detections",[])]
            with Image.open(safe_path(root,item["sourcePath"])) as source,Image.open(safe_path(root,item["path"])) as target:
                if boxes:
                    crop=(max(0,min(b[0] for b in boxes)-24),max(0,min(b[1] for b in boxes)-20),min(source.width,max(b[2] for b in boxes)+24),min(source.height,max(b[3] for b in boxes)+24))
                else:
                    crop=(0,0,source.width,source.height)
                x,y=(index%2)*600,(index//2)*210
                for offset,image in [(0,source),(300,target)]:
                    tile=ImageOps.contain(image.convert("RGB").crop(crop),(290,165))
                    sheet.paste(tile,(x+offset+5,y+18))
                draw.text((x+5,y+2),"source | "+key[:24],fill="black")
                draw.text((x+305,y+2),"cleaned - visual acceptance pending",fill="black")
                draw.text((x+5,y+188),item.get("reason","")[:80],fill="black")
        path=folder/f"before-after-{start//24+1:03d}.png"
        sheet.save(path)
        paths.append(relative(root,path))
    return paths


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply",action="store_true",help="Write approved copies; does not publish or upload")
    parser.add_argument("--limit",type=int,default=0,help="Process at most this many new verified images")
    parser.add_argument("--workers",type=int,default=8)
    parser.add_argument("--follow-downloads",action="store_true")
    parser.add_argument("--retry-failed",action="store_true")
    parser.add_argument("--download-manifest",type=Path,default=ROOT/"artifacts/media-download.json")
    parser.add_argument("--manifest",type=Path,default=ROOT/"artifacts/media-cleanup.json")
    args=parser.parse_args()
    template_folder=ROOT/"artifacts/media-cleanup/templates"
    version=pipeline_version(template_folder)
    if args.manifest.exists():
        manifest=json.loads(args.manifest.read_text("utf-8"))
    else:
        manifest={"schemaVersion":1,"createdAt":utcnow(),"images":{},"references":{}}
    if manifest.get("pipelineVersion")!=version:
        for item in manifest["images"].values():
            if item.get("state")!="pending":
                item["previousState"]=item["state"]
                item["state"]="pending"
                item["reason"]="pipeline_changed_requires_new_scan"
    manifest.update(pipelineVersion=version,config=CONFIG,apply=args.apply,publicationReady=False,inventoryOnly=False)
    manifest["totals"]=summarize(manifest)
    atomic_json(args.manifest,manifest)
    scheduled=set()
    settled=set()
    pending={}
    completed=0
    last_checkpoint=0.
    checkpoint_completed=-1
    last_load=0.
    download={}
    source_changed=False
    with ThreadPoolExecutor(max_workers=max(1,min(8,args.workers))) as executor:
        try:
            while True:
                now=time.monotonic()
                if now-last_load>2 or not download:
                    download=json.loads(args.download_manifest.read_text("utf-8"))
                    manifest["references"]=download.get("references",{})
                    manifest["sourceCatalogSha256"]=download.get("sourceCatalogSha256")
                    for key,entry in download.get("images",{}).items():
                        if key not in manifest["images"]:
                            manifest["images"][key]={"state":"pending","sourceSha":entry.get("sha256"),"url":entry.get("url")}
                        if entry.get("status")=="failed" and key not in scheduled:
                            manifest["images"][key].update(state="failed",reason="source_download_failed")
                    last_load=now
                capacity=max(1,min(8,args.workers))*2-len(pending)
                if capacity>0 and (not args.limit or len(scheduled)<args.limit):
                    for key,entry in download.get("images",{}).items():
                        if capacity<=0 or (args.limit and len(scheduled)>=args.limit):
                            break
                        if entry.get("status")!="verified" or key in scheduled or key in settled:
                            continue
                        existing=manifest["images"].get(key,{})
                        if not (args.retry_failed and existing.get("state")=="failed") and resume_valid(existing,entry,version,ROOT):
                            settled.add(key)
                            continue
                        scheduled.add(key)
                        pending[executor.submit(process_entry,key,entry,ROOT,ROOT/"artifacts/media-cleaned",args.apply)]=key
                        capacity-=1
                if pending:
                    done,_=wait(pending,timeout=1,return_when=FIRST_COMPLETED)
                    for future in done:
                        key=pending.pop(future)
                        report=future.result()
                        report["pipelineVersion"]=version
                        report_path=ROOT/"artifacts/media-cleanup/reports"/(key+".json")
                        atomic_json(report_path,report)
                        fields=["state","sourceSha","sourcePath","sourceBytes","outputSha","path","filename","mime","bytes","width","height","reason","updatedAt","maskCoverage","reviewCrops","pipelineVersion"]
                        manifest["images"][key]={name:report[name] for name in fields if name in report}
                        manifest["images"][key]["report"]=relative(ROOT,report_path)
                        completed+=1
                if completed!=checkpoint_completed and completed and (completed%25==0 or now-last_checkpoint>10):
                    manifest.update(updatedAt=utcnow(),totals=summarize(manifest))
                    atomic_json(args.manifest,manifest)
                    print(json.dumps({"updatedAt":manifest["updatedAt"],"completedThisRun":completed,**manifest["totals"]}),flush=True)
                    last_checkpoint=now
                    checkpoint_completed=completed
                if not pending:
                    if args.limit and len(scheduled)>=args.limit:
                        break
                    awaiting=sum(1 for item in download.get("images",{}).values() if item.get("status")=="pending")
                    if not args.follow_downloads or not awaiting:
                        break
                    time.sleep(2)
        except KeyboardInterrupt:
            print("Checkpointing after active workers complete",file=sys.stderr,flush=True)
            for future,key in list(pending.items()):
                report=future.result()
                report["pipelineVersion"]=version
                path=ROOT/"artifacts/media-cleanup/reports"/(key+".json")
                atomic_json(path,report)
                manifest["images"][key]={**report,"report":relative(ROOT,path)}
    manifest["reviewContactSheets"]=contact_sheets(ROOT,manifest)
    manifest["cleanedContactSheets"]=cleaned_contact_sheets(ROOT,manifest)
    manifest.update(updatedAt=utcnow(),totals=summarize(manifest))
    atomic_json(args.manifest,manifest)
    print(json.dumps({"manifest":str(args.manifest),"pipelineVersion":version,**manifest["totals"]}),flush=True)


if __name__=="__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
