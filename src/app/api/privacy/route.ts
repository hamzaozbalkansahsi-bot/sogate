/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/app/api/privacy/route.ts
 * Açıklama   : İlgili kişi başvurusu alır ve yalnız sahibi veya asgari takip yetkisiyle durum döndürür.
 */
import {NextRequest,NextResponse} from 'next/server';
import {getPrincipal} from '@/server/auth';
import {createPrivacyRequest,getPrivacyRequest,myPrivacyRequests} from '@/server/privacy';
import {privacyQuota} from '@/server/privacy-rate';
import {HttpError,enforceSameOrigin,readJsonLimited,publicFailure} from '@/server/security';
export const runtime='nodejs';export const dynamic='force-dynamic';
const headers={'Cache-Control':'private, no-store','X-Robots-Tag':'noindex, nofollow'};
function failure(error:unknown,request:NextRequest){
 const result=publicFailure(error),en=request.headers.get('accept-language')?.startsWith('en');
 const english:Record<number,string>={400:'Check the email address and request fields.',401:'Sign in to view your requests.',403:'You cannot access this request.',404:'Request not found.',409:'The current request state does not allow this action.',429:'Too many requests. Please try again in a minute.',503:'The request service is temporarily unavailable. Please try again.'};
 return NextResponse.json({error:en?(english[result.status]??'Your request could not be completed.'):(result.message??'Başvuru işlemi tamamlanamadı.')},{status:result.status,headers});
}
export async function GET(request:NextRequest){
 try{const principal=await getPrincipal(request.headers),id=request.nextUrl.searchParams.get('case');if(id)return NextResponse.json(await getPrivacyRequest(id,request.nextUrl.searchParams.get('token'),principal),{headers});if(!principal)throw new HttpError(401,'Başvurularınızı görmek için giriş yapın.');return NextResponse.json({requests:await myPrivacyRequests(principal)},{headers});}catch(error){return failure(error,request);}
}
export async function POST(request:NextRequest){
 try{enforceSameOrigin(request,process.env.APP_URL!);await privacyQuota(request);const principal=await getPrincipal(request.headers);const result=await createPrivacyRequest(await readJsonLimited(request,32768),principal);return NextResponse.json(result,{status:201,headers});}catch(error){return failure(error,request);}
}
