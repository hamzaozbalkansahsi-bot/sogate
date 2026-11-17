/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : native-store/storefront/ui.js
 * Açıklama   : Gizlilik girişini footera taşır; ürün rafları ve özellik açılışını erişilebilir biçimde yönetir.
 */
import {storefrontCopy} from './sexogate-storefront-copy.js?v=storefront';
import {railEdges,railStepDelta} from './sexogate-gallery-experience-core.js?v=storefront';
const copy=()=>storefrontCopy[document.documentElement.lang]||storefrontCopy.tr;
let queued=false,privacy=null;const observed=new Set(),railControls=new WeakMap();
const railSelector='.product-row,.sg-collection-rail,.collection-row,.collections-row,.campaign-row,.sg-campaign-rail,.side-campaigns,.category-circles,.sg-home-shortcuts,.sg-home-tabs,.sg-category-tabs,.root-links,.product-section-nav,.sg-product-section-nav';
function changeStyle(name,value){const root=document.documentElement;if(root.style.getPropertyValue(name)!==value)root.style.setProperty(name,value);}
function chrome(){const nav=document.querySelector('.bottom-nav'),purchase=document.querySelector('.mobile-purchase');const visible=e=>e&&getComputedStyle(e).display!=='none'?Math.ceil(e.getBoundingClientRect().height):0;changeStyle('--sg-purchase-height',visible(purchase)+'px');changeStyle('--sg-nav-height',visible(nav)+'px');changeStyle('--sg-header-height',visible(document.querySelector('.store-header'))+'px');document.body.classList.toggle('sg-product-view',!!document.querySelector('.product-page'));}
const resize=new ResizeObserver(()=>{chrome();schedule();});
function railState(rail){const controls=railControls.get(rail);if(!controls)return;const state=railEdges(rail);controls.hidden=!state.overflow;for(const step of[-1,1]){const button=controls.querySelector('[data-sg-step="'+step+'"]');if(!button)continue;const hidden=step<0?state.previousHidden:state.nextHidden;button.hidden=hidden;button.disabled=hidden;}}
function enhance(){queued=false;for(const element of observed)if(!element.isConnected){resize.unobserve(element);observed.delete(element);}const footer=document.querySelector('.store-footer'),candidate=document.querySelector('.insights-settings');if(candidate)privacy=candidate;
 if(footer&&privacy){let slot=footer.querySelector('.sg-footer-preferences');if(!slot){slot=document.createElement('div');slot.className='sg-footer-preferences';footer.append(slot);}if(privacy.parentElement!==slot)slot.append(privacy);if(privacy.textContent!==copy().privacy)privacy.textContent=copy().privacy;}
 for(const rail of document.querySelectorAll(railSelector)){if(rail.closest('.gallery-thumbs,.carousel-thumbnails')||!['auto','scroll'].includes(getComputedStyle(rail).overflowX))continue;if(!rail.dataset.sgReady){rail.dataset.sgReady='true';if(!rail.hasAttribute('tabindex'))rail.tabIndex=0;const shelf=rail.closest('.product-shelf,.collection-shelf,.campaign-shelf,.category-discovery'),heading=shelf?.querySelector('.section-heading');if(heading){const controls=document.createElement('div');controls.className='sg-rail-controls';controls.innerHTML='<button type="button" data-sg-step="-1" aria-label="'+copy().previous+'"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="m14 6-6 6 6 6"/></svg></button><button type="button" data-sg-step="1" aria-label="'+copy().next+'"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="m10 6 6 6-6 6"/></svg></button>';heading.append(controls);railControls.set(rail,controls);for(const button of controls.querySelectorAll('button'))button.onclick=()=>rail.scrollBy({left:railStepDelta(button.dataset.sgStep,rail.clientWidth,getComputedStyle(rail).direction),behavior:matchMedia('(prefers-reduced-motion:reduce)').matches?'instant':'smooth'});}
   rail.addEventListener('scroll',()=>railState(rail),{passive:true});rail.addEventListener('keydown',event=>{if(event.target===rail&&['ArrowLeft','ArrowRight'].includes(event.key)){event.preventDefault();rail.scrollBy({left:(event.key==='ArrowRight'?1:-1)*rail.clientWidth*.75,behavior:matchMedia('(prefers-reduced-motion:reduce)').matches?'instant':'smooth'});}});}
  railState(rail);if(!observed.has(rail)){observed.add(rail);resize.observe(rail);}
 }
 for(const element of document.querySelectorAll('.bottom-nav,.mobile-purchase,.store-header'))if(!observed.has(element)){observed.add(element);resize.observe(element);}
 chrome();
}
document.addEventListener('click',event=>{const link=event.target.closest('a[href="#product-specs"]');if(link){const details=document.querySelector('#sg-all-features');if(details)details.open=true;}},true);
document.addEventListener('click',event=>{const trigger=event.target.closest('[data-sg-cart-summary]');if(!trigger)return;const summary=document.querySelector('.basket-summary');if(!summary)return;const dialog=document.createElement('dialog');dialog.className='sg-cart-summary-dialog';dialog.setAttribute('aria-label',summary.querySelector('h2')?.textContent||'Sepet');const close=document.createElement('button');close.type='button';close.className='button';close.textContent=copy().close||'Kapat';close.addEventListener('click',()=>dialog.close());dialog.append(summary.cloneNode(true),close);document.body.append(dialog);dialog.addEventListener('close',()=>{dialog.remove();trigger.focus({preventScroll:true});},{once:true});dialog.showModal();});
function schedule(){if(!queued){queued=true;requestAnimationFrame(enhance);}}
new MutationObserver(schedule).observe(document.body,{childList:true,subtree:true});addEventListener('resize',schedule,{passive:true});enhance();
