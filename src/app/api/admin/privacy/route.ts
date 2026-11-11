/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/app/api/admin/privacy/route.ts
 * Açıklama   : Rol, oturum MFA ve kritik yapılandırmada parola doğrulamasıyla başvuru yönetimini sunar.
 */
import {NextRequest,NextResponse} from 'next/server';
import {getAuth,requirePrincipal} from '@/server/auth';
import {privacyAdmin,privacyAction,saveController,savePrivacyPolicy} from '@/server/privacy';
import {HttpError,enforceSameOrigin,readJsonLimited,publicFailure} from '@/server/security';
export const runtime='nodejs';export const dynamic='force-dynamic';
const headers={'Cache-Control':'private, no-store','X-Robots-Tag':'noindex, nofollow'};
function failure(error:unknown){const result=publicFailure(error);return NextResponse.json({error:result.message??'Gizlilik yönetimi işlemi tamamlanamadı.'},{status:result.status,headers});}
export async function GET(request:NextRequest){
 try{const principal=await requirePrincipal(request.headers,true),params=request.nextUrl.searchParams;return NextResponse.json(await privacyAdmin(principal,{page:Number(params.get('page')??1),q:params.get('q')??'',id:params.get('id')??undefined,status:params.get('status')||undefined}),{headers});}catch(error){return failure(error);}
}
export async function POST(request:NextRequest){
 try{
  enforceSameOrigin(request,process.env.APP_URL!);const principal=await requirePrincipal(request.headers,true),raw=await readJsonLimited(request,32768);
  if(!raw||typeof raw!=='object'||Array.isArray(raw))throw new HttpError(400,'İşlem biçimi geçersiz.');
  const input=raw as Record<string,unknown>;
  if(input.action==='controller'||input.action==='policy'){
   if(principal.role!=='admin')throw new HttpError(403,'Bu yapılandırmayı yalnız yönetici değiştirebilir.');
   const password=input.password;if(typeof password!=='string'||password.length<12)throw new HttpError(400,'Parolanızı yeniden doğrulayın.');
   await getAuth().api.verifyPassword({headers:request.headers,body:{password}}).catch(()=>{throw new HttpError(403,'Parola doğrulaması başarısız.');});
   const body=Object.fromEntries(Object.entries(input).filter(([key])=>key!=='password'));
   return NextResponse.json(input.action==='controller'?await saveController(body,principal):await savePrivacyPolicy(body,principal),{headers});
  }
  return NextResponse.json(await privacyAction(input,principal),{headers});
 }catch(error){return failure(error);}
}
