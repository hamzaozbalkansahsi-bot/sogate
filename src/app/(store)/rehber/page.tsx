/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/app/(store)/rehber/page.tsx
 * Açıklama   : İlgili müşteri veya yönetim sayfasını sunar.
 */
import {Journal} from "@/components/editorial";
import {pageMetadata} from '@/server/page-metadata';
export function generateMetadata(){return pageMetadata('/rehber','Rehber','Journal','Ürün seçimi, bakım ve bilinçli alışveriş için kısa rehberler.','Short guides to product selection, care and thoughtful shopping.');}
export default function Page(){return <Journal/>;}
