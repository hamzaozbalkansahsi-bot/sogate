import importlib.util
from pathlib import Path
import unittest
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('chair_repair',ROOT/'scripts/media-gaming-chair-repair.py')
chair=importlib.util.module_from_spec(spec);spec.loader.exec_module(chair)


class ChairRepairTests(unittest.TestCase):
    def test_full_word_fill_preserves_source_color_alpha_silhouette_and_red_dimension_arrow(self):
        source=np.full((220,220,4),255,np.uint8)
        source[20:200,20:200,:3]=[40,55,65]
        source[85:95,70:125,:3]=235
        source[60:125,96:99,:3]=[220,20,25]
        source[150:152,70:135,:3]=5
        original=source.copy()
        output,mask,_=chair.bounded_surface(source,[[65,80],[130,80],[130,101],[65,101]],True)
        self.assertTrue(np.array_equal(source,original))
        self.assertTrue(np.array_equal(output[mask==0],source[mask==0]))
        self.assertTrue(np.array_equal(output[:,:,3],source[:,:,3]))
        self.assertTrue(np.array_equal(output[60:125,96:99],source[60:125,96:99]))
        self.assertTrue(np.array_equal(output[150:152,70:135],source[150:152,70:135]))
        # No copied leather slit/black cut can appear in this original flat face.
        self.assertLessEqual(np.max(np.abs(output[86:94,72:90,:3].astype(int)-[40,55,65])),2)

    def test_drawing_word_fill_keeps_connected_original_outline_even_when_review_box_crosses_it(self):
        source=np.full((500,500,4),255,np.uint8)
        source[180:190,350:390,:3]=0
        source[60:450,409:412,:3]=0
        output,mask,_=chair.drawing_word(source,[[345,175],[415,175],[415,196],[345,196]])
        self.assertTrue(np.array_equal(output[60:450,409:412],source[60:450,409:412]))
        self.assertTrue(np.all(output[180:190,350:390,:3]==255))
        self.assertTrue(np.array_equal(output[mask==0],source[mask==0]))
        self.assertTrue(np.array_equal(output[:,:,3],source[:,:,3]))

    def test_pad_full_field_removes_pale_ink_and_preserves_connected_black_bevel(self):
        source=np.full((300,300,4),255,np.uint8)
        source[80:220,20:280,:3]=[75,74,76]
        source[170:174,20:280,:3]=[20,20,20]
        source[163:166,90:150,:3]=[93,82,84]
        source[160:164,155:190,:3]=[190,150,140]
        output,mask,_=chair.bounded_surface(source,[[85,157],[195,157],[195,176],[85,176]],pad_field=True)
        self.assertTrue(np.array_equal(output[170:174,20:280],source[170:174,20:280]))
        self.assertTrue(np.array_equal(output[mask==0],source[mask==0]))
        self.assertTrue(np.array_equal(output[:,:,3],source[:,:,3]))
        self.assertLess(np.max(output[162:167,90:190,:3]),90)


if __name__=='__main__':unittest.main()
