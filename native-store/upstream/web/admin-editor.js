export const editorLocales=[['tr','Türkçe'],['en','İngilizce'],['ru','Rusça'],['ar','Arapça'],['de','Almanca'],['az','Azerbaycanca'],['kk','Kazakça'],['tk','Türkmence'],['uz','Özbekçe'],['ky','Kırgızca'],['fa','Farsça']];
export function fieldLocale(key){return editorLocales.find(([locale])=>key.endsWith('_'+locale))?.[0]??null;}
export function recordSearchText(row,product,title){return JSON.stringify([title,row.id,row.data,product?.code,product?.color]).toLocaleLowerCase('tr');}
// Display inherited catalogue values, but never freeze them as new overrides.
export function editorChanges(initial,current,overrides={}){
 const result={...overrides};
 for(const key of new Set([...Object.keys(initial),...Object.keys(current)])){
  const before=initial[key]??'',after=current[key]??'';
  if(before===after)continue;
  if(after==='')delete result[key];else result[key]=after;
 }
 return result;
}
