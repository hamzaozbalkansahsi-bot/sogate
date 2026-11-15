"""Export the reviewed customer catalogue; private supplier links are a separate CSV."""
from pathlib import Path
import argparse,json,csv,collections,io,html
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPDF
R=Path(__file__).resolve().parents[1];O=R/'artifacts/supplier-expansion/publication'
a=argparse.ArgumentParser();a.add_argument('--release',required=True);args=a.parse_args();release=R/args.release
catalog=json.loads((release/'private/catalog.json').read_bytes());products=[p for p in catalog['products']if p.get('productType')=='supplier-item'];assert len(products)==2581
brand=json.loads((R/'data/brand.json').read_bytes());categories={c['id']:c['name']['tr']for c in catalog['categories']};source={p['id']:p for p in json.loads((O/'content-tr.json').read_bytes())['products']}
out=R/'output/pdf/NODENO_Ahsap_Urun_Katalogu_2026_Temiz.pdf';out.parent.mkdir(exist_ok=True)
font=R/'NODENO_Tam_Marka_Paketi/NODENO_Marka_Paketi/07_NODENO_Sans/NODENOSans-Regular.ttf';pdfmetrics.registerFont(TTFont('NodenoClean',str(font)))
navy=HexColor(brand['colors']['navy']);muted=HexColor(brand['colors']['muted']);line=HexColor(brand['colors']['line'])
styles={name:ParagraphStyle(name,fontName='NodenoClean',fontSize=size,leading=size*1.35,textColor=navy)for name,size in [('title',11),('small',8),('price',10)]}
c=canvas.Canvas(str(out),pagesize=(595,842));c.setTitle('NODENO Ahşap Ürün Kataloğu 2026');c.setAuthor('NODENO');logo=svg2rlg(str(R/'web/assets/brand/logo-horizontal.svg'))
def draw_text(text,x,y,width,style='small'):
 p=Paragraph(html.escape(text),styles[style]);_,h=p.wrap(width,1000);p.drawOn(c,x,y-h);return y-h
def header(page):
 c.setFillColor(HexColor(brand['colors']['ivory']));c.rect(0,0,595,842,fill=1,stroke=0)
 c.saveState();c.translate(30,793);factor=140/logo.width;c.scale(factor,factor);renderPDF.draw(logo,c,0,0);c.restoreState()
 c.setFillColor(navy);c.setFont('NodenoClean',9);c.drawRightString(565,806,brand['slogan']['tr']);c.setFont('NodenoClean',8);c.drawString(30,777,'Ahşap mobilya ve malzemeler · 10 Kasım 2026');c.setStrokeColor(line);c.line(30,764,565,764)
 c.setFont('NodenoClean',8);c.setFillColor(muted);c.drawString(30,25,brand['domain']+'  |  '+brand['contact']['email']);c.drawRightString(565,25,str(page))
header(1);c.setFillColor(navy);c.setFont('NodenoClean',30);c.drawString(40,687,'Ahşabın doğal çizgileri');c.setFont('NodenoClean',15);c.drawString(40,651,'Mobilya, tamamlayıcı parçalar ve üretim malzemeleri')
draw_text('Bu katalogda 2.581 ürün ve varyasyon kaydı bulunur. Her kartta satış birimi ayrıca belirtilir; adet, metre, tam boy, kilogram ve takım fiyatları birbirinden farklıdır.',40,607,500,'title')
draw_text('Fiyatı doğrulanmış ürünler güncel kaynak satış fiyatına %20 ilave edilerek listelenmiştir. Fiyatı olmayan ürünlerde teklif alınır. Seçenekli ürünlerde malzeme ve ölçüye göre ilgili varyasyonu seçin. Güncel ürün bilgileri ve fiyatlar ürün bağlantısında yer alır.',40,535,500,'title')
image_cache={}
def image_reader(path):
 if path not in image_cache:
  with Image.open(release/'public'/path.lstrip('/'))as im:
   im=im.convert('RGB');im.thumbnail((650,650));b=io.BytesIO();im.save(b,format='JPEG',quality=86);image_cache[path]=ImageReader(io.BytesIO(b.getvalue()))
 return image_cache[path]
heroes=[next(p for p in products if p['salePriceMinor']and cat in p['categoryIds'])for cat in ['ahsap-masalar','ahsap-sandalyeler','ahsap-citalar']]
for i,p in enumerate(heroes):c.drawImage(image_reader(p['images'][0]),40+i*172,220,width=158,height=245,preserveAspectRatio=True,anchor='c',mask='auto')
c.showPage();ordered=sorted(products,key=lambda p:(categories[p['categoryIds'][-1]],p['name']['tr'],p['code']));units={'piece':'adet','metre':'metre','length':'tam boy','kg':'kg','set':'takım'}
for i,p in enumerate(ordered):
 pos=i%4
 if pos==0:header(i//4+2)
 x=30+(pos%2)*275;y=420-(pos//2)*365;w=260;h=329
 c.setFillColor(HexColor('#FFFFFF'));c.setStrokeColor(line);c.roundRect(x,y,w,h,5,fill=1,stroke=1)
 if p['images']:c.drawImage(image_reader(p['images'][0]),x+10,y+132,width=240,height=182,preserveAspectRatio=True,anchor='c',mask='auto')
 else:draw_text('Bu ürün için henüz fotoğraf bulunmuyor.',x+25,y+230,210)
 ty=draw_text(p['name']['tr'],x+12,y+121,236,'title');ty=draw_text(p['code'],x+12,ty-5,236)
 price=('Seçenek belirleyin'if p.get('variationSelectionRequired')else 'Teklif alın')if p['salePriceMinor']is None else format(p['salePriceMinor']/100,',.2f').replace(',','@').replace('.',',').replace('@','.')+' TL'+(' / '+units[p['saleUnit']]if p['saleUnit']in units else' (birim teyidi gerekir)')
 ty=draw_text(price,x+12,ty-6,236,'price')
 specs=[s['value']['tr']for s in p['specs']if s['label']['tr']in ['Ölçüler','Ölçü bilgisi','Standart boy']]
 if specs:ty=draw_text('Ölçü: '+' · '.join(specs),x+12,ty-5,236)
 if p.get('variantLabel')and not p.get('variationSelectionRequired'):ty=draw_text(p['variantLabel']['tr'],x+12,ty-4,236)
 c.linkURL('https://nodenohome.com/?lang=tr&product='+p['id'],(x,y,x+w,y+h),relative=0,thickness=0)
 if pos==3 or i==len(ordered)-1:c.showPage()
c.save()
csvout=R/'output/supplier-catalog/NODENO_Fiyat_Kontrol_ve_Tedarikci_Eslesmeleri.csv';csvout.parent.mkdir(exist_ok=True)
with csvout.open('w',encoding='utf-8-sig',newline='')as f:
 w=csv.writer(f,delimiter=';');w.writerow(['NODENO kodu','Ürün','Tedarikçi','Kaynak kodu','Kaynak bağlantısı','Fiyat durumu','Satış birimi','Kaynak fiyat TRY','NODENO fiyat TRY'])
 for p in ordered:
  s=source[p['id']];money=lambda n:''if n is None else f'{n/100:.2f}';w.writerow([p['code'],p['name']['tr'],s['supplierId'],s['sourceCode'],s['sourceUrl'],s['priceStatus'],units.get(p['saleUnit'],'Teklif ile'),money(s.get('sourcePriceMinor')),money(p['salePriceMinor'])])
print(json.dumps({'pdf':str(out.relative_to(R)),'pages':1+(len(products)+3)//4,'records':len(products),'bytes':out.stat().st_size,'prices':dict(collections.Counter(s['priceStatus']for s in source.values()))}))
