/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : native-store/storefront/notifications.js
 * Açıklama   : Bildirim iznini kullanıcının seçimiyle alır; favori stok takibini yönetir.
 */
const base=new URL('.',import.meta.url),endpoint=new URL('api/notifications',base);
const labels={tr:{entry:'Bildirim tercihleri',title:'Haberin olsun',intro:'Favorileriniz yeniden stokta olduğunda bu cihaza bildirim gönderelim. Ürün adı ve görseli kilit ekranında görünmez.',enable:'Stok bildirimlerini aç',disable:'Bildirimleri kapat',close:'Kapat',ready:'Bu cihaz için stok bildirimleri açık.',off:'Bildirimler kapalı.',unsupported:'iPhone kullanıyorsanız önce siteyi ana ekranınıza ekleyin, ardından buradan bildirimleri açın. Bu tarayıcı bildirimleri desteklemiyor olabilir.',denied:'Bildirim izni kapalı. Tarayıcı veya cihaz ayarlarından izin verebilirsiniz.',empty:'Takip etmek istediğiniz ürünleri favorilerinize ekleyin.',loading:'Hazırlanıyor…',failed:'Bağlantı kurulamadı. Yeniden deneyin.',withdraw:'İzninizi buradan istediğiniz zaman geri alabilirsiniz. Takip kaydı 90 gün saklanır.'},en:{entry:'Notification preferences',title:'Keep me posted',intro:'Get notified on this device when your favourites are back in stock. Product names and photos stay off your lock screen.',enable:'Enable stock alerts',disable:'Turn off notifications',close:'Close',ready:'Stock alerts are enabled on this device.',off:'Notifications are off.',unsupported:'On iPhone, add this site to your Home Screen first, then enable notifications here. This browser may not support notifications.',denied:'Notifications are blocked. You can allow them in your browser or device settings.',empty:'Add the products you want to follow to your favourites.',loading:'Getting ready…',failed:'Could not connect. Try again.',withdraw:'You can withdraw permission here at any time. Watch records are retained for 90 days.'}};
const copy=()=>labels[document.documentElement.lang]||labels.en;
let state=null,registration=null,dialog=null,busy=false,timer=null,restoring=false;
const hint='sexogate.notifications.enabled.v1';
function remember(value){try{if(value)localStorage.setItem(hint,'true');else localStorage.removeItem(hint);}catch{}}
const favorites=()=>{try{const value=JSON.parse(localStorage.getItem('nodeno.saved.v1')||'[]');return Array.isArray(value)?[...new Set(value.filter(v=>typeof v==='string'&&/^sg_[a-z0-9_]+$/.test(v)))].slice(0,100):[];}catch{return[];}};
async function request(method='GET',body){const r=await fetch(endpoint,{method,credentials:'same-origin',cache:'no-store',headers:{...(body?{'Content-Type':'application/json','X-CSRF-Token':state.csrfToken}:{})},...(body?{body:JSON.stringify(body)}:{})});if(!r.ok)throw Error('notifications_unavailable');return r.json();}
function message(value){if(dialog?.open)dialog.querySelector('[role=status]').textContent=value;}
function button(text,action){const b=document.createElement('button');b.type='button';b.className='button';b.textContent=text;b.addEventListener('click',action);return b;}
async function open(){
 if(dialog?.open)return;const c=copy(),focus=document.activeElement;dialog=document.createElement('dialog');dialog.className='sg-notify-dialog';dialog.setAttribute('aria-labelledby','sg-notify-title');
 const heading=document.createElement('h2');heading.id='sg-notify-title';heading.textContent=c.title;const intro=document.createElement('p');intro.textContent=c.intro;const status=document.createElement('p');status.setAttribute('role','status');status.textContent=c.loading;
 const enable=button(c.enable,async()=>{
  if(busy||!registration||!state)return;busy=true;enable.disabled=true;
  try{
   const permission=await Notification.requestPermission();if(permission!=='granted'){message(c.denied);return;}
   const bytes=Uint8Array.from(atob(state.publicKey.replace(/-/g,'+').replace(/_/g,'/')),ch=>ch.charCodeAt(0));
   const subscription=await registration.pushManager.getSubscription()||await registration.pushManager.subscribe({userVisibleOnly:true,applicationServerKey:bytes});
   await request('POST',{consent:true,subscription:subscription.toJSON(),productIds:favorites()});state={...state,enabled:true,productIds:favorites()};remember(true);message(c.ready);disable.hidden=false;enable.hidden=true;
  }catch{message(c.failed);}finally{busy=false;enable.disabled=false;}
 });enable.classList.add('button-dark');enable.disabled=true;
 const disable=button(c.disable,async()=>{if(busy||!state)return;busy=true;disable.disabled=true;try{await request('DELETE',{});state={...state,enabled:false,productIds:[]};remember(false);const sub=await registration?.pushManager.getSubscription();await sub?.unsubscribe();message(c.off);disable.hidden=true;enable.hidden=false;}catch{message(c.failed);}finally{busy=false;disable.disabled=false;}});disable.hidden=true;
 const note=document.createElement('p');note.className='sg-notify-note';note.textContent=c.withdraw;const close=button(c.close,()=>dialog.close());
 dialog.append(heading,intro,status,enable,disable,close,note);document.body.append(dialog);dialog.addEventListener('close',()=>{dialog.remove();dialog=null;focus?.focus({preventScroll:true});},{once:true});dialog.showModal();
 try{
  state=await request();disable.hidden=!state.enabled;
  if(!('serviceWorker'in navigator)||!('PushManager'in window)||!('Notification'in window)){message(c.unsupported);return;}
  registration=await navigator.serviceWorker.register(new URL('sg-notifications-sw.js',base),{scope:base.pathname,updateViaCache:'none'});
  await navigator.serviceWorker.ready;if(!dialog?.open)return;
  enable.disabled=false;enable.hidden=state.enabled;message(state.enabled?c.ready:Notification.permission==='denied'?c.denied:favorites().length?c.off:c.empty);
 }catch{message(c.failed);}
}
function enhance(){
 if(!state&&!restoring){let enabled=false;try{enabled=localStorage.getItem(hint)==='true';}catch{}if(enabled){restoring=true;request().then(value=>{state=value;remember(value.enabled);enhance();}).catch(()=>{}).finally(()=>{restoring=false;});}}
 const footer=document.querySelector('.sg-footer-preferences');if(footer&&!footer.querySelector('[data-sg-notifications]')){const b=button(copy().entry,open);b.dataset.sgNotifications='';b.className='sg-notify-entry';footer.append(b);}
 const header=document.querySelector('.favorites-page .page-heading,.shopping-page:has(.favorites-grid) .page-heading');if(header&&!header.querySelector('[data-sg-notifications]')){const b=button(copy().entry,open);b.dataset.sgNotifications='';header.append(b);}
 if(state?.enabled&&!busy){clearTimeout(timer);timer=setTimeout(async()=>{const ids=favorites();if(JSON.stringify(ids)===JSON.stringify(state.productIds))return;busy=true;try{await request('PUT',{productIds:ids});state.productIds=ids;}catch{}finally{busy=false;}},500);}
}
new MutationObserver(enhance).observe(document.body,{childList:true,subtree:true});enhance();
