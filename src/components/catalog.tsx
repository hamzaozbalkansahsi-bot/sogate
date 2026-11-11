"use client";
/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/components/catalog.tsx
 * Açıklama   : Erişilebilir müşteri veya yönetim etkileşimini sunar.
 */
import Image from "next/image";
import {Suspense,useEffect,useState} from "react";
import {usePathname,useRouter,useSearchParams} from "next/navigation";
import Link from "./localized-link";
import {Search,SlidersHorizontal,ArrowUpRight} from "lucide-react";
import {catalogQueryKeys,type Product,type CatalogResult,type CatalogFacet} from "@/shared/contracts";
import {categories,categoryLabel,localePath} from "@/shared/i18n";
import {api} from "./api";
import {useStore} from "./store-context";
import {Busy,Empty,Modal,PageHeading,Status} from "./ui";
import {ProductCard} from "./product-card";
import {usePublicCMS} from "./cms-client";
import styles from './catalog-filters.module.css';

export function Catalog({initialResult,initialError=''}:{initialResult?:CatalogResult;initialError?:string}){
 const {locale,t,currency}=useStore(),params=useSearchParams(),router=useRouter(),pathname=usePathname();
 const query=params.toString(),category=params.get('category'),requestKey=[query,locale,currency].join('|');
 const [result,setResult]=useState<CatalogResult|null>(initialResult??null),[loadedQuery,setLoadedQuery]=useState<string|null>(()=>initialResult||initialError?requestKey:null),[error,setError]=useState(initialError),[formError,setFormError]=useState(''),[filters,setFilters]=useState(false);
 const loading=loadedQuery!==requestKey,products=result?.products??[],facets=result?.facets;
 useEffect(()=>{
  let active=true;const controller=new AbortController(),source=new URLSearchParams(query),requestParams=new URLSearchParams();
  for(const key of catalogQueryKeys)for(const value of source.getAll(key))requestParams.append(key,value);
  requestParams.set('locale',locale);requestParams.set('currency',currency);
  api<CatalogResult>(`/api/catalog?${requestParams.toString()}`,{signal:controller.signal}).then(data=>{if(active){setResult(data);setError('');}}).catch(cause=>{if(active){setError(cause.message);setResult(null);}}).finally(()=>{if(active)setLoadedQuery(requestKey);});
  return()=>{active=false;controller.abort();};
 },[query,locale,currency,requestKey]);
 const featureLabel=(feature:string)=>feature==='liquid'?(locale==='tr'?'Sıvı ürün':'Liquid product'):(locale==='tr'?'Hijyen mührü':'Hygiene seal');
 function filterForm(location:'desktop'|'mobile'){
  function select(name:string,label:string,options:CatalogFacet[]|undefined){
   if(!options?.length)return null;const selected=params.get(name)??'';
   return <label>{label}<select name={name} defaultValue={selected}><option value="">{locale==='tr'?'Tümü':'All'}</option>{selected&&!options.some(option=>option.value===selected)&&<option value={selected}>{selected} (0)</option>}{options.map(option=><option key={option.value} value={option.value}>{option.label??option.value} ({option.count})</option>)}</select></label>;
  }
  return <form key={`${requestKey}|${location}`} className={`form-stack filter-form ${styles.form}`} onSubmit={event=>{
   event.preventDefault();const data=new FormData(event.currentTarget),next=new URLSearchParams();setFormError('');
   for(const [key,value]of data.entries()){
    const text=String(value);if(!text)continue;
    if(key==='min'||key==='max'){
     if(!/^\d+(\.\d{1,2})?$/.test(text)){setFormError(locale==='tr'?'Fiyat aralığını kontrol edin.':'Check the price range.');return;}
     const [whole,fraction='']=text.split('.'),amount=BigInt(whole)*100n+BigInt(fraction.padEnd(2,'0'));
     if(amount>9_000_000_000_000n){setFormError(locale==='tr'?'Fiyat aralığını kontrol edin.':'Check the price range.');return;}next.set(key,amount.toString());
    }else next.append(key,text);
   }
   router.push(localePath(`${pathname}${next.size?'?'+next.toString():''}`,locale));setFilters(false);
  }}>
   <label>{t('search')}<div className="search-input"><Search size={18} aria-hidden="true"/><input name="q" defaultValue={params.get('q')??''} maxLength={120} type="search" autoComplete="off" placeholder={locale==='tr'?'Ürün adı, malzeme…':'Product name, material…'}/></div></label>
   {select('category',t('category'),facets?.categories)}{select('brand',locale==='tr'?'Marka':'Brand',facets?.brands)}{select('material',t('material'),facets?.materials)}
   {select('size',locale==='tr'?'Beden':'Size',facets?.sizes)}{select('color',locale==='tr'?'Renk':'Color',facets?.colors)}{select('power',locale==='tr'?'Pil / güç türü':'Battery / power type',facets?.power)}
   {Boolean(facets?.features.length)&&<fieldset className={styles.options}><legend>{locale==='tr'?'Özellikler':'Features'}</legend>{facets!.features.map(feature=><label className="checkbox" key={feature.value}><input type="checkbox" name="features" value={feature.value} defaultChecked={params.getAll('features').includes(feature.value)}/>{featureLabel(feature.value)} ({feature.count})</label>)}</fieldset>}
   <div className="form-grid">{(['min','max']as const).map(key=><label key={key}>{locale==='tr'?`${key==='min'?'En düşük':'En yüksek'} fiyat (${currency})`:`${key==='min'?'Minimum':'Maximum'} price (${currency})`}<input name={key} inputMode="decimal" type="number" min="0" max="90000000000" step="0.01" defaultValue={params.has(key)?Number(params.get(key))/100:''}/></label>)}</div>
   <label>{t('sort')}<select name="sort" defaultValue={(params.get('sort')??'newest').replace('-','_')}><option value="newest">{locale==='tr'?'En yeni':'Newest'}</option><option value="price_asc">{locale==='tr'?'Fiyat: düşükten yükseğe':'Price: low to high'}</option><option value="price_desc">{locale==='tr'?'Fiyat: yüksekten düşüğe':'Price: high to low'}</option><option value="name">{locale==='tr'?'Ürün adı':'Name'}</option></select></label>
   <label className="checkbox"><input type="checkbox" name="available" value="1" defaultChecked={params.get('available')==='1'}/>{t('onlyAvailable')}</label>
   {formError&&<p className="error" role="alert">{formError}</p>}<button className="button" type="submit">{t('filter')}</button><Link className="text-link" href="/urunler" onClick={()=>{setFilters(false);setFormError('');}}>{t('clearFilters')}</Link>
  </form>;
 }
 const title=category?(facets?.categories.find(option=>option.value===category)?.label??categoryLabel(category,locale)):t('all');
 function pageLink(page:number){const next=new URLSearchParams(query);next.set('page',String(page));return `/urunler?${next.toString()}`;}
 return <div className="container catalog-page"><nav className="breadcrumb"><Link href="/">{t('home')}</Link><span>/</span><span>{category?title:t('products')}</span></nav><PageHeading eyebrow="SEXSOGATE COLLECTION" title={title} description={locale==='tr'?'Kendi ritminizde, size ait bir keşif.':'A personal discovery, at your own pace.'}/>
  <div className="catalog-toolbar"><p className={styles.total} aria-live="polite">{loading?t('loading'):`${result?.total??0} ${locale==='tr'?'ürün':'pieces'}`}</p><button className="button button-outline mobile-filter" type="button" onClick={event=>{event.currentTarget.focus();setFilters(true);}} aria-haspopup="dialog"><SlidersHorizontal size={17}/>{t('filter')}</button></div>
  <div className="catalog-layout"><aside className="catalog-sidebar" aria-label={t('filter')}>{filterForm('desktop')}</aside><div aria-busy={loading}><Status error={error}/>{loading?<Busy/>:error?null:products.length?<><div className="product-grid catalog-grid">{products.map(product=><ProductCard product={product} key={product.id}/>)}</div><nav className="pagination" aria-label={locale==='tr'?'Ürün sayfaları':'Product pages'}>{result!.page>1&&<Link className="button button-outline" href={pageLink(result!.page-1)}>{t('previous')}</Link>}<p>{result!.page} / {Math.ceil(result!.total/result!.pageSize)}</p>{result!.page*result!.pageSize<result!.total&&<Link className="button button-outline" href={pageLink(result!.page+1)}>{t('next')}</Link>}</nav></>:<Empty title={t('noResults')} text={t('noResultsText')} href="/urunler" label={t('clearFilters')}/>}</div></div>
  <Modal open={filters} onClose={()=>setFilters(false)} title={t('filter')}><div className={styles.drawer}>{filterForm('mobile')}</div></Modal>
 </div>;
}
export function Collections(){return <Suspense fallback={<Busy/>}><CollectionContents/></Suspense>;}
function CollectionContents(){const {locale,t}=useStore(),params=useSearchParams(),selected=params.get("collection")??undefined,page=Number(params.get("page")??1),{content,loading,error}=usePublicCMS(selected,page);return <div className="container section"><PageHeading eyebrow="SEXSOGATE COLLECTION" title={content?.collection?.title??t("collections")} description={content?.collection?.description??t("categoriesSub")}/><Status error={error}/>{selected?(loading?<Busy/>:content?.collection?<><Link className="text-link" href="/koleksiyonlar">{t("collections")}</Link><div className="product-grid">{content.products?.map(product=><ProductCard key={product.id} product={product}/>)}</div><div className="pagination">{page>1&&<Link className="button button-outline" href={`/koleksiyonlar?collection=${selected}&page=${page-1}`}>{t("previous")}</Link>}{page*24<(content.total??0)&&<Link className="button button-outline" href={`/koleksiyonlar?collection=${selected}&page=${page+1}`}>{t("next")}</Link>}</div></>:<Empty title={t("notPublished")} href="/koleksiyonlar" label={t("collections")}/>):<div className="category-grid collection-grid">{content?.collections.length?content.collections.map(item=><Link className="category-tile" href={`/koleksiyonlar?collection=${item.key}`} key={item.key}><Image unoptimized src={item.image} alt={item.title} width={480} height={420}/><div><h2>{item.title}</h2><ArrowUpRight size={22}/></div></Link>):categories.map(c=><Link className="category-tile" href={`/urunler?category=${c.slug}`} key={c.slug}><Image unoptimized src={`/media/atelier-${c.image}.svg`} alt="" width={480} height={420}/><div><h2>{categoryLabel(c.slug,locale)}</h2><ArrowUpRight size={22}/></div></Link>)}</div>}</div>;}
export function Favorites(){const {t,user,currency,locale}=useStore(),[products,setProducts]=useState<Product[]>([]),[error,setError]=useState(""),[loading,setLoading]=useState(true);useEffect(()=>{api<{items:Product[]}>(`/api/favorites?currency=${currency}&locale=${locale}`).then(d=>setProducts(d.items)).catch(e=>setError(e.message)).finally(()=>setLoading(false));},[user,currency,locale]);return <div className="container section"><PageHeading title={t("favorites")}/>{user?<><Status error={error}/>{loading?<Busy/>:products.length?<div className="product-grid">{products.map(p=><ProductCard product={p} key={p.id}/>)}</div>:<Empty title={t("wishlistEmpty")} text={t("wishlistText")} href="/urunler" label={t("discover")}/>}</>:<Empty title={t("wishlistEmpty")} text={t("loginRequired")} href="/hesap" label={t("signIn")}/>}</div>;}
