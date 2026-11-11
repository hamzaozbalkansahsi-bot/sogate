/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/app/(store)/hesap/page.tsx
 * Açıklama   : İlgili müşteri veya yönetim sayfasını sunar.
 */
import {Account} from "@/components/account";
export const metadata={title:"Hesabım | SEXSOGATE",robots:{index:false,follow:false}};
export default function Page(){return <Account/>;}

export const dynamic="force-dynamic";
