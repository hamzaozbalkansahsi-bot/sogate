/* native-locale-copy */
import {localeCopy} from './locale-runtime.js?v=storefront-recovery-20261112-r1';
const labels=localeCopy({tr:{notice:'KVKK aydınlatma metni',acknowledge:'Talebimle ilgili kişisel veri aydınlatmasını okudum.'},en:{notice:'Personal data notice',acknowledge:'I have read the personal data notice for my request.'},ru:{notice:'Уведомление о персональных данных',acknowledge:'Я прочитал уведомление об обработке данных по моему запросу.'},ar:{notice:'إشعار البيانات الشخصية',acknowledge:'قرأت إشعار البيانات الشخصية المتعلق بطلبي.'}});
export function legalNotice(locale='tr'){return labels[locale]||labels.en;}
export function mountLegalNotices(locale='tr'){
 const text=legalNotice(locale);
 for(const form of document.querySelectorAll('#register-form')){
  if(form.dataset.membershipLoading||form.dataset.membershipHash)continue;form.dataset.membershipLoading='1';const button=form.querySelector('[type=submit]');if(button)button.disabled=true;
  fetch('/api/account/membership-terms?lang='+locale,{credentials:'same-origin',cache:'no-store'}).then(async response=>{if(!response.ok)throw new Error('membership_unavailable');const value=await response.json();if(!form.isConnected)return;form.dataset.membershipVersion=value.version;form.dataset.membershipHash=value.hash;form.dataset.membershipLocale=value.locale;if(button)button.disabled=false;}).catch(()=>{if(form.isConnected){delete form.dataset.membershipLoading;const status=form.querySelector('.form-status');if(status)status.textContent=localeCopy({tr:'Üyelik koşulları alınamadı. Sayfayı yenileyin.',en:'Membership terms could not be loaded. Reload the page.',ru:'Не удалось загрузить условия. Обновите страницу.',ar:'تعذر تحميل الشروط. أعد تحميل الصفحة.'})[locale];}});
 }
 for(const form of document.querySelectorAll('#guest-checkout-form,#wholesale-form,#door-inquiry-form,#door-quote-form,.store-support-form')){
  const consent=form.querySelector('input[name=consent]');
  if(consent){const label=consent.closest('label');if(label&&!label.dataset.legalAcknowledgement){const input=consent;label.replaceChildren(input,document.createTextNode(' '+text.acknowledge+' '));label.dataset.legalAcknowledgement='1';}}
  if(form.querySelector('[data-legal-notice]'))continue;
  const notice=document.createElement('p');notice.dataset.legalNotice='';notice.className='field-hint';const link=document.createElement('a');link.href='/legal/kvkk?lang='+locale;link.target='_blank';link.rel='noopener';link.textContent=text.notice;notice.append(link);form.append(notice);
 }
}
