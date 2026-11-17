/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : native-store/storefront/product-experience-renderers.js
 * Açıklama   : Ürün ayrıntıları, sayfa içi iade ve görselli keşif alanlarını üretir.
 */
import {localText,productFacts,productStory,productDiscovery} from './product-experience-core.js?v=storefront';
const arrow='<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 12h15m-6-6 6 6-6 6"/></svg>';
const chevron='<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m6 9 6 6 6-6"/></svg>';
const feedbackIcon='<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M21 11.5a8.4 8.4 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.4 8.4 0 0 1-3.8-.9L3 21l1.9-5.7a8.4 8.4 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.4 8.4 0 0 1 3.8-.9h.5A8.5 8.5 0 0 1 21 11v.5ZM8 11h8m-8 4h5"/></svg>';
const words=ctx=>ctx.copy||{};
const facts=(p,ctx)=>productFacts(p,ctx.locale,ctx.factLabels||{});
const paragraph=(text,esc)=>String(text||'').split(/\n\s*\n/u).filter(v=>v.trim()).map(v=>`<p>${esc(v.trim())}</p>`).join('');
export function renderProductHighlights(p,ctx){
 const {esc}=ctx,c=words(ctx),rows=facts(p,ctx).slice(0,8);if(!rows.length)return '';
 return `<section class="product-spec-overview sg-product-highlights" aria-labelledby="product-highlights-title"><div class="spec-overview-heading"><h2 id="product-highlights-title">${esc(c.highlights)}</h2><a class="specs-all-link" href="#product-specs" data-specs-link data-sg-open-features>${esc(c.allFeatures)}${arrow}</a></div><dl class="sg-highlight-grid">${rows.map(row=>`<div data-spec-fact="${esc(row.id)}"><dt>${esc(row.label)}</dt><dd>${esc(row.value)}</dd></div>`).join('')}</dl></section>`;
}
export function renderProductNavigation(p,ctx){
 const {esc,locale}=ctx,c=words(ctx),story=productStory(p,locale),items=[['product-information',c.information],['product-specs',c.features]];
 if(story.care||story.safety)items.push(['product-questions',c.care]);items.push(['product-faq',c.returns]);
 return `<nav class="product-section-nav sg-product-section-nav" aria-label="${esc(c.information)}">${items.map(([id,label])=>`<a href="#${id}" data-specs-link data-sg-product-section>${esc(label)}</a>`).join('')}</nav>`;
}
export function renderProductStory(p,ctx){
 const {esc,image,locale}=ctx,c=words(ctx),story=productStory(p,locale),hasMore=story.paragraphs.length||story.bullets.length||story.packageContents.length;
 const body=story.paragraphs.map(v=>paragraph(v,esc)).join('')+(story.bullets.length?`<ul class="sg-story-bullets">${story.bullets.map(v=>`<li>${esc(v)}</li>`).join('')}</ul>`:'')+(story.packageContents.length?`<section class="sg-story-package"><h3>${esc(c.packageContents)}</h3><ul>${story.packageContents.map(v=>`<li>${esc(v)}</li>`).join('')}</ul></section>`:'');
 return `<div class="sg-product-story sg-product-editorial"><figure>${image(p,p.coverIndex||0,{lazy:true})}</figure><div><p class="sg-product-intro">${esc(story.intro)}</p>${hasMore?`<details class="sg-story-details" data-sg-story-details><summary class="sg-more-link"><span class="sg-when-closed">${esc(c.more)}</span><span class="sg-when-open">${esc(c.less)}</span>${chevron}</summary><div class="sg-story-expanded">${body}</div></details>`:''}</div></div>`;
}
export function renderProductFeatures(p,ctx){
 const {esc}=ctx,c=words(ctx),rows=facts(p,ctx);if(p.code)rows.push({id:'code',label:c.code,value:p.code});
 if(!rows.length)return '';
 return `<details class="sg-all-features sg-product-attributes" id="sg-all-features"><summary><span class="sg-when-closed">${esc(c.allFeatures)}</span><span class="sg-when-open">${esc(c.hideFeatures)}</span>${chevron}</summary><div class="sg-features-body"><dl class="sg-feature-list sg-attribute-table">${rows.map(row=>`<div><dt>${esc(row.label)}</dt><dd>${esc(row.value)}</dd></div>`).join('')}</dl></div></details>`;
}
export function renderProductCare(p,ctx){
 const {locale,esc}=ctx,c=words(ctx),story=productStory(p,locale);if(!story.care&&!story.safety)return '';
 return `<section class="detail-section sg-product-care" id="product-questions" tabindex="-1"><h2>${esc(c.care)}</h2><div class="sg-care-grid">${story.care?`<article><h3>${esc(c.care)}</h3>${paragraph(story.care,esc)}</article>`:''}${story.safety?`<article><h3>${esc(c.safety)}</h3>${paragraph(story.safety,esc)}</article>`:''}</div></section>`;
}
export function renderProductReturns(p,ctx){
 const {esc,href,locale,config={}}=ctx,c=words(ctx),policy=ctx.returnPolicy||ctx.returnsPolicy||config.productExperience?.returns?.[locale]||{},items=Array.isArray(policy.items)?policy.items:[],paragraphs=Array.isArray(policy.paragraphs)?policy.paragraphs:[];
 return `<section class="detail-section sg-product-returns" id="product-faq" tabindex="-1" aria-labelledby="sg-product-returns-title"><h2 id="sg-product-returns-title">${esc(c.returns)}</h2><details class="sg-inline-policy" data-sg-returns-details><summary>${esc(policy.title||c.returns)}${chevron}</summary><div>${paragraphs.map(v=>paragraph(v,esc)).join('')}${items.length?`<ul>${items.map(v=>`<li>${typeof v==='string'?esc(v):`<strong>${esc(v.title||'')}</strong><span>${esc(v.body||'')}</span>`}</li>`).join('')}</ul>`:''}<p>${esc(c.returnGuidance)}</p><a class="sg-inline-return-action" href="${esc(href('return-center'))}" data-nav>${esc(c.startReturn)}${arrow}</a></div></details></section>`;
}
export function renderProductCollections(model,ctx){
 const {esc,locale,image,href}=ctx,c=words(ctx);if(!model.collections.length)return '';
 return `<section class="product-shelf sg-product-collections" aria-labelledby="sg-product-collections-title"><div class="section-heading"><h2 id="sg-product-collections-title">${esc(c.collections)}</h2></div><div class="product-row sg-collection-rail" role="region" tabindex="0" aria-label="${esc(c.collections)}">${model.collections.map(group=>`<a class="sg-product-collection" href="${esc(href('catalog',group.params))}" data-nav data-sg-product-collection="${esc(group.id)}"><h3>${esc(localText(group.title,locale))}</h3><span class="sg-collection-mosaic">${group.products.map(product=>`<span>${image(product,product.coverIndex||0,{lazy:true,alt:''})}</span>`).join('')}</span><span class="sg-collection-caption"><span>${group.count} ${esc(c.productCount)}</span><strong>${esc(c.collectionAction)}${arrow}</strong></span></a>`).join('')}</div></section>`;
}
export function renderProductRail(key,title,products,ctx){
 if(!products.length)return '';const {esc,productCard}=ctx;
 return `<section class="product-shelf sg-product-shelf" id="product-shelf-${key}"><div class="section-heading"><h2>${esc(title)}</h2></div><div class="product-row sg-product-rail" tabindex="0" role="region" aria-label="${esc(title)}">${products.slice(0,12).map(productCard).join('')}</div></section>`;
}
export function renderProductRelatedLinks(model,ctx){
 const {esc,locale,href}=ctx,c=words(ctx);if(!model.links.length)return '';
 return `<section class="detail-section sg-related-discovery" aria-labelledby="sg-related-discovery-title"><h2 id="sg-related-discovery-title">${esc(c.related)}</h2><nav class="sg-related-chips" aria-label="${esc(c.related)}">${model.links.map(link=>`<a href="${esc(href('catalog',link.params))}" data-nav>${esc(localText(link.title,locale))}</a>`).join('')}</nav></section>`;
}
export function renderProductExplore(p,ctx){
 const c=words(ctx),model=productDiscovery(p,ctx.catalog,ctx.config,ctx.recent||[]),feedback=`<div class="sg-product-feedback"><button type="button" data-sg-feedback="${ctx.esc(p.id)}">${feedbackIcon}<span>${ctx.esc(c.feedback)}</span>${arrow}</button></div>`;
 return renderProductCare(p,ctx)+renderProductReturns(p,ctx)+feedback+renderProductCollections(model,ctx)+renderProductRail('productSimilar',c.similar,model.similar,ctx)+renderProductRail('productComplementary',c.recommendations,model.complementary.length?model.complementary:model.selection,ctx)+renderProductRail('selection',model.hasPopularity?c.popular:c.selection,model.hasPopularity?model.popular:model.selection,ctx)+renderProductRail('recent',c.recent,model.recent,ctx)+renderProductRelatedLinks(model,ctx);
}
