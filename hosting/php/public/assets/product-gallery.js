/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/public/assets/product-gallery.js
 * Açıklama   : Gerçek galeri ve seçilen varyantın fiyat/stok bilgisini birlikte günceller.
 */
(()=>{
 'use strict';
 function mount(root=document){
  const detail=root.querySelector('[data-product-detail]');if(!detail)return;
  const main=detail.querySelector('[data-gallery-main]'),select=detail.querySelector('[data-product-variant]'),buttons=[...detail.querySelectorAll('[data-gallery-image]')];
  function image(button){if(!button)return;main.src=button.dataset.galleryImage;main.alt=button.dataset.galleryAlt;for(const b of buttons)b.setAttribute('aria-pressed',String(b===button));}
  for(const b of buttons)b.addEventListener('click',()=>image(b));
  function variant(){const option=select?.selectedOptions[0];if(!option)return;detail.querySelector('[data-variant-price]').textContent=option.dataset.price;detail.querySelector('[data-variant-meta]').textContent=option.dataset.sku+' · '+option.dataset.stock;detail.querySelector('[data-product-add]').disabled=option.dataset.buyable!=='true';image(buttons.find(b=>b.dataset.galleryVariant===option.value)||buttons.find(b=>!b.dataset.galleryVariant));}
  select?.addEventListener('change',variant);variant();
 }
 mount();document.addEventListener('sexogate:content',e=>mount(e.detail.root));
})();
