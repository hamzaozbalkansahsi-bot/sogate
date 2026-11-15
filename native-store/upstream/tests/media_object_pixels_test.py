from pathlib import Path
import hashlib,importlib.util,unittest
import numpy as np
R=Path(__file__).resolve().parents[1];s=importlib.util.spec_from_file_location('pixels',R/'lib/media_object_pixels.py');p=importlib.util.module_from_spec(s);s.loader.exec_module(p)
sha=lambda b:hashlib.sha256(b).hexdigest()
class FootprintExceptionTest(unittest.TestCase):
 def setUp(self):
  self.a=np.full((10,10,4),255,np.uint8);self.b=self.a.copy();self.m=np.zeros((10,10),bool);self.m[0,0]=True;self.b[0,0]=[230,220,210,0];self.pin={'sourceSha256':'a'*64,'outputSha256':'b'*64,'maskSha256':'c'*64,'width':10,'height':10,'sourceRgbaSha256':sha(self.a.tobytes()),'outputRgbaSha256':sha(self.b.tobytes()),'maskPixels':1,'alphaChangedPixels':1}
 def test_only_exact_reviewed_source_output_mask_pixels_allow_alpha(self):
  self.assertTrue(p.verify_footprint_exception(self.pin,'a'*64,'b'*64,'c'*64,self.a,self.b,self.m))
  for key in ['sourceSha256','outputSha256','maskSha256','sourceRgbaSha256','outputRgbaSha256']:
   pin={**self.pin,key:'d'*64}
   with self.subTest(key=key),self.assertRaises(ValueError):p.verify_footprint_exception(pin,'a'*64,'b'*64,'c'*64,self.a,self.b,self.m)
 def test_alpha_or_rgb_outside_approved_mask_is_rejected(self):
  for channel in [0,3]:
   b=self.b.copy();b[9,9,channel]=0;pin={**self.pin,'outputRgbaSha256':sha(b.tobytes()),'alphaChangedPixels':int(np.count_nonzero(b[:,:,3]!=self.a[:,:,3]))}
   with self.subTest(channel=channel),self.assertRaisesRegex(ValueError,'outside'):p.verify_footprint_exception(pin,'a'*64,'b'*64,'c'*64,self.a,b,self.m)
 def test_large_mask_is_exact_count_bound_and_invisible_pixels_fail(self):
  m=np.ones((10,10),bool);pin={**self.pin,'maskPixels':100}
  self.assertTrue(p.verify_footprint_exception(pin,'a'*64,'b'*64,'c'*64,self.a,self.b,m))
  with self.assertRaises(ValueError):p.verify_footprint_exception(self.pin,'a'*64,'b'*64,'c'*64,self.a,self.b,m)
  a=self.a.copy();a[1,1,3]=0;pin={**pin,'sourceRgbaSha256':sha(a.tobytes()),'alphaChangedPixels':2}
  with self.assertRaisesRegex(ValueError,'invisible'):p.verify_footprint_exception(pin,'a'*64,'b'*64,'c'*64,a,self.b,m)
if __name__=='__main__':unittest.main()
