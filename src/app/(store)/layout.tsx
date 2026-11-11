/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/app/(store)/layout.tsx
 * Açıklama   : Sayfa kabuğu, dil ve gezinme düzenini kurar.
 */
import {StoreShell} from "@/components/store-shell";
import {publicCMSForRender} from '@/server/cms';
import {storePreferences} from '@/server/store-preferences';
export default async function StoreLayout({children}:{children:React.ReactNode}){const {locale,currency}=await storePreferences();return <StoreShell initialCMS={await publicCMSForRender(locale,currency)}>{children}</StoreShell>;}
