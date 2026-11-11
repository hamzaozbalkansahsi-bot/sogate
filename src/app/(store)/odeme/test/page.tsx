/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/app/(store)/odeme/test/page.tsx
 * Açıklama   : İlgili müşteri veya yönetim sayfasını sunar.
 */
import {Suspense} from "react";
import {TestPayment} from "@/components/checkout";
export const metadata={title:"Test ödemesi | SEXSOGATE",robots:{index:false,follow:false}};
export default function Page(){return <Suspense><TestPayment/></Suspense>;}

export const dynamic="force-dynamic";
