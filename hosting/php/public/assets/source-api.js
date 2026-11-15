/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/public/assets/source-api.js
 * Açıklama   : Yönetimde etkin API işinin durumunu özel uçtan güvenle yeniler.
 */
(()=>{
 'use strict';const cards=[...document.querySelectorAll('[data-source-api]')],base=document.body.dataset.base||'',message=document.getElementById('source-api-message');if(!cards.some(card=>card.dataset.active==='true'))return;
 async function poll(){try{const response=await fetch(base+'/api/admin/source-api',{cache:'no-store'});if(!response.ok)throw Error();const data=await response.json();let active=false;for(const row of data.rows){const card=cards.find(card=>card.dataset.sourceApi===row.vendor);if(!card)continue;const running=!!row.active_run_id;active||=running;card.querySelector('[data-api-status]').textContent=running?'API sayfaları alınıyor':row.run_status==='complete'?'Son API alımı başarılı':row.run_status==='access_required'?'Sunucu erişimi engellendi':row.run_status==='failed'?'Son alım tamamlanamadı':'Bayi erişimi bekleniyor';card.querySelector('[data-api-error]').textContent=['SOURCE_API_HTTP_403','SOURCE_API_HTTP_401'].includes(row.last_error)?'Tedarikçi sunucu bağlantısını reddetti. Bayi erişimi veya sunucu erişim izni gerekiyor.':'';card.querySelector('[data-api-progress]').textContent=running?(row.resource==='categories'?'Kategoriler':'Ürünler')+' · '+row.page+'. sayfa':'';card.querySelector('button')?.toggleAttribute('disabled',running);const enabled=card.querySelector('[name=enabled]');if(enabled){enabled.checked=!!Number(row.enabled);enabled.disabled=!row.last_success_at||!!row.last_error;}}if(active)setTimeout(poll,10000);else{message.textContent='Bağlantı kontrolü sonuçlandı. Katalog ve bağlantı ayrıntılarını güncelleyebilirsiniz.';document.querySelector('[data-api-refresh]').hidden=false;}}catch{message.textContent='API durumu okunamadı. Yönetim oturumunuzu ve bağlantınızı kontrol edip sayfayı yenileyin.';}}
 setTimeout(poll,3000);
})();
