"""Prepare an incremental, reviewed paint batch from immutable source receipts."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,csv,gzip,hashlib,importlib.util,json,re,time,urllib.parse
import requests
R=Path(__file__).resolve().parents[1];E=R/'artifacts/paint-completion-20261112';OLD=R/'artifacts/bianca-20261112'
def module(name,path):
 s=importlib.util.spec_from_file_location(name,R/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
m=module('paint_completion_source','lib/marketplace_paints.py');prep=module('paint_completion_prepare','scripts/prepare-paint-catalogue.py')
def save(path,v):path.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
def norm(v):return re.sub(r'\s+',' ',str(v).translate(str.maketrans({'İ':'i','ı':'i'})).casefold()).strip()
def finish(p):
 if p.get('finish'):return p['finish']
 if p['family']=='aqualux':return 'gloss'
 if p['family']=='maximo':
  return 'silk'if 'ipek'in norm(p['color'])else'gloss'if 'parlak'in norm(p['color'])else'default'
 if p['family']!='afilli':return 'default'
 t=norm(p['title'])
 return 'silk'if re.search('silk|ipeksi',t)else'matt'if re.search(r'\bmat\b|matt',t)else'gloss'if 'parlak'in t else'default'
def signature(p):
 package=tuple(sorted((k,str(v.normalize()))for k,v in m.package_value(p['package'])))
 color=norm(p['color'])
 if p['family']=='metallic':color=re.sub(r'^metalik\s+','',color)
 if color=='antik beyazz':color='antik beyaz'
 color=re.sub(r'[\s_-]+','',color)
 return(norm(p['brand']),p['family'],color,package or norm(p['package']),finish(p))
REASONS={
 'title_and_selected_package_conflict':'İlan başlığı ve seçili ambalaj farklı.',
 'title_and_selected_colour_conflict':'İlan başlığı ve seçili renk farklı.',
 'manufacturer_600g_and_marketplace_600ml_need_package_confirmation':'Üretici 600 g, ilan 600 ml belirtiyor; yoğunluk varsayılmadan ambalaj doğrulanmalı.',
 'bundle_contents_require_review':'Birden çok parçalı setin içeriği ve ambalajları doğrulanmalı.',
 'package_size_missing':'Ambalaj miktarı doğrulanamadı.',
 'duplicate_variant':'Aynı marka, seri, renk, ambalaj ve bitiş başka bir ilanla eşleşiyor.',
 'qualified_merchant_not_verified':'Yetkili satıcı rozeti ve en az 9,0 puan birlikte doğrulanamadı.',
 'source_rate_limit_pending':'Kaynak erişim sınırı sonrası yeniden kontrol bekliyor.',
 'pending_check':'Kaynak sayfa yeniden kontrol sırasını bekliyor.',
 'http_404':'Kaynak ürün sayfası bulunamadı.',
 'source_out_of_stock':'Seçili satıcıda ürün satışa uygun veya stokta görünmüyor.',
 'unsupported_family_review':'Seri için ürün açıklaması ve kullanım kapsamı incelemesi gerekiyor.'}
def review_record(p,reason,**extra):
 group='conflict'if'conflict'in reason or'manufacturer_600g'in reason else'duplicate'if'duplicate'in reason else'bundle'if'bundle'in reason else'source'
 url=p.get('sourceUrl',p.get('url',''));sourceid=p.get('sourceProductId')or p.get('id')or(m.product_id(url)if url else'')
 return {'group':group,'reason':reason,'reasonTr':REASONS.get(reason,reason),'sourceProductId':sourceid,'title':p.get('title',''),'color':p.get('color',''),'package':p.get('package',''),'sourceUrl':url,'checkedAt':p.get('fetchedAt'),**extra}
def select():
 report=json.loads((E/'source-checks.json').read_bytes());previous=json.loads((OLD/'selected-offers.json').read_bytes());oldoffers=json.loads((OLD/'offers.json').read_bytes());lookup={p['sourceProductId']:p for p in oldoffers['products']};held=[]
 existing={p['sourceProductId']for p in previous['products']};seen={signature(p):p['sourceProductId']for p in previous['products']};selected=[]
 for p in sorted(report['products'],key=lambda p:(-p['merchant']['score'],int(p['merchant']['id']),int(p['sourceProductId']))):
  if p['sourceProductId']in existing:continue
  if p['family']=='marble'and not re.search('mermer.*(?:efekt|sprey)|marble',norm(p['title'])):p['family']='acrylic'if'stella'in norm(p['title'])else'unknown'
  p['finish']=finish(p);reason=m.offer_review(p)
  if not reason and p['family']not in prep.FAMILIES:reason='unsupported_family_review'
  if reason:held.append(review_record(p,reason));continue
  key=signature(p)
  if key in seen:held.append(review_record(p,'duplicate_variant',duplicateOf=seen[key]));continue
  seen[key]=p['sourceProductId'];selected.append(p)
 for h in previous['held']:
  sourceid=h.get('sourceProductId',h.get('id'))
  if sourceid in {p['sourceProductId']for p in report['products']}:continue
  p=lookup.get(sourceid,h);reason=m.offer_review(p)if p.get('title')else None
  reason=reason or ('duplicate_variant'if str(h.get('reason','')).startswith('duplicate')else h.get('reason','pending_check'))
  held.append(review_record(p,reason,previousCheck=True))
 for h in report['held']:
  if m.product_id(h['url'])in existing|{p['sourceProductId']for p in report['products']}:continue
  file=E/'pages'/(hashlib.sha256(h['url'].encode()).hexdigest()[:24]+'.html.gz')
  if file.exists():
   try:
    parsed=m.parse(gzip.decompress(file.read_bytes()),h['url']);h={**h,**{k:parsed[k]for k in ['sourceProductId','title','color','package']}}
   except ValueError:pass
  held.append(review_record(h,h['reason']))
 for url in report['pending']:
  if m.product_id(url)not in existing:held.append(review_record({'url':url},'pending_check'))
 save(E/'selected-offers.json',{'products':selected,'held':held,'checkedAt':report['checkedAt']});save(E/'offers.json',{'products':selected,'held':[h for h in held if h['group']=='source']});save(E/'review-list.json',held)
 out=R/'output/paint-catalogue';out.mkdir(parents=True,exist_ok=True)
 for name,rows in [('NODENO_Boya_Renk_Ambalaj_Celiskileri.csv',[h for h in held if h['group']=='conflict']),('NODENO_Boya_Diger_Bekleyenler.csv',[h for h in held if h['group']!='conflict'])]:
  with(out/name).open('w',encoding='utf-8-sig',newline='')as f:
   w=csv.writer(f,delimiter=';');w.writerow(['Grup','Ürün kimliği','Ürün','Seçili renk','Seçili ambalaj','Neden','Kaynak bağlantısı','Kontrol tarihi'])
   for h in rows:w.writerow([h['group'],h['sourceProductId'],h['title'],h['color'],h['package'],h['reasonTr'],h['sourceUrl'],h['checkedAt']or'Önceki kontrolden / kontrol sırası bekliyor'])
 print(json.dumps({'selected':len(selected),'brands':{b:sum(p['brand']==b for p in selected)for b in ['Bianca','Filli Boya']},'reviewGroups':{k:sum(h['group']==k for h in held)for k in ['conflict','duplicate','bundle','source']}}))
def media():
 from PIL import Image,ImageOps,ImageDraw,ImageFont
 selected=json.loads((E/'selected-offers.json').read_bytes());folder=E/'media';folder.mkdir(exist_ok=True);rows=json.loads((E/'media-index.json').read_bytes())if(E/'media-index.json').exists()else[];session=requests.Session()
 for p in selected['products']:
  for url in p['images']:
   u=urllib.parse.urlsplit(url)
   if u.scheme!='https'or not(u.hostname=='cdn.dsmcdn.com'or u.hostname.endswith('.dsmcdn.com')):raise RuntimeError('image_host_rejected')
   cached=next((x for x in rows if x['url']==url),None)
   if cached:
    if hashlib.sha256((R/cached['file']).read_bytes()).hexdigest()!=cached['sha256']:raise RuntimeError('cached_image_changed')
    continue
   response=session.get(url,timeout=(10,30),allow_redirects=False);response.raise_for_status();body=response.content
   if response.status_code!=200 or len(body)>15000000:raise RuntimeError('image_fetch_rejected')
   import io
   image=Image.open(io.BytesIO(body));image.verify();image=Image.open(io.BytesIO(body));ext={ 'JPEG':'.jpg','PNG':'.png','WEBP':'.webp'}.get(image.format)
   if not ext:raise RuntimeError('image_type_rejected')
   digest=hashlib.sha256(body).hexdigest();file=folder/(digest+ext)
   if not file.exists():file.write_bytes(body)
   rows.append({'url':url,'sha256':digest,'file':file.relative_to(R).as_posix(),'width':image.width,'height':image.height});save(E/'media-index.json',rows);time.sleep(.2)
 save(E/'media-index.json',rows);cards=[]
 font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',15);small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',13)
 for p in selected['products']:
  for i,url in enumerate(p['images']):
   row=next(x for x in rows if x['url']==url);tile=Image.new('RGB',(280,370),'white');im=Image.open(R/row['file']).convert('RGB');im=ImageOps.contain(im,(270,270));tile.paste(im,((280-im.width)//2,5+(270-im.height)//2));draw=ImageDraw.Draw(tile);draw.text((7,282),p['sourceProductId']+' / '+str(i),fill='black',font=font);draw.text((7,306),p['color'][:36],fill='black',font=font);draw.text((7,330),p['family']+' | '+p['package'],fill='black',font=small);cards.append(tile)
 sheets=[]
 for start in range(0,len(cards),20):
  group=cards[start:start+20];sheet=Image.new('RGB',(1120,370*((len(group)+3)//4)), '#ddd')
  for i,tile in enumerate(group):sheet.paste(tile,((i%4)*280,(i//4)*370))
  path=E/('review-'+str(start//20+1)+'.jpg');sheet.save(path,quality=90);sheets.append({'file':path.relative_to(R).as_posix(),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
 save(E/'review-sheets.json',sheets);print(json.dumps({'products':len(selected['products']),'images':len(rows),'sheets':len(sheets)}))
def prepare():
 selected=json.loads((E/'selected-offers.json').read_bytes())
 for p in selected['products']:
  body=gzip.decompress((R/p['sourceEvidence']['file']).read_bytes())
  assert hashlib.sha256(body).hexdigest()==p['sourceEvidence']['sha256']
  fresh=m.parse(body,p['sourceUrl'],p['merchant']['id'])
  assert fresh['merchant']['authorized']and fresh['merchant']['score']>=9
  assert all(fresh[k]==p[k]for k in ['sourceProductId','sourceCode','title','color','itemNumber','barcode','sourcePriceMinor','salePriceMinor','images'])
  assert p['salePriceMinor']==m.markup(p['sourcePriceMinor'])and m.offer_review(p)is None
 proof=json.loads((E/'base.json').read_bytes());prep.O=E;prep.B=R/proof['releases'][0];prep.main()
 # Retain original source media privately; omit a different Aqua Reno series advertisement.
 data=json.loads((E/'catalogue-prepared.json').read_bytes());index={r['url']:r for r in json.loads((E/'media-index.json').read_bytes())};excluded=[]
 for p in selected['products']:
  if p['sourceProductId']in ['1131626017','1131626020']:
   row=index[p['images'][1]];path='/assets/suppliers/'+row['sha256']+Path(row['file']).suffix
   product=next(x for x in data['products']if x['id']=='paint-ty-'+p['sourceProductId']);product['images']=[u for u in product['images']if u!=path]
   assert product['images'];excluded.append({'productId':product['id'],'sourceUrl':row['url'],'sha256':row['sha256'],'reason':'Banyo ürününün galerisindeki farklı Aqua Reno serisi reklamı yayımlanmadı; özgün dosya arşivde korundu.'})
 referenced={u for p in data['products']for u in p['images']};data['assets']={k:v for k,v in data['assets'].items()if k in referenced};save(E/'catalogue-prepared.json',data);save(E/'media-exclusions.json',excluded)
 review=json.loads((E/'media-review.json').read_bytes());review['images']=data['assets'];review['excluded']=excluded;save(E/'media-review.json',review)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('phase',choices=['select','media','prepare']);args=a.parse_args();globals()[args.phase]()
