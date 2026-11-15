"""Select exact verified alternatives; preserve source colour/size identity privately."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,gzip,hashlib,importlib.util,json,re
R=Path(__file__).resolve().parents[1];E=R/'artifacts/paint-alternatives-20261112'
def module(n,f):
 s=importlib.util.spec_from_file_location(n,R/f);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
c=module('alt_catalogue','scripts/complete-paint-catalogue.py');c.E=E;v=module('alt_merchant_review','scripts/verify-alternative-merchants.py');m=c.m
def select():
 rows=json.loads((E/'verified-alternatives.json').read_bytes());registry=json.loads((E/'trusted-merchants.json').read_bytes());selected=[];held=[];duplicates=[];seen={}
 for p in sorted([p for p in rows if not p.get('held')],key=lambda p:(-p['merchant']['score'],p['merchant']['id'],int(p['sourceProductId']))):
  p['finish']=c.finish(p);pid=p['sourceProductId'];p['displayColor']=re.sub(r'\b\d+(?:[.,]\d+)?\s*(?:ml|lt|litre|l)\b','',p['color'],flags=re.I).strip()
  if pid=='321243594':
   p['package']='120 ml';p['finish']='silk';p['manualReview']={'kind':'package_label','sourceImageSha256':'c7bde4f23a64231fdf14d7dd890e3dfd96204a24d80d87242001e4bbd0482706','declaredPackage':'120 ml','manufacturerUrl':'https://www.filliboya.com/uploads/TDS_AFILLI_MS_SILK.PDF'}
  if pid=='847549960':
   p['family']='acrylic-kit';p['manualReview']={'kind':'bundle_contents','components':['1 L Bianca Stella acrylic paint','one silk brush','one velour roller','one tray'],'sourceImageUrl':p['images'][0],'sourceDocumentSha256':p['sourceEvidence']['sha256']}
  if pid=='1211564095':
   held.append(c.review_record(p,'gallery_and_selected_package_conflict',reasonTr='Seçili miktar 250 ml; galeri hem 250 ml hem 120 ml ambalaj gösteriyor.'));continue
  code=re.search(r'Andezit\s*(\d+)',p['title'],re.I)
  if code and not re.search(r'Andezit\s*'+code[1]+r'\b',p['displayColor'],re.I):
   held.append(c.review_record(p,'title_and_selected_colour_conflict'));continue
  reason=m.offer_review(p)
  if reason=='bundle_contents_require_review'and pid=='847549960':reason=None
  if reason:held.append(c.review_record(p,reason));continue
  if p['family']not in c.prep.FAMILIES:held.append(c.review_record(p,'unsupported_family_review'));continue
  assert p['merchant']['authorized']or v.independent(p['merchant'],p['brand'],registry)
  view={**p,'color':p['displayColor']};key=c.signature(view)
  if key in seen:duplicates.append(c.review_record(p,'duplicate_variant',duplicateOf=seen[key]));continue
  seen[key]=pid;selected.append(p)
 for p in rows:
  if p.get('held'):held.append(c.review_record({'sourceProductId':p['sourceProductId']},p['reason']))
 old=json.loads((R/'artifacts/paint-resolution-20261112/review-list.json').read_bytes());lookup={p['sourceProductId']:p for p in old};held=[{**lookup.get(h['sourceProductId'],{}),**{k:v for k,v in h.items()if v not in [None,'']}}for h in held]
 known={p['sourceProductId']for p in selected+held+duplicates}
 held += [p for p in old if p['sourceProductId']not in known]
 replacements={'789301423':('847549960','Aynı Kırık Beyaz 1 L boya, İpek fırça, kadife rulo ve tava içeren satıcı seti.'),'258202753':('1218082121','Çelişkili 3 L seçimi yerine bağımsız doğrulanan Siyah 2,5 L ilanı.')}
 decisions=[{'sourceProductId':p['sourceProductId'],'status':'new_verified','replacementId':p['sourceProductId']}for p in selected]
 decisions += [{'sourceProductId':p['sourceProductId'],'status':'covered','replacementId':p['duplicateOf'],'reason':p['reasonTr']}for p in duplicates]
 for pid,(target,why)in replacements.items():
  assert target in {p['sourceProductId']for p in selected}
  decisions.append({'sourceProductId':pid,'status':'covered','replacementId':target,'reason':why})
 held=[p for p in held if p['sourceProductId']not in replacements]
 for h in held:
  if h['reason']=='no_verified_alternative_merchant':h['reasonTr']='En az 9 puanlı, platform rozeti veya üretici bayi kaydıyla kimliği doğrulanan aktif alternatif satıcı bulunamadı.'
 decisions += [{'sourceProductId':p['sourceProductId'],'status':'held','reason':p['reason'],'sourceUrl':p['sourceUrl']}for p in held]
 assert len(decisions)==len(old)==107 and {p['sourceProductId']for p in decisions}==set(lookup)
 c.save(E/'decisions.json',decisions);c.save(E/'selected-offers.json',{'products':selected,'held':held,'checkedAt':datetime.now(timezone.utc).isoformat()});c.save(E/'offers.json',{'products':selected,'held':[h for h in held if h['group']=='source']});c.save(E/'review-list.json',held);c.save(E/'duplicate-alternatives.json',duplicates)
 print(json.dumps({'selected':len(selected),'held':len(held),'duplicates':len(duplicates),'byFamily':{f:sum(p['family']==f for p in selected)for f in {p['family']for p in selected}}}))
def prepare():
 proof=json.loads((E/'base.json').read_bytes());rows=json.loads((E/'selected-offers.json').read_bytes())['products'];registry=json.loads((E/'trusted-merchants.json').read_bytes())
 for p in rows:
  body=gzip.decompress((R/p['sourceEvidence']['file']).read_bytes());assert hashlib.sha256(body).hexdigest()==p['sourceEvidence']['sha256'];fresh=m.parse(body,p['sourceUrl'],p['merchant']['id']);assert all(fresh[k]==p[k]for k in ['sourceProductId','sourceCode','title','color','itemNumber','barcode','sourcePriceMinor','salePriceMinor','images'])
  assert fresh['merchant']['authorized']or v.independent(fresh['merchant'],fresh['brand'],registry)
  if not fresh['merchant']['authorized']:
   full=m.states(body)['__envoy__SHARED_PROPS']['product']['merchantListing']['merchant'];e=registry[str(full['id'])];assert all(full[k]==e[k]for k in ['officialName','cityName','address']);d=e['manufacturerEvidence'];assert hashlib.sha256((R/d['file']).read_bytes()).hexdigest()==d['sha256']
  assert p['salePriceMinor']==m.markup(p['sourcePriceMinor'])
  if p['sourceProductId']=='321243594':
   image=next(row for row in json.loads((E/'media-index.json').read_bytes())if row['url']==fresh['images'][0]);assert image['sha256']==p['manualReview']['sourceImageSha256'] and hashlib.sha256((R/image['file']).read_bytes()).hexdigest()==image['sha256'] and p['package']=='120 ml' and fresh['selectedSize']==''
  if p['sourceProductId']=='847549960':assert p['manualReview']['sourceImageUrl']==fresh['images'][0] and p['package']==fresh['package']=='1 L'
  reason=m.offer_review(p)
  if reason:assert p['sourceProductId']=='847549960'and reason=='bundle_contents_require_review'and p['manualReview']['sourceDocumentSha256']==p['sourceEvidence']['sha256']
 c.prep.O=E;c.prep.B=R/proof['releases'][0];c.prep.main();data=json.loads((E/'catalogue-prepared.json').read_bytes())
 for p in data['products']:
  if p['id']=='paint-ty-201093804':p['coverIndex']=1
  if p['paintUse']['family']=='afilli':
   p['paintUse']['officialEvidence']='https://www.filliboya.com/uploads/TDS_AFILLI_MS_SILK.PDF';p['paintUse']['excludeHorizontal']=True
   finish=c.prep.loc('İpeksi','Silk','Шелковистый','حريري','Seidenglanz','İpək','Жібек','Ýüpek','Ipak','Жибек','ابریشمی')
   for spec in p['specs']:
    if spec['label']['en']=='Finish':spec['value']=finish
   for lang in c.prep.LANGS:p['variantLabel'][lang]=' · '.join([p['variantColor'][lang],next(s['value'][lang]for s in p['specs']if s['label']['en']=='Package size'),finish[lang]])
   warning=c.prep.loc('Lake yüzeylerde, yatay ve ıslak zeminlerde veya gıda ile temas eden yüzeylerde kullanmayın.','Do not apply to lacquered surfaces, horizontal or wet floors, or food-contact surfaces.','Не наносить на лакированные поверхности, горизонтальные или мокрые полы и поверхности, контактирующие с пищей.','لا يُستخدم على الأسطح المطلية باللاكيه أو الأرضيات الأفقية والرطبة أو الأسطح الملامسة للطعام.','Nicht auf lackierten Oberflächen, horizontalen oder nassen Böden und Flächen mit Lebensmittelkontakt anwenden.','Laklı səthlərdə, üfüqi və yaş döşəmələrdə, qida ilə təmas edən səthlərdə istifadə etməyin.','Лакталған беттерге, көлденең не ылғал едендерге және тағаммен жанасатын беттерге қолданбаңыз.','Lakly ýüzlerde, kese we çyg pollarda ýa-da iýmit bilen galtaşýan ýüzlerde ulanmaň.','Laklangan sirtlarda, gorizontal yoki nam pollarda va oziq-ovqat tegadigan yuzalarda ishlatmang.','Лакталган беттерге, туурасынан жайгашкан же нымдуу полдорго жана тамак-аш тийген беттерге колдонбоңуз.','روی سطوح لاکی، کف‌های افقی یا مرطوب و سطوح در تماس با مواد غذایی استفاده نشود.')
   for lang in c.prep.LANGS:data['descriptions'][p['id']][lang]+='\n\n'+warning[lang]
  if p['paintUse']['family']=='acrylic-kit':
   for spec in p['specs']:
    if spec['label']['en']=='Sales unit':spec['value']=c.prep.loc('set','set','комплект','طقم','Set','dəst','жиынтық','toplum','to‘plam','топтом','ست')
   next(s for s in data['seed']if s['id']==p['id'])['salesUnit']='Set'
 c.save(E/'catalogue-prepared.json',data)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('phase',choices=['select','media','prepare']);args=a.parse_args();c.media()if args.phase=='media'else globals()[args.phase]()
