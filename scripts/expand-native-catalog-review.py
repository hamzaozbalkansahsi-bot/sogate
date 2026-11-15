#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/expand-native-catalog-review.py
# Açıklama   : Değiştirilmemiş kaynak kapakları özel inceleme paftalarına indeksler; otomatik yayın onayı vermez.
import hashlib,json,math,re
from pathlib import Path
from PIL import Image,ImageDraw,ImageOps

HOME=Path('D:/sexogate-local-artifacts-20261114/private-installs/native-catalog-20261115')
data=json.loads((HOME/'catalog-source.json').read_text('utf8'))
images=json.loads((HOME/'images.json').read_text('utf8'))
products={p['id']:p for p in data['products']}
folder=HOME/'review/expansion';folder.mkdir(parents=True,exist_ok=True)
rows=[]
for vendor in ['sistina','liona','xshopum']:
 for work in data['workbench']:
  product=products[work['id']]
  if work['source']['vendor']!=vendor or work['source']['publicInStock']is not True or work['eligibilityHold']or not product['salePriceMinor']:continue
  if re.search(r'\b(çocuk|bebek|liseli|lise|teen|kids|junior|schoolgirl)\b',product['name']['tr'],re.I):continue
  media=next((images[url]for url in work['sourceImages']if 'file'in images.get(url,{})),None)
  if not media:continue
  file=HOME/'media'/media['file']
  assert hashlib.sha256(file.read_bytes()).hexdigest()==media['sha256']
  rows.append({'index':len(rows),'id':product['id'],'vendor':vendor,'name':product['name']['tr'],'sha256':media['sha256'],'file':media['file']})
for offset in range(0,len(rows),64):
 sheet=Image.new('RGB',(1600,1920),'#ece9e6');draw=ImageDraw.Draw(sheet)
 for position,row in enumerate(rows[offset:offset+64]):
  x=(position%8)*200;y=(position//8)*240
  with Image.open(HOME/'media'/row['file'])as original:
   thumb=ImageOps.contain(ImageOps.exif_transpose(original).convert('RGB'),(190,210))
   sheet.paste('white',(x+3,y+3,x+197,y+215));sheet.paste(thumb,(x+(200-thumb.width)//2,y+4+(210-thumb.height)//2))
  draw.text((x+8,y+219),f"{row['index']} {row['vendor']}",fill='black')
 sheet.save(folder/f'sheet-{offset//64:02}.jpg',quality=92)
(folder/'candidates.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'candidates':len(rows),'sheets':math.ceil(len(rows)/64),'approved':False,'originalImagesChanged':False}))
