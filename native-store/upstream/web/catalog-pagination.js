/* native-locale-copy */
import {localeCopy} from './locale-runtime.js?v=storefront-recovery-20261112-r1';
export const CATALOG_PAGE_SIZE=24;
export function catalogPage(total,raw=''){
 const validNumber=raw===''||/^[1-9]\d{0,5}$/.test(String(raw));
 const page=raw===''?1:Number(raw),pages=Math.max(1,Math.ceil(total/CATALOG_PAGE_SIZE));
 return {page,pages,offset:(page-1)*CATALOG_PAGE_SIZE,valid:validNumber&&page<=pages};
}
export function catalogPagination(total,raw,locale,href,escape){
 const state=catalogPage(total,raw);if(!state.valid||state.pages<2)return'';
 const copy=localeCopy({tr:['Ürün sayfaları','Önceki sayfa','Sonraki sayfa'],en:['Product pages','Previous page','Next page'],ru:['Страницы товаров','Предыдущая','Следующая'],ar:['صفحات المنتجات','الصفحة السابقة','الصفحة التالية']})[locale]||['Product pages','Previous page','Next page'];
 const pages=[...new Set([1,...Array.from({length:5},(_,i)=>state.page+i-2).filter(n=>n>1&&n<state.pages),state.pages])].sort((a,b)=>a-b);
 const link=(page,label,current=false)=>`<a class="button" href="${escape(href(page))}" data-nav${current?' aria-current="page"':''}>${escape(label)}</a>`;
 return`<nav class="catalog-pagination" aria-label="${escape(copy[0])}">${state.page>1?link(state.page-1,copy[1]):''}${pages.map(page=>link(page,new Intl.NumberFormat(locale).format(page),page===state.page)).join('')}${state.page<state.pages?link(state.page+1,copy[2]):''}</nav>`;
}
