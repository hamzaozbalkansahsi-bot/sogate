/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/app/(store)/iletisim/page.tsx
 * Açıklama   : İlgili müşteri veya yönetim sayfasını sunar.
 */
import {Contact} from "@/components/editorial";
import {pageMetadata} from '@/server/page-metadata';
export function generateMetadata(){return pageMetadata('/iletisim','İletişim','Contact','Ürün, sipariş ve teslimat sorularınız için destek kanalları.','Support channels for product, order and delivery questions.');}
export default function Page(){return <Contact/>;}
