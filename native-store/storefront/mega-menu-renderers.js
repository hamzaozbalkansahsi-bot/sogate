/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : native-store/storefront/mega-menu-renderers.js
 * Açıklama   : Dolu kategorileri gerçek ürün fotoğraflı, klavye kancalarını koruyan mega menü kartlarına dönüştürür.
 */
import{megaMenuModel,megaPhotoIndex}from'./mega-menu-core.js';
const fallback='<svg viewBox="0 0 48 48" aria-hidden="true" focusable="false"><rect x="9" y="9" width="30" height="30" rx="7"/><path d="M17 24h14M24 17v14"/></svg>';
export function renderMegaMenu(ctx){
 const {catalog,roots,active,esc,loc,href,image,categoryPhoto,t,count,icon}=ctx,model=megaMenuModel(catalog,{roots,active,categoryPhoto});if(!model.active)return '';
 const label=category=>loc(category.name),quantity=value=>`${count?count(value):String(value)} ${t('categoryProducts')}`,photo=value=>value.photo?image(value.photo,megaPhotoIndex(value.photo),{alt:'',lazy:true}):fallback;
 return `<nav class="mega-sidebar sg-mega-sidebar" aria-label="${esc(t('categories'))}">${model.roots.map(root=>`<button type="button" data-mega="${esc(root.category.id)}" aria-pressed="${root.category.id===model.active.category.id}"><span class="sg-mega-root-photo">${photo(root)}</span><span class="sg-mega-root-label">${esc(label(root.category))}<small>${esc(quantity(root.count))}</small></span><span class="breadcrumb-separator" aria-hidden="true"></span></button>`).join('')}</nav><div class="mega-content sg-mega-content"><div class="mega-title sg-mega-title"><a href="${esc(href('catalog',{category:model.active.category.id}))}" data-nav>${esc(label(model.active.category))}<small>${esc(quantity(model.active.count))}</small></a><button type="button" class="icon-button" data-action="close-mega" aria-label="${esc(t('close'))}">${icon('close')}</button></div><div class="mega-columns sg-mega-grid">${model.cards.map(card=>`<a class="sg-mega-card" href="${esc(href('catalog',{category:card.category.id}))}" data-nav data-mega-category="${esc(card.category.id)}"><span class="sg-mega-card-photo">${photo(card)}</span><span class="sg-mega-card-caption">${card.parent?`<small class="sg-mega-card-parent">${esc(label(card.parent))}</small>`:''}<strong>${esc(label(card.category))}</strong><span>${esc(quantity(card.count))}</span></span></a>`).join('')}</div><div class="sg-mega-footer"><a href="${esc(href('categories'))}" data-nav>${esc(t('allCategories'))}</a><a href="${esc(href('catalog',{category:model.active.category.id}))}" data-nav>${esc(t('allProducts'))} (${esc(count?count(model.active.count):String(model.active.count))})</a></div></div>`;
}
