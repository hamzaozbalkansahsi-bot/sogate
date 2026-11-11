/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/app/(store)/rehber/[slug]/page.tsx
 * Açıklama   : İlgili müşteri veya yönetim sayfasını sunar.
 */
import {Content} from "@/components/editorial";
import {publicGuideForRender} from '@/server/cms';
import {storePreferences} from '@/server/store-preferences';
import {notFound} from 'next/navigation';
import type {Metadata} from 'next';
export const dynamic='force-dynamic';
export async function generateMetadata({params}:{params:Promise<{slug:string}>}):Promise<Metadata>{
 const {slug}=await params,{locale}=await storePreferences(),page=await publicGuideForRender(slug,locale);if(!page)return {title:locale==='en'?'Guide not found':'Rehber bulunamadı',robots:{index:false,follow:false}};
 const [tr,en]=await Promise.all([publicGuideForRender(slug,'tr'),publicGuideForRender(slug,'en')]);
 const path=`${locale==='en'?'/en':''}/rehber/${slug}`,description=page.body.replace(/^#+\s*/gm,'').replace(/\s+/g,' ').trim().slice(0,180),languages={...(tr?{'tr-TR':`/rehber/${slug}`} :{}),...(en?{en:`/en/rehber/${slug}`} :{}),'x-default':tr?`/rehber/${slug}`:path};
 return {title:page.title,description,alternates:{canonical:path,languages},openGraph:{title:page.title,description,url:path,locale:locale==='en'?'en_GB':'tr_TR',images:['/brand/share-preview.png']},robots:page.fixture?{index:false,follow:false}:undefined};
}
export default async function Page({params}:{params:Promise<{slug:string}>}){const {slug}=await params,{locale}=await storePreferences(),page=await publicGuideForRender(slug,locale);if(!page)notFound();return <Content slug={slug} initialPage={page}/>;}
