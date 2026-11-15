"""Compile original NODENO editorial content, local illustrations and checked language variants."""
from pathlib import Path
from urllib.parse import urlparse
from html import escape
import argparse,collections,hashlib,json,re,textwrap,statistics,base64,io,functools,shutil,sys
from fontTools import subset
from fontTools.ttLib import TTFont
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R))
from lib.blog_bundle import pack_bundle,merge_bundles
E=R/'artifacts/blog-20261112'
CATEGORIES={'small-spaces','entryway','living','bedroom','work','care','planning','color','paint-math','surfaces','application','renewal'}
HOSTS={'www.adoremobilya.com','adoremobilya.com','www.filliboya.com','filliboya.com','biancastella.com.tr','www.biancastella.com.tr'}
def body(a):return ' '.join([a['intro'],*[p for s in a['sections']for p in [s['heading'],*s['paragraphs'],*s.get('list',[])]],*a['checklist']])
def validate_articles(articles,minimum=250):
 if len(articles)<minimum:raise ValueError('not_enough_articles')
 ids=set();slugs=set();titles=set();paragraphs={};fingerprints=[]
 for a in articles:
  for key in ['id','slug','category','title','description','keywords','intro','sections','checklist','tool','sources','visual']:
   if key not in a:raise ValueError('missing_'+key)
  if not re.fullmatch('[a-z0-9][a-z0-9_-]{0,99}',a['id'])or not re.fullmatch('[a-z0-9][a-z0-9-]{0,150}',a['slug']):raise ValueError('invalid_identity')
  if a['id']in ids or a['slug']in slugs or a['title'].casefold()in titles:raise ValueError('duplicate_identity')
  ids.add(a['id']);slugs.add(a['slug']);titles.add(a['title'].casefold())
  if a['category']not in CATEGORIES or a['tool']not in ['space','paint','palette']:raise ValueError('invalid_category_or_tool')
  if len(a['sections'])<4 or len(a['checklist'])<3 or len(a['keywords'])<3:raise ValueError('incomplete_guide')
  words=body(a).split()
  if len(words)<200:raise ValueError('short_article_'+a['id'])
  if len(a['description'])>210 or len(a['description'])<55:raise ValueError('invalid_description_'+a['id'])
  shingles={' '.join(words[i:i+5]).casefold()for i in range(len(words)-4)}
  for old_id,old in fingerprints:
   if len(shingles&old)/max(1,len(shingles|old))>.42:raise ValueError('duplicate_content_'+a['id']+'_'+old_id)
  fingerprints.append((a['id'],shingles))
  for s in a['sections']:
   if not s['heading'].strip()or not s['paragraphs']:raise ValueError('empty_section')
   for p in s['paragraphs']:
    normalized=' '.join(p.split()).casefold()
    if len(normalized)>100:
     if normalized in paragraphs:raise ValueError('duplicate_content_paragraph_'+a['id']+'_'+paragraphs[normalized])
     paragraphs[normalized]=a['id']
  for source in a['sources']:
   url=urlparse(source['url'])
   if url.scheme!='https'or url.hostname not in HOSTS or url.username or url.password:raise ValueError('source_not_approved')
 return articles
def wrap(value,width=31):return textwrap.wrap(value,width=width,break_long_words=False,break_on_hyphens=False)[:3]
@functools.lru_cache(maxsize=2048)
def diagram_font(characters,weight):
 font=TTFont(R/'web/assets/fonts'/('NODENOSans-Bold.woff'if weight==700 else'NODENOSans-Regular.woff'),recalcTimestamp=False);options=subset.Options();options.flavor='woff';options.drop_tables+=['FFTM'];subsetter=subset.Subsetter(options=options);subsetter.populate(text=characters);subsetter.subset(font);font.flavor='woff';out=io.BytesIO();font.save(out);return base64.b64encode(out.getvalue()).decode('ascii')
def svgtext(value,x,y,size=24,color='#172D38',width=31,weight='400',rtl=False):
 return ''.join(f'<text x="{x}" y="{y+i*(size+8)}" fill="{color}" font-size="{size}" font-weight="{weight}" direction="'+('rtl'if rtl else'ltr')+'">'+escape(line)+'</text>'for i,line in enumerate(wrap(value,width)))
def diagram(a):
 v=a['visual'];kind=v['type'];labels=v.get('labels',[])[:5];seed=int(hashlib.sha256(a['slug'].encode()).hexdigest()[:8],16);parts=[]
 # Geometry communicates the type of decision; no invented product measurements appear.
 if kind in ['palette']:
  families=[['#D7D0BD','#8A8249','#6A7977','#292925'],['#E3DFD1','#9DAD9B','#425A63','#172D38'],['#D9CBBA','#B8947D','#819393','#364B52']];colors=families[seed%3]
  for i,color in enumerate(colors):parts.append(f'<rect x="{80+i*165}" y="260" width="145" height="270" rx="18" fill="{color}"/>')
  parts.append('<path d="M85 590H710" stroke="#536770" stroke-width="2"/>')
 elif kind in ['area','layers','surface']:
  if kind=='area':
   parts.append('<path d="M95 300L420 220L710 300V570L420 650L95 570Z" fill="#FFFFFF" stroke="#172D38" stroke-width="4"/><path d="M420 220V650M95 300L420 385L710 300" fill="none" stroke="#536770" stroke-width="3"/><path d="M235 340V540L340 570V370Z" fill="#D8EC81" stroke="#172D38" stroke-width="3"/><path d="M510 375V470L630 435V342Z" fill="#F5F2E9" stroke="#172D38" stroke-width="3"/>')
  else:
   for i,color in enumerate(['#172D38','#AEBBB5','#D8EC81','#FFFFFF']):
    y=520-i*75;parts.append(f'<path d="M100 {y}L390 {y-90}L710 {y}L420 {y+90}Z" fill="{color}" stroke="#536770" stroke-width="3"/>')
 elif kind=='process':
  for i in range(4):
   x=90+(i%2)*330;y=270+(i//2)*210;parts.append(f'<rect x="{x}" y="{y}" width="280" height="160" rx="15" fill="'+('#D8EC81'if i==seed%4 else'#FFFFFF')+'" stroke="#536770" stroke-width="3"/>');parts.append(svgtext(str(i+1),x+25,y+65,size=35))
 elif kind=='care':
  parts.append('<rect x="90" y="330" width="590" height="70" rx="8" fill="#172D38"/><path d="M130 400V610M640 400V610" stroke="#172D38" stroke-width="20"/><path d="M240 320L310 235L480 260L420 340Z" fill="#D8EC81" stroke="#536770" stroke-width="3"/><path d="M220 460C260 480 290 450 330 470M340 460C380 480 410 450 450 470" fill="none" stroke="#536770" stroke-width="4"/>')
 elif kind=='storage':
  parts.append('<rect x="170" y="240" width="440" height="390" rx="7" fill="#FFFFFF" stroke="#172D38" stroke-width="6"/>')
  for y in [360,490]:parts.append(f'<path d="M170 {y}H610" stroke="#172D38" stroke-width="5"/>')
  for i in range(6):
   x=205+(i%3)*125;y=275+(i//3)*130;parts.append(f'<rect x="{x}" y="{y}" width="85" height="70" rx="7" fill="'+('#D8EC81'if i==seed%6 else'#DADDD6')+'"/>')
 else:
  parts.append('<rect x="80" y="225" width="640" height="415" rx="9" fill="#FFFFFF" stroke="#172D38" stroke-width="5"/>')
  if kind=='desk':parts.append('<rect x="110" y="255" width="410" height="135" rx="8" fill="#172D38"/><rect x="260" y="405" width="110" height="110" rx="25" fill="#D8EC81" stroke="#536770" stroke-width="3"/><path d="M310 530V600" stroke="#536770" stroke-dasharray="9 9" stroke-width="4"/>')
  elif kind=='clearance':parts.append('<rect x="110" y="250" width="150" height="360" rx="8" fill="#172D38"/><rect x="550" y="250" width="140" height="360" rx="8" fill="#AEBBB5"/><rect x="285" y="275" width="240" height="310" rx="20" fill="#D8EC81"/><path d="M305 430H505M305 414V446M505 414V446" stroke="#172D38" stroke-width="4"/>')
  else:parts.append('<rect x="110" y="255" width="260" height="170" rx="10" fill="#172D38"/><rect x="475" y="255" width="210" height="95" rx="8" fill="#AEBBB5"/><rect x="425" y="465" width="220" height="120" rx="12" fill="#D8EC81"/><path d="M160 515H350V590" fill="none" stroke="#536770" stroke-width="5" stroke-dasharray="11 9"/>')
  parts.append('<path d="M80 570V640H155M80 570A75 75 0 0 1 155 640" fill="#F5F2E9" stroke="#536770" stroke-width="3"/>')
 locale=a.get('_locale','tr');rtl=locale=='ar'
 line_title=svgtext(a['title'],1135 if rtl else 65,70,size=32,width=56,weight='700',rtl=rtl)
 label_svg=''
 for i,label in enumerate(labels):
  y=260+i*95;label_svg+=f'<circle cx="810" cy="{y-7}" r="5" fill="#172D38"/>'+svgtext(label,1135 if rtl else 835,y,size=22,width=25,rtl=rtl)
 notes={'tr':'NODENO · Açıklayıcı çizim / Ölçekli değildir','en':'NODENO · Explanatory illustration / Not to scale','ru':'NODENO · Поясняющий рисунок / Не в масштабе','ar':'NODENO · رسم توضيحي / ليس بمقياس رسم'}
 # Stable per-language subsets keep every SVG self-contained without reloading and
 # subsetting both original fonts for every article in a large editorial bank.
 latin='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzÇĞİÖŞÜçğıöşü0123456789 ·/(),.-–—:;!?%²×÷=+<>_%'
 extra=(''.join(chr(code)for code in range(0x400,0x500))if locale=='ru'else ''.join(chr(code)for code in range(0x600,0x700))if locale=='ar'else'')
 characters=''.join(sorted(set(latin+extra)))
 font_css='<style>'+''.join('@font-face{font-family:NodenoDiagram;font-weight:'+str(weight)+';src:url(data:font/woff;base64,'+diagram_font(characters,weight)+') format("woff")}'for weight in[400,700])+'text{font-family:NodenoDiagram,Arial,sans-serif}</style>'
 return '<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="800" viewBox="0 0 1200 800" role="img"><title>'+escape(a['title'])+'</title><desc>'+escape('; '.join(labels))+'</desc>'+font_css+'<rect width="1200" height="800" fill="#F5F2E9"/>'+line_title+'<path d="M780 225V685" stroke="#DADDD6" stroke-width="2"/>'+''.join(parts)+label_svg+svgtext(notes[locale],1135 if rtl else 65,755,size=18,width=90,rtl=rtl)+'</svg>'
def translation_hash(a):
 values=[a['title'],a['description'],a['intro'],*a['keywords'],*[text for s in a['sections']for text in [s['heading'],*s['paragraphs'],*s.get('list',[])]],*a['checklist']]
 return hashlib.sha256(json.dumps(values,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
def translation_approved(receipt,source_hash):
 digest=hashlib.sha256(json.dumps(receipt.get('content'),ensure_ascii=False,sort_keys=True).encode()).hexdigest();hashes=[receipt[key]for key in ['editorialContentSha256','reviewedBodySha256']if receipt.get(key)]
 return receipt.get('sourceSha256')==source_hash and not receipt.get('checks')and receipt.get('reviewStatus')=='editor-reviewed'and not receipt.get('visualReviewPending')and bool(hashes)and all(value==digest for value in hashes)
def compile_bank(minimum=250):
 articles=[]
 for path in sorted((R/'data/blog').glob('*/*.json')):articles.extend(json.loads(path.read_bytes()))
 validate_articles(articles,minimum)
 # Alternate home/workshop themes, so the daily pair serves different needs.
 groups=[sorted([a for a in articles if a['id'].startswith(prefix)],key=lambda a:a['id'])for prefix in ['home-','workshop-']]
 ordered=[]
 for i in range(max(map(len,groups))):
  for group in groups:
   if i<len(group):ordered.append(group[i])
 output=R/'web/assets/blog';output.mkdir(parents=True,exist_ok=True);translated=collections.Counter();held=[];products=json.loads((R/'data/blog-products.json').read_bytes())['categories']if(R/'data/blog-products.json').exists()else{}
 for a in ordered:
  svg=diagram(a).encode('utf8');file=output/(a['slug']+'-'+hashlib.sha256(svg).hexdigest()[:12]+'.svg');file.write_bytes(svg)
  a['image']={'url':'/assets/blog/'+file.name,'alt':a['title']+' — açıklayıcı çizim','width':1200,'height':800,'kind':'original-diagram','storage':'private-bundle','sha256':hashlib.sha256(svg).hexdigest()}
  a['related']=[x['slug']for x in ordered if x['id']!=a['id']and x['category']==a['category']][:4]
  linked=products.get(a['category'],[]);a['products']=[{'id':p['id'],'name':p['names']['tr'],'image':p['image']}for p in linked]
  a['locales']={}
  visual=a['visual']
  for lang in ['en','ru','ar']:
   file=R/'data/blog-translations'/lang/(a['id']+'.json')
   if not file.exists():held.append({'id':a['id'],'locale':lang,'reason':'missing_translation'});continue
   receipt=json.loads(file.read_bytes())
   if not translation_approved(receipt,translation_hash(a)):
    held.append({'id':a['id'],'locale':lang,'reason':'translation_quality_gate'});continue
   content=receipt['content'];translated_visual={**visual,'labels':content.get('visualLabels',visual['labels'])}
   localized=diagram({**a,'title':content['title'],'visual':translated_visual,'_locale':lang}).encode('utf8');localized_path=output/(a['slug']+'-'+lang+'-'+hashlib.sha256(localized).hexdigest()[:12]+'.svg');localized_path.write_bytes(localized)
   a['locales'][lang]={k:v for k,v in content.items()if k!='visualLabels'};a['locales'][lang]['imageAlt']=content['title'];a['locales'][lang]['image']={'url':'/assets/blog/'+localized_path.name,'alt':content['title'],'width':1200,'height':800,'kind':'original-diagram','storage':'private-bundle','sha256':hashlib.sha256(localized).hexdigest()};a['locales'][lang]['products']=[{'id':p['id'],'name':p['names'].get(lang,p['names']['tr']),'image':p['image']}for p in linked]
   translated[lang]+=1
  if a['category']=='surfaces':a['tool']='surface'
  del a['visual']
 ready=minimum>=250 and len(ordered)>=250 and not held
 bank={'schemaVersion':1,'publicationReady':ready,'timezone':'Europe/Istanbul','dailySlots':['09:30','18:30'],'launchImmediately':True,'articles':ordered}
 target=R/'data/blog-bank.json';target.write_text(json.dumps(bank,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf8')
 words=[len(body(a).split())for a in ordered];E.mkdir(exist_ok=True)
 keep={Path(a['image']['url']).name for a in ordered}|{Path(t['image']['url']).name for a in ordered for t in a['locales'].values()};archived=0
 bundle_index,bundle=pack_bundle({'/assets/blog/'+filename:{'bytes':(output/filename).read_bytes(),'mime':'image/svg+xml'}for filename in keep})
 if(E/'deployment.json').exists()and(R/'data/blog-images.json').exists()and(R/'data/blog-images.bin').exists():bundle_index,bundle=merge_bundles(json.loads((R/'data/blog-images.json').read_bytes()),(R/'data/blog-images.bin').read_bytes(),bundle_index,bundle)
 (R/'data/blog-images.bin').write_bytes(bundle)
 (R/'data/blog-images.json').write_text(json.dumps(bundle_index,separators=(',',':'))+'\n',encoding='utf8')
 if not(E/'deployment.json').exists():
  archive=E/'discarded-illustrations';archive.mkdir(exist_ok=True)
  for file in output.glob('*.svg'):
   if file.name in keep:continue
   destination=archive/file.name
   if not file.resolve().is_relative_to(output.resolve())or not destination.resolve().is_relative_to(archive.resolve())or file.is_symlink():raise ValueError('unsafe_illustration_archive_path')
   if destination.exists():destination=archive/(file.stem+'-'+hashlib.sha256(file.read_bytes()).hexdigest()[:12]+file.suffix)
   shutil.move(str(file),str(destination));archived+=1
 report={'articles':len(ordered),'publicationReady':ready,'categories':dict(collections.Counter(a['category']for a in ordered)),'wordCount':{'min':min(words),'median':statistics.median(words),'max':max(words),'total':sum(words)},'uniqueSlugs':len({a['slug']for a in ordered}),'originalIllustrations':len(ordered),'localizedIllustrations':len(keep),'previewIllustrationsArchived':archived,'verifiedProductPhotos':sum(map(len,products.values())),'translations':dict(translated),'heldTranslations':held,'bankSha256':hashlib.sha256(target.read_bytes()).hexdigest(),'paidApiCalls':0,'daysAtTwoPerDay':len(ordered)/2,'sourcesPreserved':True,'publicationDatesInBank':False}
 (E/'content-quality.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({k:v for k,v in report.items()if k!='heldTranslations'},ensure_ascii=True));return report
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--minimum',type=int,default=250);args=p.parse_args();compile_bank(args.minimum)
