/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/app/(store)/hesap/parola-yenile/page.tsx
 * Açıklama   : İlgili müşteri veya yönetim sayfasını sunar.
 */
import {PasswordReset} from "@/components/account";
export const metadata={title:"Parola yenile | SEXSOGATE",robots:{index:false,follow:false}};
export default function Page(){return <PasswordReset/>;}

export const dynamic="force-dynamic";
