/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/app/(store)/odeme/page.tsx
 * Açıklama   : İlgili müşteri veya yönetim sayfasını sunar.
 */
import {Checkout} from "@/components/checkout";
export const metadata={title:"Ödeme | SEXSOGATE",robots:{index:false,follow:false}};
export default function Page(){return <Checkout/>;}

export const dynamic="force-dynamic";
