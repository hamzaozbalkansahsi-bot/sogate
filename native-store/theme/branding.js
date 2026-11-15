/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : native-store/theme/branding.js
 * Açıklama   : Özgün motoru değiştirmeden yalnız marka alanlarının görünür adını günceller.
 */
(()=>{'use strict';const scope='.sidebar-brand,.sidebar-foot,.topbar,.auth-brand,.auth-stage,.footer-brand,.store-footer,.site-footer,.logo,.eyebrow';
function brand(){for(const box of document.querySelectorAll(scope)){const walker=document.createTreeWalker(box,NodeFilter.SHOW_TEXT);let node;while(node=walker.nextNode())if(!node.parentElement.closest('script,style,code,pre,input,textarea')){const value=node.data.replace(/\bNODENO\b/g,'SEXOGATE').replace(/nodenohome\.com(?:\.tr)?/g,'sexogate.com').replace(/İyi tasarım\. Kolay yaşam\./g,'Tutkunu Keşfet.');if(value!==node.data)node.data=value;}for(const node of box.querySelectorAll('[alt],[aria-label]'))for(const attr of ['alt','aria-label']){const value=node.getAttribute(attr);if(value?.includes('NODENO'))node.setAttribute(attr,value.replace(/\bNODENO\b/g,'SEXOGATE'));}}}
const originalBrand=brand;
brand=function(){originalBrand();
 for(const node of document.querySelectorAll('[data-furniture-nav],[data-wholesale-nav],[data-wholesale-only]'))node.remove();
 for(const node of document.querySelectorAll('a[href]')){try{const target=new URL(node.href,location.href);if(target.origin===location.origin&&/\/(?:araclar|tools)(?:\/|$)/.test(target.pathname))node.remove();}catch{}}
 const footer=document.querySelector('.store-footer');if(!footer)return;
 const links=footer.querySelector('nav');if(links&&!links.querySelector('[data-sexogate-blog]')){const a=document.createElement('a');a.href='/blog';a.dataset.sexogateBlog='true';a.textContent=document.documentElement.lang==='tr'?'Blog':'Journal';links.append(a);}
 const social=footer.querySelector('.social-links');if(social&&!social.dataset.sexogateIcons){social.dataset.sexogateIcons='true';social.replaceChildren();
 const platforms=[['Instagram','https://www.instagram.com/sexogate/','<rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/><path d="M17.5 6.5h.01"/>'],['Facebook','https://www.facebook.com/sexogate','<path d="M14 21v-8h3l.5-4H14V7c0-1 .5-2 2-2h2V2h-3c-4 0-5 3-5 5v2H7v4h3v8"/>'],['X','https://x.com/sexogate','<path d="M4 3h4l12 18h-4L4 3Zm16 0L4 21"/>'],['TikTok','https://www.tiktok.com/@sexogate','<path d="M14 3v12.5a4.5 4.5 0 1 1-4-4.5v3a1.5 1.5 0 1 0 1 1.5V3h3c.5 3 2 4.5 5 5v3c-2-.2-3.5-.8-5-2"/>']];
 for(const [label,url,geometry]of platforms){const a=document.createElement('a');a.href=url;a.target='_blank';a.rel='noopener noreferrer';a.setAttribute('aria-label',label);a.innerHTML='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true">'+geometry+'</svg>';social.append(a);}}
};
brand();new MutationObserver(brand).observe(document.body,{childList:true,subtree:true});})();
