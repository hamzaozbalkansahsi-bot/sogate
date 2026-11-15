"""Create labelled source/candidate review sheets without approving any image."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageOps
import argparse,hashlib,json,math
R=Path(__file__).resolve().parents[1];O=R/'artifacts/supplier-expansion';D=O/'publication/media-review';D.mkdir(parents=True,exist_ok=True)
p=argparse.ArgumentParser();p.add_argument('--group',choices=['altinis','alka-source-clean','alka-candidates','alka-refined'],required=True);args=p.parse_args()
if args.group=='alka-refined':
 data=json.loads((O/'watermark-refined/receipt.json').read_bytes());rows=[{'sourceSha256':r['sourceSha256'],'path':r['outputPath'],'outputSha256':r['outputSha256'],'cleaningVerified':False}for r in data['images']]
elif args.group=='alka-candidates':
 data=json.loads((O/'watermark-aligned/receipt.json').read_bytes());rows=[{'sourceSha256':r['sourceSha256'],'path':r['outputPath'],'outputSha256':r['outputSha256']}for r in data['products']if r['status']=='candidate_ready']
else:
 supplier='altinis'if args.group=='altinis'else'alka';audit=json.loads((O/(supplier+'-branding-audit.json')).read_bytes());rows=[]
 for r in audit['images']:
  if r.get('error')or r.get('source',{}).get('brandMatches'):continue
  with Image.open(R/r['sourceFile'])as im:
   if supplier=='alka'and max(im.size)>=1200:continue
  rows.append({'sourceSha256':r['sourceSha256'],'path':r['sourceFile'],'outputSha256':r['sourceSha256']})
rows.sort(key=lambda r:r['sourceSha256']);sheets=[]
for start in range(0,len(rows),72):
 part=rows[start:start+72];sheet=Image.new('RGB',(1536,9*190),'#e6e9e6');draw=ImageDraw.Draw(sheet)
 for i,row in enumerate(part):
  body=(R/row['path']).read_bytes();assert hashlib.sha256(body).hexdigest()==row['outputSha256'];im=Image.open(R/row['path']).convert('RGB');im.thumbnail((184,164));x=(i%8)*192;y=(i//8)*190;sheet.paste(im,(x+(184-im.width)//2,y));draw.text((x+3,y+166),row['sourceSha256'][:16],fill='#172d38');row['sheetIndex']=len(sheets);row['sheetCell']=i
 target=D/(args.group+'-'+str(len(sheets)+1).zfill(3)+'.jpg');sheet.save(target,quality=94);sheets.append({'path':target.relative_to(R).as_posix(),'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'images':len(part)})
report={'group':args.group,'images':rows,'sheets':sheets,'contactSheetsInspected':False,'publicationReady':False};(D/(args.group+'.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({'group':args.group,'images':len(rows),'sheets':len(sheets)}))
