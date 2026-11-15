/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : native-store/storefront/ui.js
 * Açıklama   : Gizlilik girişini footera taşır; ürün rafları ve özellik açılışını erişilebilir biçimde yönetir.
 */
import {storefrontCopy} from './sexogate-storefront-copy.js?v=storefront';
const copy=()=>storefrontCopy[document.documentElement.lang]||storefrontCopy.tr;
let queued=false,privacy=null;const observed=new Set();
function changeStyle(name,value){const root=document.documentElement;if(root.style.getPropertyValue(name)!==value)root.style.setProperty(name,value);}
function chrome(){const nav=document.querySelector('.bottom-nav'),purchase=document.querySelector('.mobile-purchase');const visible=e=>e&&getComputedStyle(e).display!=='none'?Math.ceil(e.getBoundingClientRect().height):0;changeStyle('--sg-purchase-height',visible(purchase)+'px');changeStyle('--sg-nav-height',visible(nav)+'px');changeStyle('--sg-header-height',visible(document.querySelector('.store-header'))+'px');document.body.classList.toggle('sg-product-view',!!document.querySelector('.product-page'));}
const resize=new ResizeObserver(chrome);
function railState(rail){const box=rail.closest('.product-shelf'),controls=box?.querySelector('.sg-rail-controls');if(!controls)return;const position=Math.abs(rail.scrollLeft),maximum=rail.scrollWidth-rail.clientWidth;controls.hidden=maximum<4;controls.querySelector('[data-sg-step="-1"]').disabled=position<=2;controls.querySelector('[data-sg-step="1"]').disabled=position>=maximum-2;}
function enhance(){queued=false;for(const element of observed)if(!element.isConnected){resize.unobserve(element);observed.delete(element);}const footer=document.querySelector('.store-footer'),candidate=document.querySelector('.insights-settings');if(candidate)privacy=candidate;
 if(footer&&privacy){let slot=footer.querySelector('.sg-footer-preferences');if(!slot){slot=document.createElement('div');slot.className='sg-footer-preferences';footer.append(slot);}if(privacy.parentElement!==slot)slot.append(privacy);if(privacy.textContent!==copy().privacy)privacy.textContent=copy().privacy;}
 for(const rail of document.querySelectorAll('.product-row')){if(!rail.dataset.sgReady){rail.dataset.sgReady='true';rail.tabIndex=0;const shelf=rail.closest('.product-shelf'),heading=shelf?.querySelector('.section-heading');if(heading){const controls=document.createElement('div');controls.className='sg-rail-controls';controls.innerHTML='<button type="button" data-sg-step="-1" aria-label="'+copy().previous+'"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="m14 6-6 6 6 6"/></svg></button><button type="button" data-sg-step="1" aria-label="'+copy().next+'"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="m10 6 6 6-6 6"/></svg></button>';heading.append(controls);for(const button of controls.querySelectorAll('button'))button.onclick=()=>rail.scrollBy({left:Number(button.dataset.sgStep)*(getComputedStyle(rail).direction==='rtl'?-1:1)*rail.clientWidth*.8,behavior:matchMedia('(prefers-reduced-motion:reduce)').matches?'instant':'smooth'});}
   rail.addEventListener('scroll',()=>railState(rail),{passive:true});rail.addEventListener('keydown',event=>{if(event.target===rail&&['ArrowLeft','ArrowRight'].includes(event.key)){event.preventDefault();rail.scrollBy({left:(event.key==='ArrowRight'?1:-1)*rail.clientWidth*.75,behavior:matchMedia('(prefers-reduced-motion:reduce)').matches?'instant':'smooth'});}});}
  railState(rail);
 }
 for(const element of document.querySelectorAll('.bottom-nav,.mobile-purchase,.store-header'))if(!observed.has(element)){observed.add(element);resize.observe(element);}
 chrome();
}
document.addEventListener('click',event=>{const link=event.target.closest('a[href="#product-specs"]');if(link){const details=document.querySelector('#sg-all-features');if(details)details.open=true;}},true);
function schedule(){if(!queued){queued=true;requestAnimationFrame(enhance);}}
new MutationObserver(schedule).observe(document.body,{childList:true,subtree:true});addEventListener('resize',schedule,{passive:true});enhance();
