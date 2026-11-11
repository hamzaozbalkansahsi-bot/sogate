/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/app/api/orders/[id]/document/route.ts
 * Açıklama   : HTTP işlemini doğrulayıp yetkili veri akışına bağlar.
 */
import {NextRequest,NextResponse} from 'next/server';
import {getPrincipal} from '@/server/auth';
import {getOrder} from '@/server/commerce';
import {pool} from '@/server/db';
import {makeOrderDocument} from '@/server/order-document';
export const dynamic='force-dynamic';export const runtime='nodejs';
const headers={'Cache-Control':'private, no-store','X-Robots-Tag':'noindex, nofollow'};
export async function GET(request:NextRequest,{params}:{params:Promise<{id:string}>}){
 const {id}=await params;const user=await getPrincipal(request.headers);const order=await getOrder(id,request.nextUrl.searchParams.get('token'),user?.id);
 if(!order)return NextResponse.json({error:'Sipariş bulunamadı.'},{status:404,headers});
 const result=await pool.query('SELECT title,body,version,body_hash,accepted_at FROM order_agreements WHERE order_id=$1 ORDER BY kind',[id]);
 const agreements=result.rows.map(row=>({title:row.title,body:row.body,version:row.version,bodyHash:row.body_hash,acceptedAt:row.accepted_at.toISOString()}));
 if(request.nextUrl.searchParams.get('format')==='json')return NextResponse.json({orderNumber:order.number,agreements},{headers});
 const pdf=await makeOrderDocument(order,agreements);return new NextResponse(new Uint8Array(pdf),{headers:{...headers,'Content-Type':'application/pdf','Content-Disposition':`attachment; filename="SEXSOGATE-${order.number}.pdf"`}});
}
