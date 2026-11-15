import importlib.util
from pathlib import Path
import unittest
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('gaming_pad_pass',ROOT/'scripts/media-gaming-pad-pass.py')
pad=importlib.util.module_from_spec(spec);spec.loader.exec_module(pad)


class FlatPadPassTests(unittest.TestCase):
    def scene(self):
        source=np.full((160,220,4),(255,255,255,255),np.uint8)
        source[40:105,20:200,:3]=(70,70,76)
        source[100:112,20:200,:3]=15
        source[70:85,60:66,:3]=8
        source[80:85,45:58,:3]=210
        source[80:85,80:110,:3]=(90,66,75)
        source[:10,:,3]=230
        base=source.copy();base[80:85,45:58,:3]=(70,70,76)
        old=np.zeros(source.shape[:2],np.uint8);old[80:85,45:58]=255
        return source,base,old

    def test_contiguous_field_removes_low_pink_ink_and_keeps_phone_bevel_alpha(self):
        source,base,old=self.scene()
        output,mask,field,audit=pad.pad_field(source,base,old,[[40,76],[140,76],[140,100],[40,100]])
        self.assertTrue(np.array_equal(output[100:112,20:200],source[100:112,20:200]))
        self.assertTrue(np.array_equal(output[70:85,60:66],source[70:85,60:66]))
        self.assertTrue(np.array_equal(output[:,:,3],source[:,:,3]))
        self.assertLess(int((output[80:85,80:110,0].astype(int)-output[80:85,80:110,1].astype(int)).max()),6)
        self.assertTrue(audit['sourceGrainOnly'])
        self.assertTrue(np.array_equal(output[mask==0],source[mask==0]))

    def test_previously_verified_leg_is_not_reprocessed_by_pad_pass(self):
        source,base,old=self.scene()
        source[120:140,175:185,:3]=210;base[120:140,175:185,:3]=25;old[120:140,175:185]=255
        output,combined,field,audit=pad.pad_field(source,base,old,[[40,76],[140,76],[140,100],[40,100]])
        self.assertTrue(np.array_equal(output[120:140,175:185],base[120:140,175:185]))
        self.assertTrue(np.all(combined[120:140,175:185]!=0))
        self.assertFalse(np.any(field[120:140,175:185]))


if __name__=='__main__':unittest.main()
