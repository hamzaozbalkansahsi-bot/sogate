/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/app/(store)/siparis/[id]/page.tsx
 * Açıklama   : İlgili müşteri veya yönetim sayfasını sunar.
 */
import {Suspense} from "react";
import {OrderPage} from "@/components/checkout";
export const metadata={title:"Siparişiniz | SEXSOGATE",robots:{index:false,follow:false}};
export default async function Page({params}:{params:Promise<{id:string}>}){const {id}=await params;return <Suspense><OrderPage id={id}/></Suspense>;}

export const dynamic="force-dynamic";
