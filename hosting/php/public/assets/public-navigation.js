/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : hosting/php/public/assets/public-navigation.js
 * Açıklama   : Kamu sayfalarında güvenli SSR içeriğini taşıyan, geri konumunu koruyan gezinme.
 */
(()=>{
 'use strict';const base=document.body.dataset.base||'',en=document.body.dataset.locale==='en',status=document.getElementById('site-status');let active,sequence=0;
 function publicUrl(value){const u=new URL(value,location.href);if(u.origin!==location.origin||u.hash)return null;let p=u.pathname;if(!p.startsWith(base+'/'))return null;p=p.slice(base.length);const targetEnglish=p==='/en'||p.startsWith('/en/');if(targetEnglish!==en)return null;if(en)p=p.slice(3)||'/';return /^\/(?:$|urunler\/?$|kategoriler\/?$|kategori\/[a-z0-9-]+\/?$|urun\/[a-z0-9-]+\/?$|blog(?:\/[a-z0-9-]+)?\/?$|rehber(?:\/[a-z0-9-]+)?\/?$|koleksiyonlar\/?$|koleksiyon\/[a-z0-9-]+\/?$|sss\/?$|iletisim\/?$|site-haritasi\/?$|yasal\/[a-z-]+\/?$)/.test(p)?u:null;}
 if(!publicUrl(location.href))return;
 async function navigate(url,{pop=false,position=0}={}){
  active?.abort();const controller=new AbortController();active=controller;const id=++sequence;const old=document.getElementById('main');old.setAttribute('aria-busy','true');status.textContent=en?'Opening page.':'Sayfa açılıyor.';
  try{
   const r=await fetch(url.href,{headers:{Accept:'text/html'},cache:'no-store',signal:controller.signal,credentials:'same-origin'});if(!r.ok||!publicUrl(r.url))throw Error('NAVIGATION_FAILED');const text=await r.text(),doc=new DOMParser().parseFromString(text,'text/html'),next=doc.getElementById('main');if(!next||doc.documentElement.lang!==(en?'en':'tr'))throw Error('INVALID_PAGE');if(id!==sequence)return;
   if(!pop)history.replaceState({...history.state,sgScrollY:scrollY},'',location.href);for(const dialog of document.querySelectorAll('dialog[open]'))dialog.close();old.replaceWith(next);document.title=doc.title;document.body.dataset.page=doc.body.dataset.page||'store';
   for(const link of document.querySelectorAll('.mobile-bottom-nav>a')){const match=doc.querySelector('.mobile-bottom-nav>a[href="'+CSS.escape(link.getAttribute('href'))+'"]');if(match?.hasAttribute('aria-current'))link.setAttribute('aria-current','page');else link.removeAttribute('aria-current');}
   for(const selector of ['meta[name="description"]','link[rel="canonical"]','meta[property^="og:"]','link[rel="alternate"][hreflang]','script[type="application/ld+json"]']){document.head.querySelectorAll(selector).forEach(n=>n.remove());for(const n of doc.head.querySelectorAll(selector))document.head.append(n.cloneNode(true));}
   const token=doc.querySelector('meta[name="csrf-token"]');if(token)document.querySelector('meta[name="csrf-token"]').content=token.content;
   if(!pop)history.pushState({sgScrollY:0},'',url.href);document.dispatchEvent(new CustomEvent('sexogate:content',{detail:{root:next}}));window.scrollTo({top:pop?position:0,behavior:'instant'});if(!pop){const heading=next.querySelector('h1');if(heading){heading.setAttribute('tabindex','-1');heading.focus({preventScroll:true});}}
   status.textContent='';
  }catch(error){if(error.name!=='AbortError'&&id===sequence)location.assign(url.href);}
  finally{if(id===sequence){document.getElementById('main')?.removeAttribute('aria-busy');active=null;}}
 }
 document.addEventListener('click',event=>{if(event.defaultPrevented||event.button!==0||event.metaKey||event.ctrlKey||event.shiftKey||event.altKey)return;const a=event.target.closest('a[href]');if(!a||a.target||a.hasAttribute('download'))return;const u=publicUrl(a.href);if(!u)return;if(u.href===location.href){event.preventDefault();return;}event.preventDefault();navigate(u);});
 document.addEventListener('submit',event=>{const form=event.target;if(event.defaultPrevented||form.method.toLowerCase()!=='get')return;const u=publicUrl(form.action);if(!u)return;event.preventDefault();u.search=new URLSearchParams(new FormData(form)).toString();navigate(u);});
 window.addEventListener('popstate',event=>{const url=publicUrl(location.href);if(url)navigate(url,{pop:true,position:Number(event.state?.sgScrollY)||0});});
})();
