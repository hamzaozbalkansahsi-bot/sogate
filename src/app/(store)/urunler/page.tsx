/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/app/(store)/urunler/page.tsx
 * Açıklama   : İlgili müşteri veya yönetim sayfasını sunar.
 */
import {Suspense} from "react";
import {Catalog} from "@/components/catalog";
import {parseCatalogQuery,searchCatalog} from '@/server/commerce/catalog';
import {catalogQueryKeys,type CatalogResult} from '@/shared/contracts';
import {DomainError} from '@/server/commerce/rules';
import {storePreferences} from '@/server/store-preferences';
import {pageMetadata} from '@/server/page-metadata';
export async function generateMetadata({searchParams}:{searchParams:Promise<Record<string,string|string[]|undefined>>}){
 const metadata=await pageMetadata('/urunler','Ürünler','Products','Ürünleri kategori, malzeme ve fiyat seçenekleriyle inceleyin.','Browse products by category, material and price.');
 if(Object.keys(await searchParams).length)metadata.robots={index:false,follow:true};return metadata;
}
export default async function Page({searchParams}:{searchParams:Promise<Record<string,string|string[]|undefined>>}){
 const values=await searchParams,params=new URLSearchParams(),preferences=await storePreferences();
 for(const key of catalogQueryKeys){const value=values[key];if(Array.isArray(value))for(const item of value)params.append(key,item);else if(value!==undefined)params.set(key,value);}
 let result:CatalogResult|undefined,error='';
 try{result=await searchCatalog({...parseCatalogQuery(params,preferences),...preferences});}catch(cause){if(!(cause instanceof DomainError))throw cause;error=cause.message;}
 return <Suspense><Catalog initialResult={result} initialError={error}/></Suspense>;
}
