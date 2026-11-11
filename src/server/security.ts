/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/server/security.ts
 * Açıklama   : İstek kökeni, gövde limiti ve dosya güvenlik sınırları.
 */
import path from 'node:path';
export class HttpError extends Error { constructor(public status:number,message:string,public code='REQUEST_REJECTED'){super(message);} }
export function publicFailure(error:unknown):{status:number;message?:string;code:string}{
 if(error instanceof HttpError)return {status:error.status,message:error.message,code:error.code};
 return {status:500,code:'SERVICE_UNAVAILABLE'};
}
export function enforceSameOrigin(request:Request,appUrl:string) {
  const origin=request.headers.get('origin');
  if(!origin || origin!==new URL(appUrl).origin) throw new HttpError(403,'Bu istek kaynağına izin verilmiyor.');
  if(request.headers.get('sec-fetch-site')==='cross-site') throw new HttpError(403,'Bu istek kaynağına izin verilmiyor.');
}
export function guardPaymentConfiguration(config:{appEnv:string;provider:string;liveEnabled:boolean;stripeApproved:boolean}){
  if(config.appEnv==='production'&&config.provider==='test') throw new HttpError(503,'Test ödemesi canlı ortamda kullanılamaz.');
  if(config.appEnv==='production'&&(!config.liveEnabled||!config.stripeApproved)) throw new HttpError(503,'Canlı ödeme kabulü ve hazırlık kontrolleri bekleniyor.');
}
export function validateRaster(data:Buffer,mime:string){
  if(data.length>8*1024*1024) throw new HttpError(400,'Görsel en fazla 8 MB olabilir.');
  if(mime==='image/png'&&data.subarray(0,8).equals(Buffer.from([137,80,78,71,13,10,26,10])))return 'png';
  if(mime==='image/jpeg'&&data[0]===255&&data[1]===216&&data[2]===255)return 'jpg';
  if(mime==='image/webp'&&data.subarray(0,4).toString()==='RIFF'&&data.subarray(8,12).toString()==='WEBP')return 'webp';
  throw new HttpError(400,'Yalnız doğrulanmış PNG, JPEG veya WebP görseli kabul edilir.');
}
export function safeObjectKey(key:string){
  if(!/^[a-zA-Z0-9][a-zA-Z0-9_./-]{0,220}$/.test(key)||key.includes('..')||path.isAbsolute(key))throw new HttpError(400,'Dosya yolu geçersiz.');
  return key;
}
export async function readBodyLimited(request:Request,maxBytes=65536){
 const reader=request.body?.getReader();if(!reader)return Buffer.alloc(0);
 const chunks:Uint8Array[]=[];let length=0;
 try{for(;;){const {value,done}=await reader.read();if(done)break;length+=value.byteLength;if(length>maxBytes){await reader.cancel();throw new HttpError(413,'İstek boyutu sınırı aşıldı.');}chunks.push(value);}}
 finally{reader.releaseLock();}
 return Buffer.concat(chunks);
}
export async function readJsonLimited(request:Request,maxBytes=65536):Promise<unknown>{
 const data=await readBodyLimited(request,maxBytes);
 try{return JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(data));}catch{throw new HttpError(400,'Geçerli UTF-8 JSON gövdesi gerekir.');}
}
