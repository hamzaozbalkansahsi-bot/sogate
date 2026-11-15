"""Create a publication snapshot only from current, fully bound four-language translations."""
from pathlib import Path
import json,re,hashlib,importlib.util,concurrent.futures
R=Path(__file__).resolve().parents[1];script=R/'scripts/translate-supplier-content.py';env={'__file__':str(script)};source=script.read_text(encoding='utf8');exec(source.split('for key,template in templates.items():')[0],env);exec(source[source.index('def bind('):source.index('def export():')],env)
O=env['O'];out=[];held=[];receipts={};excluded=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=24)as pool:
 prefetched=dict(pool.map(lambda file:(file.name,file.read_bytes()),env['CACHE'].glob('*.json')))
name_spec=importlib.util.spec_from_file_location('supplier_titles',R/'lib/supplier_titles.py');naming=importlib.util.module_from_spec(name_spec);name_spec.loader.exec_module(naming)
orthography={'tekli':'Tekli','teklı':'Tekli','dılsız':'Dilsiz','usak':'Uşak','klasık':'Klasik','kıtaplık':'Kitaplık','islemeli':'İşlemeli','ı̇şlemeli':'İşlemeli','çalışma':'Çalışma','çalısma':'Çalışma','çızgılı':'Çizgili','dösemelı':'Döşemeli','sıfonyer':'Şifonyer','cevız':'Ceviz','mese':'Meşe','kose':'Köşe','baslık':'Başlık','sılver':'Silver','krıstal':'Kristal'}
def corrected_title(text):return re.sub(r'\b[^\W\d_]+\b',lambda m:orthography.get(m[0].lower(),m[0]),text)
def check(key,lang):
 identity=(key,lang)
 if identity in receipts:return receipts[identity]
 file=env['file'](key,lang);body=prefetched[file.name];value=json.loads(body);env['validate'](env['templates'][key],value['translation'])
 if value.get('source')!=env['templates'][key]or value.get('sourceSha256')!=key:raise ValueError('translation_source_hash_mismatch')
 if value.get('localOnly')and value.get('glossaryVersion')!=3:raise ValueError('obsolete_terminology')
 receipts[identity]={'sha256':hashlib.sha256(body).hexdigest(),'provider':value.get('provider'),'numericTokensVerified':True,'translation':value['translation']};return receipts[identity]
env['translated']=lambda key,lang:receipts[(key,lang)]['translation']
for position,p in enumerate(env['rows']):
 if position%500==0:print(json.dumps({'checkingProducts':position,'approved':len(out),'held':len(held)}),flush=True)
 try:
  bindings=env['bindings'][p['id']];name={'tr':corrected_title(p['title'])};paragraphs={'tr':p['paragraphs']}
  for lang in env['languages']:
   if lang=='ar'and p['supplierId']=='altinis':name[lang]=naming.titles(p)[lang]
   else:
    check(bindings['title']['key'],lang);name[lang]=env['bind'](bindings['title'],lang,'')
   expected={'bedside':('bedside|nightstand','тумб'),'dresser':('chest.*drawers|dresser|chiffonier|commode','комод'),'headboard':('headboard','изголов'),'leg':('leg','ножк'),'table-leg':('leg','ножк'),'cabriole':('leg','ножк'),'turned-leg':('leg','ножк'),'ottoman':('(?:ottoman|pouf).*frame','каркас'),'seating':('(?:seating|sofa|lounge).*set','комплект'),'sideboard':('sideboard|buffet','буфет|комод'),'console':('console','консол'),'mirror':('mirror.*frame','рам')}.get(naming.kind(p))
   if p['supplierId']=='altinis'and expected and lang in ['en','ru']and not re.search(expected[0 if lang=='en'else 1],name[lang],re.I):name[lang]=naming.titles(p)[lang]
   for entry in bindings['paragraphs']:check(entry['key'],lang)
   paragraphs[lang]=[env['bind'](entry,lang,name[lang])for entry in bindings['paragraphs']]
  if p['id']=='alka-2d5463b045':name.update(en='Wooden newel cap',ru='Деревянное навершие лестничного столба',ar='غطاء خشبي لعمود الدرج')
  # Supplier keyword stuffing is not customer-facing product information; archived source stays intact.
  keep=[]
  for i,text in enumerate(p['paragraphs']):
   low=text.casefold();keyword_tail=text.count(',')>=2 and not re.search(r'[.!?;]',text)and any(low.count(word)>=3 for word in ['sehpa','sandalye','dresuar','masa','ayna','komodin','şifonyer'])
   if keyword_tail:excluded.append({'id':p['id'],'sourceParagraphSha256':hashlib.sha256(text.encode()).hexdigest(),'reason':'supplier_search_keyword_tail'})
   else:keep.append(i)
  paragraphs={lang:[texts[i]for i in keep]for lang,texts in paragraphs.items()}
  out.append({**p,'paragraphs':[p['paragraphs'][i]for i in keep],'name':name,'translatedParagraphs':paragraphs,'translationVerified':True,'translationVerification':{'numericSlotsPreserved':True,'currentTerminology':True,'locales':['tr','en','ru','ar']}})
 except (ValueError,OSError,KeyError)as e:held.append({'id':p['id'],'reason':str(e).split('translation-cache')[-1][-160:]})
report={'products':len(out),'expected':len(env['rows']),'held':held,'verifiedUniqueTranslationReceipts':len(receipts),'supplierKeywordParagraphsExcluded':len(excluded),'sourceContentSha256':hashlib.sha256((O/'content-tr.json').read_bytes()).hexdigest(),'publicationReady':False}
target=O/'content-publication-approved.json';temp=target.with_suffix('.tmp');temp.write_text(json.dumps({'products':out,'report':report},ensure_ascii=False,indent=2)+'\n',encoding='utf8');temp.replace(target)
(O/'publication-translation-review.json').write_text(json.dumps({**report,'keywordExclusions':excluded},ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({k:v for k,v in report.items()if k!='held'}),flush=True)
