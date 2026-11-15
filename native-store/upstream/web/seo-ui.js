import {seoPage} from './seo-core.js?v=search-automation-20261112-r1';
let lastKey='',lastTitle='';
export function updateStoreSEO(catalog,config){
 const seoURL=new URL(location.href);if(!['tr','en','ru','ar','de','az','kk','tk','uz','ky','fa'].includes(seoURL.searchParams.get('lang')))seoURL.searchParams.set('lang',document.documentElement.lang);
 const selected=catalog.products?.find(p=>String(p.id)===seoURL.searchParams.get('product'));
 const key=seoURL.href+'|'+String(catalog.meta?.controlRevision||catalog.meta?.releaseHash||'')+'|'+JSON.stringify(config)+'|'+JSON.stringify(selected?{name:selected.name,modelName:selected.modelName,description:selected.description,seoTitle:selected.seoTitle,seoDescription:selected.seoDescription,variantLabel:selected.variantLabel,variantColor:selected.variantColor,specs:selected.specs}:null);if(key===lastKey){document.title=lastTitle;return;}lastKey=key;
 const page=seoPage(catalog,config,seoURL);lastTitle=page.title;document.title=page.title;
 document.head.querySelectorAll('meta[name="description"],meta[name="robots"],meta[property^="og:"],meta[name^="twitter:"],link[rel="canonical"],link[rel="alternate"][hreflang],script[data-nodeno-seo],meta[name="google-site-verification"],meta[name="msvalidate.01"],meta[name="yandex-verification"]').forEach(node=>node.remove());
 function meta(key,value){const node=document.createElement('meta');node.setAttribute(key.startsWith('og:')?'property':'name',key);node.content=value;document.head.append(node);}
 for(const [key,value]of Object.entries({'description':page.description,'robots':page.indexable?'index,follow,max-image-preview:large':'noindex,follow','og:title':page.title,'og:description':page.description,'og:type':page.kind==='product'?'product':'website','og:site_name':'NODENO','twitter:card':'summary_large_image',...(page.canonical?{'og:url':page.canonical}:{}),...(page.image?{'og:image':page.image}:{})}))meta(key,value);
 for(const [field,name]of [['googleVerification','google-site-verification'],['bingVerification','msvalidate.01'],['yandexVerification','yandex-verification']])if(page.verification?.[field])meta(name,page.verification[field]);
 if(page.canonical){const link=document.createElement('link');link.rel='canonical';link.href=page.canonical;document.head.append(link);}
 for(const row of page.alternates){const link=document.createElement('link');link.rel='alternate';link.hreflang=row.locale;link.href=row.url;document.head.append(link);}
 if(page.jsonld.length){const script=document.createElement('script');script.type='application/ld+json';script.dataset.nodenoSeo='';const nonce=document.querySelector('script[nonce]')?.nonce;if(nonce)script.nonce=nonce;script.textContent=JSON.stringify(page.jsonld);document.head.append(script);}
}
