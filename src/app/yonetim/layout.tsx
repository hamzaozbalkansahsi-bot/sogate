/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/app/yonetim/layout.tsx
 * Açıklama   : Sayfa kabuğu, dil ve gezinme düzenini kurar.
 */
import {AdminShell} from "@/components/admin";
export const metadata={title:"Yönetim | SEXSOGATE",robots:{index:false,follow:false}};
export default function Layout({children}:{children:React.ReactNode}){return <AdminShell>{children}</AdminShell>;}

export const dynamic="force-dynamic";
