/* native-locale-copy */
import {localeCopy,ensureLocale} from './locale-runtime.js?v=storefront-recovery-20261112-r1';
import {setOptionalPreference,readPrivacyPreference} from './privacy-preferences.js?v=storefront-recovery-20261112-r1';
const locale=document.documentElement.lang;
await ensureLocale(locale);
const copy=localeCopy({tr:['Analiz ve kişiselleştirmeye izin ver','Yalnız gerekli','Tercihiniz kaydedildi.','Kaydedilemedi. Yeniden deneyin.'],en:['Allow analytics and personalisation','Necessary only','Your preference was saved.','Could not save. Please retry.'],ru:['Разрешить аналитику и персонализацию','Только необходимые','Настройка сохранена.','Не удалось сохранить. Повторите попытку.'],ar:['السماح بالتحليلات والتخصيص','الضروري فقط','تم حفظ اختيارك.','تعذر الحفظ. حاول مجدداً.']})[locale]||[];
document.querySelector('[data-legal-print]')?.addEventListener('click',()=>window.print());
document.querySelector('[data-legal-preferences]')?.addEventListener('click',()=>{
 const target=document.querySelector('.legal-feedback');target.replaceChildren();
 for(const [label,value]of [[copy[0],true],[copy[1],false]]){const button=document.createElement('button');button.textContent=label;button.type='button';button.className='legal-preference-choice';button.onclick=async()=>{target.querySelectorAll('button').forEach(b=>b.disabled=true);try{await setOptionalPreference(value);target.textContent=copy[2];}catch{target.querySelectorAll('button').forEach(b=>b.disabled=false);button.textContent=copy[3];}};target.append(button);}
 target.dataset.preference=String(readPrivacyPreference());
});
