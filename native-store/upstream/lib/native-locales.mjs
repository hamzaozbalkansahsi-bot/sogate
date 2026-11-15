import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import path from 'node:path';
import {nativeLocales,registerLocaleDictionary} from '../web/locale-runtime.js';
const hash=body=>createHash('sha256').update(body).digest('hex');
export async function loadNativeDictionaries(root,{testOnly=false}={}){
 const proof=JSON.parse(await readFile(path.join(root,'artifacts/target-locales-20261111/coverage.json'),'utf8'));
 if(!testOnly&&(proof.complete!==true||proof.missingCount!==0))throw new Error('Native dictionaries incomplete; draft translations cannot be published.');
 if(!testOnly){
  const languageAudit=JSON.parse(await readFile(path.join(root,'artifacts/target-locales-20261111/language-audit.json'),'utf8'));
  if(languageAudit.passed!==true||languageAudit.candidateCount!==0||languageAudit.coverageSha256!==hash(await readFile(path.join(root,'artifacts/target-locales-20261111/coverage.json')))||JSON.stringify(languageAudit.files)!==JSON.stringify(proof.files))throw new Error('Native language quality audit is missing or stale.');
  if(hash(await readFile(path.join(root,'artifacts/target-locales-20261111/inventory.json')))!==proof.sourceInventorySha256)throw new Error('Native translation inventory changed.');
  for(const [name,digest]of Object.entries(proof.sourceFiles||{})){
   if(!/^(?:web\/[A-Za-z0-9_-]+\.js|hosting\/[A-Za-z0-9_-]+\.php|data\/localization\/[A-Za-z0-9_.-]+\.json|data\/legal\/[A-Za-z0-9_-]+\.en\.json|lib\/target_locale_templates\.py|scripts\/(?:inventory-target-locales\.mjs|compile-target-locales\.py))$/.test(name)||hash(await readFile(path.join(root,name)))!==digest)throw new Error('Native translation source changed: '+name);
  }
 }
 const dictionaries={};
 for(const locale of nativeLocales){
  let payload;
  for(const kind of ['ui','catalogue']){
   const bytes=await readFile(path.join(root,'web/locales',locale+(kind==='ui'?'':'.catalogue')+'.json')),part=JSON.parse(bytes);
   if(hash(bytes)!==proof.files[locale][kind]||part.sourceInventorySha256!==proof.sourceInventorySha256||part.kind!==kind)throw new Error('Native dictionary digest mismatch: '+locale);
   payload=payload?{...payload,translations:{...payload.translations,...part.translations}}:part;
  }
  if(!testOnly&&Object.keys(payload.translations||{}).length<proof.sources)throw new Error('Native dictionary coverage mismatch.');
  registerLocaleDictionary(locale,payload);dictionaries[locale]=payload;
 }
 return {dictionaries,proof};
}
export function verifyNativeCatalogue(value,dictionaries,seen=new WeakSet()){
 if(!value||typeof value!=='object'||seen.has(value))return;
 seen.add(value);
 if(['tr','en','ru','ar'].every(lang=>Object.hasOwn(value,lang))&&typeof value.en==='string'){
  const source=value.en;
  if(['tr','ru','ar'].every(lang=>value[lang]===source)||!/[A-Za-z]{2}/.test(source)||/^(?:https?:\/\/|\/|[\w.+-]+@[\w.-]+\.[A-Za-z]+$)/.test(source))return;
  for(const locale of nativeLocales)if(!value[locale]&&!dictionaries[locale]?.translations?.[source])throw new Error('Native catalogue translation missing: '+locale+' '+source.slice(0,90));
  return;
 }
 for(const item of Object.values(value))verifyNativeCatalogue(item,dictionaries,seen);
}
