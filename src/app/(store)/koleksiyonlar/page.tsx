/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/app/(store)/koleksiyonlar/page.tsx
 * Açıklama   : İlgili müşteri veya yönetim sayfasını sunar.
 */
import {Collections} from "@/components/catalog";
import {pageMetadata} from '@/server/page-metadata';
export function generateMetadata(){return pageMetadata('/koleksiyonlar','Koleksiyonlar','Collections','Kendine ve birlikte geçirdiğin zamana yer açan koleksiyonlar.','Collections for yourself and the time you share.');}
export default function Page(){return <Collections/>;}
