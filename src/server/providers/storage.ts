/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/server/providers/storage.ts
 * Açıklama   : Yerel ve S3 uyumlu özel dosya depolama adaptörleri.
 */
import {mkdir,writeFile,realpath,open,type FileHandle} from 'node:fs/promises';
import path from 'node:path';
import {Readable} from 'node:stream';
import {S3Client,PutObjectCommand,GetObjectCommand} from '@aws-sdk/client-s3';
import type {StorageProvider,StorageReadOptions} from './contracts';
import {safeObjectKey,HttpError} from '../security';
export const DEFAULT_STORAGE_READ_LIMIT=8*1024*1024;
function policy(options:StorageReadOptions={}){
 const maxBytes=options.maxBytes??DEFAULT_STORAGE_READ_LIMIT,timeoutMs=options.timeoutMs??5000;
 if(!Number.isSafeInteger(maxBytes)||maxBytes<1||maxBytes>16*1024*1024||!Number.isInteger(timeoutMs)||timeoutMs<1||timeoutMs>30000)throw new HttpError(400,'Dosya okuma sınırı geçersiz.');
 return {maxBytes,timeoutMs};
}
async function budget<T>(timeoutMs:number,work:(controller:AbortController)=>Promise<T>,stop:()=>void){
 const controller=new AbortController();let timer:ReturnType<typeof setTimeout>|undefined;
 const expiry=new Promise<never>((_,reject)=>{timer=setTimeout(()=>{reject(new HttpError(504,'Dosya okuma süresi aşıldı.','STORAGE_TIMEOUT'));controller.abort();stop();},timeoutMs);});
 try{return await Promise.race([work(controller),expiry]);}finally{if(timer)clearTimeout(timer);}
}
function tooLarge(){return new HttpError(413,'Dosya izin verilen okuma sınırını aşıyor.','STORAGE_LIMIT');}
// Sabit uygulama varlıkları da aynı kök ve byte sınırından okunabilir.
export async function readConfinedFile(rootPath:string,key:string,options?:StorageReadOptions){
   const {maxBytes,timeoutMs}=policy(options),checked=safeObjectKey(key);let handle:FileHandle|undefined;
   return budget(timeoutMs,async controller=>{
    try{
     const root=await realpath(path.resolve(rootPath)),file=await realpath(path.resolve(rootPath,checked)),relative=path.relative(root,file);
     if(relative==='..'||relative.startsWith('..'+path.sep)||path.isAbsolute(relative))throw new HttpError(400,'Dosya depolama kökünün dışında.');
     if(controller.signal.aborted)throw new HttpError(504,'Dosya okuma süresi aşıldı.');
     handle=await open(file,'r');const info=await handle.stat();if(!info.isFile())throw new HttpError(400,'Yalnız düzenli dosya okunabilir.');if(info.size>maxBytes)throw tooLarge();
     const data=Buffer.allocUnsafe(info.size+1);let length=0;
     while(length<data.length){if(controller.signal.aborted)throw new HttpError(504,'Dosya okuma süresi aşıldı.');const {bytesRead}=await handle.read(data,length,Math.min(65536,data.length-length),length);if(!bytesRead)break;length+=bytesRead;if(length>maxBytes)throw tooLarge();}
     if(length!==info.size)throw new HttpError(409,'Dosya okunurken değişti. Tekrar deneyin.','STORAGE_CHANGED');
     return data.subarray(0,length);
    }catch(error){if((error as {code?:string}).code==='ENOENT')throw new HttpError(404,'Dosya bulunamadı.');throw error;}
    finally{await handle?.close().catch(()=>{});}
   },()=>{void handle?.close().catch(()=>{});});
}
export class LocalStorage implements StorageProvider {
  constructor(private root=process.env.STORAGE_LOCAL_PATH??'.local/media'){if(process.env.APP_ENV==='production')throw new HttpError(503,'Canlı ortam için özel nesne depolama yapılandırın.');}
  async put(key:string,data:Buffer){const file=path.resolve(this.root,safeObjectKey(key));await mkdir(path.dirname(file),{recursive:true});await writeFile(file,data,{mode:0o600});}
  async get(key:string,options?:StorageReadOptions){return readConfinedFile(this.root,key,options);}

}
export class S3Storage implements StorageProvider {
  private client:S3Client;private bucket:string;
  constructor(){const {S3_ENDPOINT,S3_REGION,S3_BUCKET,S3_ACCESS_KEY_ID,S3_SECRET_ACCESS_KEY}=process.env;if(!S3_BUCKET||!S3_REGION||!S3_ACCESS_KEY_ID||!S3_SECRET_ACCESS_KEY)throw new HttpError(503,'Dosya depolama ayarları eksik.');this.bucket=S3_BUCKET;this.client=new S3Client({endpoint:S3_ENDPOINT,region:S3_REGION,forcePathStyle:!!S3_ENDPOINT,credentials:{accessKeyId:S3_ACCESS_KEY_ID,secretAccessKey:S3_SECRET_ACCESS_KEY}});}
  async put(key:string,data:Buffer,contentType:string){await this.client.send(new PutObjectCommand({Bucket:this.bucket,Key:safeObjectKey(key),Body:data,ContentType:contentType,ServerSideEncryption:'AES256'}));}
  async get(key:string,options?:StorageReadOptions){
   const {maxBytes,timeoutMs}=policy(options),checked=safeObjectKey(key);let stream:Readable|undefined;
   return budget(timeoutMs,async controller=>{
    const response=await this.client.send(new GetObjectCommand({Bucket:this.bucket,Key:checked,Range:`bytes=0-${maxBytes}`}),{abortSignal:controller.signal});
    if(!response.Body)throw new HttpError(404,'Dosya bulunamadı.');
    if(!(response.Body instanceof Readable))throw new HttpError(503,'Dosya akışı doğrulanamadı.');stream=response.Body;
    try{
     if(controller.signal.aborted)throw new HttpError(504,'Dosya okuma süresi aşıldı.');
     const total=response.ContentRange?Number(/\/(\d+)$/.exec(response.ContentRange)?.[1]):undefined;
     if((response.ContentLength??0)>maxBytes||(total!==undefined&&total>maxBytes))throw tooLarge();
     const chunks:Buffer[]=[];let length=0;
     for await(const chunk of stream){const data=Buffer.isBuffer(chunk)?chunk:Buffer.from(chunk);length+=data.length;if(length>maxBytes)throw tooLarge();chunks.push(data);}
     return Buffer.concat(chunks,length);
    }catch(error){controller.abort();throw error;}finally{stream.destroy();}
   },()=>stream?.destroy());
  }
}
export const storage=()=>process.env.STORAGE_PROVIDER==='s3'?new S3Storage():new LocalStorage();
