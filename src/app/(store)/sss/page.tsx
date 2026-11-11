/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/app/(store)/sss/page.tsx
 * Açıklama   : İlgili müşteri veya yönetim sayfasını sunar.
 */
import {FAQ} from "@/components/editorial";
import {pageMetadata} from '@/server/page-metadata';
export function generateMetadata(){return pageMetadata('/sss','Sık sorulan sorular','Frequently asked questions','Sipariş, teslimat, gizlilik ve iadeler hakkında sorularınız.','Answers about orders, delivery, privacy and returns.');}
export default function Page(){return <FAQ/>;}
