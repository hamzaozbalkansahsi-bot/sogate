import {welcomeMapData} from './welcome-map-data.js?v=storefront-recovery-20261112-r1';
import {localizedValue,nativeLocales,nativeText,storeLocales} from './locale-runtime.js?v=storefront-recovery-20261112-r1';
const names=new Map(welcomeMapData.regions.filter(r=>/^[A-Z]{2}$/.test(r.code)).map(r=>[r.code,r.names]));
// The regional poster does not include the Americas, but delivery forms include US.
const usNames=['Amerika Birleşik Devletleri','United States','Соединённые Штаты','الولايات المتحدة','Vereinigte Staaten','Amerika Birləşmiş Ştatları','Америка Құрама Штаттары','Amerikanyň Birleşen Ştatlary','Amerika Qoʻshma Shtatlari','Америка Кошмо Штаттары','ایالات متحده آمریکا'];
export function countryLabel(code,locale){
 if(code==='US')return usNames[storeLocales.indexOf(locale)]||code;
 const source=names.get(code);
 if(source)return nativeLocales.includes(locale)?nativeText(source.en,locale):localizedValue(source,locale);
 if(!nativeLocales.includes(locale))try{return new Intl.DisplayNames([locale],{type:'region'}).of(code)||code;}catch{}
 // An unknown ISO code is factual; never substitute another language's name.
 return code;
}
