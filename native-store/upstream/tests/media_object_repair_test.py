from pathlib import Path
import importlib.util,unittest
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[1];spec=importlib.util.spec_from_file_location('repair',R/'lib/media_object_repair.py');repair=importlib.util.module_from_spec(spec);spec.loader.exec_module(repair)
class ObjectRepairTests(unittest.TestCase):
 def test_blank_magnet_is_removed_and_a_real_seam_is_restored_from_nearby_material(self):
  clean=np.full((40,70,4),(210,208,204,255),np.uint8);clean[20,:,0:3]=100;clean[21:,:,0:3]=190;bad=clean.copy();bad[16:24,45:58,:3]=15;mask=np.zeros((40,70),bool);mask[16:24,45:58]=True;y,x=np.indices(mask.shape,dtype=np.float32);out=repair.restore_from_donor(bad,mask,x-25,y);self.assertTrue(np.array_equal(out,clean));self.assertTrue(np.array_equal(out[~mask],bad[~mask]));self.assertGreater(int(out[16:20,45:58,:3].min()),180)
 def test_reported_mira_blank_plate_cannot_survive_a_real_source_pixel_repair(self):
  im=np.full((880,880,4),255,np.uint8);im[420:457,450:674,:3]=210;im[457:520,450:674,:3]=180;im[450:457,654:676,:3]=15;mask=np.zeros(im.shape[:2],bool);mask[447:460,651:679]=True;y,x=np.indices(mask.shape,dtype=np.float32);mx=x.copy();my=y.copy();mx[mask]=x[mask]-32;lower=mask&(y>=457);mx[lower]=x[lower];my[lower]=y[lower]+12;right=mask&(x>np.where(y<457,.2*y+584.35,673.9));mx[right]=x[right]+30;out=repair.restore_from_donor(im,mask,mx,my);self.assertGreater(int(out[450:457,654:676,:3].min()),120);self.assertTrue(np.array_equal(im[~mask],out[~mask]));self.assertTrue(np.array_equal(im[:,:,3],out[:,:,3]))
 def test_wrong_empty_or_donor_inside_sticker_is_rejected(self):
  a=np.full((20,30,4),255,np.uint8);mask=np.zeros((20,30),bool);mask[8:11,20:24]=True;y,x=np.indices(mask.shape,dtype=np.float32)
  for args in [(a,np.zeros_like(mask),x,y),(a,mask,x,y),(a,mask,x-50,y),(a,mask,x[:2],y)]:
   with self.subTest(shape=np.shape(args[2])):
    with self.assertRaises(ValueError):repair.restore_from_donor(*args)
 def test_alpha_can_only_be_restored_inside_explicitly_authorized_object_footprint(self):
  a=np.full((20,30,4),(180,180,180,255),np.uint8);a[:,:10,3]=0;a[:,:10,:3]=[13,37,59];mask=np.zeros((20,30),bool);mask[8:11,20:24]=True;y,x=np.indices(mask.shape,dtype=np.float32)
  with self.assertRaisesRegex(ValueError,'alpha'):repair.restore_from_donor(a,mask,x-16,y)
  out=repair.restore_from_donor(a,mask,x-16,y,allow_alpha_repair=True);self.assertTrue(np.array_equal(out[~mask],a[~mask]));self.assertTrue(np.all(out[mask,3]==0));self.assertTrue(np.array_equal(out[:,:10],a[:,:10]))
 def test_second_known_sticker_is_never_used_as_a_donor(self):
  a=np.full((20,40,4),255,np.uint8);mask=np.zeros((20,40),bool);mask[8:11,25:29]=True;forbidden=mask.copy();forbidden[8:11,10:14]=True;y,x=np.indices(mask.shape,dtype=np.float32)
  with self.assertRaisesRegex(ValueError,'donor'):repair.restore_from_donor(a,mask,x-15,y,forbidden_mask=forbidden)
if __name__=='__main__':unittest.main()
