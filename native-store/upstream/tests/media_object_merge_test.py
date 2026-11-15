from pathlib import Path
import importlib.util,unittest
import numpy as np
R=Path(__file__).resolve().parents[1];s=importlib.util.spec_from_file_location('repair',R/'lib/media_object_repair.py');repair=importlib.util.module_from_spec(s);s.loader.exec_module(repair)

class WholeObjectMergeTests(unittest.TestCase):
 def setUp(self):self.source=np.full((40,60,4),(190,170,150,255),np.uint8);self.source[:4,:,3]=0
 def field(self,box,color,mask_box=None):
  x,y,X,Y=box;m=np.zeros(self.source.shape[:2],bool);a,b,A,B=mask_box or box;m[b:B,a:A]=True;p=self.source[y:Y,x:X].copy();p[m[y:Y,x:X]]=color;return {'box':box,'mask':m,'rgba':p}
 def test_two_badges_survive_neither_and_unrelated_rgba_stays_exact(self):
  a=self.field([8,10,14,14],[180,160,140,255]);b=self.field([33,25,40,29],[175,155,135,255]);out,union=repair.merge_reviewed_patches(self.source,[a,b]);self.assertTrue(np.array_equal(out[a['mask']],[180,160,140,255]*np.ones((24,1),np.uint8)));self.assertTrue(np.array_equal(out[b['mask']],[175,155,135,255]*np.ones((28,1),np.uint8)));self.assertTrue(np.array_equal(out[~union],self.source[~union]));self.assertTrue(np.array_equal(out[:,:,3],self.source[:,:,3]))
 def test_conflicting_overlaps_cannot_undo_another_reviewed_body_repair(self):
  a=self.field([8,10,14,14],[180,160,140,255]);b=self.field([12,11,16,15],[200,180,160,255])
  with self.assertRaisesRegex(ValueError,'overlap'):repair.merge_reviewed_patches(self.source,[a,b])
 def test_identical_overlapping_pixels_merge_without_double_paint(self):
  a=self.field([8,10,14,14],[180,160,140,255]);b=self.field([12,11,16,15],[180,160,140,255]);out,union=repair.merge_reviewed_patches(self.source,[a,b]);self.assertTrue(np.all(out[union]==[180,160,140,255]))
 def test_cropped_rectangle_must_not_overwrite_pixels_outside_its_real_mask(self):
  a=self.field([8,10,17,17],[180,160,140,255],[10,12,14,14]);a['rgba'][0,0]=[5,6,7,255]
  with self.assertRaisesRegex(ValueError,'outside'):repair.merge_reviewed_patches(self.source,[a])
 def test_empty_wrong_sized_or_transparent_source_masks_fail(self):
  a=self.field([8,10,14,14],[180,160,140,255]);bad={**a,'mask':np.zeros((40,60),bool)}
  for p in [bad,{**a,'rgba':a['rgba'][:1]},self.field([8,2,14,4],[180,160,140,255])]:
   with self.subTest(shape=p['rgba'].shape):
    with self.assertRaises(ValueError):repair.merge_reviewed_patches(self.source,[p])
if __name__=='__main__':unittest.main()
