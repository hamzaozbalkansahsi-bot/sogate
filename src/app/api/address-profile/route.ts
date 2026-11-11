/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/app/api/address-profile/route.ts
 * Açıklama   : Yalnız açık ülkenin onaylı adres alanlarını sunar; özel onay referanslarını yayımlamaz.
 */
import {NextRequest,NextResponse} from 'next/server';
import {publicAddressProfile} from '@/server/address-profiles';
import {publicFailure} from '@/server/security';
import {customerErrorMessage} from '@/shared/errors';
export const runtime='nodejs';export const dynamic='force-dynamic';
const headers={'Cache-Control':'private, no-store','X-Robots-Tag':'noindex, nofollow'};
export async function GET(request:NextRequest){
 try{return NextResponse.json(await publicAddressProfile(request.nextUrl.searchParams.get('country')??''),{headers});}
 catch(error){const failure=publicFailure(error);return NextResponse.json({error:customerErrorMessage(failure.code,failure.status,failure.message,request.headers.get('accept-language')?.startsWith('en')?'en':'tr')},{status:failure.status,headers});}
}
