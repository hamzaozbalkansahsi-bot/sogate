from pathlib import Path
import importlib.util,unittest,copy
R=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('blog_compile',R/'scripts/compile-blog.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def article():
 return {'id':'home-001','slug':'oda-olcumu','category':'planning','title':'Bir odanın ölçüsünü kaydetmek','description':'Duvarlar, kapılar ve geçişler için uygulanabilir ölçü notları.','keywords':['oda ölçüsü','mobilya planı','geçiş alanı'],'intro':'Bir örnek plan hazırlayın.','sections':[{'heading':'Adım '+str(i),'paragraphs':[' '.join('örnek'+str(i)+'kelime'+str(j)for j in range(55))]}for i in range(4)],'checklist':['Duvarı ölçün.','Kapıyı açın.','Notu saklayın.'],'tool':'space','related':[],'sources':[{'url':'https://www.adoremobilya.com/blog','title':'Mobilya blogu'}],'visual':{'type':'plan','labels':['Duvar','Kapı','Geçiş']}}
class BlogCompilerTest(unittest.TestCase):
 def test_editorial_images_are_deterministic_across_fresh_font_loads(self):
  import time
  first=m.diagram(article());time.sleep(1.1);m.diagram_font.cache_clear();self.assertEqual(first,m.diagram(article()))
 def test_editor_approval_does_not_survive_a_body_change(self):
  import hashlib,json
  content={'title':'Denetlenmiş metin','sections':[{'heading':'Ölçü','paragraphs':['Örnekte kapıyı açın.']}]};receipt={'sourceSha256':'source','content':content,'reviewStatus':'editor-reviewed','checks':[],'editorialContentSha256':hashlib.sha256(json.dumps(content,ensure_ascii=False,sort_keys=True).encode()).hexdigest()}
  self.assertTrue(m.translation_approved(receipt,'source'));receipt['content']['sections'][0]['paragraphs'][0]='Onaydan sonra değiştirilmiş talimat.';self.assertFalse(m.translation_approved(receipt,'source'));self.assertFalse(m.translation_approved(receipt,'another-source'))
 def test_short_and_repeated_content_cannot_pass_quality_gate(self):
  a=article();m.validate_articles([a],minimum=1)
  a['sections'][0]['paragraphs']=['Kısa yazı.']
  with self.assertRaisesRegex(ValueError,'short'):m.validate_articles([a],minimum=1)
 def test_duplicate_identity_and_unsafe_source_are_rejected(self):
  a=article()
  with self.assertRaisesRegex(ValueError,'duplicate'):m.validate_articles([a,copy.deepcopy(a)],minimum=1)
  a['sources'][0]['url']='javascript:alert(1)'
  with self.assertRaisesRegex(ValueError,'source'):m.validate_articles([a],minimum=1)
 def test_unrelated_skeleton_with_only_title_change_is_rejected(self):
  a=article();b=copy.deepcopy(a);b.update(id='home-002',slug='diger-plan',title='Başka plan başlığı')
  with self.assertRaisesRegex(ValueError,'duplicate_content'):m.validate_articles([a,b],minimum=1)
 def test_svg_does_not_allow_markup_or_external_resources(self):
  a=article();a['visual']['labels']=['<script>alert(1)</script>','Geçiş','Duvar']
  svg=m.diagram(a);self.assertIn('&lt;script&gt;',svg);self.assertNotIn('<script>',svg);self.assertNotIn('http://',svg.replace('http://www.w3.org/2000/svg',''))
if __name__=='__main__':unittest.main()
