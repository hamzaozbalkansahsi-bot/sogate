/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/app/api/admin/media/route.ts
 * Açıklama   : HTTP işlemini doğrulayıp yetkili veri akışına bağlar.
 */
import {NextResponse} from 'next/server';
import {randomUUID,createHash} from 'node:crypto';
import sharp from 'sharp';
import {requirePrincipal} from '@/server/auth';
import {pool,transaction} from '@/server/db';
import {enforceSameOrigin,HttpError,readBodyLimited,validateRaster} from '@/server/security';
import {storage} from '@/server/providers/storage';
const headers={'Cache-Control':'private, no-store','X-Robots-Tag':'noindex'};
export const runtime='nodejs';export const dynamic='force-dynamic';
async function authorized(request:Request){const principal=await requirePrincipal(request.headers,true);if(!['admin','catalog','marketing'].includes(principal.role))throw new HttpError(403,'Medya yönetimi için yetkiniz yok.');return principal;}
export async function GET(request:Request){try{await authorized(request);return NextResponse.json({rows:(await pool.query('SELECT id,object_key,mime_type,size_bytes,rights_reference,created_at FROM media_assets ORDER BY created_at DESC LIMIT 50')).rows.map(r=>({id:r.id,url:`/uploads/${r.object_key.split('/').pop()}`,mimeType:r.mime_type,sizeBytes:r.size_bytes,rightsReference:r.rights_reference,createdAt:r.created_at}))},{headers});}catch{return NextResponse.json({error:'Medya için yetkili oturum gerekir.'},{status:403,headers});}}
export async function POST(request:Request){
 try{
  enforceSameOrigin(request,process.env.APP_URL!);const principal=await authorized(request);const buffer=await readBodyLimited(request,9*1024*1024);
  const form=await new Response(new Uint8Array(buffer),{headers:{'Content-Type':request.headers.get('content-type')??''}}).formData();const file=form.get('file');const rights=String(form.get('rightsReference')??'').trim();
  if(!(file instanceof File)||rights.length<5||rights.length>1000)throw new HttpError(400,'Görsel ve kullanım hakkı kaynağını girin.');
  const input=Buffer.from(await file.arrayBuffer());validateRaster(input,file.type);
  const image=await sharp(input,{limitInputPixels:20_000_000,failOn:'error'}).rotate().resize({width:1800,height:1800,fit:'inside',withoutEnlargement:true}).webp({quality:85}).toBuffer();
  const key=`products/${randomUUID()}.webp`;await storage().put(key,image,'image/webp');
  const id=await transaction(async client=>{const row=(await client.query('INSERT INTO media_assets(object_key,mime_type,size_bytes,sha256,rights_reference,actor_id) VALUES($1,\'image/webp\',$2,$3,$4,$5) RETURNING id',[key,image.length,createHash('sha256').update(image).digest('hex'),rights,principal.id])).rows[0];await client.query('INSERT INTO audit_log(actor_id,action,resource,resource_id) VALUES($1,\'upload\',\'media\',$2)',[principal.id,row.id]);return row.id;});
  return NextResponse.json({id,url:`/uploads/${key.split('/').pop()}`,sizeBytes:image.length},{status:201,headers});
 }catch(error){const e=error as {status?:number;message?:string};return NextResponse.json({error:e.status&&e.status<500?e.message:'Görsel işlenemedi. Dosya biçimini ve depolama bağlantısını kontrol edin.'},{status:e.status??400,headers});}
}
