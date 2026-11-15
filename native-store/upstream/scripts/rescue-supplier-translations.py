"""Translate held fragments while copying immutable model and numeric slots explicitly."""
from pathlib import Path
import argparse,json,re,hashlib,time
R=Path(__file__).resolve().parents[1];source=R/'scripts/translate-supplier-offline.py';scope={'__file__':str(source)};exec(source.read_text(encoding='utf8').split("for lang,pair in [('en'")[0],scope)
parser=argparse.ArgumentParser();parser.add_argument('--language',choices=['en','ru','ar'],required=True);args=parser.parse_args();lang=args.language;env=scope['env'];O=scope['O'];templates=scope['templates'];engine=scope['engine']({'en':'tr_en','ru':'en_ru','ar':'en_ar'}[lang]);token=re.compile(r'(ZXQ(?:TERM\d+|\d+|PN|MODEL[A-Z])ZXQ)')
changed=set(json.loads((O/'english-rescued-keys.json').read_bytes()))if(O/'english-rescued-keys.json').exists()else set();pending=[]
for key in scope['keys']:
 old=json.loads(env['file'](key,lang).read_bytes())if env['file'](key,lang).exists()else{}
 if not env['cached'](key,lang)or(old.get('localOnly')and old.get('glossaryVersion')!=3)or(lang!='en'and key in changed and old.get('localOnly')):pending.append(key)
print(json.dumps({'rescueLanguage':lang,'pending':len(pending)}),flush=True);saved=[];held=[]
for start in range(0,len(pending),24):
 batch=pending[start:start+24];prepared=[];fragments=[];fragment_map=[]
 for key in batch:
  restore={}
  if lang=='en':
   text=templates[key]
   def protect(match):
    value=next(v for k,v in scope['terms'].items()if k.replace('ı','i').casefold().replace('i̇','i')==match.group().replace('ı','i').casefold().replace('i̇','i'));slot='ZXQTERM'+str(len(restore))+'ZXQ';restore[slot]=value;return' '+slot+' '
   text=scope['term_pattern'].sub(protect,text)
  else:
   if not env['cached'](key,'en'):held.append({'key':key,'reason':'english_pending'});continue
   text=json.loads(env['file'](key,'en').read_bytes())['translation']
  parts=token.split(text);index=len(prepared);prepared.append((key,parts,restore))
  for pos,part in enumerate(parts):
   if token.fullmatch(part)or not re.search(r'[A-Za-zÇĞİÖŞÜçğıöşüА-Яа-я]',part):continue
   fragments.append(part.strip());fragment_map.append((index,pos))
 translated=scope['translate_many'](engine,fragments)if fragments else[]
 for (index,pos),value in zip(fragment_map,translated):prepared[index][1][pos]=value
 for key,parts,restore in prepared:
  try:
   text=' '.join(part.strip()for part in parts if part.strip());text=re.sub(r'\s+([,.;:!?])',r'\1',text)
   for slot,value in restore.items():
    if text.count(slot)!=1:raise ValueError('terminology_slot_mismatch')
    text=text.replace(slot,value)
   env['validate'](templates[key],text)
   if lang=='en':text=text.replace('hot wooden texture','warm wood grain').replace('the only service','a single combined service')
   if lang=='ru':text=text.replace('Живопись','Покраска').replace('живопись','покраска').replace('скелет','каркас')
   if lang=='ar'and not re.search(r'[\u0600-\u06ff]',text)and len(token.sub('',templates[key]).strip())>8:raise ValueError('arabic_script_missing')
   receipt={'source':templates[key],'sourceSha256':key,'targetLanguage':lang,'translation':text,'provider':'Argos offline clause translation with explicitly copied model/numeric/terminology slots','numericTokensVerified':True,'localOnly':True,'glossaryVersion':3,'slotPreservation':'explicit','fetchedAt':time.time()}
   if lang!='en':receipt['pivotSourceSha256']=hashlib.sha256(json.loads(env['file'](key,'en').read_bytes())['translation'].encode()).hexdigest()
   env['file'](key,lang).write_text(json.dumps(receipt,ensure_ascii=False)+'\n',encoding='utf8');saved.append(key)
  except ValueError as e:held.append({'key':key,'reason':str(e)})
 if start%240==0:print(json.dumps({'rescueLanguage':lang,'processed':start+len(batch),'saved':len(saved),'held':len(held)}),flush=True)
if lang=='en':(O/'english-rescued-keys.json').write_text(json.dumps(sorted(changed|set(saved)))+'\n')
(O/('rescue-'+lang+'-report.json')).write_text(json.dumps({'saved':len(saved),'held':held},indent=2)+'\n');print(json.dumps({'rescueLanguage':lang,'saved':len(saved),'held':len(held)}),flush=True)
