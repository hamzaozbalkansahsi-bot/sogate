"""Native RGB/soft-mask patching without layout or shared-image side effects."""
import hashlib
import fitz
import numpy as np

def _sha(body):return hashlib.sha256(body).hexdigest()

def patch_native_object(doc,xref,replacement_rgb,mask,*,replacement_alpha=None,allow_alpha_repair=False):
 if doc.xref_get_key(xref,'Subtype')!=('name','/Image'):raise ValueError('native image xref required')
 pix=fitz.Pixmap(doc,xref);w,h=pix.width,pix.height
 if not pix.colorspace or pix.colorspace.n!=3 or pix.alpha or doc.xref_get_key(xref,'BitsPerComponent')!=('int','8') or doc.xref_get_key(xref,'Decode')[1]!='null':raise ValueError('unsupported native RGB geometry or encoding')
 cs=doc.xref_get_key(xref,'ColorSpace');cs_text=doc.xref_object(int(cs[1].split()[0]))if cs[0]=='xref'else cs[1]
 if '/DeviceRGB'not in cs_text and '/ICCBased'not in cs_text:raise ValueError('unsupported native color space')
 before=np.frombuffer(pix.samples,np.uint8).reshape(h,w,3).copy();rgb=np.asarray(replacement_rgb);mask=np.asarray(mask)
 if rgb.dtype!=np.uint8 or rgb.shape!=before.shape or mask.dtype!=bool or mask.shape!=(h,w)or not mask.any():raise ValueError('native patch/mask dimensions or samples differ')
 sm=doc.extract_image(xref).get('smask',0);old_alpha=np.full((h,w),255,np.uint8)
 if sm:
  ap=fitz.Pixmap(doc,sm)
  if ap.n!=1 or (ap.width,ap.height)!=(w,h) or doc.xref_get_key(sm,'BitsPerComponent')[1]not in ['1','2','4','8']or doc.xref_get_key(sm,'Decode')[1]!='null':raise ValueError('unsupported native soft mask')
  old_alpha=np.frombuffer(ap.samples,np.uint8).reshape(h,w).copy()
 if np.any(mask&(old_alpha==0)):raise ValueError('object mask includes invisible native pixels')
 updated=before.copy();updated[mask]=rgb[mask];new_alpha=old_alpha.copy()
 if replacement_alpha is not None:
  alpha=np.asarray(replacement_alpha)
  if alpha.dtype!=np.uint8 or alpha.shape!=(h,w):raise ValueError('alpha dimensions or samples differ')
  if not np.array_equal(alpha[~mask],old_alpha[~mask]):raise ValueError('alpha outside object mask changed')
  if not np.array_equal(alpha,old_alpha) and allow_alpha_repair is not True:raise ValueError('alpha restoration needs explicit footprint approval')
  if not sm and not np.all(alpha==255):raise ValueError('cannot introduce a new native transparency channel')
  new_alpha[mask]=alpha[mask]
 alpha_changed=not np.array_equal(new_alpha,old_alpha)
 if np.array_equal(updated,before)and not alpha_changed:raise ValueError('selected patch makes no native correction')
 props=['Width','Height','ColorSpace','BitsPerComponent','Decode','Intent','Interpolate','Mask','Matte'];properties={k:doc.xref_get_key(xref,k)for k in props};original_sm_hash=_sha(doc.xref_stream(sm))if sm else None
 new_sm=sm
 if alpha_changed:
  # Clone even an apparently private mask: another image may reference it.
  new_sm=doc.get_new_xref();doc.update_object(new_sm,doc.xref_object(sm,compressed=False));doc.update_stream(new_sm,new_alpha.tobytes(),compress=True);doc.xref_set_key(new_sm,'BitsPerComponent','8');doc.xref_set_key(new_sm,'DecodeParms','null')
 doc.update_stream(xref,updated.tobytes(),compress=True);doc.xref_set_key(xref,'DecodeParms','null')
 if new_sm!=sm:doc.xref_set_key(xref,'SMask',f'{new_sm} 0 R')
 if properties!={k:doc.xref_get_key(xref,k)for k in props}:raise ValueError('native image semantic properties changed')
 actual_pix=fitz.Pixmap(doc,xref);actual=np.frombuffer(actual_pix.samples,np.uint8).reshape(h,w,3)
 if not np.array_equal(actual,updated):raise ValueError('native encoding changed RGB samples')
 if sm and _sha(doc.xref_stream(sm))!=original_sm_hash:raise ValueError('original shared soft mask changed')
 if not np.array_equal(updated[~mask],before[~mask])or not np.array_equal(new_alpha[~mask],old_alpha[~mask]):raise ValueError('native samples outside object footprint changed')
 return {'xref':xref,'width':w,'height':h,'beforeRgbSha256':_sha(before.tobytes()),'afterRgbSha256':_sha(updated.tobytes()),'beforeAlphaSha256':_sha(old_alpha.tobytes()),'afterAlphaSha256':_sha(new_alpha.tobytes()),'sourceSoftMaskXref':sm,'outputSoftMaskXref':new_sm,'originalSoftMaskUnchanged':True,'maskPixels':int(mask.sum()),'maskCoverage':float(mask.mean()),'alphaChangedPixels':int(np.count_nonzero(new_alpha!=old_alpha)),'rgbChangedPixels':int(np.count_nonzero(np.any(updated!=before,axis=2))),'outsideMaskRgbaExact':True,'propertiesPreserved':properties}
