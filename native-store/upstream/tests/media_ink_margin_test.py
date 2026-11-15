import importlib.util
from pathlib import Path
import unittest
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('ink_margin',ROOT/'scripts/media-ink-margin.py');margin=importlib.util.module_from_spec(spec);spec.loader.exec_module(margin)


class MarginTests(unittest.TestCase):
    def test_residual_underline_removed_while_red_product_and_white_frame_stay_exact(self):
        source=np.full((130,260,3),(180,25,20),np.uint8)
        source[38:62,98:172]=235
        source[40:60,100:170]=(15,10,8)
        source[53:55,106:164]=(180,55,20)
        source[43:51,159:162]=245
        oldmask=np.zeros((130,260),np.uint8);oldmask[42:52,104:158]=255
        current=source.copy();current[oldmask!=0]=(15,10,8)
        detections=[{'box':[101,39,169,61]}]
        output,extra,audit=margin.remove_margin_ink(source,current,oldmask,detections,[[15,10,8]])
        self.assertGreater(np.count_nonzero(extra),50,audit)
        self.assertTrue(np.array_equal(output[source[:,:,0]==180],current[source[:,:,0]==180]) is False)
        outside=np.ones((130,260),bool);outside[40:60,100:170]=False
        self.assertTrue(np.array_equal(output[outside],current[outside]))
        self.assertTrue(np.all(output[53:55,110:160]==(15,10,8)))

    def test_empty_ink_margin_is_exact_noop(self):
        source=np.full((60,100,3),230,np.uint8);source[20:35,30:70]=15
        mask=np.zeros((60,100),np.uint8);mask[22:33,32:68]=255
        output,extra,_=margin.remove_margin_ink(source,source.copy(),mask,[{'box':[30,20,70,35]}],[[15,15,15]])
        self.assertFalse(np.any(extra));self.assertTrue(np.array_equal(output,source))

    def test_physical_white_frame_is_protected_when_dark_opening_is_below_it(self):
        source=np.full((120,240,3),230,np.uint8)
        source[40:58,100:170]=15
        source[58,100:170]=220
        source[59:95,100:170]=15
        source[54:56,105:165]=(180,45,10)
        mask=np.zeros((120,240),np.uint8);mask[42:53,103:167]=255
        current=source.copy();current[mask!=0]=15
        out,_,_=margin.remove_margin_ink(source,current,mask,[{'box':[100,39,170,61]}],[[15,15,15]])
        self.assertTrue(np.array_equal(out[58,100:170],source[58,100:170]))


if __name__=='__main__':unittest.main()
