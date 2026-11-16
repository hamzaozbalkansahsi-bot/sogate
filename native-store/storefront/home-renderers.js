/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : native-store/storefront/home-renderers.js
 * Açıklama   : Kategori kısayolları, ürün rafları ve sekmeli keşif alanını oluşturur.
 */
import {homeModel} from './sexogate-home-core.js?v=storefront';
import {homeCopy} from './sexogate-home-copy.js?v=storefront';
const arrow='<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 12h15m-6-6 6 6-6 6"/></svg>';
const local=(v,locale)=>typeof v==='string'?v:v?.[locale]||v?.tr||'';
export function homeShelf(ctx,title,products,kind,params={}){
 if(!products.length)return '';const {esc,t,href,productCard}=ctx;
 return `<section class="product-shelf sg-product-shelf sg-home-shelf sg-home-${kind}" data-home-shelf="${kind}"><div class="section-heading"><h2>${esc(title)}</h2><a class="text-link" href="${esc(href('catalog',params))}" data-nav>${esc(t('allProducts'))}${arrow}</a></div><div class="product-row sg-product-rail" tabindex="0" role="region" aria-label="${esc(title)}">${products.map(productCard).join('')}</div></section>`;
}
export function renderHomeDiscovery(ctx){
 const {catalog,locale,esc,t,href,productCard,selectedHomeCategory=''}=ctx,c=homeCopy[locale],m=homeModel(catalog,{category:selectedHomeCategory});
 return `<section id="sg-home-discovery" class="product-shelf sg-home-discovery" data-selected-category="${esc(m.selected?.id||'')}"><div class="section-heading"><h2>${esc(c.discover)}</h2><a class="text-link" href="${esc(href('catalog',{category:m.selected?.id||''}))}" data-nav>${esc(t('allProducts'))}${arrow}</a></div><div class="sg-home-tabs" role="tablist" aria-label="${esc(c.discover)}">${[{id:'',name:c.all},...m.roots].map(v=>`<button type="button" role="tab" id="sg-home-tab-${esc(v.id||'all')}" aria-controls="sg-home-results" aria-selected="${(m.selected?.id||'')===v.id}" tabindex="${(m.selected?.id||'')===v.id?'0':'-1'}" data-home-category="${esc(v.id)}">${esc(local(v.name,locale))}</button>`).join('')}</div><div id="sg-home-results" role="tabpanel" aria-labelledby="sg-home-tab-${esc(m.selected?.id||'all')}" tabindex="0"><div class="product-row sg-product-rail" tabindex="0" role="region" aria-label="${esc(c.discover)}">${m.discovery.map(productCard).join('')}</div></div></section>`;
}
export function renderHome(ctx){
 const {catalog,config,locale,esc,t,href,image,productName,productLink,selectedHomeCategory='',recent=[]}=ctx,c=homeCopy[locale],m=homeModel(catalog,{category:selectedHomeCategory,featuredId:config.appearance?.enabled?config.appearance.heroProductId:'',recentIds:recent});
 const shortcuts=m.shortcuts.map(v=>{const p=m.photo(v.id);return `<a href="${esc(href('catalog',{category:v.id}))}" data-nav data-home-shortcut="${esc(v.id)}"><span>${image(p,p.coverIndex||0,{lazy:false,alt:''})}</span><strong>${esc(local(v.name,locale))}</strong></a>`;}).join('');
 const campaigns=m.campaigns.map(({category,product:p})=>{const content=`<span class="sg-campaign-image">${image(p,p.coverIndex||0,{lazy:false,alt:''})}</span><span class="sg-campaign-caption"><strong>${esc(category?local(category.name,locale):productName(p))}</strong>${arrow}</span>`;return category?`<a class="sg-campaign-card" href="${esc(href('catalog',{category:category.id}))}" data-nav>${content}</a>`:productLink(p.id,content,'sg-campaign-card');}).join('');
 const title=config.appearance?.enabled&&config.appearance['heroTitle_'+locale]||t('heroTitle');
 return `<div class="wrap home-page sg-home sg-market-home sg-home-page"><nav class="sg-home-shortcuts" aria-label="${esc(t('categories'))}">${shortcuts}</nav><div class="sg-home-heading"><h1 tabindex="-1">${esc(title)}</h1><a class="text-link" href="${esc(href('categories'))}" data-nav>${esc(c.categories)}${arrow}</a></div>${homeShelf(ctx,c.selection,m.selection,'selection')}<section class="sg-home-campaigns" aria-label="${esc(c.collections)}"><div class="section-heading"><h2>${esc(c.collections)}</h2></div><div class="sg-campaign-grid">${campaigns}</div></section>${m.lingerie?homeShelf(ctx,local(m.lingerie.name,locale),m.lingerieProducts,'lingerie',{category:m.lingerie.id}):''}${renderHomeDiscovery(ctx)}${homeShelf(ctx,t('recent'),m.recent,'recent')}<section class="sg-home-guides"><div><span>SEXOGATE</span><h2>${esc(c.guide)}</h2><p>${esc(c.guideBody)}</p><a href="${esc(href().split('?')[0]+'blog?lang='+encodeURIComponent(locale))}" data-home-blog>${esc(c.guideAction)}${arrow}</a></div><nav aria-label="${esc(t('help'))}"><a href="${esc(href('help'))}" data-nav>${esc(t('help'))}${arrow}</a><a href="${'mailto:info@sexogate.com'}" data-nav>${esc(t('contact'))}${arrow}</a></nav></section>${ctx.homeCollections()}</div>`;
}
