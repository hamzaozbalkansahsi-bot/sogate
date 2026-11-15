"""Remove only the catalogue's identified grey caption rules, never photo pixels."""
import hashlib,math
import fitz

RULE_FILL=(0.8939498066902161,0.8977340459823608,0.8938124775886536)

def caption_rules(page):
 result=[]
 for draw in page.get_drawings():
  rect=fitz.Rect(draw['rect']);fill=draw.get('fill');items=draw.get('items',[])
  if draw['type']!='f'or not fill or len(fill)!=3 or max(abs(a-b)for a,b in zip(fill,RULE_FILL))>.0001:continue
  if not (2.80<=rect.height<=2.87 and 15<=rect.width<=220):continue
  if len(items)!=1 or items[0][0]!='re':continue
  result.append(rect)
 return result

def image_streams(page):
 doc=page.parent;result=[]
 for row in page.get_images(full=True):
  xref,mask=row[:2]
  result.append((xref,hashlib.sha256(doc.xref_stream(xref)).hexdigest(),mask,hashlib.sha256(doc.xref_stream(mask)).hexdigest()if mask else None))
 return sorted(result)

def remove_caption_rules(page):
 rules=caption_rules(page)
 if not rules:return []
 # The PDF exporter also rasterised tiny overlapping fragments of some rules.
 # Only delete a thin image wholly inside the already identified caption rule.
 before=image_streams(page)
 for rect in rules:page.add_redact_annot(rect+(-.1,-.1,.1,.1),fill=False,cross_out=False)
 page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE,graphics=fitz.PDF_REDACT_LINE_ART_REMOVE_IF_COVERED,text=fitz.PDF_REDACT_TEXT_NONE)
 if image_streams(page)!=before:raise ValueError('Native product image or alpha stream changed')
 if caption_rules(page):raise ValueError('Caption rules were not fully removed')
 return [list(r)for r in rules]

def caption_rule_fragments(page):
 rules=caption_rules(page);result=[]
 for info in page.get_image_info(xrefs=True):
  box=fitz.Rect(info['bbox'])
  if info['xref'] and 2.7<=box.height<=3.2 and 1<=box.width<=160 and any((r+(-.3,-.3,.3,.3)).contains(box)for r in rules):result.append(box)
 return result

def clean_fragment_pixels(pix,scale,fragments):
 # Keep the native photo and alpha streams intact. The PDF's tiny raster rule
 # overlays are neutral grey only. Remove that ink in their verified bounds,
 # retaining all coloured/product pixels and all pixels elsewhere exactly.
 import numpy as np
 from PIL import Image
 pixels=np.frombuffer(pix.samples,np.uint8).reshape(pix.height,pix.width,3).copy()
 for rect in fragments:
  x0=max(0,math.floor(rect.x0*scale-pix.x)-1);y0=max(0,math.floor(rect.y0*scale-pix.y)-1)
  x1=min(pix.width,math.ceil(rect.x1*scale-pix.x)+1);y1=min(pix.height,math.ceil(rect.y1*scale-pix.y)+1)
  if x1<=x0 or y1<=y0:continue
  region=pixels[y0:y1,x0:x1];ink=(region.min(axis=2)>=225)&(region.max(axis=2)-region.min(axis=2)<=2)
  region[ink]=255
 return Image.fromarray(pixels)
