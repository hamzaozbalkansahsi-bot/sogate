"""Resume missing public translations locally; never overwrite validated cached translations."""
from pathlib import Path
import ctranslate2,sentencepiece as sp,json,re,hashlib,time
R=Path(__file__).resolve().parents[1];script=R/'scripts/translate-supplier-content.py';env={'__file__':str(script)};exec(script.read_text(encoding='utf8').split("print(json.dumps({'templates':")[0],env)
O=env['O'];models=O/'local-models';templates=env['templates'];keys=list(templates);title_keys={b['title']['key']for b in env['bindings'].values()};keys.sort(key=lambda k:(k not in title_keys,len(templates[k])))
terms={
 'kayın kaplama':'beech veneer','kayın ağacı':'beech wood','kayın ahşap':'beech wood','gürgen ağacı':'hornbeam wood','çam ağacı':'pine wood','meşe ağacı':'oak wood','ayous ağacı':'ayous wood','ıhlamur ağacı':'lime wood','dişbudak':'ash wood','kestane':'chestnut','boyasız':'unpainted','cilasız':'unvarnished','döşemesiz':'without upholstery','iskeleti':'frame','iskelet':'frame','metretül':'linear metre','dilsiz uşak':'valet stand','merdiven babası':'newel post','merdiven topuzu':'newel cap','lü kens':'cabriole','lükens':'cabriole'}
terms.update({'şifonyer':'chest of drawers','sıfonyer':'chest of drawers','komodin':'bedside cabinet','gardırop':'wardrobe','oymalı':'carved','oyma':'carving','işlemeli':'ornamented','i̇şlemeli':'ornamented','islemeli':'ornamented','işelemeli':'ornamented','hasırlı':'cane-seated','hasır':'woven cane','hazeran':'woven cane','oturum':'seat','fitilli':'fluted','çizgili':'grooved','çızgılı':'grooved','ayak':'furniture leg','ayaklar':'furniture legs','ayakları':'furniture legs','kayın':'beech','çam':'pine','meşe':'oak','mese':'oak','ceviz':'walnut','cevız':'walnut','ıhlamur':'lime wood','gürgen':'hornbeam','kaplama':'veneer','kapak':'door panel','kapaklı':'with doors','çekmece':'drawer','çekmeceli':'with drawers','sandalye':'chair','sandalyesi':'chair','masa':'table','masası':'table','sehpa':'occasional table','sehpası':'occasional table','zigon':'nesting','dresuar':'console table','konsol':'sideboard','berjer':'armchair','koltuk':'sofa','oturma grubu':'seating set','kitaplık':'bookcase','ayna':'mirror','çerçeve':'frame','başlık':'headboard','karyola':'bed frame','baza':'bed base','puf':'ottoman','tabure':'stool','gümüşlük':'display cabinet','vitrin':'display cabinet','saksılık':'plant stand','askılık':'coat stand','dümen':'ship wheel','rozet':'rosette','göbek':'ornamental medallion','aplik':'wooden applique','çıta':'moulding','çıtası':'moulding','çıtalar':'mouldings','panjur':'louvre','seperatör':'divider','separatör':'divider','kulp':'handle','kavela':'dowel','boyanabilir':'paintable','ham':'unfinished','döşeme':'upholstery','kumaş':'fabric','sünger':'foam','dolgusuz':'without padding','döşemeli':'upholstered','dösemelı':'upholstered','fabrikasyon':'factory-made','masif':'solid wood','doğal ahşap':'natural wood','gerçek ağaç':'solid wood','kayın ahşabı':'beech wood','ahşap':'wooden','ahsap':'wooden','genişlik':'width','yükseklik':'height','derinlik':'depth','malzeme':'material','ağırlık':'weight','sabit':'fixed','açılır':'extendable','acılır':'extendable','döner':'swivel','döşemesiz':'without upholstery','boyama işlemi isteğe bağlıdır ve ücrete dahil değildir; seçilen renge göre ayrıca ücretlendirilir.':'Painting is optional, excluded from the price and charged separately according to the chosen colour.'})
terms.update({'hasırlı':'cane','tv sehpası':'TV stand','çalışma masası':'desk','çalışma masaları':'desks','orta sehpa':'coffee table','yan sehpa':'side table','zigon sehpa':'nesting tables','masatablası':'tabletop','masa tablası':'tabletop','ayak malzemesi':'leg material','ayak yapısı':'leg construction','oturum':'seat','sırt':'backrest','sırtlı':'with a backrest','sırtlık':'backrest','hammadde':'raw material'})
term_pattern=re.compile(r'(?<!\w)(?:'+'|'.join(re.escape(k)for k in sorted(terms,key=len,reverse=True))+r')(?!\w)',re.I)
token_re=re.compile(r'ZXQ(?:\d+|PN|MODEL[A-Z])ZXQ')

def engine(pair):
 folder=next((models/('translate-'+pair)).glob('*/sentencepiece.model')).parent
 return sp.SentencePieceProcessor(model_file=(folder/'sentencepiece.model').relative_to(R).as_posix()),ctranslate2.Translator((folder/'model').relative_to(R).as_posix(),device='cpu',compute_type='int8',inter_threads=2,intra_threads=4)

def translate_many(engine,texts):
 tokenizer,translator=engine;segments=[];owners=[]
 for i,text in enumerate(texts):
  parts=re.split(r'(?<=[.!?;])\s+',text)
  for part in parts:
   chunks=re.split(r'(?<=,)\s+',part)if len(part)>380 else[part]
   for chunk in chunks:
    while len(chunk)>380:
     cut=chunk.rfind(' ',0,380)
     if cut<50:cut=380
     segments.append(chunk[:cut]);owners.append(i);chunk=chunk[cut:].strip()
    if chunk:segments.append(chunk);owners.append(i)
 results=translator.translate_batch([tokenizer.encode(t,out_type=str)for t in segments],beam_size=2,replace_unknowns=True,max_batch_size=2048,batch_type='tokens',max_input_length=0,max_decoding_length=384,length_penalty=.2,repetition_penalty=1.1)
 output=[''for _ in texts]
 for owner,result in zip(owners,results):output[owner]+=(' 'if output[owner]else'')+tokenizer.decode(result.hypotheses[0])
 return output

for lang,pair in [('en','tr_en'),('ru','en_ru'),('ar','en_ar')]:
 engine_pair=engine(pair);pending=[k for k in keys if not env['cached'](k,lang)or(json.loads(env['file'](k,lang).read_bytes()).get('localOnly')and json.loads(env['file'](k,lang).read_bytes()).get('glossaryVersion')!=3)];done=0;failed=[];start=time.time();print(json.dumps({'localTranslation':lang,'pending':len(pending)}),flush=True)
 for offset in range(0,len(pending),32):
  batch=pending[offset:offset+32];entries=[]
  for key in batch:
   if lang=='en':source=templates[key]
   elif env['cached'](key,'en'):source=json.loads(env['file'](key,'en').read_bytes())['translation']
   else:failed.append({'key':key,'reason':'english_pending'});continue
   restore={}
   if lang=='en':
    def protect(match):
     token='ZXQTERM'+str(len(restore))+'ZXQ';restore[token]=next(value for name,value in terms.items()if name.replace('ı','i').casefold().replace('i̇','i')==match.group().replace('ı','i').casefold().replace('i̇','i'));return' '+token+' '
    source=term_pattern.sub(protect,source)
   source=token_re.sub(lambda m:' '+m[0]+' ',source)
   entries.append((key,source,restore))
  texts=translate_many(engine_pair,[t[1]for t in entries])if entries else[]
  for (key,source,restore),text in zip(entries,texts):
   try:
    for token,word in restore.items():
     if text.count(token)!=1:raise ValueError('terminology_placeholder_lost')
     text=text.replace(token,word)
    text=re.sub(r'\bWood chair skeleton\b','Wooden chair frame',text,flags=re.I)
    if lang=='en':text=text.replace('hot wooden texture','warm wood grain').replace('fashionable surface','elegant surface').replace('the only service','a single combined service')
    if lang=='ru':text=text.replace('Живопись','Покраска').replace('живопись','покраска').replace('скелет','каркас')
    env['validate'](templates[key],text)
    if lang=='ar'and len(re.sub(r'ZXQ\w+ZXQ','',templates[key]))>8 and not re.search(r'[\u0600-\u06ff]',text):raise ValueError('arabic_script_missing')
    receipt={'sourceLanguage':'tr','targetLanguage':lang,'sourceSha256':key,'source':templates[key],'translation':text,'provider':'Argos official offline models / CTranslate2; English pivot for ru/ar','numericTokensVerified':True,'localOnly':True,'glossaryVersion':3,'modelPair':pair,'fetchedAt':time.time()};env['file'](key,lang).write_text(json.dumps(receipt,ensure_ascii=False)+'\n',encoding='utf8');done+=1
   except ValueError as e:failed.append({'key':key,'reason':str(e)})
  if offset%256==0:print(json.dumps({'language':lang,'processed':offset+len(batch),'saved':done,'held':len(failed),'seconds':round(time.time()-start)}),flush=True)
  if offset and offset%1024==0:env['export']()
 (O/('local-translation-'+lang+'-failures.json')).write_text(json.dumps(failed,indent=2)+'\n');env['export']();del engine_pair
