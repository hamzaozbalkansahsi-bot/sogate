/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/public/assets/media-admin.js
 * Açıklama   : Galeri için yalnız seçilen ürüne ait gerçek seçenekleri yükler.
 */
(()=>{
 'use strict';const product=document.querySelector('[data-media-product]'),variant=document.querySelector('[data-media-variant]');if(!product||!variant)return;let generation=0,request;
 product.addEventListener('change',async()=>{const id=++generation;request?.abort();request=new AbortController();variant.replaceChildren(new Option('Bütün seçeneklerde göster',''));if(!product.value)return;variant.disabled=true;try{const response=await fetch((document.body.dataset.base||'')+'/api/admin/product-variants?productId='+encodeURIComponent(product.value),{signal:request.signal,cache:'no-store'});const data=await response.json();if(!response.ok)throw Error(data.error);if(id!==generation)return;for(const row of data.rows)variant.add(new Option(row.sku+' · '+row.name,row.id));}catch(e){if(e.name!=='AbortError')product.form.querySelector('.form-message').textContent='Ürün seçenekleri yüklenemedi. Yeniden seçin.';}finally{if(id===generation)variant.disabled=false;}});
})();
