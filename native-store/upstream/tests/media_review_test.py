import importlib.util
from pathlib import Path
import unittest
import numpy as np
import cv2

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('media_review',ROOT/'scripts/media-review.py')
review=importlib.util.module_from_spec(spec);spec.loader.exec_module(review)


class ReviewTests(unittest.TestCase):
    def test_quad_retouch_leaves_every_product_pixel_outside_the_plaque_exact(self):
        image=np.full((200,400,3),(90,130,110),np.uint8)
        image[70:100,50:310]=(160,105,60)
        image[72:96,220:300]=(15,10,8)
        image[77:89:3,227:294]=245
        image[91:93,225:295]=(180,55,18)
        quad=[[221,73],[298,73],[298,94],[221,94]]
        output,mask,tone=review.fill_quad(image,quad)
        self.assertTrue(np.array_equal(image[mask==0],output[mask==0]))
        self.assertTrue(np.array_equal(image[:70],output[:70]))
        self.assertLess(max(tone),30)
        self.assertEqual(np.count_nonzero(output[75:94,223:297]>100),0)

    def test_component_fit_stays_at_isolated_rotated_plaque_not_dark_opening(self):
        image=np.full((200,300,3),235,np.uint8)
        polygon=np.array([[100,60],[180,50],[184,78],[104,88]],np.int32)
        cv2.fillConvexPoly(image,polygon,(12,10,8))
        cv2.putText(image,'adore',(109,76),cv2.FONT_HERSHEY_SIMPLEX,.30,(245,245,245),1)
        image[105:170,105:185]=8
        detection={'box':[98,49,186,90],'polygon':polygon.tolist()}
        quad,meta=review.component_quad(image,detection)
        self.assertIsNotNone(quad,meta)
        self.assertLess(max(p[1] for p in quad),100)
        self.assertLess(max(p[0] for p in quad)-min(p[0] for p in quad),100)


if __name__=='__main__':unittest.main()
