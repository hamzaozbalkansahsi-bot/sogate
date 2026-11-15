"""Narrow source-pixel restoration of reviewed physical sticker footprints."""
import cv2
import numpy as np

def merge_reviewed_patches(rgba, patches):
 """Merge exact mask pixels; this function grants no publication acceptance."""
 if not isinstance(rgba,np.ndarray) or rgba.dtype!=np.uint8 or rgba.ndim!=3 or rgba.shape[2]!=4:raise ValueError('uint8 RGBA source required')
 h,w=rgba.shape[:2];out=rgba.copy();union=np.zeros((h,w),bool)
 for field in patches:
  box=field['box'];mask=np.asarray(field['mask']);patch=np.asarray(field['rgba'])
  if len(box)!=4 or any(type(v)is not int for v in box):raise ValueError('invalid patch box')
  x,y,X,Y=box
  if not(0<=x<X<=w and 0<=y<Y<=h) or mask.shape!=(h,w) or mask.dtype!=bool or not mask.any():raise ValueError('invalid object mask or dimensions')
  if patch.dtype!=np.uint8 or patch.shape!=(Y-y,X-x,4):raise ValueError('patch dimensions differ from box')
  if np.any(mask&(rgba[:,:,3]==0)):raise ValueError('object mask includes invisible source pixels')
  local=mask[y:Y,x:X]
  if int(local.sum())!=int(mask.sum()):raise ValueError('object mask extends outside patch box')
  baseline=rgba[y:Y,x:X];dest=out[y:Y,x:X]
  if not np.array_equal(patch[~local],baseline[~local]):raise ValueError('patch changes pixels outside its real object mask')
  overlap=union[y:Y,x:X]&local
  if not np.array_equal(dest[overlap],patch[overlap]):raise ValueError('conflicting reviewed patch overlap')
  dest[local]=patch[local];union|=mask
 assert np.array_equal(out[~union],rgba[~union])
 return out,union


def restore_from_donor(rgba,mask,map_x,map_y,*,allow_alpha_repair=False,forbidden_mask=None):
 if not isinstance(rgba,np.ndarray)or rgba.dtype!=np.uint8 or rgba.ndim!=3 or rgba.shape[2]!=4:raise ValueError('uint8 RGBA source required')
 h,w=rgba.shape[:2];mask=np.asarray(mask);mx=np.asarray(map_x);my=np.asarray(map_y)
 if mask.shape!=(h,w)or mask.dtype!=bool or mx.shape!=(h,w)or my.shape!=(h,w):raise ValueError('source, mask and donor map dimensions differ')
 if not mask.any()or mask.mean()>.05:raise ValueError('empty or excessive object footprint')
 if np.any(mask&(rgba[:,:,3]==0)):raise ValueError('object mask includes invisible source pixels')
 forbidden=mask if forbidden_mask is None else np.asarray(forbidden_mask)
 if forbidden.shape!=mask.shape or forbidden.dtype!=bool:raise ValueError('invalid forbidden donor mask')
 forbidden=forbidden|mask;xs=mx[mask];ys=my[mask]
 if not np.all(np.isfinite(xs))or not np.all(np.isfinite(ys))or xs.min()<0 or ys.min()<0 or xs.max()>w-1 or ys.max()>h-1:raise ValueError('donor map is outside source bounds')
 xa=np.floor(xs).astype(int);ya=np.floor(ys).astype(int);xb=np.ceil(xs).astype(int);yb=np.ceil(ys).astype(int)
 for xx,yy in [(xa,ya),(xa,yb),(xb,ya),(xb,yb)]:
  if forbidden[yy,xx].any():raise ValueError('donor intersects another sticker or repair footprint')
 sampled=cv2.remap(rgba,mx.astype(np.float32),my.astype(np.float32),cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
 if allow_alpha_repair is not True and not np.array_equal(sampled[:,:,3][mask],rgba[:,:,3][mask]):raise ValueError('alpha restoration requires explicit object-footprint review')
 out=rgba.copy();out[mask]=sampled[mask]
 if np.array_equal(out[mask],rgba[mask]):raise ValueError('donor did not remove or change the observed sticker')
 assert np.array_equal(out[~mask],rgba[~mask])
 return out
