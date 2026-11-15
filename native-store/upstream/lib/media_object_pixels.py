"""Narrow native-pixel exceptions for individually reviewed whole-object footprints."""
import hashlib
import numpy as np

def verify_footprint_exception(pin,source_sha,output_sha,mask_sha,source,output,mask):
 if any(pin.get(k)!=v for k,v in [('sourceSha256',source_sha),('outputSha256',output_sha),('maskSha256',mask_sha)]):raise ValueError('footprint source/output/mask hash mismatch')
 if source.shape!=output.shape or source.dtype!=np.uint8 or output.dtype!=np.uint8 or source.ndim!=3 or source.shape[2]!=4 or mask.dtype!=bool or mask.shape!=source.shape[:2]:raise ValueError('footprint native geometry differs')
 if(pin.get('width'),pin.get('height'))!=(source.shape[1],source.shape[0])or pin.get('maskPixels')!=int(mask.sum()):raise ValueError('footprint dimensions or mask count differ')
 if not mask.any()or np.any(mask&(source[:,:,3]==0)):raise ValueError('footprint includes empty or invisible source pixels')
 if not np.array_equal(source[~mask],output[~mask]):raise ValueError('RGBA outside approved object footprint changed')
 if pin.get('alphaChangedPixels')!=int(np.count_nonzero(source[:,:,3]!=output[:,:,3])):raise ValueError('footprint alpha count differs')
 for name,value in [('sourceRgbaSha256',source),('outputRgbaSha256',output)]:
  if pin.get(name)!=hashlib.sha256(value.tobytes()).hexdigest():raise ValueError('footprint decoded pixel hash differs')
 return True
