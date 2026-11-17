#!/usr/bin/env python3
# Proje      : SEXOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/marketplace-review-sheets.py
# Açıklama   : Asıl fotoğrafları değiştirmeden yalnız özel görsel inceleme sayfaları ve hash eşlemesi oluşturur.
import json,hashlib,math
from pathlib import Path
from PIL import Image,ImageOps,ImageDraw,ImageFont
BASE=Path('D:/sexogate-local-artifacts-20261114/private-installs');HOME=BASE/'marketplace-catalog-20261117';FIRST=BASE/'marketplace-catalog-20261116'
def build():
 source=json.loads((HOME/'catalog-source.json').read_text('utf8'));old={r['id']:r for r in json.loads((FIRST/'cover-review.json').read_text('utf8'))};folder=HOME/'review-sheets';folder.mkdir(exist_ok=True);rows=[];auto=[];decisions=json.loads((HOME/'visual-decisions.json').read_text('utf8'))if(HOME/'visual-decisions.json').exists()else{}
 for p,w in zip(source['products'],source['workbench']):
  previous=old.get(p['id']);media=w['media'];approved=[]
  if previous and previous['coverApproved']and media and previous['sha256']==media[0]['sha256']and decisions.get(media[0]['sha256'])!='rejected':approved=[0]
  approved=sorted(set(approved+[i for i,m in enumerate(media)if decisions.get(m['sha256'])=='approved']))
  state='actual_hash_review'if any(m['sha256']in decisions for m in media)else'previous_actual_hash_review'if approved else'pending'
  auto.append({'id':p['id'],'approvedIndices':approved,'imageHashes':[m['sha256']for m in media],'originalBytesChanged':False,'reviewState':state,'coverApproved':bool(approved),'sha256':media[0]['sha256']if media else None})
  if not approved:
   for index,m in enumerate(media):
    if decisions.get(m['sha256'])not in ['approved','rejected']:rows.append({'id':p['id'],'index':index,'file':m['file'],'sha256':m['sha256'],'title':w['rawSourceTitle'][:85],'sourceId':w['rawSourceId']})
 font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',14);small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',11)
 for offset in range(0,len(rows),30):
  canvas=Image.new('RGB',(1500,1500),'#e8e1de');draw=ImageDraw.Draw(canvas)
  for n,row in enumerate(rows[offset:offset+30]):
   x=n%6*250;y=n//6*300;path=HOME/'media'/row['file'];assert hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256']
   with Image.open(path)as source_image:thumb=ImageOps.contain(source_image.convert('RGB'),(242,237));canvas.paste(thumb,(x+(250-thumb.width)//2,y+23+(237-thumb.height)//2))
   draw.text((x+5,y+3),str(offset+n)+' · '+row['sourceId']+' / '+str(row['index']),fill='#5a0a20',font=font)
   for line in range(3):draw.text((x+4,y+258+line*13),row['title'][line*33:(line+1)*33],fill='#24191d',font=small)
  canvas.save(folder/('sheet-'+str(offset//30).zfill(3)+'.jpg'),quality=90)
 (folder/'manifest.json').write_text(json.dumps(rows,ensure_ascii=False),'utf8');(HOME/'cover-review.json').write_text(json.dumps(auto,ensure_ascii=False),'utf8');print(json.dumps({'images':len(rows),'sheets':math.ceil(len(rows)/30),'previousReviewedCovers':sum(bool(r['approvedIndices'])for r in auto)}))
if __name__=='__main__':build()
