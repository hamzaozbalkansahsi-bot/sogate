/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/app/api/admin/address-profiles/route.ts
 * Açıklama   : Yönetici MFA ve kritik onayda parola doğrulamasıyla adres alanı sürümlerini yönetir.
 */
import {NextRequest,NextResponse} from 'next/server';
import {getAuth,requirePrincipal} from '@/server/auth';
import {listAddressProfiles,manageAddressProfile} from '@/server/address-profiles';
import {HttpError,enforceSameOrigin,readJsonLimited,publicFailure} from '@/server/security';
export const runtime='nodejs';export const dynamic='force-dynamic';
const headers={'Cache-Control':'private, no-store','X-Robots-Tag':'noindex, nofollow'};
function failure(error:unknown){const result=publicFailure(error);return NextResponse.json({error:result.message??'Adres kuralları işlemi tamamlanamadı.'},{status:result.status,headers});}
export async function GET(request:NextRequest){try{const principal=await requirePrincipal(request.headers,true);return NextResponse.json(await listAddressProfiles(principal,{country:request.nextUrl.searchParams.get('country')||undefined,page:Number(request.nextUrl.searchParams.get('page')??1),q:request.nextUrl.searchParams.get('q')??''}),{headers});}catch(error){return failure(error);}}
export async function POST(request:NextRequest){
 try{
  enforceSameOrigin(request,process.env.APP_URL!);const principal=await requirePrincipal(request.headers,true);if(principal.role!=='admin')throw new HttpError(403,'Adres kurallarını yalnız yönetici değiştirebilir.');
  const input=await readJsonLimited(request,32768);if(!input||typeof input!=='object'||Array.isArray(input))throw new HttpError(400,'İşlem biçimi geçersiz.');
  const value=input as Record<string,unknown>;
  if(value.action==='approve'||value.action==='archive'){
   if(typeof value.password!=='string'||value.password.length<12)throw new HttpError(400,'Parolanızı yeniden doğrulayın.');
   await getAuth().api.verifyPassword({headers:request.headers,body:{password:value.password}}).catch(()=>{throw new HttpError(403,'Parola doğrulaması başarısız.');});
  }
  return NextResponse.json(await manageAddressProfile(Object.fromEntries(Object.entries(value).filter(([key])=>key!=='password')),principal),{headers});
 }catch(error){return failure(error);}
}
