/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : native-store/storefront/product-experience-ui.js
 * Açıklama   : Ürün içi bilgi bağlantılarında ilgili ayrıntıyı açar ve sayfada kalır.
 */
document.addEventListener('click',event=>{
 const link=event.target.closest('a[data-sg-product-section]');if(!link||event.defaultPrevented||event.button!==0||event.ctrlKey||event.metaKey||event.altKey||event.shiftKey)return;
 const target=document.getElementById(link.hash.slice(1));if(!target)return;
 if(target.id==='product-faq'){const details=target.querySelector('[data-sg-returns-details]');if(details)details.open=true;}
 if(target.id==='product-specs'){const details=target.querySelector('#sg-all-features');if(details)details.open=true;}
},true);
