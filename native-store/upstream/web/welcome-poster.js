/* native-locale-copy */
import {localeCopy} from './locale-runtime.js?v=storefront-recovery-20261112-r1';
import {createWelcomeCountryMap} from './welcome-country-map.js?v=storefront-recovery-20261112-r1';
export const WELCOME_TIMEOUT=30_000;
export const WELCOME_KEY='nodeno.international-welcome.hidden';
export const welcomeCountries=[
 localeCopy({code:'DE',tr:'Almanya',en:'Germany',ru:'Германия',ar:'ألمانيا'}),
 localeCopy({code:'GB',tr:'Birleşik Krallık',en:'United Kingdom',ru:'Великобритания',ar:'المملكة المتحدة'}),
 localeCopy({code:'AZ',tr:'Azerbaycan',en:'Azerbaijan',ru:'Азербайджан',ar:'أذربيجان'}),
 localeCopy({code:'KZ',tr:'Kazakistan',en:'Kazakhstan',ru:'Казахстан',ar:'كازاخستان'}),
 localeCopy({code:'TM',tr:'Türkmenistan',en:'Turkmenistan',ru:'Туркменистан',ar:'تركمانستان'}),
 localeCopy({code:'UZ',tr:'Özbekistan',en:'Uzbekistan',ru:'Узбекистан',ar:'أوزبكستان'}),
 localeCopy({code:'KG',tr:'Kırgızistan',en:'Kyrgyzstan',ru:'Кыргызстан',ar:'قيرغيزستان'}),
 localeCopy({code:'IQ',tr:'Irak',en:'Iraq',ru:'Ирак',ar:'العراق'}),
 localeCopy({code:'IR',tr:'İran',en:'Iran',ru:'Иран',ar:'إيران'}),
 localeCopy({code:'SY',tr:'Suriye',en:'Syria',ru:'Сирия',ar:'سوريا'})
];
export const welcomeCopy=localeCopy({
 tr:{eyebrow:'Türkiye’den dünyaya',title:['İyi tasarım.','Kolay yaşam.'],intro:'Avrupa, Orta Asya ve Orta Doğu’dan gelen mobilya ve toplu sipariş talepleriniz için buradayız.',countries:'Sipariş kabul ettiğimiz ülkeler',continue:'Mağazayı keşfet',close:'Karşılama posterini kapat',origin:'İzmir, Türkiye',regions:'Avrupa · Orta Asya · Orta Doğu'},
 en:{eyebrow:'From Türkiye to the world',title:['Good design.','Easy living.'],intro:'We welcome furniture and wholesale enquiries from Europe, Central Asia and the Middle East.',countries:'Countries we accept orders from',continue:'Explore the store',close:'Close welcome poster',origin:'Izmir, Türkiye',regions:'Europe · Central Asia · Middle East'},
 ru:{eyebrow:'Из Турции в мир',title:['Продуманный дизайн.','Простая жизнь.'],intro:'Принимаем запросы на мебель и оптовые заказы из Европы, Центральной Азии и Ближнего Востока.',countries:'Страны, из которых принимаем заказы',continue:'Перейти в магазин',close:'Закрыть приветствие',origin:'Измир, Турция',regions:'Европа · Центральная Азия · Ближний Восток'},
 ar:{eyebrow:'من تركيا إلى العالم',title:['تصميم متقن.','حياة أسهل.'],intro:'نرحب بطلبات الأثاث واستفسارات الجملة من أوروبا وآسيا الوسطى والشرق الأوسط.',countries:'الدول التي نقبل الطلبات منها',continue:'اكتشف المتجر',close:'إغلاق الترحيب',origin:'إزمير، تركيا',regions:'أوروبا · آسيا الوسطى · الشرق الأوسط'}
});
Object.assign(welcomeCopy.tr,{dontShow:'Bir daha gösterme',preferenceError:'Tercihiniz bu tarayıcıda kaydedilemedi.',mapLabel:'Ülkeler haritası',mapHelp:'Ok tuşlarıyla ülkeler arasında gezinebilirsiniz.',accepting:'Bu ülkeden sipariş kabul ediyoruz',turkeyStore:'Türkiye mağazası',otherCountry:'Bu ülke için bizimle görüşebilirsiniz'});
Object.assign(welcomeCopy.en,{dontShow:'Do not show again',preferenceError:'Your preference could not be saved in this browser.',mapLabel:'Country map',mapHelp:'Use the arrow keys to explore countries.',accepting:'We accept orders from this country',turkeyStore:'Türkiye store',otherCountry:'Contact us about this country'});
Object.assign(welcomeCopy.ru,{dontShow:'Больше не показывать',preferenceError:'Не удалось сохранить настройку в этом браузере.',mapLabel:'Карта стран',mapHelp:'Используйте клавиши со стрелками для выбора страны.',accepting:'Принимаем заказы из этой страны',turkeyStore:'Магазин в Турции',otherCountry:'Уточните условия для этой страны'});
Object.assign(welcomeCopy.ar,{dontShow:'عدم الإظهار مرة أخرى',preferenceError:'تعذر حفظ تفضيلك في هذا المتصفح.',mapLabel:'خريطة الدول',mapHelp:'استخدم مفاتيح الأسهم للتنقل بين الدول.',accepting:'نقبل الطلبات من هذه الدولة',turkeyStore:'متجر تركيا',otherCountry:'تواصل معنا للاستفسار عن هذه الدولة'});
export function welcomeEligible(page){return ['home','catalog','product','sets','wholesale','categories'].includes(page);}
export function createWelcomeMemory(storage){
 return {
  hidden(){try{return storage?.getItem(WELCOME_KEY)==='1';}catch{return false;}},
  setHidden(value){try{if(!storage)return false;if(value)storage.setItem(WELCOME_KEY,'1');else storage.removeItem(WELCOME_KEY);return this.hidden()===value;}catch{return false;}}
 };
}
const escape=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

export function mountWelcomePoster({state,onCountrySelect=()=>{},document:doc=globalThis.document,window:win=globalThis.window}={}){
 if(!doc||!win||doc.getElementById('international-welcome'))return;
 let storage;try{storage=win.localStorage;}catch{}
 const memory=createWelcomeMemory(storage);
 if(memory.hidden())return;
 let timeout,opening,deadline=0,dialog,previousFocus,countryMap;
 function cleanup(){
  win.clearTimeout(timeout);win.clearTimeout(opening);
  doc.removeEventListener('visibilitychange',onVisibility);
  win.removeEventListener('pagehide',onPageHide);
  countryMap?.destroy();
 }
 function dismiss(){if(dialog?.open)dialog.close();}
 function onVisibility(){if(dialog?.open){if(Date.now()>=deadline)dismiss();}else if(!dialog&&doc.visibilityState==='visible')show();}
 function onPageHide(){dismiss();cleanup();}
 function show(){
  if(doc.visibilityState!=='visible')return;
  if(memory.hidden()){cleanup();return;}
  const snapshot=state();
  // Do not cover an active task or stack this over another native dialog.
  if(!welcomeEligible(snapshot.route?.page)||doc.querySelector('dialog[open]')||doc.activeElement?.matches('input,textarea,select,[contenteditable="true"]')){cleanup();return;}
  const locale=Object.hasOwn(welcomeCopy,snapshot.locale)?snapshot.locale:'tr',text=welcomeCopy[locale];
  previousFocus=doc.activeElement;
  dialog=doc.createElement('dialog');dialog.id='international-welcome';dialog.className='welcome-poster';
  dialog.lang=locale;dialog.dir=['ar','fa'].includes(locale)?'rtl':'ltr';
  dialog.setAttribute('aria-labelledby','welcome-poster-title');dialog.setAttribute('aria-describedby','welcome-poster-intro');
  dialog.innerHTML=`<button class="welcome-poster-close" type="button" aria-label="${escape(text.close)}" autofocus><svg viewBox="0 0 24 24" aria-hidden="true"><path d="m6 6 12 12M18 6 6 18"/></svg></button>
   <div class="welcome-poster-scroll"><div class="welcome-poster-layout">
    <section class="welcome-poster-story"><img class="welcome-poster-logo" src="/assets/brand/logo-horizontal.svg?v=social-keywords-20261113-v6" width="1600" height="360" alt="NODENO"><p class="welcome-poster-eyebrow">${escape(text.eyebrow)}</p><h2 id="welcome-poster-title">${text.title.map(line=>`<span>${escape(line)}</span>`).join('')}</h2><p id="welcome-poster-intro">${escape(text.intro)}</p><button class="welcome-poster-continue" type="button">${escape(text.continue)}</button><label class="welcome-poster-preference"><input id="welcome-dont-show" type="checkbox">${escape(text.dontShow)}</label><p class="welcome-preference-error" role="status" hidden></p><p class="welcome-poster-origin">${escape(text.origin)}</p></section>
    <section class="welcome-poster-world" aria-labelledby="welcome-countries-title"><div class="welcome-map-slot"></div><div class="welcome-poster-destinations"><h3 id="welcome-countries-title">${escape(text.countries)}</h3><ul>${welcomeCountries.map(country=>`<li data-country="${country.code}"><button type="button" data-country-select="${country.code}" aria-pressed="false"><span class="welcome-country-dot" aria-hidden="true"></span>${escape(country[locale])}</button></li>`).join('')}</ul></div></section>
   </div></div><div class="welcome-poster-progress" aria-hidden="true"><span></span></div>`;
  dialog.querySelector('.welcome-poster-close').addEventListener('click',dismiss);
  dialog.querySelector('.welcome-poster-continue').addEventListener('click',dismiss);
  dialog.querySelector('#welcome-dont-show').addEventListener('change',event=>{
   const saved=memory.setHidden(event.target.checked),error=dialog.querySelector('.welcome-preference-error');
   error.hidden=saved;error.textContent=saved?'':text.preferenceError;
  });
  countryMap=createWelcomeCountryMap({doc,win,locale,countries:welcomeCountries,text,onActivate:code=>{dismiss();onCountrySelect(code);},onSelect:code=>dialog.querySelectorAll('[data-country-select]').forEach(button=>{const active=button.dataset.countrySelect===code;button.classList.toggle('is-active',active);button.setAttribute('aria-pressed',String(active));})});
  dialog.querySelector('.welcome-map-slot').replaceWith(countryMap.element);
  dialog.querySelectorAll('[data-country-select]').forEach(button=>{button.addEventListener('pointerenter',event=>{if(event.pointerType!=='touch')countryMap.select(button.dataset.countrySelect);});button.addEventListener('focus',()=>countryMap.select(button.dataset.countrySelect));button.addEventListener('click',()=>{const code=button.dataset.countrySelect;dismiss();onCountrySelect(code);});});
  dialog.addEventListener('keydown',event=>{
   if(event.key!=='Tab')return;
   const targets=[...dialog.querySelectorAll('button,input,[tabindex="0"]')].filter(el=>!el.disabled&&!el.hidden),first=targets[0],last=targets.at(-1);
   if(event.shiftKey&&doc.activeElement===first){event.preventDefault();last.focus();}
   else if(!event.shiftKey&&doc.activeElement===last){event.preventDefault();first.focus();}
  });
  dialog.addEventListener('click',event=>{if(event.target!==dialog)return;const rect=dialog.getBoundingClientRect();if(event.clientX<rect.left||event.clientX>rect.right||event.clientY<rect.top||event.clientY>rect.bottom)dismiss();});
  dialog.addEventListener('close',()=>{cleanup();dialog.remove();if(previousFocus?.isConnected&&previousFocus!==doc.body)previousFocus.focus({preventScroll:true});},{once:true});
  doc.body.append(dialog);
  try{dialog.showModal();}catch{dialog.remove();cleanup();return;}
  deadline=Date.now()+WELCOME_TIMEOUT;
  timeout=win.setTimeout(dismiss,WELCOME_TIMEOUT);
 }
 doc.addEventListener('visibilitychange',onVisibility);
 win.addEventListener('pagehide',onPageHide);
 opening=win.setTimeout(show,450);
 return {dismiss};
}
