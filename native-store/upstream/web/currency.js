import {convertTryMinor} from './door-core.js?v=storefront-recovery-20261112-r1';
let active='TRY',snapshot=null;
export function currencyState(){return {currency:active,snapshot};}
export function setCurrency(code,rates=null){
 if(rates)snapshot=rates;
 if(code!=='TRY'&&(!/^[A-Z]{3}$/.test(code)||!snapshot?.rates?.[code]||snapshot.policy!=='week_to_date_highest_forex_selling'||snapshot.validUntil*1000<Date.now()))throw new TypeError('exchange_rate_unavailable');
 active=code;return active;
}
export function displayMoney(tryMinor,locale='tr'){
 if(!Number.isSafeInteger(tryMinor)||tryMinor<0)return null;
 const language=['tr','en','ru','ar','de','az','kk','tk','uz','ky','fa'].includes(locale)?locale:'tr';let code=active,minor=tryMinor;
 const formatter=new Intl.NumberFormat(language,{style:'currency',currency:code});const exponent=formatter.resolvedOptions().maximumFractionDigits;
 if(code!=='TRY'){
  if(!snapshot?.rates?.[code]||snapshot.validUntil*1000<Date.now())return null;
  minor=convertTryMinor(tryMinor,snapshot.rates[code],exponent);
 }
 const scale=10n**BigInt(exponent),exact=BigInt(minor),decimal=exponent?`${exact/scale}.${String(exact%scale).padStart(exponent,'0')}`:String(exact);
 return formatter.format(decimal);
}
