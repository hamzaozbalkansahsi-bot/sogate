/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/app/(store)/sepet/page.tsx
 * Açıklama   : İlgili müşteri veya yönetim sayfasını sunar.
 */
import {CartPage} from "@/components/checkout";
export const metadata={title:"Sepetim | SEXSOGATE",robots:{index:false,follow:false}};
export default function Page(){return <CartPage/>;}

export const dynamic="force-dynamic";
