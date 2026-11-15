import {readFile,writeFile} from 'node:fs/promises';
import {nativeLocales,registerLocaleDictionary} from '../web/locale-runtime.js';
const tables=[];
for(const file of ['i18n','shop-i18n','shopping-i18n','door-i18n','measurement-i18n','furniture-set-i18n','wholesale-i18n','cabinet-front-ui','home-vitrine','welcome-poster','payments']){
 const mod=await import('../web/'+file+'.js');
 for(const [name,value]of Object.entries(mod))if(value&&typeof value==='object'&&!Array.isArray(value)&&Object.hasOwn(value,'en')&&Object.hasOwn(value,'tr'))tables.push({name:file+'.'+name,value});
}
const missing=[],checked={};
for(const locale of nativeLocales){
 registerLocaleDictionary(locale,JSON.parse(await readFile('web/locales/'+locale+'.json','utf8')));let count=0;
 function walk(value,path){if(typeof value==='string'){count++;return;}if(!value||typeof value!=='object')return;
  for(const key of Object.keys(value))try{walk(value[key],path+'/'+key);}catch(error){missing.push({locale,path:path+'/'+key,source:error.translationSource??'',reason:error.message});}
 }
 for(const table of tables)try{walk(table.value[locale],table.name);}catch(error){missing.push({locale,path:table.name,source:error.translationSource??'',reason:error.message});}
 checked[locale]=count;
}
await writeFile('artifacts/target-locales-20261111/interface-missing.json',JSON.stringify(missing,null,2)+'\n');
const result={passed:missing.length===0,checked,missing:missing.length};await writeFile('artifacts/target-locales-20261111/interface-audit.json',JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result));
if(missing.length)process.exitCode=1;
