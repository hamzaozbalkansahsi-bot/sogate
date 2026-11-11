/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/app/api/admin/imports/route.ts
 * Açıklama   : HTTP işlemini doğrulayıp yetkili veri akışına bağlar.
 */
import {NextResponse} from 'next/server';
import {requirePrincipal} from '@/server/auth';
import {enforceSameOrigin,HttpError,readBodyLimited,readJsonLimited} from '@/server/security';
import {previewImport,commitImport,getImportTemplate} from '@/server/imports';
import {z} from 'zod';
export const runtime='nodejs';export const dynamic='force-dynamic';
const headers={'Cache-Control':'private, no-store','X-Robots-Tag':'noindex'};
async function authorized(request:Request){const principal=await requirePrincipal(request.headers,true);if(!['admin','catalog'].includes(principal.role))throw new HttpError(403,'İçe aktarma için katalog veya yönetici yetkisi gerekir.');return principal;}
export async function GET(request:Request){try{await authorized(request);const params=new URL(request.url).searchParams,format=z.enum(['csv','xlsx']).parse(params.get('format')??'csv'),mode=z.enum(['legacy','extended']).parse(params.get('mode')??'legacy');const template=await getImportTemplate(format,mode);return new NextResponse(new Uint8Array(template),{headers:{...headers,'Content-Type':format==='xlsx'?'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':'text/csv; charset=utf-8','Content-Disposition':`attachment; filename="sexsogate-product-import-${mode}.${format}"`}});}catch(error){return NextResponse.json({error:error instanceof HttpError?error.message:'Şablon biçimini ve yetkili oturumunuzu kontrol edin.'},{status:error instanceof HttpError?error.status:400,headers});}}
export async function POST(request:Request){
 try{
  enforceSameOrigin(request,process.env.APP_URL!);const principal=await authorized(request);
  if(request.headers.get('content-type')?.startsWith('multipart/form-data')){
   const buffer=await readBodyLimited(request,3*1024*1024);const form=await new Response(new Uint8Array(buffer),{headers:{'Content-Type':request.headers.get('content-type')!}}).formData();const file=form.get('file');
   if(!(file instanceof File))throw new HttpError(400,'CSV veya XLSX dosyası seçin.');
   const mapping=form.get('mapping');const parsed=mapping?z.record(z.string(),z.string()).parse(JSON.parse(String(mapping))):undefined;
   return NextResponse.json(await previewImport(Buffer.from(await file.arrayBuffer()),file.type,file.name,parsed,principal),{headers});
  }
  const input=z.object({previewId:z.string().min(1)}).strict().parse(await readJsonLimited(request));return NextResponse.json(await commitImport(input.previewId,principal),{headers});
 }catch(error){const e=error as {status?:number;message?:string};return NextResponse.json({error:e.status&&e.status<500?e.message:'Dosya işlenemedi. Biçimi ve önizleme hatalarını kontrol edin.'},{status:e.status??400,headers});}
}
