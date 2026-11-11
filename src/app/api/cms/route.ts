/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/app/api/cms/route.ts
 * Açıklama   : Genel yayınları ve MFA korumalı CMS sürüm işlemlerini ayrı yanıtlarla sunar.
 */
import {NextRequest,NextResponse} from 'next/server';
import {z} from 'zod';
import {requirePrincipal} from '@/server/auth';
import {cmsAdmin,cmsHistory,cmsPreview,publicCMS,saveCMS} from '@/server/cms';
import {enforceSameOrigin,readJsonLimited,publicFailure} from '@/server/security';
export const runtime='nodejs';export const dynamic='force-dynamic';
const headers={'Cache-Control':'private, no-store','X-Robots-Tag':'noindex, nofollow'};
function failure(error:unknown,request:NextRequest){const params=request.nextUrl.searchParams,en=request.method==='GET'&&(params.get('view')??'public')==='public'&&(params.get('locale')??request.headers.get('accept-language')??'tr').startsWith('en');if(error instanceof z.ZodError)return NextResponse.json({error:en?'Please check your request and try again.':'İstek alanlarını kontrol edin.'},{status:400,headers});const e=publicFailure(error);return NextResponse.json({error:en?(e.status>=500?'Content is temporarily unavailable. Please try again.':'Please check your request and try again.'):e.message??'İçerik işlemi tamamlanamadı.',code:e.code},{status:e.status,headers});}
export async function GET(request:NextRequest){try{const params=request.nextUrl.searchParams,view=params.get('view')??'public';if(view==='public'){const locale=z.enum(['tr','en']).parse(params.get('locale')??'tr'),currency=z.enum(['TRY','EUR','USD','GBP']).parse(params.get('currency')??'TRY');const key=params.get('collection');if(key)z.string().regex(/^[a-z0-9]+(?:-[a-z0-9]+)*$/).max(100).parse(key);return NextResponse.json(await publicCMS(locale,currency,key??undefined,Number(params.get('page')??1)),{headers});}const principal=await requirePrincipal(request.headers,true);if(view==='admin')return NextResponse.json(await cmsAdmin(principal,{locale:params.get('locale')??'tr',page:Number(params.get('page')??1),q:params.get('q')??''}),{headers});const id=z.string().min(1).max(100).parse(params.get('id'));if(view==='history')return NextResponse.json(await cmsHistory(principal,id,params.get('pageContent')==='1'),{headers});if(view==='preview')return NextResponse.json(await cmsPreview(principal,id,params.get('pageContent')==='1'),{headers});return NextResponse.json({error:'İçerik görünümü bulunamadı.'},{status:404,headers});}catch(error){return failure(error,request);}}
export async function POST(request:NextRequest){try{enforceSameOrigin(request,process.env.APP_URL!);const principal=await requirePrincipal(request.headers,true);return NextResponse.json(await saveCMS(await readJsonLimited(request),principal),{headers});}catch(error){return failure(error,request);}}
