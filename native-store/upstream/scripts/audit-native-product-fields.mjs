import {readFile,writeFile} from 'node:fs/promises';
import {loadNativeDictionaries} from '../lib/native-locales.mjs';
import {nativeLocales,nativeText} from '../web/locale-runtime.js';
await loadNativeDictionaries(process.cwd(),{testOnly:true});
const catalog=JSON.parse(await readFile('artifacts/cpanel-release-vitrine-20261111/private/catalog.json','utf8'));
const missing=new Map();let fields=0;
function walk(value,path){
 if(!value||typeof value!=='object')return;
 if(['tr','en','ru','ar'].every(lang=>Object.hasOwn(value,lang))&&typeof value.en==='string'){
  if(['tr','ru','ar'].every(lang=>value[lang]===value.en))return;
  for(const locale of nativeLocales)try{if(!value[locale])nativeText(value.en,locale);fields++;}catch(error){const row=missing.get(value.en)||{source:value.en,locales:new Set(),contexts:[]};row.locales.add(locale);if(row.contexts.length<3)row.contexts.push(path);missing.set(value.en,row);}
  return;
 }
 for(const[key,item]of Object.entries(value))walk(item,path+'/'+key);
}
walk(catalog,'catalog');
const rows=[...missing.values()].map(r=>({...r,locales:[...r.locales]}));
await writeFile('artifacts/target-locales-20261111/canonical-missing.json',JSON.stringify(rows,null,2)+'\n');
const result={passed:rows.length===0,fields,missingSources:rows.length};await writeFile('artifacts/target-locales-20261111/canonical-audit.json',JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result));
