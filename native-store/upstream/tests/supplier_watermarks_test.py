import importlib.util,unittest
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[1]
class WatermarkTests(unittest.TestCase):
 def setUp(self):
  s=importlib.util.spec_from_file_location('supplier_watermarks',R/'lib/supplier_watermarks.py');self.assertTrue(Path(s.origin).exists(),'Watermark repair module missing');self.m=importlib.util.module_from_spec(s);s.loader.exec_module(self.m)
 def test_inverse_overlay_recovers_texture_and_keeps_every_other_pixel_exact(self):
  original=np.full((20,20,3),[195,150,100],np.uint8);original[5:10,:,0]=220
  transmission=np.ones((20,20,3),np.float32);mask=np.zeros((20,20),bool);mask[2:4,2:12]=True;transmission[mask]=.9
  source=np.rint(original*transmission).astype(np.uint8);out=self.m.reverse_multiply(source,transmission,mask)
  self.assertLessEqual(int(np.max(np.abs(out.astype(int)-original.astype(int)))),1)
  self.assertTrue(np.array_equal(out[~mask],source[~mask]))
 def test_large_or_dark_overlays_are_not_automatically_repaired(self):
  src=np.full((10,10,3),200,np.uint8);mask=np.ones((10,10),bool)
  with self.assertRaises(ValueError):self.m.reverse_multiply(src,np.full(src.shape,.9,np.float32),mask)
  mask[:]=False;mask[0,0]=True
  with self.assertRaises(ValueError):self.m.reverse_multiply(src,np.full(src.shape,.4,np.float32),mask)
 def test_white_background_residuals_do_not_change_warm_wood_or_unmasked_pixels(self):
  src=np.array([[[249,249,248],[250,220,180],[249,249,248]]],np.uint8);mask=np.array([[True,True,False]])
  out=self.m.clear_background_residual(src,mask)
  self.assertEqual(out[0,0].tolist(),[255,255,255]);self.assertEqual(out[0,1].tolist(),[250,220,180]);self.assertEqual(out[0,2].tolist(),[249,249,248])
 def test_overlay_alignment_recovers_a_shifted_scaled_stamp_field(self):
  import cv2
  reference=np.full((500,500,3),255,np.uint8)
  for y in range(70,500,110):
   for x in range(15,500,160):cv2.putText(reference,'ALKA',(x,y),cv2.FONT_HERSHEY_SIMPLEX,.8,(225,225,225),2,cv2.LINE_AA)
  transform=np.array([[.94,0,17],[0,.94,13]],np.float32)
  overlay=cv2.warpAffine(reference,transform,(500,500),borderValue=(255,255,255));original=np.full((500,500,3),255,np.uint8);original[150:350,160:330]=[205,155,105]
  source=np.rint(original.astype(float)*overlay/255).astype(np.uint8)
  result=self.m.align_overlay(source,reference)
  self.assertIsNotNone(result)
  self.assertGreaterEqual(result['inliers'],12)
  out=self.m.reverse_multiply(source,result['transmission'],result['mask'])
  self.assertLess(float(np.abs(out.astype(float)-original).mean()),2.5)
if __name__=='__main__':unittest.main()
