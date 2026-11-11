/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/app/api/admin/compliance/route.ts
 * Açıklama   : Özel SKU belge ve uygunluk işlemlerinde oturum, MFA, köken ve girdi sınırını uygular.
 */
import {NextResponse} from 'next/server';
import {z} from 'zod';
import {requirePrincipal} from '@/server/auth';
import {enforceSameOrigin,readJsonLimited,publicFailure,HttpError} from '@/server/security';
import {listCompliance,getCompliance,complianceAction} from '@/server/compliance';
export const runtime='nodejs';export const dynamic='force-dynamic';
const headers={'Cache-Control':'private, no-store','X-Robots-Tag':'noindex, nofollow'};
function failure(error:unknown){const problem=error instanceof z.ZodError?{status:400,message:'Arama ve sayfa alanlarını kontrol edin.',code:'INVALID_FILTER'}:publicFailure(error);return NextResponse.json({error:problem.message??'Belge işlemi tamamlanamadı.',code:problem.code},{status:problem.status,headers});}
export async function GET(request:Request){try{const principal=await requirePrincipal(request.headers,true),params=new URL(request.url).searchParams;for(const key of params.keys())if(params.getAll(key).length!==1)throw new HttpError(400,'Sorgu alanları tekrarlanamaz.');const data=z.object({variantId:z.string().min(1).max(300).optional(),q:z.string().max(100).optional(),page:z.coerce.number().int().min(1).max(100000).optional(),state:z.enum(['all','pending','approved','revoked']).optional()}).strict().parse(Object.fromEntries(params));return NextResponse.json(data.variantId?await getCompliance(data.variantId,principal):await listCompliance(principal,data),{headers});}catch(error){return failure(error);}}
export async function POST(request:Request){try{enforceSameOrigin(request,process.env.APP_URL??'http://127.0.0.1:3000');const principal=await requirePrincipal(request.headers,true);return NextResponse.json(await complianceAction(await readJsonLimited(request),principal),{headers});}catch(error){return failure(error);}}
