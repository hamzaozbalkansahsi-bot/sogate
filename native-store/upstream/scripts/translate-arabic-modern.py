"""Complete held Arabic technical paragraphs with the pinned Helsinki-NLP model."""
from pathlib import Path
import json,re,time,hashlib,os
import ctranslate2
from transformers import MarianTokenizer
R=Path(__file__).resolve().parents[1];script=R/'scripts/translate-supplier-content.py';env={'__file__':str(script)};exec(script.read_text(encoding='utf8').split('for key,template in templates.items():')[0],env)
O=env['O'];base='artifacts/supplier-expansion/publication/local-models/opus-tc-big-en-ar';tokenizer=MarianTokenizer.from_pretrained(base,local_files_only=True);model=ctranslate2.Translator(base+'-ct2',compute_type='int8',intra_threads=4,inter_threads=2)
title_keys={entry['title']['key']for entry in env['bindings'].values()}
if os.environ.get('NODENO_ARABIC_QUALITY_REPAIR')=='1':
 keys=[row['key']for row in json.loads((O/'language-quality-flags.json').read_bytes())]
else:keys=[key for key in env['templates']if key not in title_keys and not env['cached'](key,'ar')]
token=re.compile(r'(ZXQ(?:\d+|PN|MODEL[A-Z])ZXQ)');saved=[];held=[]
def translate(texts):
 encoded=[tokenizer.convert_ids_to_tokens(tokenizer.encode('>>ara<< '+text))for text in texts]
 result=model.translate_batch(encoded,beam_size=3,replace_unknowns=True,max_batch_size=2048,batch_type='tokens',max_input_length=0,max_decoding_length=512)
 return[tokenizer.decode(tokenizer.convert_tokens_to_ids(row.hypotheses[0]),skip_special_tokens=True)for row in result]
def polish(text,english):
 if re.search(r'chest\s+of\s+drawers',english,re.I):
  text=re.sub(r'(?:الصدر|صدر)\s+(?:من\s+)?(?:ال)?أدراج','خزانة الأدراج',text)
 if re.search(r'\bpainting\b',english,re.I):
  text=text.replace('اللوحة اختيارية وغير مدرجة','الطلاء اختياري وغير مشمول').replace('اللوحة اختيارية','الطلاء اختياري').replace('اللوحة','الطلاء')
 text=text.replace('خشب الزان القشرة','قشرة خشب الزان').replace('قشرة الزان','قشرة خشب الزان')
 return text
print(json.dumps({'modernArabicParagraphs':len(keys)}),flush=True)
for start in range(0,len(keys),16):
 batch=keys[start:start+16];english=[json.loads(env['file'](key,'en').read_bytes())['translation']for key in batch]
 translated=translate(english)
 for key,source,text in zip(batch,english,translated):
  try:
   try:env['validate'](env['templates'][key],text)
   except ValueError:
    parts=token.split(source);indices=[i for i,value in enumerate(parts)if value.strip()and not token.fullmatch(value)]
    values=translate([parts[i]for i in indices])
    for i,value in zip(indices,values):parts[i]=value
    text=' '.join(parts);env['validate'](env['templates'][key],text)
   text=polish(text,source)
   if 'ZXQ' in token.sub('',text):raise ValueError('orphan_placeholder')
   if not re.search(r'[\u0600-\u06ff]',text):raise ValueError('arabic_script_missing')
   receipt={'source':env['templates'][key],'sourceSha256':key,'targetLanguage':'ar','translation':text,'provider':'Helsinki-NLP/opus-mt-tc-big-en-ar, pinned official model, reviewed furniture corrections','localOnly':True,'glossaryVersion':3,'numericTokensVerified':True,'fetchedAt':time.time(),'pivotSourceSha256':hashlib.sha256(source.encode()).hexdigest()};env['file'](key,'ar').write_text(json.dumps(receipt,ensure_ascii=False)+'\n',encoding='utf8');saved.append(key)
  except ValueError as e:held.append({'key':key,'reason':str(e)})
 if start%64==0:print(json.dumps({'processed':start+len(batch),'saved':len(saved),'held':len(held)}),flush=True)
(O/'modern-arabic-report.json').write_text(json.dumps({'saved':len(saved),'held':held},indent=2)+'\n');print(json.dumps({'modernArabicSaved':len(saved),'held':len(held)}),flush=True)
