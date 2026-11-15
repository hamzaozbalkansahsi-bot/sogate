import sys,unittest
from pathlib import Path
import fitz,numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from lib.cabinet_front_decoration import RULE_FILL,caption_rules,image_streams,remove_caption_rules,caption_rule_fragments,clean_fragment_pixels

class CaptionRules(unittest.TestCase):
 def test_only_identified_rules_are_removed_and_photo_alpha_and_text_are_preserved(self):
  doc=fitz.open();p=doc.new_page(width=300,height=300)
  photo=fitz.Pixmap(fitz.csRGB,fitz.IRect(0,0,20,20),False);photo.clear_with(170)
  p.insert_image(fitz.Rect(20,20,150,250),pixmap=photo)
  p.insert_text((170,60),'MODEL 740')
  p.draw_rect(fitz.Rect(160,35,230,37.835),color=None,fill=RULE_FILL)
  p.draw_rect(fitz.Rect(160,90,230,92.835),color=None,fill=RULE_FILL)
  p.draw_rect(fitz.Rect(160,120,230,123.5),color=None,fill=RULE_FILL)
  before=image_streams(p);assert len(caption_rules(p))==2
  old=p.get_pixmap();removed=remove_caption_rules(p);new=p.get_pixmap()
  self.assertEqual(len(removed),2);self.assertEqual(before,image_streams(p));self.assertIn('MODEL 740',p.get_text())
  a=np.frombuffer(old.samples,np.uint8).reshape(old.height,old.width,3);b=np.frombuffer(new.samples,np.uint8).reshape(new.height,new.width,3)
  changed=np.any(a!=b,axis=2);allowed=np.zeros(changed.shape,bool);allowed[34:39,159:232]=True;allowed[89:94,159:232]=True
  self.assertTrue(changed.any());self.assertFalse((changed&~allowed).any());self.assertEqual(len(p.get_drawings()),1)

 def test_no_matching_rule_is_a_noop(self):
  doc=fitz.open();p=doc.new_page();p.draw_rect(fitz.Rect(20,20,100,22.835),color=None,fill=(.7,.7,.7));before=p.get_pixmap().samples
  self.assertEqual(remove_caption_rules(p),[]);self.assertEqual(before,p.get_pixmap().samples)

 def test_raster_rule_fragment_is_removed_without_changing_product_image(self):
  doc=fitz.open();p=doc.new_page(width=300,height=300)
  photo=fitz.Pixmap(fitz.csRGB,fitz.IRect(0,0,20,20),False);photo.clear_with(170)
  x=p.insert_image(fitz.Rect(20,20,150,250),pixmap=photo)
  p.draw_rect(fitz.Rect(160,35,230,37.835),color=None,fill=RULE_FILL)
  fragment=fitz.Pixmap(fitz.csRGB,fitz.IRect(0,0,81,13),False);fragment.clear_with(228)
  p.insert_image(fitz.Rect(159.97,34.93,180,37.91),pixmap=fragment)
  source=doc.xref_stream(x);fragments=caption_rule_fragments(p);remove_caption_rules(p)
  self.assertEqual(source,doc.xref_stream(x));pix=p.get_pixmap()
  a=np.array(clean_fragment_pixels(pix,1,fragments))
  self.assertTrue(np.all(a[34:39,159:232]==255))

if __name__=='__main__':unittest.main()
