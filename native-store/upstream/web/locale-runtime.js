// Locale dictionaries are public display data. They never change product facts.
export const baseLocales=['tr','en','ru','ar'];
export const nativeLocales=['de','az','kk','tk','uz','ky','fa'];
export const storeLocales=[...baseLocales,...nativeLocales];
const key=Symbol.for('nodeno.locale-dictionaries.v1');
const state=globalThis[key]??(globalThis[key]={dictionaries:new Map(),pending:new Map(),catalogues:new Set(),inventories:new Map()});
export function registerLocaleDictionary(locale,payload,{merge=false}={}){
 if(!nativeLocales.includes(locale))throw new TypeError('invalid_locale');
 if(payload?.schema!==1||payload.locale!==locale||!payload.translations||typeof payload.translations!=='object'||Array.isArray(payload.translations))throw new TypeError('invalid_locale_dictionary');
 const translations=new Map();for(const [source,target]of Object.entries(payload.translations)){
  if(typeof target!=='string'||!target.trim())throw new TypeError('invalid_locale_translation');translations.set(source,target);
 }
 if(merge){
  if(!state.dictionaries.has(locale)||!payload.sourceInventorySha256||payload.sourceInventorySha256!==state.inventories.get(locale))throw new TypeError('locale_inventory_mismatch');
  for(const [source,target]of state.dictionaries.get(locale))if(!translations.has(source))translations.set(source,target);
 }
 state.dictionaries.set(locale,translations);state.inventories.set(locale,payload.sourceInventorySha256);
}
export function resetLocaleDictionaries(){state.dictionaries.clear();state.pending.clear();state.catalogues.clear();state.inventories.clear();}
export function nativeText(source,locale){
 if(!nativeLocales.includes(locale)||!source||!/[A-Za-z]{2}/.test(source)||/^(?:https?:\/\/|\/|[\w.+-]+@[\w.-]+\.[A-Za-z]+$)/.test(source))return source;
 const dictionary=state.dictionaries.get(locale);if(!dictionary)throw new Error('locale_dictionary_unavailable:'+locale);
 if(!dictionary.has(source)){
  if(source.includes('\n\n'))return source.split('\n\n').map(part=>nativeText(part,locale)).join('\n\n');
  const error=new Error('locale_translation_missing:'+locale);
  Object.defineProperty(error,'translationSource',{value:source});throw error;
 }
 return dictionary.get(source);
}
function translateTree(value,locale){
 if(typeof value==='string')return nativeText(value,locale);
 if(Array.isArray(value))return value.map(item=>translateTree(item,locale));
 if(value&&typeof value==='object'){
  const result={},converted=new Map();
  for(const [key,item]of Object.entries(value))Object.defineProperty(result,key,{enumerable:true,get(){
   if(!converted.has(key))converted.set(key,translateTree(item,locale));return converted.get(key);
  }});
  return result;
 }
 return value;
}
export function localeCopy(copy,targets=nativeLocales){
 if(!copy||typeof copy!=='object'||!('en'in copy))throw new TypeError('invalid_locale_copy');
 const cached=new Map();
 // Existing source-merge loops enumerate the four original languages at module
 // initialization, before any async dictionary is loaded. Native views are lazy.
 for(const locale of targets)if(!(locale in copy))Object.defineProperty(copy,locale,{enumerable:false,configurable:true,get(){
  if(baseLocales.every(lang=>copy[lang]===copy.en))return copy.en;
  const dictionary=state.dictionaries.get(locale),old=cached.get(locale);
  if(old&&old.dictionary===dictionary)return old.value;
  const value=translateTree(copy.en,locale);cached.set(locale,{dictionary,value});return value;
 }});
 return copy;
}
export function localizeDataTree(value,locale,seen=new WeakSet()){
 if(!nativeLocales.includes(locale))return value;
 if(!value||typeof value!=='object'||seen.has(value))return value;
 seen.add(value);for(const item of Object.values(value))localizeDataTree(item,locale,seen);
 if(baseLocales.every(lang=>Object.hasOwn(value,lang)))localeCopy(value,[locale]);
 return value;
}
export function localizedValue(value,locale='tr'){
 if(value==null)return '';
 if(typeof value!=='object')return String(value);
 if(Object.hasOwn(value,locale))return value[locale]??'';
 if(nativeLocales.includes(locale)){
  const source=value.en;if(typeof source!=='string')return '';
  if(baseLocales.every(lang=>value[lang]===source))return source;
  return nativeText(source,locale);
 }
 return value[locale]??value.tr??value.en??'';
}
const defaultRevision='storefront-recovery-20261112-r1';
export async function ensureLocale(locale,{fetcher=globalThis.fetch,revision=defaultRevision}={}){
 if(!storeLocales.includes(locale))throw new TypeError('invalid_locale');
 if(!nativeLocales.includes(locale)||state.dictionaries.has(locale))return;
 if(!state.pending.has(locale))state.pending.set(locale,(async()=>{
  const response=await fetcher('/locales/'+locale+'.json?v='+encodeURIComponent(revision),{credentials:'same-origin'});
  if(!response.ok)throw new Error('locale_dictionary_unavailable:'+locale);
  registerLocaleDictionary(locale,await response.json());
 })().finally(()=>state.pending.delete(locale)));
 return state.pending.get(locale);
}
export function hasLocaleData(value,locale,seen=new WeakSet()){
 if(!nativeLocales.includes(locale)||!value||typeof value!=='object'||seen.has(value))return true;
 seen.add(value);
 const own=Object.getOwnPropertyDescriptors(value);
 if(baseLocales.every(lang=>Object.hasOwn(own,lang))&&typeof own.en.value==='string'){
  if(own[locale]&&Object.hasOwn(own[locale],'value'))return true;
  const source=own.en.value;
  if(baseLocales.every(lang=>own[lang].value===source)||!/[A-Za-z]{2}/.test(source))return true;
  return state.dictionaries.get(locale)?.has(source)===true;
 }
 return Object.values(own).every(descriptor=>!Object.hasOwn(descriptor,'value')||hasLocaleData(descriptor.value,locale,seen));
}
export async function ensureLocaleData(value,locale,{fetcher=globalThis.fetch,revision=defaultRevision}={}){
 await ensureLocale(locale,{fetcher,revision});
 if(hasLocaleData(value,locale))return;
 const pendingKey=locale+':catalogue';
 if(!state.catalogues.has(locale)&&!state.pending.has(pendingKey))state.pending.set(pendingKey,(async()=>{
  const response=await fetcher('/locales/'+locale+'.catalogue.json?v='+encodeURIComponent(revision),{credentials:'same-origin'});
  if(!response.ok)throw new Error('locale_catalogue_unavailable:'+locale);
  registerLocaleDictionary(locale,await response.json(),{merge:true});state.catalogues.add(locale);
 })().finally(()=>state.pending.delete(pendingKey)));
 await state.pending.get(pendingKey);
 if(!hasLocaleData(value,locale))throw new Error('locale_catalogue_incomplete:'+locale);
}
