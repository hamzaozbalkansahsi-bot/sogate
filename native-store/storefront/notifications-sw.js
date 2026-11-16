/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : native-store/storefront/notifications-sw.js
 * Açıklama   : Mahrem stok bildirimini gösterir; özel sayfaları önbelleğe almaz.
 */
self.addEventListener('push',event=>{
 let data;try{data=event.data?.json();}catch{return;}
 if(!data||typeof data.tag!=='string'||!/^[a-f0-9]{64}$/.test(data.tag))return;
 const root=new URL(self.registration.scope),url=new URL(data.url||root.href,root);
 if(url.origin!==root.origin||url.pathname!==root.pathname||!/^sg_[a-z0-9_]+$/.test(url.searchParams.get('product')||''))return;
 event.waitUntil(self.registration.showNotification('SEXOGATE',{
  body:'Takip ettiğiniz bir ürün yeniden stokta. Ayrıntıları güvenli ekrandan inceleyin.',
  icon:new URL('assets/brand/app/app-icon-192.png',root).href,
  badge:new URL('assets/brand/app/app-icon-192.png',root).href,
  tag:data.tag,data:{url:url.href},actions:[{action:'view',title:'İncele'}],renotify:false
 }));
});
self.addEventListener('notificationclick',event=>{
 event.notification.close();const root=new URL(self.registration.scope),url=new URL(event.notification.data?.url||root.href,root);
 if(url.origin!==root.origin||url.pathname!==root.pathname)return;
 event.waitUntil((async()=>{const clients=await self.clients.matchAll({type:'window',includeUncontrolled:true});const client=clients.find(c=>new URL(c.url).pathname.startsWith(root.pathname));if(client){await client.navigate(url.href);return client.focus();}return self.clients.openWindow(url.href);})());
});
