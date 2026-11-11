/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/app/yonetim/giris/page.tsx
 * Açıklama   : İlgili müşteri veya yönetim sayfasını sunar.
 */
import Image from "next/image";
import {SignIn} from "@/components/account";
export default function Page(){return <div className="admin-login-wrap"><Image unoptimized src="/brand/logo-horizontal.svg" alt="SEXSOGATE" width={690} height={114}/><SignIn admin/></div>;}
