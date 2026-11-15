/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : native-store/storefront/renderers.js
 * Açıklama   : Gerçek katalog için marka vitrini, okunabilir ürün anlatımı ve kaydırılan rafları üretir.
 */
import {storefrontCopy} from './sexogate-storefront-copy.js?v=storefront';
const labels=locale=>storefrontCopy[locale]||storefrontCopy.tr;
const arrow='<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 12h15m-6-6 6 6-6 6"/></svg>';
export function renderSexogateHero(ctx){
 const {hero,locale,esc,image,productLink,productName}=ctx;if(!hero)return '';
 return productLink(hero.id,`<span class="sg-campaign-image">${image(hero,hero.coverIndex||0,{lazy:false})}</span><span class="sg-campaign-caption"><strong>${esc(productName(hero))}</strong>${arrow}</span>`,'sg-campaign-card');
}
export function renderSexogateHome(ctx){
 const {catalog,config,locale,esc,t,image,href,productLink,productName,byId,rootCategories,categoryCount,categoryPhoto,productShelf,homeCollections,recent,recommendedIds}=ctx;
 const roots=rootCategories().filter(c=>categoryCount(c.id)),seen=new Set();
 const picks=[...recommendedIds.map(byId).filter(Boolean),...catalog.products].filter(p=>{const id=p.modelId||p.id;if(seen.has(id))return false;seen.add(id);return true;});
 const shortcuts=roots.map(category=>{const photo=categoryPhoto(category.id),name=category.name[locale]||category.name.tr;return `<a href="${esc(href('catalog',{category:category.id}))}" data-nav><span>${photo?image(photo,photo.coverIndex||0,{lazy:false}):''}</span><strong>${esc(name)}</strong></a>`;}).join('');
 const featured=config.appearance?.enabled?byId(config.appearance.heroProductId):null;
 const cards=(featured?renderSexogateHero({...ctx,hero:featured}):'')+roots.slice(0,featured?3:4).map(category=>{const photo=categoryPhoto(category.id),name=category.name[locale]||category.name.tr;if(!photo)return '';return `<a class="sg-campaign-card" href="${esc(href('catalog',{category:category.id}))}" data-nav><span class="sg-campaign-image">${image(photo,photo.coverIndex||0,{lazy:false})}</span><span class="sg-campaign-caption"><strong>${esc(name)}</strong>${arrow}</span></a>`;}).join('');
 const title=config.appearance?.enabled&&config.appearance['heroTitle_'+locale]||t('heroTitle');
 return `<div class="wrap home-page sg-home sg-market-home"><nav class="sg-home-shortcuts" aria-label="${esc(t('categories'))}">${shortcuts}</nav><div class="sg-home-heading"><h1 tabindex="-1">${esc(title)}</h1><a class="text-link" href="${esc(href('catalog'))}" data-nav>${esc(t('allProducts'))}${arrow}</a></div><section class="sg-campaign-grid" aria-label="${esc(labels(locale).collection)}">${cards}</section>${productShelf('homeSelection',picks)}${productShelf('recent',recent.map(byId).filter(Boolean))}${homeCollections()}</div>`;
}
export function renderSexogateStory(p,{locale,esc,image}){
 const c=labels(locale),story=p.storefrontStory?.[locale]||p.storefrontStory?.tr;const intro=story?.intro||p.name?.[locale]||p.name?.tr||'';
 return `<div class="sg-product-story"><figure>${image(p,p.coverIndex||0,{lazy:true})}</figure><div><p class="sg-product-intro">${esc(intro)}</p><a class="sg-more-link" href="#product-specs" data-specs-link data-sg-open-features>${esc(c.more)}${arrow}</a></div></div>`;
}
export function renderSexogateFeatures(p,{locale,esc}){
 const c=labels(locale),story=p.storefrontStory?.[locale]||p.storefrontStory?.tr||{},rows=Object.entries(p.storefrontFacts||{});if(!rows.length&&!story.care&&!story.safety)return '';
 const paragraphs=text=>text.split(/\n\s*\n|(?<=[.!?])\s+(?=[A-ZİŞÇĞÜÖ])/u).filter(Boolean).map(value=>`<p>${esc(value)}</p>`).join('');
 return `<details class="sg-all-features" id="sg-all-features"><summary><span class="sg-when-closed">${esc(c.allFeatures)}</span><span class="sg-when-open">${esc(c.less)}</span><svg viewBox="0 0 24 24" aria-hidden="true"><path d="m6 9 6 6 6-6"/></svg></summary><div class="sg-features-body">${rows.length?`<dl class="sg-feature-list">${rows.map(([key,value])=>`<div><dt>${esc(c[key]||key)}</dt><dd>${esc(value)}</dd></div>`).join('')}</dl>`:''}${story.care?`<section><h3>${esc(c.care)}</h3>${paragraphs(story.care)}</section>`:''}${story.safety?`<section><h3>${esc(c.safety)}</h3>${paragraphs(story.safety)}</section>`:''}</div></details>`;
}
export function renderSexogateShelf({title,products,esc,link,card}){
 if(!products.length)return '';return `<section class="product-shelf sg-product-shelf"><div class="section-heading"><h2>${esc(title)}</h2>${link}</div><div class="product-row sg-product-rail" tabindex="0" role="region" aria-label="${esc(title)}">${products.slice(0,12).map(card).join('')}</div></section>`;
}
