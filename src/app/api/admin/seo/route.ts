/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/app/api/admin/seo/route.ts
 * Açıklama   : MFA ve rol denetimiyle SEO düzenleme ve rapor isteklerini karşılar.
 */
import {NextRequest,NextResponse} from 'next/server';
import {requirePrincipal} from '@/server/auth';
import {seoReport} from '@/server/seo';
import {manageRedirect,redirects,saveProductSEO} from '@/server/seo-management';
import {enforceSameOrigin,readJsonLimited,publicFailure} from '@/server/security';
export const runtime='nodejs';export const dynamic='force-dynamic';
const headers={'Cache-Control':'private, no-store','X-Robots-Tag':'noindex, nofollow'};
function failure(error:unknown){const result=publicFailure(error);return NextResponse.json({error:result.message??'İşlem tamamlanamadı.'},{status:result.status,headers});}
export async function GET(request:NextRequest){
 try{const principal=await requirePrincipal(request.headers,true);const params=request.nextUrl.searchParams;return NextResponse.json(params.get('view')==='redirects'?{rows:await redirects(principal)}:await seoReport(principal,{locale:params.get('locale')==='en'?'en':'tr',page:Number(params.get('page')??1),q:params.get('q')??''}),{headers});}catch(error){return failure(error);}
}
export async function POST(request:NextRequest){
 try{enforceSameOrigin(request,process.env.APP_URL!);const principal=await requirePrincipal(request.headers,true);const body=await readJsonLimited(request);return NextResponse.json((body as {action?:string}).action==='redirect'?await manageRedirect(body,principal):await saveProductSEO(body,principal),{headers});}catch(error){return failure(error);}
}
