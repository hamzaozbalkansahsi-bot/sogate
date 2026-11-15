import importlib.util
from pathlib import Path
import tempfile
import unittest

import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('media_review_special',ROOT/'scripts/media-review-special.py')
review=importlib.util.module_from_spec(spec);spec.loader.exec_module(review)
combined_spec=importlib.util.spec_from_file_location('media_review_combined',ROOT/'scripts/media-review-combined.py')
combined=importlib.util.module_from_spec(combined_spec);combined_spec.loader.exec_module(combined)


class SpecialMediaReviewTests(unittest.TestCase):
    def test_rgba_edit_preserves_all_alpha_and_unmasked_rgb_after_png_decode(self):
        rgba=np.full((30,40,4),(90,100,110,255),np.uint8)
        rgba[:5,:,3]=230
        rgb=rgba[:,:,:3].copy();mask=np.zeros((30,40),np.uint8);mask[10:15,15:25]=255;rgb[mask!=0]=20
        output=review.combine_opaque_mask(rgba,rgb,mask)
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'output.png';Image.fromarray(output).save(path)
            decoded=np.array(Image.open(path).convert('RGBA'))
            audit=review.validate_rgba(rgba,decoded,mask)
        self.assertEqual(audit['alphaMaxDelta'],0)
        self.assertEqual(audit['outsideMaskRgbMaxDelta'],0)
        self.assertTrue(np.array_equal(decoded[:,:,3],rgba[:,:,3]))

    def test_nonopaque_lettering_mask_is_not_silently_edited(self):
        rgba=np.full((20,20,4),(40,40,40,255),np.uint8);rgba[5,5,3]=240
        mask=np.zeros((20,20),np.uint8);mask[5:8,5:8]=255
        with self.assertRaisesRegex(ValueError,'opaque'):
            review.combine_opaque_mask(rgba,rgba[:,:,:3].copy(),mask)

    def test_unmasked_decode_changes_are_rejected(self):
        rgba=np.full((20,20,4),(40,40,40,255),np.uint8);edited=rgba.copy();edited[5,5,0]=41
        with self.assertRaisesRegex(ValueError,'Outside'):
            review.validate_rgba(rgba,edited,np.zeros((20,20),np.uint8))

    def test_animated_lossless_encoder_preserves_timeline_when_identical_frames_merge(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);paths=[]
            for i,color in enumerate(['red','red','green']):
                path=root/f'{i}.png';Image.new('RGBA',(40,30),color).save(path);paths.append(path)
            output=root/'movie.webp';review.encode_staged_animation(paths,[100,200,300],0,output)
            result=review.validate_staged_animation(paths,[100,200,300],0,output)
            self.assertEqual(result['totalDurationMs'],600)
            self.assertEqual(len(result['sourceToOutputMapping']),3)
            self.assertEqual(result['rgbMaxDelta'],0)
            self.assertEqual(result['alphaMaxDelta'],0)

    def test_lettering_mask_does_not_include_dark_fabric_outside_allowed_quad(self):
        rgb=np.full((80,80,3),60,np.uint8);rgb[25:30,30:42]=225;rgb[35:38,35:40]=(225,65,15)
        quad=[[28,22],[45,22],[45,42],[28,42]]
        mask=review.lettering_mask(rgb,quad)
        self.assertTrue(np.all(mask[25:30,30:42]!=0))
        self.assertEqual(int(mask[10,10]),0)
        self.assertEqual(int(mask[50,50]),0)

    def test_low_brightness_red_ink_is_removed_without_leaving_red_smear(self):
        rgb=np.full((80,80,3),42,np.uint8);rgb[25:45,35:40]=(85,12,8);rgb[27:33,37:41]=200
        mask=review.lettering_mask(rgb,[[30,22],[45,22],[45,48],[30,48]])
        output=review.retouch_ink(rgb,mask)
        self.assertTrue(np.array_equal(output[mask==0],rgb[mask==0]))
        self.assertLess(int((output[:,:,0].astype(int)-output[:,:,1].astype(int))[mask!=0].max()),10)

    def test_isolated_plaque_mask_keeps_the_surrounding_light_material_exact(self):
        rgb=np.full((90,130,3),(190,170,140),np.uint8)
        rgb[25:50,30:100]=(45,44,43)
        rgb[30:45,37:95:6]=220
        det={'box':[31,25,100,50]}
        output,mask,info=review.isolated_light_surround_plaque(rgb,[det])
        physical=np.zeros((90,130),bool);physical[25:50,30:100]=True
        self.assertTrue(info['accepted'])
        self.assertFalse(np.any((mask!=0)&~physical))
        self.assertTrue(np.array_equal(output[~physical],rgb[~physical]))

    def test_contiguous_woven_print_field_loses_letters_but_keeps_real_texture(self):
        y,x=np.indices((140,90));base=(25+((x+y)%4)*15).astype(np.uint8)
        rgb=np.repeat(base[:,:,None],3,axis=2)
        rgb[30:38,25:54]=225;rgb[52:60,26:56]=225;rgb[20:112,12:15]=(210,85,7)
        plan={'quad':[[8,8],[76,8],[76,128],[8,128]],'size':[69,121],'fieldLeft':12,'fieldTop':8,'fieldBottomMargin':5}
        output,mask,quads,audit=review.texture_clone_print_field(rgb,plan)
        self.assertTrue(np.array_equal(output[mask==0],rgb[mask==0]))
        self.assertLess(int(output[31:37,26:53].max()),155)
        self.assertGreater(float(output[mask!=0].std()),8)
        self.assertTrue(audit['contiguousPrintField'])

    def test_surface_print_replacement_keeps_original_geometry_and_source_grain(self):
        y,x=np.indices((160,220));surface=(70+x*.03+y*.05+((x+y)%3-1)*2).astype(np.uint8)
        rgb=np.repeat(surface[:,:,None],3,axis=2);rgb[55:65,70:135]=15
        output,mask,audit=review.source_surface_print_retouch(rgb,[[60,45],[145,45],[145,75],[60,75]],donor_offset=35)
        self.assertTrue(np.array_equal(output[mask==0],rgb[mask==0]))
        self.assertGreater(float(output[56:64,75:130].std()),.5)
        self.assertGreater(int(output[56:64,75:130].min()),55)
        self.assertTrue(audit['sourceGrainOnly'])

    def test_colored_print_is_not_blended_back_at_the_mask_feather(self):
        rgb=np.full((140,180,3),50,np.uint8);rgb[52:65,53:58]=(210,40,9)
        output,mask,audit=review.source_surface_print_retouch(rgb,[[50,45],[100,45],[100,80],[50,80]],donor_offset=35,ring_radius=7,colored_print=True)
        self.assertLess(int((output[52:65,53:58,0].astype(int)-output[52:65,53:58,1].astype(int)).max()),5)
        self.assertTrue(audit['coloredInkNeverFeatheredBack'])

    def test_oblique_print_removal_preserves_white_background_and_unmasked_geometry(self):
        rgb=np.full((180,200,3),255,np.uint8);rgb[:,30:170]=130;rgb[55:65,85:115]=15
        output,mask,audit=combined.vertical_surface_retouch(rgb,[[78,47],[122,47],[122,77],[78,77]])
        self.assertTrue(np.array_equal(output[mask==0],rgb[mask==0]))
        self.assertTrue(np.array_equal(output[:,:30],rgb[:,:30]))
        self.assertGreater(int(output[55:65,85:115].min()),100)

    def test_joined_gaming_word_is_checked_even_when_main_detection_list_is_empty(self):
        rows=combined.joined_brand_rows({'ocr':[{'text':'sdoregaming'},{'text':'adorggsming'},{'text':'RYZE'},{'text':'ProX'}]})
        self.assertEqual(len(rows),2)

    def test_explicit_vertical_translation_matches_original_donor_offset_api(self):
        rgb=np.full((140,180,3),70,np.uint8);rgb[45:55,60:80]=15;quad=[[50,35],[95,35],[95,65],[50,65]]
        old,mask,_=review.source_surface_print_retouch(rgb,quad,donor_offset=30)
        explicit,other,audit=review.source_surface_print_retouch(rgb,quad,donor_translation=[0,30])
        self.assertTrue(np.array_equal(old,explicit));self.assertTrue(np.array_equal(mask,other));self.assertEqual(audit['donorTranslation'],[0,30])
        with self.assertRaisesRegex(ValueError,'canvas'):
            review.source_surface_print_retouch(rgb,quad,donor_translation=[-100,-100])


if __name__=='__main__':unittest.main()
