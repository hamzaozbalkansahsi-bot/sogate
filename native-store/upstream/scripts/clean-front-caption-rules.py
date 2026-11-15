"""Generate reviewed candidates from native PDF paths, preserving all photo streams."""
from pathlib import Path
import copy,hashlib,json,math,sys,io
import fitz,numpy as np
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
from lib.cabinet_front_decoration import caption_rules,remove_caption_rules,caption_rule_fragments,clean_fragment_pixels
E=R/'artifacts/front-image-integrity-20261115';sha=lambda b:hashlib.sha256(b).hexdigest()

def main():
 E.mkdir(exist_ok=True);(E/'candidates').mkdir(exist_ok=True)
 raw=(R/'data/cabinet-fronts.json').read_bytes();old=json.loads(raw);data=copy.deepcopy(old)
 if not (E/'cabinet-fronts-before.json').exists():(E/'cabinet-fronts-before.json').write_bytes(raw)
 assert raw==(E/'cabinet-fronts-before.json').read_bytes(),'Source changed after candidate generation; use a new evidence directory'
 docs={x['sha256']:fitz.open(R.parent/x['name'])for x in old['sourceDocuments']};pages={};replacements={};results=[]
 for digest,a in old['assets'].items():
  source=docs[a['sourceDocumentSha256']];sourcepage=source[a['sourcePage']-1];rect=fitz.Rect(a['sourceRect'])
  rules=[r for r in caption_rules(sourcepage)if r.intersects(rect)];fragments=caption_rule_fragments(sourcepage)+rules
  if not rules:continue
  key=(a['sourceDocumentSha256'],a['sourcePage'])
  if key not in pages:
   pdf=fitz.open();pdf.insert_pdf(source,from_page=a['sourcePage']-1,to_page=a['sourcePage']-1);page=pdf[0]
   for block in page.get_text('blocks'):
    if len(block)>6 and block[6]==0:page.add_redact_annot(fitz.Rect(block[:4]),fill=False,cross_out=False)
   page.apply_redactions(images=0,graphics=0,text=0);remove_caption_rules(page);pages[key]=pdf
  scale=min(3,1800/max(rect.width,rect.height));pix=pages[key][0].get_pixmap(matrix=fitz.Matrix(scale,scale),clip=rect,alpha=False);cleaned=clean_fragment_pixels(pix,scale,fragments);buffer=io.BytesIO();cleaned.save(buffer,format='PNG');body=buffer.getvalue();newsha=sha(body)
  previous=np.array(Image.open(R/'web'/a['path'].lstrip('/')).convert('RGB'));now=np.array(cleaned)
  assert previous.shape==now.shape
  mask=Image.new('1',(pix.width,pix.height));draw=ImageDraw.Draw(mask)
  for r in rules:draw.rectangle([math.floor(r.x0*scale-pix.x)-2,math.floor(r.y0*scale-pix.y)-2,math.ceil(r.x1*scale-pix.x)+2,math.ceil(r.y1*scale-pix.y)+2],fill=1)
  changed=np.any(previous!=now,axis=2);assert not np.any(changed&~np.array(mask,bool)),digest+' changes outside rule footprint'
  assert np.all(now[changed]>=previous[changed]),digest+' introduced new dark pixels'
  if not changed.any():continue
  (E/'candidates'/(newsha+'.png')).write_bytes(body)
  data['assets'].pop(digest);entry=copy.deepcopy(a);entry.update(path='/assets/fronts/'+newsha+'.png',sha256=newsha,bytes=len(body),nativeCaptionRulesExcluded=True,reviewRequired=True);data['assets'][newsha]=entry;replacements[digest]=newsha
  results.append({'before':digest,'after':newsha,'sourcePage':a['sourcePage'],'nativeRulesRemoved':len(rules),'changedPixels':int(changed.sum()),'outsideRulePixelsExact':True,'noNewDarkPixels':True,'sourcePhotoAndAlphaStreamsExact':True,'dimensionsUnchanged':True})
 for p in data['products']:p['assetHashes']=[replacements.get(h,h)for h in p['assetHashes']]
 data.update(publicationReady=False,reviewRequired=True)
 (E/'cabinet-fronts-candidate.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8');(E/'rule-removal.json').write_text(json.dumps({'imagesChanged':len(results),'replacements':replacements,'images':results},indent=2)+'\n')
 labels={h:p['code']for p in old['products']for h in p['assetHashes']}
 for start in range(0,len(results),10):
  subset=results[start:start+10];sheet=Image.new('RGB',(1000,math.ceil(len(subset)/2)*280),'#eeeeee');pen=ImageDraw.Draw(sheet)
  for i,row in enumerate(subset):
   for j,kind in enumerate(['before','after']):
    path=R/'web/assets/fronts'/(row[kind]+'.png')if kind=='before'else E/'candidates'/(row[kind]+'.png');im=Image.open(path);im.thumbnail((238,245));x=(i%2)*500+j*250;y=(i//2)*280;sheet.paste(im,(x+(245-im.width)//2,y));pen.text((x+5,y+248),labels[row['before']]+' / p'+str(row['sourcePage'])+' / '+kind,fill='black')
  sheet.save(E/f'rules-review-{start//10+1}.png')
 print(json.dumps({'candidateImages':len(results),'reviewSheets':math.ceil(len(results)/10),'readyForVisualReview':True}))

if __name__=='__main__':main()
