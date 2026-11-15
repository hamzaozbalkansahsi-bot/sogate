// Human-facing dates follow the selected country. Storage and API timestamps remain ISO/UTC.
const defaults={TR:'Europe/Istanbul',GB:'Europe/London',US:'America/New_York',CA:'America/Toronto',AU:'Australia/Sydney',NZ:'Pacific/Auckland',DE:'Europe/Berlin',RU:'Europe/Moscow',AZ:'Asia/Baku',KZ:'Asia/Almaty',TM:'Asia/Ashgabat',UZ:'Asia/Tashkent',KG:'Asia/Bishkek',IR:'Asia/Tehran',IQ:'Asia/Baghdad',SY:'Asia/Damascus',SA:'Asia/Riyadh',AE:'Asia/Dubai',CN:'Asia/Shanghai',IN:'Asia/Kolkata',BR:'America/Sao_Paulo',MX:'America/Mexico_City',ID:'Asia/Jakarta',ES:'Europe/Madrid',PT:'Europe/Lisbon',FR:'Europe/Paris',NL:'Europe/Amsterdam',IT:'Europe/Rome',UA:'Europe/Kyiv',JP:'Asia/Tokyo',KR:'Asia/Seoul',ZA:'Africa/Johannesburg',EG:'Africa/Cairo',PK:'Asia/Karachi',BD:'Asia/Dhaka',CL:'America/Santiago',AR:'America/Argentina/Buenos_Aires'};
export function selectedCountry(){
 try{const raw=globalThis.localStorage?.getItem('nodeno.market-country.v1');if(raw){let value;try{value=JSON.parse(raw);}catch{value=raw;}if(typeof value==='string'&&/^[A-Z]{2}$/.test(value))return value;}}catch{}
 const cookie=globalThis.document?.cookie?.match(/(?:^|;\s*)nodeno_market_country=([A-Z]{2})(?:;|$)/);return cookie?.[1]||'TR';
}
export function dateTimeSettings(country=selectedCountry(),options={}){
 country=typeof country==='string'&&/^[A-Z]{2}$/.test(country)?country:'TR';let locale='tr-TR',zones=[];
 try{const region=new Intl.Locale('und-'+country);locale=region.maximize().language+'-'+country;zones=typeof region.getTimeZones==='function'?region.getTimeZones():(region.timeZones||[]);}catch{country='TR';}
 const device=options.deviceTimeZone||Intl.DateTimeFormat().resolvedOptions().timeZone;
 let timeZone=options.timeZone||(country==='TR'?'Europe/Istanbul':zones.includes(device)?device:(defaults[country]||zones[0]||'UTC'));
 try{new Intl.DateTimeFormat(locale,{timeZone});}catch{timeZone=defaults[country]||'Europe/Istanbul';}
 return {country,locale,timeZone,...(country==='TR'?{hourCycle:'h23',calendar:'gregory',numberingSystem:'latn'}:{})};
}
function dateValue(value){if(value instanceof Date)return new Date(value.getTime());if(typeof value==='number')return new Date(Math.abs(value)<100000000000?value*1000:value);if(typeof value==='string'&&value)return new Date(value);return new Date(NaN);}
function settings(options){return dateTimeSettings(options.country||selectedCountry(),options);}
export function formatDate(value,options={}){
 const s=settings(options),civil=typeof value==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(value),date=dateValue(civil?value+'T12:00:00Z':value);if(!Number.isFinite(date.getTime())||(civil&&date.toISOString().slice(0,10)!==value))return '';
 const fmt=new Intl.DateTimeFormat(s.locale,{day:'2-digit',month:'2-digit',year:'numeric',calendar:'gregory',timeZone:civil?'UTC':s.timeZone,...(s.country==='TR'?{numberingSystem:'latn'}:{})});
 if(s.country==='TR'){const p=Object.fromEntries(fmt.formatToParts(date).map(x=>[x.type,x.value]));return p.day+'/'+p.month+'/'+p.year;}return fmt.format(date);
}
export function formatTime(value,options={}){
 const s=settings(options),date=dateValue(value);if(!Number.isFinite(date.getTime()))return '';
 return new Intl.DateTimeFormat(s.locale,{hour:'2-digit',minute:'2-digit',timeZone:s.timeZone,...(s.hourCycle?{hourCycle:s.hourCycle}:{})}).format(date);
}
export function formatDateTime(value,options={}){const day=formatDate(value,options),time=formatTime(value,options);return day&&time?day+' '+time:'';}
export function dateTimeInput(value,options={}){
 const s=settings(options),date=dateValue(value);if(!Number.isFinite(date.getTime()))return '';
 const p=Object.fromEntries(new Intl.DateTimeFormat('en-CA',{timeZone:s.timeZone,calendar:'gregory',numberingSystem:'latn',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hourCycle:'h23'}).formatToParts(date).map(x=>[x.type,x.value]));
 return p.year+'-'+p.month+'-'+p.day+'T'+p.hour+':'+p.minute;
}
export function parseDateTimeInput(value,options={}){
 if(typeof value!=='string'||!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/.test(value))throw new RangeError('invalid_local_time');
 const desired=Date.parse(value+'Z');if(!Number.isFinite(desired))throw new RangeError('invalid_local_time');let guess=desired;
 for(let i=0;i<4;i++){const rendered=dateTimeInput(new Date(guess),options);const difference=desired-Date.parse(rendered+'Z');if(!difference)break;guess+=difference;}
 const matches=[];for(const delta of[-7200000,-3600000,0,3600000,7200000])if(dateTimeInput(new Date(guess+delta),options)===value)matches.push(guess+delta);
 if(!matches.length)throw new RangeError('nonexistent_local_time');return new Date(Math.min(...matches));
}
let mounted=false;
export function mountDateTime(){
 if(typeof document==='undefined'||mounted)return;mounted=true;let previous='';
 const update=()=>{
  const country=selectedCountry();if(country!==previous){previous=country;const preference=dateTimeSettings(country),suffix='; Path=/; Max-Age=31536000; SameSite=Lax'+(location.protocol==='https:'?'; Secure':'');document.cookie='nodeno_market_country='+country+suffix;document.cookie='nodeno_date_timezone='+preference.timeZone+suffix;document.documentElement.dataset.dateCountry=country;document.documentElement.dataset.dateTimeZone=preference.timeZone;window.dispatchEvent(new CustomEvent('nodeno:date-preference',{detail:preference}));}
  for(const node of document.querySelectorAll('time[datetime], [data-date-value]')){
   const raw=node.getAttribute('datetime')||node.dataset.dateValue,kind=node.dataset.dateKind||(String(raw).includes('T')?'datetime':'date');const value=kind==='time'?formatTime(raw):kind==='date'?formatDate(raw):formatDateTime(raw);if(value&&node.textContent!==value)node.textContent=value;
  }
 };
 update();new MutationObserver(update).observe(document.documentElement,{childList:true,subtree:true,attributes:true,attributeFilter:['lang','data-visitor-country','datetime','data-date-value']});window.addEventListener('storage',update);window.addEventListener('pageshow',update);document.addEventListener('visibilitychange',()=>{if(!document.hidden)update();});document.addEventListener('change',()=>queueMicrotask(update));document.addEventListener('click',()=>queueMicrotask(update));
}
