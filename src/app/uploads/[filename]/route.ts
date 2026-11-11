/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/app/uploads/[filename]/route.ts
 * Açıklama   : HTTP işlemini doğrulayıp yetkili veri akışına bağlar.
 */
import {NextResponse} from 'next/server';
import {pool} from '@/server/db';
import {getPrincipal} from '@/server/auth';
import {storage} from '@/server/providers/storage';
import {publicCMSAsset} from '@/server/cms';
import {PUBLIC_PRODUCT_SQL} from '@/server/public-catalog';
export const dynamic='force-dynamic';export const runtime='nodejs';
export async function GET(request:Request,{params}:{params:Promise<{filename:string}>}){
 const {filename}=await params;const headers={'Cache-Control':'private, no-store','X-Content-Type-Options':'nosniff'};
 if(!/^[a-f0-9-]{36}\.webp$/.test(filename))return new NextResponse(null,{status:404,headers});
 const result=await pool.query('SELECT id FROM media_assets WHERE object_key=$1',[`products/${filename}`]);if(!result.rowCount)return new NextResponse(null,{status:404,headers});
 const published=await pool.query(`SELECT p.id FROM products p WHERE p.image=$1 AND ${PUBLIC_PRODUCT_SQL} AND(p.fixture=false OR $2=true) LIMIT 1`,[`/uploads/${filename}`,['development','test'].includes(process.env.APP_ENV??'')]);
 if(!published.rowCount&&!await publicCMSAsset(filename)){const principal=await getPrincipal(request.headers);if(!principal?.mfa||!['admin','catalog','marketing'].includes(principal.role))return new NextResponse(null,{status:404,headers});}
 try{const body=await storage().get(`products/${filename}`);return new NextResponse(new Uint8Array(body),{headers:{...headers,'Content-Type':'image/webp'}});}catch{return new NextResponse(null,{status:404,headers});}
}
