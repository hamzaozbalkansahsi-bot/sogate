/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/app/(store)/page.tsx
 * Açıklama   : İlgili müşteri veya yönetim sayfasını sunar.
 */
import {Home} from "@/components/home";
import {pageMetadata} from '@/server/page-metadata';
import {listProducts} from '@/server/commerce';
import {storePreferences} from '@/server/store-preferences';
import {publicCMSForRender} from '@/server/cms';
export function generateMetadata(){return pageMetadata('/','Tutkunu Keşfet.','Discover your desire.','SEXSOGATE koleksiyonlarını ve yakınlığa dair rehberleri keşfet.','Explore SEXSOGATE collections and thoughtful guides to closeness.');}
export default async function Page(){const preferences=await storePreferences();const [products,content]=await Promise.all([listProducts(preferences),publicCMSForRender(preferences.locale,preferences.currency)]);return <Home initialProducts={products} initialCMS={content}/>;}
