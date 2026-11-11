/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/app/(store)/urun/[slug]/page.tsx
 * Açıklama   : Dil bazlı canonical ürün yolunu, gerçek metaveriyi ve ürün sayfasını sunar.
 */
import {notFound} from 'next/navigation';
import {getProduct} from '@/server/commerce';
import {ProductDetail} from '@/components/product-detail';
import type {Metadata} from 'next';
import {headers,cookies} from 'next/headers';
import {productSEO} from '@/server/seo-management';
import {localizedProductPath} from '@/shared/seo-rules';
import {productStructuredData} from '@/shared/product-seo';
import {getMarkets} from '@/server/markets';
import type {Currency} from '@/shared/contracts';
export const dynamic='force-dynamic';
async function preferences(){
 const locale=(await headers()).get('x-site-locale')==='en'?'en' as const:'tr' as const;
 const value=(await cookies()).get('sexsogate_currency')?.value;
 const currency:Currency=['TRY','EUR','USD','GBP'].includes(value??'')?value as Currency:'TRY';return {locale,currency};
}
export async function generateMetadata({params}:{params:Promise<{slug:string}>}):Promise<Metadata>{
 const {slug}=await params;const {locale,currency}=await preferences();const product=await getProduct(slug,locale,currency);
 if(!product)return {title:locale==='en'?'Product not found':'Ürün bulunamadı',robots:{index:false}};
 const fields=await productSEO(product.id,locale);const en=locale==='en';
 const title=fields?.title||(en?product.nameEn:product.name),description=fields?.description||(en?product.descriptionEn:product.description);
 const tr=localizedProductPath('tr',product.localizedSlugs?.tr??product.slug),english=localizedProductPath('en',product.localizedSlugs?.en??product.slug),canonical=en?english:tr;
 const languages={'tr-TR':tr,...(product.nameEn.trim()&&product.descriptionEn.trim()?{en:english}:{}),'x-default':tr};
 return {title,description,alternates:{canonical,languages},openGraph:{title,description,url:canonical,locale:en?'en_GB':'tr_TR',images:[{url:product.image,alt:fields?.alt||(en?product.nameEn:product.name)}]},robots:product.fixture?{index:false,follow:false}:undefined};
}
export default async function Page({params}:{params:Promise<{slug:string}>}){
 const {slug}=await params;const {locale,currency}=await preferences();const product=await getProduct(slug,locale,currency);if(!product)notFound();
 const canonical=product.localizedSlugs?.[locale]??product.slug;if(slug!==canonical)notFound();
 const country=(await cookies()).get('sexsogate_country')?.value??'TR';
 const market=(await getMarkets()).markets.find(value=>value.countryCode===country);
 const structured=productStructuredData(product,locale,currency,process.env.APP_URL??'http://127.0.0.1:3000',market?.settlementCurrency??null);
 return <>{structured&&<script type="application/ld+json" dangerouslySetInnerHTML={{__html:JSON.stringify(structured).replace(/</g,'\\u003c')}}/>}<ProductDetail product={product}/></>;
}
