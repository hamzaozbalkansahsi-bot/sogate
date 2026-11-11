/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/app/(store)/favoriler/page.tsx
 * Açıklama   : İlgili müşteri veya yönetim sayfasını sunar.
 */
import {Favorites} from "@/components/catalog";
export const metadata={title:"Favorilerim | SEXSOGATE",robots:{index:false,follow:false}};
export default function Page(){return <Favorites/>;}

export const dynamic="force-dynamic";
