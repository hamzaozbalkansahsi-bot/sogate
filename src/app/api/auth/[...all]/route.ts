/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/app/api/auth/[...all]/route.ts
 * Açıklama   : HTTP işlemini doğrulayıp yetkili veri akışına bağlar.
 */
import { getAuth } from '@/server/auth';
export const runtime='nodejs';
export const dynamic='force-dynamic';
export async function GET(request:Request){return getAuth().handler(request);}
export async function POST(request:Request){return getAuth().handler(request);}
