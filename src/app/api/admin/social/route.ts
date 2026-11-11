/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/app/api/admin/social/route.ts
 * Açıklama   : Yetkili katalog kaynakları ve özel, indirilebilir sosyal SVG çıktısı.
 */
import {NextRequest,NextResponse} from 'next/server';
import {requirePrincipal} from '@/server/auth';
import {generateSocialAsset,socialSources,socialSizes} from '@/server/social-assets';
import {enforceSameOrigin,readJsonLimited,publicFailure} from '@/server/security';
export const runtime='nodejs';
export const dynamic='force-dynamic';
const headers={'Cache-Control':'private, no-store','X-Robots-Tag':'noindex, nofollow','X-Content-Type-Options':'nosniff'};
function failure(error:unknown){const result=publicFailure(error);return NextResponse.json({error:result.message??'Sosyal tasarım hazırlanamadı.'},{status:result.status,headers});}
export async function GET(request:NextRequest){
 try{const principal=await requirePrincipal(request.headers,true),params=request.nextUrl.searchParams;return NextResponse.json(await socialSources(principal,{...Object.fromEntries(params),...(params.has('page')?{page:Number(params.get('page'))}:{})}),{headers});}catch(error){return failure(error);}
}
export async function POST(request:NextRequest){
 try{
  enforceSameOrigin(request,process.env.APP_URL!);const principal=await requirePrincipal(request.headers,true);
  const result=await generateSocialAsset(await readJsonLimited(request,16384),principal),snapshot=result.snapshot;
  const metadata={...socialSizes[snapshot.template],template:snapshot.template,theme:snapshot.theme,locale:snapshot.locale,source:snapshot.source,sku:snapshot.sku,priceMinor:snapshot.priceMinor,currency:snapshot.currency,fixture:snapshot.fixture,generatedAt:snapshot.generatedAt,filename:result.filename,sha256:result.sha256};
  return new Response(result.svg,{headers:{...headers,'Content-Type':'image/svg+xml; charset=utf-8','Content-Disposition':`attachment; filename="${result.filename}"`,'Content-Security-Policy':"sandbox; default-src 'none'; img-src data:; font-src data:; style-src 'unsafe-inline'",'X-Social-Metadata':encodeURIComponent(JSON.stringify(metadata)),'X-Content-SHA256':result.sha256}});
 }catch(error){return failure(error);}
}
