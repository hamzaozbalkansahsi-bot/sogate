/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/public/assets/app.js
 * Açıklama   : PHP formlarını erişilebilir durum/hata, imzalı özet ve açık kullanıcı onayıyla çalıştırır.
 */
(()=>{
 'use strict';
 const base=document.body.dataset.base||'',en=document.body.dataset.locale==='en',csrf=document.querySelector('meta[name="csrf-token"]')?.content||'';
 const message=en?'The request could not be completed. Try again.':'İşlem tamamlanamadı. Yeniden deneyin.';
 const id=()=>crypto.randomUUID();
 async function api(path,data){const response=await fetch(base+path,{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':csrf},body:JSON.stringify(data),cache:'no-store'});let body;try{body=await response.json();}catch{throw Error(message);}if(!response.ok){const error=Error(body.error||message);error.code=body.code;throw error;}return body;}
 function fields(form){const data=Object.fromEntries(new FormData(form));for(const input of form.querySelectorAll('input[type="checkbox"]'))data[input.name]=input.checked;for(const key of ['quantity','priceMinor','costMinor','unitCostMinor','version','leadDays','minDays','maxDays','safetyStock'])if(key in data){if(!/^\d+$/.test(data[key]))throw Error(message);data[key]=Number(data[key]);}for(const input of form.querySelectorAll('input[type="datetime-local"]'))if(data[input.name])data[input.name]=new Date(data[input.name]).toISOString();return data;}
 function show(form,text){const output=form.querySelector('.form-message');if(output){output.textContent=text;output.focus?.();}}
 function redirect(path){if(typeof path==='string'&&path.startsWith(base+'/')&&!path.startsWith('//'))location.assign(path);}
 async function quote(){const form=document.getElementById('checkout-form');const data=fields(form);delete data.quoteToken;const result=await api('/api/quote',data);form.elements.quoteToken.value=result.quoteToken;for(const node of form.querySelectorAll('[data-total]')){const value=result[node.dataset.total];if(Number.isSafeInteger(value))node.textContent=new Intl.NumberFormat(en?'en-GB':'tr-TR',{style:'currency',currency:result.currency}).format(value/100);}form.elements.privacyAccepted.checked=false;form.elements.termsAccepted.checked=false;return result;}
 for(const form of document.querySelectorAll('form[data-api]')){
  const key=form.querySelector('input[name="idempotencyKey"]');if(key&&!key.value)key.value=id();
  form.addEventListener('submit',async event=>{event.preventDefault();if(!form.reportValidity())return;const button=form.querySelector('button[type="submit"],button:not([type])');if(button)button.disabled=true;show(form,'');
   try{const result=await api(form.dataset.api,fields(form));
    if(form.id==='mfa-start'){document.getElementById('mfa-secret').textContent=result.secret;document.getElementById('mfa-setup').hidden=false;form.hidden=true;}
    else if(form.id==='mfa-confirm'){document.getElementById('mfa-setup').hidden=true;const recovery=document.getElementById('mfa-recovery');recovery.hidden=false;recovery.querySelector('pre').textContent=result.recoveryCodes.join('\n');}
    else if(result.mfaRequired){location.reload();}
    else if(result.paymentUrl){redirect(result.paymentUrl);}
    else if(result.redirect){redirect(result.redirect);}
    else if(form.dataset.next){redirect(form.dataset.next);}
    else if(form.dataset.reload){location.reload();}
    else show(form,result.recorded?(en?'Your request has been recorded.':'İsteğiniz kaydedildi.'):(en?'Saved.':'İşlem kaydedildi.'));
   }catch(error){show(form,error.message||message);if(error.code==='CHECKOUT_QUOTE_CHANGED'||error.code==='CHECKOUT_QUOTE_EXPIRED'){try{await quote();show(form,en?'Review the updated total and confirm again.':'Güncellenen toplamı inceleyip yeniden onaylayın.');}catch{}}}
   finally{if(button)button.disabled=false;}
  });
 }
 document.getElementById('refresh-quote')?.addEventListener('click',async()=>{try{await quote();show(document.getElementById('checkout-form'),en?'Review the updated total.':'Güncellenen toplamı inceleyin.');}catch(error){show(document.getElementById('checkout-form'),error.message);}});
 const tokenForm=document.getElementById('token-form');if(tokenForm){tokenForm.elements.token.value=new URLSearchParams(location.hash.slice(1)).get('token')||'';history.replaceState(null,'',location.pathname);}
 document.getElementById('age-exit')?.addEventListener('click',()=>location.replace('about:blank'));
 const dialog=document.getElementById('age-notice');if(dialog&&!document.cookie.split(';').some(c=>c.trim().startsWith('sg_age=1'))){dialog.showModal();dialog.addEventListener('cancel',e=>e.preventDefault());}
 document.getElementById('age-accept')?.addEventListener('click',()=>{document.cookie='sg_age=1; Path='+(base||'/')+'; Max-Age=604800; SameSite=Lax'+(location.protocol==='https:'?'; Secure':'');dialog.close();document.querySelector('main')?.focus({preventScroll:true});});
})();
