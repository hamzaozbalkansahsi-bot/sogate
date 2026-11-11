/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/app/api/admin/lots/route.ts
 * Açıklama   : MFA ve rol denetimli lot yönetimi ile geri çağırma rapor uçları.
 */
import {NextRequest,NextResponse} from 'next/server';
import {requirePrincipal} from '@/server/auth';
import {listLots,manageLot,recallOrders,unknownLotReturns,lotSources} from '@/server/commerce/lots';
import {HttpError,enforceSameOrigin,readJsonLimited,publicFailure} from '@/server/security';
export const runtime='nodejs';export const dynamic='force-dynamic';
const headers={'Cache-Control':'private, no-store','X-Robots-Tag':'noindex, nofollow'};
function failure(error:unknown){const result=publicFailure(error);return NextResponse.json({error:result.message??'Lot işlemi tamamlanamadı.'},{status:result.status,headers});}
export async function GET(request:NextRequest){
 try{
  const principal=await requirePrincipal(request.headers,true),params=request.nextUrl.searchParams;
  if(params.get('view')==='sources'){
   const keys=[...params.keys()],allowed=new Set(['view','lotId','q','page']);
   const lotId=(params.get('lotId')??'').trim(),q=(params.get('q')??'').trim(),page=Number(params.get('page')??1);
   if(keys.some(key=>!allowed.has(key))||new Set(keys).size!==keys.length||!lotId||lotId.length>300||q.length>100||/[\u0000-\u001f\u007f]/.test(lotId+q)||!Number.isSafeInteger(page)||page<1||page>100000)throw new HttpError(400,'Mal kabulü kaynağı arama alanlarını kontrol edin.','INVALID_LOT_FILTER');
   return NextResponse.json(await lotSources(principal,lotId,{q,page}),{headers});
  }
  return NextResponse.json(params.get('view')==='recall'?await recallOrders(params.get('lotId')??'',principal,Number(params.get('page')??1)):params.get('view')==='holds'?await unknownLotReturns(principal,Object.fromEntries(params)):await listLots(principal,Object.fromEntries(params)),{headers});
 }catch(error){return failure(error);}
}
export async function POST(request:NextRequest){try{enforceSameOrigin(request,process.env.APP_URL!);const principal=await requirePrincipal(request.headers,true);return NextResponse.json(await manageLot(await readJsonLimited(request),principal),{headers});}catch(error){return failure(error);}}
