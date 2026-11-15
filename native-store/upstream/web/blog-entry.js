import {mountDateTime} from './date-time.js?v=20261113-r2';
mountDateTime();
// Add blog entry points without coupling the independent storefront and admin editors.
const labels={tr:['Rehberler','Ölçü ve boya araçları'],en:['Guides','Planning and paint tools'],ru:['Руководства','Расчёты и инструменты'],ar:['الأدلة','أدوات القياس والطلاء'],de:['Ratgeber','Planungs- und Farbwerkzeuge'],az:['Bələdçilər','Ölçü və boya alətləri'],kk:['Нұсқаулықтар','Өлшеу және бояу құралдары'],tk:['Gollanmalar','Ölçeg we reňk gurallary'],uz:['Qoʻllanmalar','Oʻlchov va boʻyoq vositalari'],ky:['Колдонмолор','Өлчөө жана боёо куралдары'],fa:['راهنماها','ابزار اندازه‌گیری و رنگ']};
const admin=location.pathname==='/yonetim'||location.pathname==='/yonetim/';
function add(){
 if(admin){const nav=document.querySelector('.sidebar nav');if(nav&&!nav.querySelector('[data-blog-entry]')){const a=document.createElement('a');a.href='/yonetim/blog';a.className='nav-link';a.dataset.blogEntry='';a.textContent='Blog yayınları';nav.append(a);}return;}
 const locale=document.documentElement.lang||'tr',target=['tr','en','ru','ar'].includes(locale)?locale:'tr',nav=document.querySelector('#footer .footer-grid>nav');
 if(nav&&!nav.querySelector('[data-blog-entry]')){for(const [i,text]of(labels[locale]||labels.tr).entries()){const a=document.createElement('a');a.href='/blog?lang='+target+(i?'&tool=paint':'');a.dataset.blogEntry='';a.textContent=text;nav.append(a);}}
}
add();const target=admin?document.querySelector('#app'):document.querySelector('#footer');if(target)new MutationObserver(add).observe(target,{childList:true,subtree:true});
