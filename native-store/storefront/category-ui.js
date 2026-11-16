/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : native-store/storefront/category-ui.js
 * Açıklama   : Kategori aramasını ve filtre çekmecesinin odak davranışını yönetir.
 */
document.addEventListener('submit',event=>{
 const form=event.target.closest('[data-sg-category-search]');if(!form)return;
 event.preventDefault();const target=new URL(location.href),query=String(new FormData(form).get('q')||'').trim();
 target.search=new URLSearchParams({page:'catalog',lang:document.documentElement.lang,...(query?{q:query}:{})}).toString();target.hash='';
 const link=document.createElement('a');link.href=target.href;link.dataset.nav='';link.hidden=true;document.body.append(link);link.click();link.remove();
});
document.addEventListener('click',event=>{
 const trigger=event.target.closest('[data-sg-facet]');if(!trigger)return;
 requestAnimationFrame(()=>{const dialog=document.querySelector('#filter-dialog[open]');if(!dialog)return;
  dialog.classList.add('sg-category-filter-dialog');
  const key=trigger.dataset.sgFacet,groups=[...dialog.querySelectorAll('[data-sg-filter-group]')];
  const group=groups.find(el=>el.dataset.sgFilterGroup===key)||groups[0];
  if(group){group.open=true;group.querySelector('summary')?.focus({preventScroll:true});group.scrollIntoView({block:'start',behavior:'instant'});}
 });
});
