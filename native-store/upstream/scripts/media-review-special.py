"""Independent review candidates for opaque badges in RGBA PNGs and chair GIFs.

Does not write the main cleanup manifest, its reports, templates, or source files.
All candidates require root visual acceptance and the separate global flame pass.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageOps, PngImagePlugin, _webp

ROOT=Path(__file__).resolve().parents[1]
FROZEN_PIPELINE="37fbdbdb594cb9d366fec3cb7f2662a694d4497ea7545607d471d23c3a9ecbd9"
DEST=ROOT/"artifacts/media-review-special"
PNG_KEYS=[
    "1f6442821b216e2eb09bdc1212e364947e625f655b49eb6e85f7eed74101eac5",
    "2c5bccfeea0d781331845605dfce5aa5228d4621d72d0dffce1a8d09944da780",
    "7b603cdf5f100c81c4635a072994e59d85d8a27ab0d647dd36b712dd8be60807",
    "fde7621f0b0d0b6ef9020e1cfe334fb085c3b0fca2131ad64a2c6db5e6956b8d",
    "4a51af4bc7660e04614911e705c031bda83f7bbd7d438513db1ac2b1e2b4ca41",
]
GIF_KEYS=[
    "c21c9627608d2a5b3cf8b3985e6b0fd4c4625611ec4321f75ae3e7a9709f957d",
    "ae03c20b84374bc113ef7dfe0fa44102e23ec52aeea42b7f182b84b6370421c7",
    "d5305d5e2696b6541338c10d7b55fe1d1fb4cbd67992fdbdea3b5822c2a4a008",
    "6f4297856e7ac2c5aa2594325686cd80c02d4c15d57ea8ca48e83a1925d9f574",
    "07980d07c377ced667cd8cb548f473a8e6cb0e565a67bcc588902682b828cd60",
]
FABRIC_PLANS={
    "d5305d5e2696b6541338c10d7b55fe1d1fb4cbd67992fdbdea3b5822c2a4a008":{
        "sourceSha":"a6df1652a63d9574240af7da707d38ece50cc34fea2a74276b8afe0dac669ba6",
        "quad":[[840,615],[947,621],[922,939],[809,931]],"size":[112,322],"fieldLeft":12,"fieldTop":10,"fieldBottomMargin":5,"underlineColumns":[6,21],"underlineSegments":[[6,21,12,310]]},
    "fae311f35e0540f48b4a3cd0181f503c2dbb22e4676ac12c60071b6be5e0cb2e":{
        "sourceSha":"e6cda1238f042d43f66c5be49fa81edce89a846291775dcd9577bd1fa9225bdf",
        "quad":[[569,415],[645,420],[628,638],[545,631]],"size":[85,222],"fieldLeft":12,"fieldTop":10,"fieldBottomMargin":4,"underlineColumns":[4,16],"underlineSegments":[[3,16,6,213]]},
    "ac659d7ea1263e444e986b8b8afe6025a96515db94edd97446e1b793b9e68401":{
        "sourceSha":"4f061a4c73249ca8d2a91979632df9ba7d4d0870643a07f41510489f037b1fe2",
        "quad":[[709,410],[802,420],[774,684],[678,675]],"size":[102,270],"fieldLeft":14,"fieldTop":10,"fieldBottomMargin":4,"underlineColumns":[2,16],"underlineSegments":[[2,16,4,100],[2,16,132,220]]},
    "6c4e9470ce3f3db2e671d5865839bbe04cef2e5a9250588bf736e05c580f4343":{
        "sourceSha":"17432255daac3229dcc15be9804e7aa146eaf3123e93d3da5bf217ed91dd10c3",
        "quad":[[665,432],[778,443],[731,768],[626,748]],"size":[113,330],"fieldLeft":14,"fieldTop":5,"fieldBottomMargin":4,"underlineColumns":[0,18],"underlineSegments":[[0,18,8,125],[0,18,148,314]],"extraOrangeCorridor":[[665,440],[677,443],[641,711],[630,708]]},
    "07980d07c377ced667cd8cb548f473a8e6cb0e565a67bcc588902682b828cd60":{
        "sourceSha":"ad24648fbdfcd990d1cabb5ac8aeb68923f8eeadcce02143117de41ec81ab0ea",
        "quad":[[988,644],[1151,655],[1076,1137],[922,1127]],"size":[166,490],"fieldLeft":20,"fieldTop":8,"fieldBottomMargin":5,"underlineColumns":[0,24],"underlineSegments":[[0,24,3,175],[0,24,220,405]],"extraOrangeCorridor":[[979,651],[996,653],[947,1036],[932,1034]]},
}
FABRIC_STILL_KEYS=[key for key in FABRIC_PLANS if key not in GIF_KEYS]
SMALL_TAG_PLANS={
    'e6ec41d6012d27b6a4429609c1fef4090acc141e0f68a916c6c4559bacb2b72c':{
        'sourceSha':'4d7016b0959a65c5b851a079b2364d1528cfcefec1ca0d03d26d0b95e793ccc9','quad':[[591,489],[600,489],[604,513],[592,513]],'group':128},
    '3e0b6b744085e45c4f2f22f7bcc2f8120deb2a21134fb28ee0ba27b9be14dbad':{
        'sourceSha':'700ada5087f753ab96fd5c19cc67ff795ebaba7b354a51927a2de645316138fc','quad':[[601,524],[611,524],[611,550],[601,550]],'group':195},
    '044323d0f4116fbf386c4773a2394ad717adfc6fe09563e4ce21610749d92fae':{
        'sourceSha':'f49b2db41fe4c4103f3ef54b106431ca991c8fbef7220da1df870e6cf461b81f','quad':[[601,524],[611,524],[611,550],[601,550]],'group':416},
}
OFFICE_GIF_KEY='6f4297856e7ac2c5aa2594325686cd80c02d4c15d57ea8ca48e83a1925d9f574'
LARGE_WOVEN_GIF_KEY='d5305d5e2696b6541338c10d7b55fe1d1fb4cbd67992fdbdea3b5822c2a4a008'
spec=importlib.util.spec_from_file_location("frozen_media_clean",ROOT/"scripts/media-clean.py")
core=importlib.util.module_from_spec(spec);spec.loader.exec_module(core)
cv2.setNumThreads(1)


def sha(data):return hashlib.sha256(data).hexdigest()
def rel(path):return path.resolve().relative_to(ROOT.resolve()).as_posix()


def combine_opaque_mask(source_rgba,edited_rgb,mask):
    if source_rgba.shape[:2]!=mask.shape or edited_rgb.shape!=source_rgba[:,:,:3].shape:
        raise ValueError("Image/mask dimensions differ")
    if np.any(source_rgba[:,:,3][mask!=0]!=255):
        raise ValueError("RGB retouch mask must be completely opaque")
    output=source_rgba.copy()
    output[:,:,:3][mask!=0]=edited_rgb[mask!=0]
    return output


def validate_rgba(source,decoded,mask):
    if source.shape!=decoded.shape:
        raise ValueError("Decoded dimensions changed")
    alpha=np.abs(source[:,:,3].astype(np.int16)-decoded[:,:,3].astype(np.int16))
    outside=mask==0
    delta=np.abs(source[:,:,:3][outside].astype(np.int16)-decoded[:,:,:3][outside].astype(np.int16))
    result={"outsideMaskRgbMaxDelta":int(delta.max()) if delta.size else 0,"outsideMaskRgbChangedValues":int(np.count_nonzero(delta)),"alphaMaxDelta":int(alpha.max()),"alphaChangedPixels":int(np.count_nonzero(alpha)),"maskOpaque":bool(np.all(source[:,:,3][mask!=0]==255))}
    if result["outsideMaskRgbMaxDelta"]:
        raise ValueError("Outside mask RGB changed after decode")
    if result["alphaMaxDelta"]:
        raise ValueError("Alpha changed after decode")
    return result


def lettering_mask(rgb,quad):
    allowed=np.zeros(rgb.shape[:2],np.uint8)
    cv2.fillConvexPoly(allowed,np.round(quad).astype(np.int32),255)
    gray=cv2.cvtColor(rgb,cv2.COLOR_RGB2GRAY)
    data=rgb.astype(np.int16)
    orange=(data[:,:,0]>25)&(data[:,:,0]>data[:,:,1]*1.35+8)&(data[:,:,0]>data[:,:,2]*1.2+8)
    core_mask=((gray>100)|orange)&(allowed!=0)
    mask=cv2.dilate(core_mask.astype(np.uint8)*255,np.ones((5,5),np.uint8))
    mask[allowed==0]=0
    return mask


def retouch_ink(rgb,mask):
    # Only small printed strokes are filled; label outline and fabric stay intact.
    if not np.any(mask):return rgb.copy()
    output=rgb.copy()
    ring=(cv2.dilate(mask,np.ones((9,9),np.uint8))!=0)&(mask==0)
    gray=cv2.cvtColor(rgb,cv2.COLOR_RGB2GRAY)
    spread=rgb.max(axis=2).astype(int)-rgb.min(axis=2).astype(int)
    neutral=(spread<18)&(gray<120)
    fallback=rgb[ring&neutral]
    if len(fallback)<5:raise ValueError("No neutral source tag substrate for ink retouch")
    fallback_tone=np.median(fallback,axis=0)
    for y in np.where(np.any(mask!=0,axis=1))[0]:
        xs=np.where(mask[y]!=0)[0];left=max(0,int(xs.min())-5);right=min(rgb.shape[1],int(xs.max())+6)
        available=rgb[y,left:right][(mask[y,left:right]==0)&neutral[y,left:right]]
        tone=np.median(available,axis=0) if len(available)>=2 else fallback_tone
        output[y,mask[y]!=0]=np.round(tone).astype(np.uint8)
    output[mask==0]=rgb[mask==0]
    return output


def isolated_light_surround_plaque(rgb,detections):
    """Reviewed four light-oak PNGs: isolate their fully bounded dark plaque.

    This is intentionally not a generic dark-hull rule. The connected plaque must
    be surrounded by light pixels inside a small reviewed source region.
    """
    output=rgb.copy();mask=np.zeros(rgb.shape[:2],np.uint8);regions=[]
    for detection in detections:
        x0,y0,x1,y1=[int(v) for v in detection['box']]
        left,top,right,bottom=max(0,x0-8),max(0,y0-8),min(rgb.shape[1],x1+8),min(rgb.shape[0],y1+8)
        crop=rgb[top:bottom,left:right];gray=cv2.cvtColor(crop,cv2.COLOR_RGB2GRAY)
        connected=cv2.morphologyEx((gray<95).astype(np.uint8),cv2.MORPH_CLOSE,np.ones((3,3),np.uint8))
        contours,_=cv2.findContours(connected,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
        if not contours:raise ValueError('Reviewed opaque plaque not isolated')
        contour=max(contours,key=cv2.contourArea);bx,by,bw,bh=cv2.boundingRect(contour)
        if bx<=0 or by<=0 or bx+bw>=crop.shape[1] or by+bh>=crop.shape[0]:raise ValueError('Dark component touches review boundary')
        if cv2.contourArea(contour)<(x1-x0)*(y1-y0)*.25:raise ValueError('Dark plaque component too small')
        hull=cv2.convexHull(contour);physical=np.zeros(gray.shape,np.uint8);cv2.fillConvexPoly(physical,hull,255)
        interior=cv2.erode(physical,np.ones((3,3),np.uint8))
        ring=(cv2.dilate(physical,np.ones((5,5),np.uint8))!=0)&(physical==0)
        if np.median(gray[ring])<110:raise ValueError('Plaque does not have the reviewed light surround')
        values=crop[(physical!=0)&(gray<85)]
        if len(values)<12:raise ValueError('Dark plaque tone lacks source samples')
        tone=np.round(np.median(values,axis=0)).astype(np.uint8)
        local=output[top:bottom,left:right];local[interior!=0]=tone
        mask[top:bottom,left:right]=cv2.bitwise_or(mask[top:bottom,left:right],interior)
        regions.append({'method':'manually_reviewed_isolated_plaque_on_light_oak','physicalQuad':(hull.reshape(-1,2)+[left,top]).tolist(),'tone':tone.tolist(),'sourceComponentBounds':[left+bx,top+by,left+bx+bw,top+by+bh],'sourceSurroundMedianGray':float(np.median(gray[ring])),'physicalOutlineRetainedPixels':1})
    output[mask==0]=rgb[mask==0]
    return output,mask,{'accepted':True,'physicalPlaqueRetained':True,'regions':regions}


def texture_clone_print_field(rgb,plan):
    """Replace the contiguous print field with actual woven source material.

    Filling only white glyph strokes can leave a readable embossed dark word.
    This copies real, unprinted textile across the print column, while retaining
    the physical outline, folded upper edge, and non-ink garment fibres.
    """
    quad=np.array(plan['quad'],np.float32)
    width,height=plan['size']
    destination=np.array([[0,0],[width-1,0],[width-1,height-1],[0,height-1]],np.float32)
    transform=cv2.getPerspectiveTransform(quad,destination)
    inverse=cv2.getPerspectiveTransform(destination,quad)
    rectified=cv2.warpPerspective(rgb,transform,(width,height),flags=cv2.INTER_NEAREST)
    rect_gray=cv2.cvtColor(rectified,cv2.COLOR_RGB2GRAY)
    rect_colors=rectified.astype(np.int16)
    rect_spread=rect_colors.max(axis=2)-rect_colors.min(axis=2)
    underline=np.zeros((height,width),np.uint8)
    line_start,line_end=plan.get('underlineColumns',[0,plan['fieldLeft']+4])
    underline[2:height-2,line_start:line_end]=1
    symbol=np.zeros_like(underline);symbol[round(height*.35):round(height*.70),round(width*.20):width-7]=1
    red=(rect_colors[:,:,0]>45)&(rect_colors[:,:,0]>rect_colors[:,:,1]*1.45+8)&(rect_colors[:,:,0]>rect_colors[:,:,2]*1.4+8)
    white=(rect_gray>155)&(rect_spread<60)
    rect_ink=white|(red&((underline!=0)|(symbol!=0)))
    rect_ink=cv2.dilate(rect_ink.astype(np.uint8),np.ones((5,5),np.uint8))
    # Do not use any original printed glyph or its immediate shadow as a donor.
    excluded=cv2.dilate(rect_ink,np.ones((7,7),np.uint8))!=0
    donor_neutral=(rect_spread<45)&(rect_gray<155)&~excluded
    field=np.zeros_like(underline)
    field[plan['fieldTop']:height-plan['fieldBottomMargin'],plan['fieldLeft']:width-3]=255
    for x0,x1,y0,y1 in plan.get('underlineSegments',[]):field[y0:y1,x0:x1]=255
    field_mask=cv2.warpPerspective(field,inverse,(rgb.shape[1],rgb.shape[0]),flags=cv2.INTER_NEAREST)
    ink_mask=cv2.warpPerspective(rect_ink,inverse,(rgb.shape[1],rgb.shape[0]),flags=cv2.INTER_NEAREST)
    allowed=np.zeros(rgb.shape[:2],np.uint8);cv2.fillConvexPoly(allowed,quad.astype(np.int32),255)
    allowed=cv2.erode(allowed,np.ones((3,3),np.uint8))
    data=rgb.astype(np.int16)
    spread=data.max(axis=2)-data.min(axis=2)
    mask=((field_mask!=0)|(ink_mask!=0)).astype(np.uint8)*255
    mask[allowed==0]=0
    # One real 2D patch prevents the barcode artifacts of per-row donor choices.
    valid=donor_neutral.astype(np.uint8)
    valid[:3]=0;valid[-3:]=0;valid[:,:3]=0;valid[:,-3:]=0
    preferred=valid.copy();preferred[:,:max(3,width-25)]=0
    distance=cv2.distanceTransform(preferred,cv2.DIST_L2,5)
    if distance.max()<5:distance=cv2.distanceTransform(valid,cv2.DIST_L2,5)
    center_y,center_x=np.unravel_index(np.argmax(distance),distance.shape)
    half=max(2,int(float(distance[center_y,center_x])/1.42)-1)
    while half>1 and not np.all(valid[center_y-half:center_y+half+1,center_x-half:center_x+half+1]):half-=1
    if half<2:raise ValueError('No sufficiently large unprinted woven source patch')
    donor_box=[center_x-half,center_y-half,center_x+half+1,center_y+half+1]
    patch=rectified[donor_box[1]:donor_box[3],donor_box[0]:donor_box[2]].copy()
    tiled=np.tile(patch,(int(np.ceil(height/patch.shape[0])),int(np.ceil(width/patch.shape[1])),1))[:height,:width]
    rect_mask=cv2.warpPerspective(mask,transform,(width,height),flags=cv2.INTER_NEAREST)
    # Feather only against verified unprinted neutral substrate. A Poisson fill
    # would import orange print/white-glyph low frequencies from its boundaries.
    distance_to_edge=cv2.distanceTransform((rect_mask!=0).astype(np.uint8),cv2.DIST_L2,5)
    alpha=np.clip(distance_to_edge/3.,0,1)
    safe_original=donor_neutral
    alpha[~safe_original]=1
    alpha=alpha[:,:,None]
    blended=np.round(tiled.astype(float)*alpha+rectified.astype(float)*(1-alpha)).astype(np.uint8)
    reconstructed=cv2.warpPerspective(blended,inverse,(rgb.shape[1],rgb.shape[0]),flags=cv2.INTER_NEAREST)
    output=rgb.copy();output[mask!=0]=reconstructed[mask!=0]
    # At a partly occluded physical edge, a few printed orange fibres can sit
    # just outside the planar face. Only source-coloured print pixels inside
    # this separately reviewed corridor are included; the upper seam is out.
    extra_mask=np.zeros(mask.shape,np.uint8)
    if plan.get('extraOrangeCorridor'):
        corridor=np.zeros(mask.shape,np.uint8);cv2.fillConvexPoly(corridor,np.array(plan['extraOrangeCorridor'],np.int32),255)
        source_red=(data[:,:,0]>30)&(data[:,:,0]>data[:,:,1]*1.35+6)&(data[:,:,0]>data[:,:,2]*1.3+6)
        extra_mask[(corridor!=0)&source_red]=255
        real_texture=cv2.warpPerspective(tiled,inverse,(rgb.shape[1],rgb.shape[0]),flags=cv2.INTER_NEAREST,borderMode=cv2.BORDER_REFLECT_101)
        output[extra_mask!=0]=real_texture[extra_mask!=0]
        mask=cv2.bitwise_or(mask,extra_mask)
    output[mask==0]=rgb[mask==0]
    return output,mask,[quad.tolist()],{'method':'contiguous_print_field_source_texture_patch_feathered','physicalQuad':quad.tolist(),'sourceDonorRectifiedBox':[int(v) for v in donor_box],'rectifiedSize':[width,height],'sourceTextureOnly':True,'contiguousPrintField':True,'originalInkOrShadowNeverFeatheredBack':True,'upperManufacturingStitchPreserved':True,'fieldLeft':plan['fieldLeft'],'fieldTop':plan['fieldTop'],'fieldBottomMargin':plan['fieldBottomMargin'],'underlineSegments':plan.get('underlineSegments',[]),'extraOrangeCorridor':plan.get('extraOrangeCorridor'),'extraOrangePixels':int(np.count_nonzero(extra_mask))}


def retouch_large_woven_tag(rgb):
    return texture_clone_print_field(rgb,FABRIC_PLANS[LARGE_WOVEN_GIF_KEY])


def source_surface_print_retouch(rgb,quad,donor_offset=50,ring_radius=17,colored_print=False,donor_patch=None,donor_translation=None):
    """Reviewed headrest print: recover smooth lighting and real source grain.

    The complete word including its embossed shadow is inside a manually
    reviewed quad. Adjacent original leather supplies texture; a cubic surface
    fitted only to the surrounding unprinted source supplies local lighting.
    This helper cannot infer a product boundary and must not cross one.
    """
    mask=np.zeros(rgb.shape[:2],np.uint8)
    cv2.fillConvexPoly(mask,np.round(quad).astype(np.int32),255)
    ys,xs=np.where(mask!=0)
    if not len(xs):raise ValueError('Empty source print region')
    left,right,top,bottom=int(xs.min()),int(xs.max()+1),int(ys.min()),int(ys.max()+1)
    shift_x,shift_y=donor_translation if donor_translation is not None else [0,donor_offset]
    if not donor_patch and (bottom+shift_y>=rgb.shape[0] or top+shift_y<0 or left+shift_x<0 or right+shift_x>=rgb.shape[1]):raise ValueError('Source grain donor leaves canvas')
    ring=(cv2.dilate(mask,np.ones((ring_radius*2+1,ring_radius*2+1),np.uint8))!=0)&(mask==0)
    yy,xx=np.where(ring)
    def basis(x,y):return np.c_[np.ones(len(x)),x,y,x*y,x*x,y*y,x*x*y,x*y*y,x*x*x,y*y*y]
    cx,cy=(left+right)/2,(top+bottom)/2
    design=basis((xx-cx)/(right-left),(yy-cy)/(bottom-top))
    coefficients=np.linalg.lstsq(design,rgb[ring].astype(float),rcond=None)[0]
    yy,xx=np.where(mask!=0)
    surface=basis((xx-cx)/(right-left),(yy-cy)/(bottom-top))@coefficients
    # Bind the recovered illumination continuously to the actual source
    # boundary. A free polynomial alone can leave a visible rectangular band.
    hx0,hy0=max(0,left-8),max(0,top-8)
    hx1,hy1=min(rgb.shape[1],right+8),min(rgb.shape[0],bottom+8)
    local_mask=mask[hy0:hy1,hx0:hx1]!=0
    harmonic=rgb[hy0:hy1,hx0:hx1].astype(np.float32)
    # Printed colour must not bleed through a blur into the fixed boundary.
    harmonic[local_mask]=surface.astype(np.float32)
    harmonic=cv2.GaussianBlur(harmonic,(0,0),2.2)
    harmonic[local_mask]=surface.astype(np.float32)
    iterations=0
    for iterations in range(2500):
        smooth=cv2.blur(harmonic,(3,3))
        delta=float(np.max(np.abs(harmonic[local_mask]-smooth[local_mask])))
        harmonic[local_mask]=smooth[local_mask]
        if delta<.0005:break
    surface=harmonic[yy-hy0,xx-hx0]
    # Keep the actual donor's grain, without copying its unrelated lighting.
    y0=max(0,top+shift_y-8);y1=min(rgb.shape[0],bottom+shift_y+8)
    x0=max(0,left+shift_x-8);x1=min(rgb.shape[1],right+shift_x+8)
    if donor_patch:
        x0,y0,x1,y1=donor_patch
        donor=rgb[y0:y1,x0:x1].astype(float)
        if donor.shape[0]<4 or donor.shape[1]<4:raise ValueError('Reviewed grain donor patch too small')
        grain=donor-cv2.GaussianBlur(donor,(0,0),2)
        samples=grain[(yy-top)%grain.shape[0],(xx-left)%grain.shape[1]]
    else:
        donor=rgb[y0:y1,x0:x1].astype(float)
        grain=donor-cv2.GaussianBlur(donor,(0,0),2)
        samples=grain[yy+shift_y-y0,xx+shift_x-x0]
    fill=np.clip(surface+samples,0,255)
    distance=cv2.distanceTransform((mask!=0).astype(np.uint8),cv2.DIST_L2,5)[yy,xx]
    alpha=np.clip(distance/6,0,1)[:,None]
    if colored_print:
        data=rgb.astype(np.int16);gray=cv2.cvtColor(rgb,cv2.COLOR_RGB2GRAY)
        print_pixels=(gray>95)|((data[:,:,0]>30)&(data[:,:,0]>data[:,:,1]*1.3+5)&(data[:,:,0]>data[:,:,2]*1.25+5))
        print_pixels=cv2.dilate(print_pixels.astype(np.uint8),np.ones((5,5),np.uint8))!=0
        alpha[print_pixels[yy,xx]]=1
    output=rgb.copy();output[yy,xx]=np.round(fill*alpha+rgb[yy,xx]*(1-alpha)).astype(np.uint8)
    return output,mask,{'method':'source_leather_grain_with_source_boundary_harmonic_illumination','manualPrintQuad':np.round(quad,4).tolist(),'sourceGrainOnly':True,'donorTranslation':None if donor_patch else [shift_x,shift_y],'sourceDonorBounds':[x0,y0,x1,y1],'reviewedGrainPatchTiled':bool(donor_patch),'illuminationInitializationDegree':3,'illuminationSource':'unprinted_source_boundary_harmonic_relaxation','harmonicIterations':iterations+1,'coloredInkNeverFeatheredBack':colored_print,'outsideMaskExact':True}


class FlameMatcher:
    """Native-resolution flame check of the visually tracked label regions."""
    def __init__(self,scales=None):
        folder=DEST/"templates"
        self.templates=[]
        self.references=[]
        self.scales=scales or [.75,1.,1.25,1.5]
        for name in ["adore-gaming-flame-frame14.png","adore-gaming-flame-gray-frame10.png"]:
            path=folder/name
            template=np.array(Image.open(path).convert("RGB"))
            self.references.append({"path":rel(path),"sha256":sha(path.read_bytes())})
            for rotation in range(4):
                rotated=np.ascontiguousarray(np.rot90(template,rotation))
                for scale in self.scales:
                    size=(max(4,round(rotated.shape[1]*scale)),max(4,round(rotated.shape[0]*scale)))
                    self.templates.append((name,rotation,scale,cv2.resize(rotated,size,interpolation=cv2.INTER_CUBIC)))

    def detect_regions(self,rgb,regions):
        hits=[];peaks=[]
        for quad in regions:
            points=np.array(quad,float)
            x0,y0=np.maximum(0,np.floor(points.min(axis=0)).astype(int)-8)
            x1,y1=np.minimum([rgb.shape[1],rgb.shape[0]],np.ceil(points.max(axis=0)).astype(int)+9)
            crop=np.ascontiguousarray(rgb[y0:y1,x0:x1])
            best={"score":0.}
            for name,rotation,scale,template in self.templates:
                if template.shape[0]>=crop.shape[0] or template.shape[1]>=crop.shape[1]:continue
                scores=cv2.matchTemplate(crop,template,cv2.TM_CCOEFF_NORMED)
                _,score,_,point=cv2.minMaxLoc(scores)
                if score>best["score"]:
                    best={"score":round(float(score),6),"template":name,"rotationQuarterTurns":rotation,"scale":scale,"box":[int(v) for v in [x0+point[0],y0+point[1],x0+point[0]+template.shape[1],y0+point[1]+template.shape[0]]]}
            peaks.append(best)
            if best["score"]>=.90:hits.append(best)
        return {"scope":"visually_tracked_label_regions_native_resolution","threshold":.90,"scaleFactors":self.scales,"hits":hits,"peaks":peaks,"references":self.references,"globalIconPassRequired":True}


def encode_staged_animation(frame_paths,durations,loop,path):
    """Stream one lossless frame at a time through Pillow's installed WebP API."""
    if len(frame_paths)!=len(durations) or not frame_paths:raise ValueError("Frame duration mismatch")
    with Image.open(frame_paths[0]) as first:size=first.size
    encoder=_webp.WebPAnimEncoder(size,0xFFFFFFFF,loop,False,9,17,False,False)
    timestamp=0
    for frame_path,duration in zip(frame_paths,durations):
        with Image.open(frame_path) as image:
            frame=image.convert("RGBA")
            if frame.size!=size:raise ValueError("Frame canvas changed")
            encoder.add(frame.getim(),round(timestamp),True,100,100,4)
        timestamp+=duration
    encoder.add(None,round(timestamp),True,100,100,0)
    data=encoder.assemble("","","")
    if data is None:raise ValueError("Animation encoder failed")
    path.write_bytes(data)


def validate_staged_animation(frame_paths,durations,loop,path):
    """Prove exact pixels and the complete timeline, even if duplicates coalesce."""
    output_durations=[]
    with Image.open(path) as image:
        if image.info.get("loop",0)!=loop:raise ValueError("Animation loop changed")
        for index in range(image.n_frames):
            image.seek(index);image.load();output_durations.append(int(image.info.get("duration",0)))
    if sum(durations)!=sum(output_durations):raise ValueError("Animation total duration changed")
    source_starts=np.cumsum([0]+list(durations))
    output_starts=np.cumsum([0]+output_durations)
    mappings=[];rgb_max=0;alpha_max=0
    with Image.open(path) as output:
        for source_index,stage in enumerate(frame_paths):
            matches=[]
            with Image.open(stage) as staged:expected=np.array(staged.convert("RGBA"))
            for output_index in range(len(output_durations)):
                overlap=max(0,min(source_starts[source_index+1],output_starts[output_index+1])-max(source_starts[source_index],output_starts[output_index]))
                if not overlap:continue
                output.seek(output_index);decoded=np.array(output.convert("RGBA"))
                if expected.shape!=decoded.shape:raise ValueError("Animation canvas changed")
                delta=np.abs(expected.astype(np.int16)-decoded.astype(np.int16))
                rgb_max=max(rgb_max,int(delta[:,:,:3].max()));alpha_max=max(alpha_max,int(delta[:,:,3].max()))
                if np.any(delta):raise ValueError("Lossless animation pixels changed")
                matches.append({"outputFrame":output_index,"durationMs":int(overlap)})
            if sum(v["durationMs"] for v in matches)!=durations[source_index]:raise ValueError("Frame timeline coverage changed")
            mappings.append({"sourceFrame":source_index,"outputSegments":matches})
    return {"sourceFrameCount":len(frame_paths),"outputFrameCount":len(output_durations),"sourceDurationsMs":list(durations),"outputDurationsMs":output_durations,"totalDurationMs":sum(durations),"loop":loop,"rgbMaxDelta":rgb_max,"alphaMaxDelta":alpha_max,"sourceToOutputMapping":mappings,"identicalAdjacentFramesMayMerge":len(frame_paths)!=len(output_durations)}


def save_png_rgba(output,path,info):
    metadata=PngImagePlugin.PngInfo()
    if info.get("chromaticity"):
        metadata.add(b"cHRM",struct.pack(">8I",*(round(v*100000) for v in info["chromaticity"])))
    Image.fromarray(output).save(path,"PNG",compress_level=9,pnginfo=metadata,**({"dpi":info["dpi"]} if info.get("dpi") else {}))


def dedupe_detections(detections):
    kept=[]
    for item in detections:
        if not any(core.box_iou(item["box"],old["box"])>.75 for old in kept):kept.append(item)
    return kept


def source_receipt(key,entry):
    if key in FABRIC_PLANS and entry['sha256']!=FABRIC_PLANS[key]['sourceSha']:
        raise ValueError('Source differs from manually reviewed fabric plan')
    if key in SMALL_TAG_PLANS and entry['sha256']!=SMALL_TAG_PLANS[key]['sourceSha']:
        raise ValueError('Source differs from visually confirmed small tag plan')
    if key==OFFICE_GIF_KEY and entry['sha256']!='d3cf6e65c63a83eb692409f5b0e260eaf10da77e411bf7c8790a26779ac6d182':
        raise ValueError('Source differs from visually confirmed office chair animation')
    path=core.safe_path(ROOT,entry["path"])
    if sha(path.read_bytes())!=entry["sha256"]:raise ValueError("Source SHA changed")
    return {"urlSha":key,"sourceSha":entry["sha256"],"sourcePath":entry["path"],"sourceBytes":entry["bytes"],"width":entry["width"],"height":entry["height"],"pipelineVersion":FROZEN_PIPELINE,"publicationReady":False,"approved":False,"globalIconPassRequired":True}


def composite_scans(rgba,engines):
    results=[]
    for background in ["white","black"]:
        composed=Image.new("RGBA",(rgba.shape[1],rgba.shape[0]),background);composed.alpha_composite(Image.fromarray(rgba))
        detections,scan=engines.scan(np.array(composed.convert("RGB")))
        results.append({"background":background,"detections":detections,"scan":scan})
    return results


def proof_pair(source,output,box,path,key):
    x0,y0,x1,y1=box
    crop=(max(0,x0-20),max(0,y0-18),min(source.width,x1+20),min(source.height,y1+20))
    sheet=Image.new("RGB",(800,280),"white");draw=ImageDraw.Draw(sheet)
    for offset,image in [(0,source),(400,output)]:
        tile=ImageOps.contain(image.convert("RGB").crop(crop),(390,230));sheet.paste(tile,(offset+5,25))
    draw.text((5,3),"source "+key[:24],fill="black");draw.text((405,3),"candidate - visual acceptance pending",fill="black");sheet.save(path)
    full=Image.new("RGB",(source.width*2,source.height),"white");full.paste(source.convert("RGB"),(0,0));full.paste(output.convert("RGB"),(source.width,0));full.thumbnail((1760,880));full.save(path.with_name(path.stem+"-full.jpg"),quality=95)


def process_png(key,entry,report,engines,flames):
    receipt=source_receipt(key,entry);folder=DEST/key;folder.mkdir(parents=True,exist_ok=True)
    with Image.open(ROOT/entry["path"]) as source:
        info=source.info.copy();rgba=np.array(source.convert("RGBA"))
    detections=dedupe_detections(report["detections"])
    output_rgb,mask,plaque=isolated_light_surround_plaque(rgba[:,:,:3].copy(),detections)
    if not plaque["accepted"]:return {**receipt,"candidateState":"review_required","reason":"plaque_fit_uncertain","plaqueAudit":plaque}
    output=combine_opaque_mask(rgba,output_rgb,mask)
    path=folder/"candidate.png";save_png_rgba(output,path,info)
    decoded=np.array(Image.open(path).convert("RGBA"));validation=validate_rgba(rgba,decoded,mask)
    post=composite_scans(decoded,engines)
    quads=[item["physicalQuad"] for item in plaque["regions"]]
    flame=flames.detect_regions(decoded[:,:,:3],quads)
    mask_path=folder/"mask.png";Image.fromarray(mask).save(mask_path)
    boxes=[d["box"] for d in detections];box=[min(b[0] for b in boxes),min(b[1] for b in boxes),max(b[2] for b in boxes),max(b[3] for b in boxes)]
    proof_pair(Image.fromarray(rgba),Image.fromarray(decoded),box,folder/"before-after.png",key)
    source_receipt(key,entry)
    valid=not any(p["detections"] for p in post) and not flame["hits"]
    return {**receipt,"candidateState":"validated_candidate" if valid else "review_required","reason":"opaque_plaque_rgb_only_alpha_preserved","path":rel(path),"outputSha":sha(path.read_bytes()),"bytes":path.stat().st_size,"mime":"image/png","frames":1,"maskPath":rel(mask_path),"maskSha":sha(mask_path.read_bytes()),"validation":validation,"plaqueAudit":plaque,"postScans":post,"postFlame":flame,"closeProof":rel(folder/"before-after.png"),"fullProof":rel(folder/"before-after-full.jpg")}


def process_fabric_still(key,entry,report,engines,flames):
    receipt=source_receipt(key,entry);folder=DEST/key;folder.mkdir(parents=True,exist_ok=True)
    with Image.open(ROOT/entry['path']) as source:
        rgba=np.array(source.convert('RGBA'));icc=source.info.get('icc_profile')
    edited,mask,quads,texture=texture_clone_print_field(rgba[:,:,:3],FABRIC_PLANS[key])
    output=combine_opaque_mask(rgba,edited,mask)
    path=folder/'candidate.webp';Image.fromarray(output).save(path,'WEBP',lossless=True,quality=100,method=4,exact=True,**({'icc_profile':icc} if icc else {}))
    decoded=np.array(Image.open(path).convert('RGBA'));validation=validate_rgba(rgba,decoded,mask)
    detections,scan=engines.scan(decoded[:,:,:3].copy());flame=flames.detect_regions(decoded[:,:,:3],quads)
    mask_path=folder/'mask.png';Image.fromarray(mask).save(mask_path)
    points=np.array(quads[0]);minimum=points.min(axis=0);maximum=points.max(axis=0);box=[*minimum,*maximum]
    proof_pair(Image.fromarray(rgba),Image.fromarray(decoded),box,folder/'before-after.png',key)
    crop=(max(0,int(minimum[0])-12),max(0,int(minimum[1])-12),min(rgba.shape[1],int(maximum[0])+12),min(rgba.shape[0],int(maximum[1])+12))
    before=Image.fromarray(rgba).convert('RGB').crop(crop);after=Image.fromarray(decoded).convert('RGB').crop(crop)
    close=Image.new('RGB',(before.width*2,before.height));close.paste(before,(0,0));close.paste(after,(before.width,0));close.save(folder/'fabric-close-native.png');close.resize((close.width*3,close.height*3),Image.Resampling.NEAREST).save(folder/'fabric-close-3x.png')
    source_receipt(key,entry)
    return {**receipt,'candidateState':'validated_candidate' if not detections and not flame['hits'] else 'review_required','reason':'contiguous_print_column_rewoven_from_original_label_donor','path':rel(path),'outputSha':sha(path.read_bytes()),'bytes':path.stat().st_size,'mime':'image/webp','frames':1,'maskPath':rel(mask_path),'maskSha':sha(mask_path.read_bytes()),'validation':validation,'textureAudit':texture,'postScans':[{'background':'opaque_source','detections':detections,'scan':scan}],'postFlame':flame,'closeProof':rel(folder/'before-after.png'),'nativeProof':rel(folder/'fabric-close-native.png'),'fullProof':rel(folder/'before-after-full.jpg')}


def process_small_static(key,entry,engines):
    receipt=source_receipt(key,entry);folder=DEST/key;folder.mkdir(parents=True,exist_ok=True)
    with Image.open(ROOT/entry['path']) as source:rgba=np.array(source.convert('RGBA'));info=source.info.copy()
    plan=SMALL_TAG_PLANS[key];quads=[plan['quad']]
    mask=lettering_mask(rgba[:,:,:3],plan['quad'])
    output=combine_opaque_mask(rgba,retouch_ink(rgba[:,:,:3],mask),mask)
    is_png=entry['format']=='PNG';path=folder/('candidate.png' if is_png else 'candidate.webp')
    if is_png:save_png_rgba(output,path,info)
    else:Image.fromarray(output).save(path,'WEBP',lossless=True,quality=100,method=4,exact=True,**({'icc_profile':info['icc_profile']} if info.get('icc_profile') else {}))
    decoded=np.array(Image.open(path).convert('RGBA'));validation=validate_rgba(rgba,decoded,mask)
    post=composite_scans(decoded,engines)
    small_flames=FlameMatcher(scales=[.33,.36,.4,.45,.5,.6,.75,1.])
    pre_flame=small_flames.detect_regions(rgba[:,:,:3],quads);post_flame=small_flames.detect_regions(decoded[:,:,:3],quads)
    mask_path=folder/'mask.png';Image.fromarray(mask).save(mask_path)
    points=np.array(plan['quad']);minimum=points.min(axis=0);maximum=points.max(axis=0);box=[*minimum,*maximum]
    proof_pair(Image.fromarray(rgba),Image.fromarray(decoded),box,folder/'before-after.png',key)
    crop=(max(0,int(minimum[0])-8),max(0,int(minimum[1])-8),min(rgba.shape[1],int(maximum[0])+8),min(rgba.shape[0],int(maximum[1])+8))
    before=Image.fromarray(rgba).convert('RGB').crop(crop);after=Image.fromarray(decoded).convert('RGB').crop(crop);pair=Image.new('RGB',(before.width*2,before.height));pair.paste(before,(0,0));pair.paste(after,(before.width,0));pair.save(folder/'native-tag-before-after.png');pair.resize((pair.width*12,pair.height*12),Image.Resampling.NEAREST).save(folder/'tag-before-after-12x.png')
    context=ROOT/f'artifacts/media-symbol-audit/review-progress/context-{plan["group"]}.png'
    review=json.loads((ROOT/'artifacts/media-symbol-audit/review-progress/review.json').read_text('utf-8'))
    group=review['groups'][plan['group']]
    if group['fileSha256']!=entry['sha256'] or not any(role['urlSha']==key for role in group['roles']):raise ValueError('Global hit source no longer matches reviewed static label')
    source_receipt(key,entry)
    valid=not any(item['detections'] for item in post) and not post_flame['hits']
    return {**receipt,'candidateState':'validated_candidate' if valid else 'review_required','reason':'visually_confirmed_small_adore_tag_word_flame_ink_removed','path':rel(path),'outputSha':sha(path.read_bytes()),'bytes':path.stat().st_size,'mime':'image/png' if is_png else 'image/webp','frames':1,'maskPath':rel(mask_path),'maskSha':sha(mask_path.read_bytes()),'validation':validation,'manualLabelQuad':plan['quad'],'sourceIdentification':{'globalAuditPassVersion':review['passVersion'],'groupIndex':plan['group'],'hitId':group['id'],'contextPath':rel(context),'contextSha':sha(context.read_bytes()),'confirmedBy':'root and independent visual inspection'},'preFlame':pre_flame,'postScans':post,'postFlame':post_flame,'closeProof':rel(folder/'before-after.png'),'nativeProof':rel(folder/'native-tag-before-after.png'),'fullProof':rel(folder/'before-after-full.jpg')}


def gif_regions(report):
    grouped=defaultdict(list)
    for detection in report["detections"]:
        if detection.get("frame") is None:continue
        x0,y0,x1,y1=detection["box"]
        # Native inspection confirms the flame is immediately above the word.
        # These are allowed label areas; the actual mask contains bright ink only.
        quad=[[x0-3,y0-6],[x1+3,y0-6],[x1+3,y1+3],[x0-3,y1+3]]
        grouped[int(detection["frame"])].append(quad)
    return grouped


def process_gif(key,entry,report,engines,flames):
    receipt=source_receipt(key,entry);folder=DEST/key;staged=folder/"staged";masks=folder/"masks";staged.mkdir(parents=True,exist_ok=True);masks.mkdir(parents=True,exist_ok=True)
    regions=gif_regions(report);audits=[];paths=[];durations=[];mask_paths=[];post_counts=0;flame_count=0
    tracking={}
    if key==OFFICE_GIF_KEY:
        track_path=DEST/'templates/office-word-track.json';track=json.loads(track_path.read_text('utf-8'))
        reference=json.loads((DEST/'templates/office-chair-word-reference.json').read_text('utf-8'))
        if reference['sourceSha']!=entry['sha256']:raise ValueError('Office tracking reference source changed')
        expected=list(range(3,9))+list(range(10,29))
        if sorted(item['frame'] for item in track)!=expected:raise ValueError('Office visible label frame set changed')
        for item in track:
            if item['score']<.60:raise ValueError('Office label tracking needs visual review')
            a,b,c,d=item['box'];regions[item['frame']]=[[[a-1,b-1],[c+1,b-1],[c+1,d+1],[a-1,d+1]]]
            tracking[item['frame']]=item
    with Image.open(ROOT/entry["path"]) as source:
        loop=int(source.info.get("loop",0));count=source.n_frames
        for frame_index in range(count):
            source.seek(frame_index);rgba=np.array(source.convert("RGBA"));duration=int(source.info.get("duration",0));durations.append(duration)
            quads=regions.get(frame_index,[]);mask=np.zeros(rgba.shape[:2],np.uint8);texture_audit=None
            if key in FABRIC_PLANS and frame_index==10:
                edited_rgb,mask,quads,texture_audit=texture_clone_print_field(rgba[:,:,:3],FABRIC_PLANS[key])
            else:
                for quad in quads:mask=cv2.bitwise_or(mask,lettering_mask(rgba[:,:,:3],quad))
                edited_rgb=retouch_ink(rgba[:,:,:3],mask)
            output=combine_opaque_mask(rgba,edited_rgb,mask)
            path=staged/f"{frame_index:03d}.png";Image.fromarray(output).save(path,"PNG",compress_level=4);paths.append(path)
            mask_path=masks/f"{frame_index:03d}.png";Image.fromarray(mask).save(mask_path);mask_paths.append(mask_path)
            validation=validate_rgba(rgba,np.array(Image.open(path).convert("RGBA")),mask)
            detections,post=engines.scan(output[:,:,:3].copy());post_counts+=len(detections)
            flame=flames.detect_regions(output[:,:,:3],quads);flame_count+=len(flame["hits"])
            audits.append({"frame":frame_index,"durationMs":duration,"maskPath":rel(mask_path),"maskSha":sha(mask_path.read_bytes()),"maskPixels":int(np.count_nonzero(mask)),"allowedLabelQuads":quads,"validation":validation,"postDetections":detections,"postScan":post,"postFlame":flame,"textureAudit":texture_audit,"wordTracking":tracking.get(frame_index)})
            if quads:
                points=np.array([point for quad in quads for point in quad]);minimum=points.min(axis=0);maximum=points.max(axis=0)
                proof_pair(Image.fromarray(rgba),Image.fromarray(output),[*minimum,*maximum],folder/f"frame-{frame_index:03d}-before-after.png",key+f" frame{frame_index}")
            print(json.dumps({"key":key[:16],"frame":frame_index+1,"frames":count,"postDetections":len(detections),"postFlameHits":len(flame["hits"])}),flush=True)
    output_path=folder/"candidate.webp";encode_staged_animation(paths,durations,loop,output_path)
    timeline=validate_staged_animation(paths,durations,loop,output_path)
    decoded_checks=[]
    with Image.open(ROOT/entry["path"]) as original,Image.open(output_path) as decoded:
        for index,mapping in enumerate(timeline["sourceToOutputMapping"]):
            original.seek(index);source_rgba=np.array(original.convert("RGBA"));mask=np.array(Image.open(mask_paths[index]).convert("L"))
            checks=[]
            for segment in mapping["outputSegments"]:
                decoded.seek(segment["outputFrame"]);checks.append(validate_rgba(source_rgba,np.array(decoded.convert("RGBA")),mask))
            decoded_checks.append({"sourceFrame":index,"checks":checks})
    source_receipt(key,entry)
    identification={}
    if key==OFFICE_GIF_KEY:
        proof=DEST/'templates/office-hit-localization.json'
        identification={'sourceEvidence':rel(proof),'sourceEvidenceSha':sha(proof.read_bytes()),'globalHits372And373':'false_positive_exact_boxes_with_independent_true_adore_label_in_adjacent_context','trackingManifest':rel(DEST/'templates/office-word-track.json'),'trackingManifestSha':sha((DEST/'templates/office-word-track.json').read_bytes()),'visuallyTrackedFrames':sorted(tracking)}
    return {**receipt,"candidateState":"validated_candidate" if post_counts==0 and flame_count==0 else "review_required","reason":"printed_tag_ink_and_flame_removed_framewise_timeline_preserved","path":rel(output_path),"outputSha":sha(output_path.read_bytes()),"bytes":output_path.stat().st_size,"mime":"image/webp","frames":timeline["outputFrameCount"],"sourceFrames":count,"timeline":timeline,"frameAudits":audits,"decodeChecks":decoded_checks,"postDetectionCount":post_counts,"postFlameHitCount":flame_count,"maskOutsideRgbMaxDelta":max(c["outsideMaskRgbMaxDelta"] for row in decoded_checks for c in row["checks"]),"alphaMaxDelta":max(c["alphaMaxDelta"] for row in decoded_checks for c in row["checks"]),'sourceIdentification':identification}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--kind",choices=["png","gif","fabric","small","all"],default="all");parser.add_argument("--key",action="append",help="Limit to explicitly listed special review key");args=parser.parse_args()
    actual=core.pipeline_version(ROOT/"artifacts/media-cleanup/templates")
    if actual!=FROZEN_PIPELINE:raise ValueError("Frozen cleanup pipeline changed; do not apply this review")
    cleanup=json.loads((ROOT/"artifacts/media-cleanup.json").read_text("utf-8"));download=json.loads((ROOT/"artifacts/media-download.json").read_text("utf-8"))
    if cleanup["pipelineVersion"]!=FROZEN_PIPELINE:raise ValueError("Cleanup manifest pipeline differs")
    fae_keys=[key for key in cleanup['images'] if key.startswith('fae311')]
    if len(fae_keys)!=1 or fae_keys[0] not in FABRIC_STILL_KEYS:raise ValueError('fae311 source key is not the uniquely reviewed asset')
    engines=core.Engines(ROOT/"artifacts/media-cleanup/templates");flames=FlameMatcher();records={}
    path=DEST/"candidates.json"
    if path.exists():records=json.loads(path.read_text("utf-8")).get("images",{})
    keys=(PNG_KEYS if args.kind in {"png","all"} else [])+(GIF_KEYS if args.kind in {"gif","all"} else [])+(FABRIC_STILL_KEYS if args.kind in {'fabric','all'} else [])+(list(SMALL_TAG_PLANS) if args.kind in {'small','all'} else [])
    if args.key:
        if any(key not in PNG_KEYS+GIF_KEYS+FABRIC_STILL_KEYS+list(SMALL_TAG_PLANS) for key in args.key):raise ValueError('Unknown special review key')
        keys=[key for key in keys if key in args.key]
    frozen={}
    for name in ['accepted-base-frozen.json','accepted-new-frozen.json']:
        snapshot=DEST/name
        if snapshot.exists():
            for row in json.loads(snapshot.read_text('utf-8'))['images']:frozen[row['urlSha']]=row
    for key in keys:
        if key in frozen:
            row=frozen[key]
            if sha((ROOT/row['path']).read_bytes())!=row['outputSha']:raise ValueError('Root-reviewed frozen candidate bytes changed')
            print(json.dumps({'key':key,'candidateState':'frozen_root_reviewed_bytes','outputSha':row['outputSha']}),flush=True)
            continue
        entry=download["images"][key];report=json.loads((ROOT/cleanup["images"][key]["report"]).read_text("utf-8"))
        try:
            if key in SMALL_TAG_PLANS:result=process_small_static(key,entry,engines)
            elif key in PNG_KEYS:result=process_png(key,entry,report,engines,flames)
            elif key in FABRIC_STILL_KEYS:result=process_fabric_still(key,entry,report,engines,flames)
            else:result=process_gif(key,entry,report,engines,flames)
        except Exception as error:
            result={**source_receipt(key,entry),"candidateState":"failed","error":f"{type(error).__name__}: {error}"}
        audit_path=DEST/key/"audit.json"
        result["report"]=rel(audit_path)
        core.atomic_json(audit_path,result)
        records[key]=result
        core.atomic_json(path,{"schemaVersion":1,"pipelineVersion":FROZEN_PIPELINE,"publicationReady":False,"globalIconPassRequired":True,"images":records})
        print(json.dumps({"key":key,"candidateState":result["candidateState"],"path":result.get("path"),"reason":result.get("reason"),"error":result.get("error")}),flush=True)


if __name__=="__main__":
    sys.stdout.reconfigure(encoding="utf-8");main()
