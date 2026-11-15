"""Build private admin seed, completeness report and browsable download catalogue."""
from pathlib import Path
import argparse,collections,csv,hashlib,html,importlib.util,json
R=Path(__file__).resolve().parents[1];O=R/'artifacts/supplier-expansion'
spec=importlib.util.spec_from_file_location('wood',R/'scripts/import-wood-suppliers.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def load():
 complete=O/'all-catalog.json'
 if complete.exists():
  d=json.loads(complete.read_bytes())
  if d['counts']=={'alka':644,'altinis':1790}and not d['errors']:
   products=d['products'];expected={'alka':644,'altinis':1790};errors=[]
   variants=json.loads((O/'alka-variants.json').read_bytes());products+=variants['products'];expected['alka_variations']=variants['expected'];errors+=variants['errors']
   return products,errors,expected
 products=[];errors=[];expected={}
 for file in (O/'alka-api').glob('*.json'):
  if file.name.endswith('.receipt.json'):continue
  rows=json.loads(file.read_bytes())
  if isinstance(rows,list):
   evidence=json.loads(file.with_suffix('.receipt.json').read_bytes())
   for row in rows:p=m.parse_alka(row);p['evidence']=evidence;products.append(p)
 expected['alka']=644
 for file in (O/'altinis-pages').glob('*.html'):
  evidence=json.loads(file.with_suffix('.receipt.json').read_bytes())
  try:p=m.parse_altinis(m.read_archive(file),evidence['url']);p['evidence']=evidence;products.append(p)
  except Exception as e:errors.append({'url':evidence['url'],'error':str(e)})
 expected['altinis']=len(set(json.loads((O/'altinis-urls.json').read_bytes())))
 if (O/'alka-variants.json').exists():
  variants=json.loads((O/'alka-variants.json').read_bytes());products+=variants['products'];errors+=variants['errors'];expected['alka_variations']=variants['expected']
 products=list({p['id']:p for p in products}.values());return products,errors,expected
def group(p):
 v=(' '.join(p['categories'])+' '+p['title']).casefold()
 for pattern,name in [('hazeran|hasır','Hasır ve hazeran'),('çıta|profil','Ahşap ve MDF çıtalar'),('aplik|göbek|rozet|oyma|taç','Dekoratif ahşap motifler'),('ayak|torna','Mobilya ayakları ve torna'),('seperat|separat|paravan','Seperatör ve paravan'),('merdiven|küpeşte|topuz|babası','Merdiven malzemeleri'),('masa|sehpa','Masa ve sehpalar'),('sandalye|tabure','Sandalye ve tabureler'),('kulp|kavela|sopa|aksesuar','Mobilya aksesuarları'),('yatak|baza|komodin|şifonyer','Yatak odası mobilyaları'),('ayna','Aynalar'),('koltuk|berjer|oturma','Oturma grupları')]:
  import re
  if re.search(pattern,v):return name
 return 'Tamamlayıcı mobilya ve malzemeler'
def display_price(p):
 if p.get('salePriceMinor'):
  return f"{p['salePriceMinor']/100:,.2f}".replace(',','@').replace('.',',').replace('@','.')+' TL'
 return {'quote_required':'Fiyat için teklif alın','variant_selection_required':'Seçenek fiyatı doğrulanmalı'}.get(p['priceStatus'],'Fiyat doğrulanmalı')
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--pdf',action='store_true');args=parser.parse_args();products,errors,expected=load()
 visibleFile=O/'alka-visible-prices.json'
 if visibleFile.exists():
  offers={p['productId']:p for p in json.loads(visibleFile.read_bytes())['products']}
  for p in products:
   v=offers.get(p['id'])
   if not v:continue
   p['visiblePriceEvidence']=v.get('evidence');p['priceStatus']=v['status'];p['sourcePriceMinor']=v.get('sourcePriceMinor');p['salePriceMinor']=None
   if v.get('salesUnit'):p['salesUnit']=v['salesUnit']
   if v['status']=='verified'and not p['variants']:p['salePriceMinor']=m.markup(v['sourcePriceMinor'],20)
   elif p['variants']and v['status']=='verified':p['priceStatus']='variant_selection_required'
 for p in products:p['merchantCategory']=group(p)
 supplierDefs=[{'id':'adore','title':'Adore Mobilya','url':'https://www.adoremobilya.com','markupPercent':30,'priceListRequired':False},{'id':'alka','title':'Alka Ahşap','url':'https://alkaahsap.com','markupPercent':20,'priceListRequired':False},{'id':'altinis','title':'Altın İş Ağaç','url':'https://www.altinisagac.com','markupPercent':20,'priceListRequired':False},{'id':'goktas','title':'Göktaş Kapak','url':None,'priceListRequired':True},{'id':'ndecor','title':'NDECOR kapı kataloğu','url':None,'priceListRequired':True}]
 source=json.loads((R/'data/catalog-source.json').read_bytes());identities={str(p['id']):p for p in json.loads((R/'data/catalog-identities.json').read_bytes())['products']};prices={p['productId']:p for p in json.loads((R/'data/catalog-prices.json').read_bytes())['products']}
 mapped=[]
 for p in source['products']:
  identity=identities.get(str(p['id']),{});price=prices[str(p['id'])]
  mapped.append({'id':str(p['id']),'code':identity.get('code',p['code']),'title':identity.get('name',p['title']),'supplierId':'adore','sourceCode':p['code'],'sourceUrl':p.get('sourceUrl'),'salesUnit':'Adet','sourcePriceMinor':price.get('sourcePriceMinor')if price['status']=='verified'else None,'salePriceMinor':price.get('salePriceMinor')if price['status']=='verified'else None,'priceStatus':price['status'],'markupPercent':30,'priceFetchedAt':price.get('fetchedAt')})
 for file,supplier in [('cabinet-fronts.json','goktas'),('door-catalog.json','ndecor')]:
  dataset=json.loads((R/'data'/file).read_bytes())
  for p in dataset['products']:
   mapped.append({'id':p['id'],'code':p['code'],'title':p['name']['tr'],'supplierId':supplier,'sourceCode':p['code'],'sourceUrl':None,'sourceEvidence':p.get('sourceEvidence'),'salesUnit':'m²'if supplier=='goktas'else 'Takım','sourcePriceMinor':None,'salePriceMinor':p.get('salePriceMinor'),'priceStatus':'catalogue_list','sourceDocuments':dataset['sourceDocuments']})
 for p in products:mapped.append({k:p.get(k)for k in ['id','code','title','supplierId','sourceCode','sourceUrl','sourcePageId','salesUnit','sourcePriceMinor','salePriceMinor','priceStatus','markupPercent','publicationReady','merchantCategory','fetchedAt','modelId','variantAttributes']})
 ids=[p['id']for p in mapped]
 if len(ids)!=len(set(ids)):raise ValueError('duplicate_product_id')
 report={'generatedAt':m.now(),'expected':expected,'downloaded':dict(collections.Counter(p['supplierId']for p in products)),'variationCount':sum('parentSourcePageId'in p for p in products),'allSourcePagesDownloaded':sum(p['supplierId']=='altinis'for p in products)==expected['altinis'],'mappedProducts':len(mapped),'sourceLinkCount':sum(bool(p['sourceUrl'])for p in mapped),'sourceDocumentOnlyCount':sum(not p['sourceUrl']for p in mapped),'categories':dict(collections.Counter(p['merchantCategory']for p in products)),'errors':errors,'publicationReady':False}
 seed={'schema':1,'generatedAt':m.now(),'suppliers':supplierDefs,'products':mapped,'report':report}
 (R/'data/supplier-catalog.json').write_text(json.dumps(seed,ensure_ascii=False,indent=2)+'\n',encoding='utf8');(O/'download-catalog.json').write_text(json.dumps({'schema':1,'products':products,'report':report},ensure_ascii=False,indent=2)+'\n',encoding='utf8');(O/'completeness.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 out=R/'output/supplier-catalog';out.mkdir(parents=True,exist_ok=True)
 with (out/'NODENO_Tedarikci_Urun_Eslesmeleri.csv').open('w',encoding='utf-8-sig',newline='')as f:
  w=csv.writer(f,delimiter=';');w.writerow(['NODENO Kodu','Tedarikçi','Kaynak Kodu','Ürün','Kaynak Bağlantısı','Birim','Kaynak Fiyat TRY','Satış Fiyat TRY'])
  for p in mapped:w.writerow([p['code'],p['supplierId'],p['sourceCode'],p['title'],p['sourceUrl'],p['salesUnit'],''if p['sourcePriceMinor']is None else f"{p['sourcePriceMinor']/100:.2f}",''if p['salePriceMinor']is None else f"{p['salePriceMinor']/100:.2f}"])
 media={}
 for p in products:
  for u in p['images']:
   file=O/'media'/(m.sha(u.encode())+'.bin')
   if file.exists():media[u]=file
 e=html.escape;cards=[]
 for p in sorted(products,key=lambda p:(p['merchantCategory'],p['title'])):
  image=next((media[u].resolve().as_uri()for u in p['images']if u in media),None)
  price=display_price(p)
  cards.append(f'<article data-search="{e((p["title"]+" "+p["code"]+" "+p["merchantCategory"]).lower())}">{f"<img src=\"{image}\" loading=\"lazy\" alt=\"\">"if image else "<div class=placeholder>Görsel indiriliyor</div>"}<small>{e(p["merchantCategory"])}</small><h2>{e(p["title"])}</h2><p>{e(p["code"])}</p><strong>{price}</strong><p>{e(p["salesUnit"]or "Birim incelenmeli")}</p><details><summary>Ürün bilgisi</summary><p>{e(p["description"])}</p><a href="{e(p["sourceUrl"])}" target="_blank" rel="noopener">Kaynak ürün sayfası</a></details></article>')
 body='<!doctype html><html lang="tr"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>NODENO Ahşap ve Mobilya Kataloğu</title><style>body{font:16px Arial;background:#f5f3ed;color:#172f38;margin:32px}header{max-width:1200px;margin:auto}input{padding:16px;width:min(90%,600px);margin:20px 0;border:1px solid #aaa;border-radius:8px}.grid{max-width:1400px;margin:auto;display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:20px}article{background:white;padding:20px;border-radius:12px}article img,.placeholder{width:100%;height:230px;object-fit:contain}h2{font-size:18px;line-height:1.4}small{color:#546568}details p{white-space:pre-line;line-height:1.5;overflow-wrap:anywhere}article[hidden]{display:none}</style><header><h1>NODENO Ahşap ve Mobilya Kataloğu</h1><p>İyi tasarım. Kolay yaşam.</p><p>Alka Ahşap ve Altın İş Ağaç kaynaklı hazırlık kataloğu. Varyant, birim, dil ve görsel incelemesi tamamlanmayan ürünler vitrine açılmamıştır.</p><input type="search" aria-label="Katalogda ara" placeholder="Ürün, kategori veya kod ara"></header><main class="grid">'+''.join(cards)+'</main><script>document.querySelector("input").oninput=e=>document.querySelectorAll("article").forEach(a=>a.hidden=!a.dataset.search.includes(e.target.value.toLowerCase()));</script></html>'
 (out/'NODENO_Ahsap_Mobilya_Katalogu.html').write_text(body,encoding='utf8')
 if args.pdf:make_pdf(products,media)
 print(json.dumps(report,ensure_ascii=False))
def make_pdf(products,media):
 from reportlab.pdfgen.canvas import Canvas
 from reportlab.pdfbase import pdfmetrics
 from reportlab.pdfbase.ttfonts import TTFont
 from reportlab.lib.utils import ImageReader
 from reportlab.lib.colors import HexColor
 from reportlab.platypus import Paragraph
 from reportlab.lib.styles import ParagraphStyle
 from PIL import Image
 from io import BytesIO
 font=R/'NODENO_Tam_Marka_Paketi/NODENO_Marka_Paketi/07_NODENO_Sans';candidates=list(font.glob('NODENOSans-Regular.ttf'))
 if not candidates:candidates=[Path('C:/Windows/Fonts/arial.ttf')]
 pdfmetrics.registerFont(TTFont('NodenoCatalog',str(candidates[0])))
 out=R/'output/pdf/NODENO_Ahsap_Mobilya_Tedarik_Katalogu_2026.pdf';out.parent.mkdir(exist_ok=True)
 c=Canvas(str(out),pagesize=(595,842));c.setTitle('NODENO Ahşap ve Mobilya Tedarik Kataloğu');c.setAuthor('NODENO')
 style=ParagraphStyle('body',fontName='NodenoCatalog',fontSize=9,leading=12,textColor=HexColor('#172f38'))
 ordered=sorted(products,key=lambda p:(p['merchantCategory'],p['title']))
 for i,p in enumerate(ordered):
  position=i%4
  if position==0:
   c.setFillColor(HexColor('#172f38'));c.setFont('NodenoCatalog',19);c.drawString(30,803,'NODENO');c.setFont('NodenoCatalog',9);c.drawRightString(565,803,'İyi tasarım. Kolay yaşam.');c.setFont('NodenoCatalog',8);c.drawString(30,782,'Ahşap ve mobilya ürünleri | Kaynak kataloğu - yönetim kullanımı | '+m.now()[:10]);c.setStrokeColor(HexColor('#d9ddd8'));c.line(30,771,565,771)
  x=30+(position%2)*275;y=414-(position//2)*359;w=260;h=340
  c.setStrokeColor(HexColor('#d9ddd8'));c.roundRect(x,y,w,h,7,stroke=1,fill=0)
  image=next((media[u]for u in p['images']if u in media),None)
  if image:
   try:
    # Export-size raster only; the archived supplier image is untouched.
    im=Image.open(image).convert('RGB');im.thumbnail((640,640),Image.Resampling.LANCZOS);stream=BytesIO();im.save(stream,'JPEG',quality=84,optimize=True);stream.seek(0)
    c.drawImage(ImageReader(stream),x+12,y+137,width=236,height=189,preserveAspectRatio=True,anchor='c',mask='auto')
   except Exception:pass
  para=Paragraph(html.escape(p['title']),style);_,ph=para.wrap(236,54);para.drawOn(c,x+12,y+115-min(ph,54))
  c.setFont('NodenoCatalog',7);c.drawString(x+12,y+49,p['code'][:58]);c.drawString(x+12,y+37,p['merchantCategory'][:50])
  c.setFont('NodenoCatalog',9);c.drawString(x+12,y+20,display_price(p))
  c.linkURL(p['sourceUrl'],(x,y,x+w,y+h),relative=0,thickness=0)
  if position==3 or i==len(ordered)-1:
   c.setFont('NodenoCatalog',7);c.drawString(30,28,'Kaynak ürünler korunmuştur. Görseller ve seçenekler yayın öncesi incelemeye tabidir.');c.drawRightString(565,28,str(i//4+1));c.showPage()
 c.save()
if __name__=='__main__':main()
