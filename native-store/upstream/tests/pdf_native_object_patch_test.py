from pathlib import Path
import importlib.util,io,unittest
import fitz,numpy as np
from PIL import Image,ImageCms
R=Path(__file__).resolve().parents[1]

class NativePdfObjectPatchTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  s=importlib.util.spec_from_file_location('native',R/'lib/pdf_native_object_patch.py');cls.mod=importlib.util.module_from_spec(s);s.loader.exec_module(cls.mod)
 def source(self,doc,xref):
  p=fitz.Pixmap(doc,xref);return np.frombuffer(p.samples,np.uint8).reshape(p.height,p.width,3).copy()
 def fixture(self):
  doc=fitz.open();page=doc.new_page(width=210,height=70);a=np.full((40,60,4),(188,170,150,255),np.uint8);a[:3,:,3]=0;a[10:15,40:48,:3]=12;ids=[]
  for j in range(2):
   q=a.copy();q[:,:,0]+=j;b=io.BytesIO();Image.fromarray(q).save(b,format='PNG');ids.append(page.insert_image(fitz.Rect(j*105,0,j*105+100,66),stream=b.getvalue()))
  sm=doc.extract_image(ids[0])['smask'];doc.xref_set_key(ids[1],'SMask',f'{sm} 0 R');return doc,ids,sm
 def test_shared_soft_mask_neighbor_and_all_outside_samples_stay_exact(self):
  d,ids,sm=self.fixture();before=self.source(d,ids[0]);a=np.frombuffer(fitz.Pixmap(d,sm).samples,np.uint8).reshape(40,60).copy();mask=np.zeros((40,60),bool);mask[10:15,40:48]=True;rgb=before.copy();rgb[mask]=[188,170,150];after_alpha=a.copy();after_alpha[12:15,45:48]=0;oldmask=d.xref_stream(sm);props={k:d.xref_get_key(ids[0],k)for k in ['Width','Height','ColorSpace','BitsPerComponent','Decode','Intent','Interpolate']}
  self.mod.patch_native_object(d,ids[0],rgb,mask,replacement_alpha=after_alpha,allow_alpha_repair=True);out=self.source(d,ids[0]);self.assertTrue(np.array_equal(out[~mask],before[~mask]));self.assertTrue(np.array_equal(out[mask],rgb[mask]));self.assertEqual(d.xref_stream(sm),oldmask);self.assertEqual(d.extract_image(ids[1])['smask'],sm);self.assertNotEqual(d.extract_image(ids[0])['smask'],sm);self.assertEqual({k:d.xref_get_key(ids[0],k)for k in props},props);actual=np.frombuffer(fitz.Pixmap(d,d.extract_image(ids[0])['smask']).samples,np.uint8).reshape(40,60);self.assertTrue(np.array_equal(actual,after_alpha))
 def test_alpha_permission_transparent_source_and_unsupported_geometry_fail(self):
  d,ids,sm=self.fixture();rgb=self.source(d,ids[0]);mask=np.zeros((40,60),bool);mask[10:15,40:48]=True;a=np.frombuffer(fitz.Pixmap(d,sm).samples,np.uint8).reshape(40,60).copy();a[mask]=0
  with self.assertRaisesRegex(ValueError,'alpha'):self.mod.patch_native_object(d,ids[0],rgb,mask,replacement_alpha=a)
  invisible=np.zeros_like(mask);invisible[:2,:3]=True
  with self.assertRaisesRegex(ValueError,'invisible'):self.mod.patch_native_object(d,ids[0],rgb,invisible)
  with self.assertRaises(ValueError):self.mod.patch_native_object(d,ids[0],rgb[:1],mask)
 def test_jpeg_is_decoded_once_then_patch_is_lossless_and_preserves_other_pixels(self):
  d=fitz.open();p=d.new_page();rng=np.random.default_rng(123);a=rng.integers(30,230,(50,80,3),dtype=np.uint8);buf=io.BytesIO();Image.fromarray(a).save(buf,format='JPEG',quality=92,subsampling=0);xr=p.insert_image(fitz.Rect(0,0,160,100),stream=buf.getvalue());before=self.source(d,xr);rgb=before.copy();m=np.zeros((50,80),bool);m[20:25,50:65]=True;rgb[m]=[180,160,140];props={k:d.xref_get_key(xr,k)for k in ['Width','Height','ColorSpace','BitsPerComponent','Decode','SMask']};self.mod.patch_native_object(d,xr,rgb,m);out=self.source(d,xr);self.assertTrue(np.array_equal(out[~m],before[~m]));self.assertTrue(np.array_equal(out[m],rgb[m]));self.assertEqual({k:d.xref_get_key(xr,k)for k in props},props)
 def test_original_icc_reference_and_profile_stream_are_preserved(self):
  d,ids,sm=self.fixture();icc=d.get_new_xref();profile=ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes();d.update_object(icc,'<< /N 3 >>');d.update_stream(icc,profile);cs=d.get_new_xref();d.update_object(cs,f'[/ICCBased {icc} 0 R]');d.xref_set_key(ids[0],'ColorSpace',f'{cs} 0 R');before=self.source(d,ids[0]);rgb=before.copy();m=np.zeros((40,60),bool);m[10:15,40:48]=True;rgb[m]=[188,170,150];self.mod.patch_native_object(d,ids[0],rgb,m);self.assertEqual(d.xref_get_key(ids[0],'ColorSpace'),('xref',f'{cs} 0 R'));self.assertEqual(d.xref_stream(icc),profile)
if __name__=='__main__':unittest.main()
