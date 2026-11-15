/* native-locale-copy */
import {localeCopy} from './locale-runtime.js?v=storefront-recovery-20261112-r1';
export const vitrineCopy=localeCopy({
 tr:{label:'NODENO ürün seçkisi',featured:'Öne çıkan ürünler',kitchen:'Mutfak',hallway:'Antre',youth:'Genç odası',previous:'Önceki ürün',next:'Sonraki ürün',pause:'Otomatik geçişi durdur',play:'Otomatik geçişi başlat',view:'Ürünü incele',collection:'Koleksiyonu incele',offers:'Kampanyalı ürünler'},
 en:{label:'NODENO product selection',featured:'Featured products',kitchen:'Kitchen',hallway:'Hallway',youth:'Youth room',previous:'Previous product',next:'Next product',pause:'Pause automatic slides',play:'Start automatic slides',view:'View product',collection:'Explore collection',offers:'Products on promotion'},
 ru:{label:'Подборка товаров NODENO',featured:'Выбранные товары',kitchen:'Кухня',hallway:'Прихожая',youth:'Молодёжная комната',previous:'Предыдущий товар',next:'Следующий товар',pause:'Остановить смену слайдов',play:'Включить смену слайдов',view:'Посмотреть товар',collection:'Посмотреть коллекцию',offers:'Товары по акции'},
 ar:{label:'تشكيلة منتجات NODENO',featured:'منتجات مميزة',kitchen:'المطبخ',hallway:'المدخل',youth:'غرفة الشباب',previous:'المنتج السابق',next:'المنتج التالي',pause:'إيقاف التنقل التلقائي',play:'تشغيل التنقل التلقائي',view:'عرض المنتج',collection:'استكشاف المجموعة',offers:'منتجات العروض'}
});
const glyph=kind=>`<svg viewBox="0 0 24 24" aria-hidden="true">${kind==='previous'?'<path d="m14 6-6 6 6 6"/>':kind==='next'?'<path d="m10 6 6 6-6 6"/>':kind==='play'?'<path d="m9 6 9 6-9 6V6Z"/>':'<path d="M8 5v14M16 5v14"/>'}</svg>`;
export function vitrineProducts(hero,campaigns,byId){
 const seen=new Set();return [{product:hero,tab:'kitchen'},...campaigns.map((c,i)=>({...c,product:byId(c.product),tab:i===0?'hallway':'youth'}))].filter(row=>{const p=row.product;if(!p?.images?.length||p.published===false||p.hidden||seen.has(p.id))return false;seen.add(p.id);return true;});
}
export function renderHomeVitrine({hero,campaigns,byId,locale,esc,t,image,href,productLink,productName,priceMarkup,heroTitle=t('heroTitle'),heroBody=t('heroBody')}){
 const copy=vitrineCopy[locale]||vitrineCopy.tr,slides=vitrineProducts(hero,campaigns,byId);
 if(!slides.length)return '';
 return `<section class="home-vitrine" aria-label="${esc(copy.label)}" data-home-vitrine>
  <div class="vitrine-rail" data-vitrine-rail>${slides.map((slide,i)=>{const p=slide.product,title=i?t(slide.title):heroTitle;return `<article class="vitrine-slide vitrine-tone-${i}" data-vitrine-slide>
   <div class="vitrine-copy"><p class="vitrine-eyebrow">${esc(copy.featured)} <span>NODENO</span></p><${i?'h2':'h1'} tabindex="-1">${esc(title)}</${i?'h2':'h1'}><p class="vitrine-body">${esc(i?t(slide.body):heroBody)}</p><p class="vitrine-name">${esc(productName(p))}</p><div class="vitrine-price">${priceMarkup(p)}</div><div class="vitrine-actions">${productLink(p.id,esc(copy.view),'button button-dark')}${slide.category?`<a class="vitrine-collection" href="${esc(href('catalog',{category:slide.category}))}" data-nav>${esc(copy.collection)}</a>`:''}</div></div>
   ${productLink(p.id,image(p,slide.photo??p.coverIndex??0,{lazy:i!==0}),'vitrine-photo')}
  </article>`;}).join('')}</div>
  <div class="vitrine-controls"><div class="vitrine-tabs">${slides.map((s,i)=>`<button type="button" data-vitrine-go="${i}" aria-current="${i===0?'true':'false'}" title="${esc(copy[s.tab])}"><span>${esc(copy[s.tab])}</span></button>`).join('')}</div><div class="vitrine-navigation"><button type="button" class="icon-button" data-vitrine-previous aria-label="${esc(copy.previous)}">${glyph('previous')}</button><button type="button" class="icon-button" data-vitrine-play aria-pressed="false" aria-label="${esc(copy.pause)}" data-label-pause="${esc(copy.pause)}" data-label-play="${esc(copy.play)}">${glyph('pause')}</button><button type="button" class="icon-button" data-vitrine-next aria-label="${esc(copy.next)}">${glyph('next')}</button></div></div>
 </section>`;
}
let rememberedIndex=0;
export function mountHomeVitrine(root){
 const box=root?.querySelector('[data-home-vitrine]');if(!box)return()=>{};
 const rail=box.querySelector('[data-vitrine-rail]'),slides=[...box.querySelectorAll('[data-vitrine-slide]')],tabs=[...box.querySelectorAll('[data-vitrine-go]')],play=box.querySelector('[data-vitrine-play]'),reduced=matchMedia('(prefers-reduced-motion:reduce)'),events=new AbortController();
 let index=Math.min(rememberedIndex,slides.length-1),paused=reduced.matches,userStarted=false,hovered=false,inView=false,frame=0;
 const options={signal:events.signal};
 function reflect(){tabs.forEach((tab,i)=>tab.setAttribute('aria-current',String(i===index)));slides.forEach((slide,i)=>{slide.inert=i!==index;slide.setAttribute('aria-hidden',String(i!==index));});rememberedIndex=index;play.setAttribute('aria-pressed',String(paused));play.setAttribute('aria-label',paused?play.dataset.labelPlay:play.dataset.labelPause);play.innerHTML=glyph(paused?'play':'pause');}
 function go(next,manual=false){index=(next+slides.length)%slides.length;const slide=slides[index].getBoundingClientRect(),host=rail.getBoundingClientRect(),rtl=getComputedStyle(rail).direction==='rtl';rail.scrollTo({left:rail.scrollLeft+(rtl?slide.right-host.right:slide.left-host.left),behavior:reduced.matches?'instant':'smooth'});if(manual){paused=true;userStarted=false;}reflect();}
 tabs.forEach((tab,i)=>tab.addEventListener('click',()=>go(i,true),options));
 box.querySelector('[data-vitrine-next]').addEventListener('click',()=>go(index+1,true),options);box.querySelector('[data-vitrine-previous]').addEventListener('click',()=>go(index-1,true),options);
 play.addEventListener('click',()=>{paused=!paused;userStarted=!paused;reflect();},options);
 box.addEventListener('pointerenter',()=>{hovered=true;},options);box.addEventListener('pointerleave',()=>{hovered=false;},options);
 rail.addEventListener('pointerdown',()=>{paused=true;reflect();},options);
 rail.addEventListener('scroll',()=>{cancelAnimationFrame(frame);frame=requestAnimationFrame(()=>{const host=rail.getBoundingClientRect();index=slides.reduce((best,slide,i)=>Math.abs(slide.getBoundingClientRect().left-host.left)<Math.abs(slides[best].getBoundingClientRect().left-host.left)?i:best,0);reflect();});},{...options,passive:true});
 const observer=new IntersectionObserver(([entry])=>{inView=entry.isIntersecting&&entry.intersectionRatio>.4;},{threshold:[0,.4,1]});observer.observe(box);
 const timer=setInterval(()=>{if(!paused&&(!reduced.matches||userStarted)&&!hovered&&inView&&!document.hidden&&!document.querySelector('dialog[open]')&&(!box.contains(document.activeElement)||userStarted&&document.activeElement===play))go(index+1);},6000);
 reflect();if(index)requestAnimationFrame(()=>go(index));
 return()=>{events.abort();observer.disconnect();clearInterval(timer);cancelAnimationFrame(frame);};
}
