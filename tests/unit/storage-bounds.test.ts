/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : tests/unit/storage-bounds.test.ts
 * Açıklama   : Özel nesne okumalarında byte, süre ve dosya kökü sınırlarını doğrular.
 */
import {beforeEach,afterEach,describe,it,expect,vi} from 'vitest';
import {mkdir,mkdtemp,writeFile,rm,symlink} from 'node:fs/promises';
import path from 'node:path';
import {Readable} from 'node:stream';
import {S3Client} from '@aws-sdk/client-s3';
import {LocalStorage,S3Storage} from '../../src/server/providers/storage';

const base=path.resolve('.local/storage-unit');let folder='';
beforeEach(async()=>{vi.stubEnv('APP_ENV','test');await mkdir(base,{recursive:true});folder=await mkdtemp(path.join(base,'case-'));});
afterEach(async()=>{vi.restoreAllMocks();vi.unstubAllEnvs();if(folder){const target=path.resolve(folder);if(!target.startsWith(base+path.sep))throw new Error('Geçersiz test temizleme yolu');await rm(target,{recursive:true,force:true});}});
function s3(){vi.stubEnv('S3_BUCKET','test-private');vi.stubEnv('S3_REGION','test-region');vi.stubEnv('S3_ACCESS_KEY_ID','test-key');vi.stubEnv('S3_SECRET_ACCESS_KEY','test-secret');return new S3Storage();}
describe('Özel depolama okuma sınırı',()=>{
 it('eski Buffer sözleşmesini ve tam byte sınırını korur',async()=>{const adapter=new LocalStorage(folder);await adapter.put('products/one.webp',Buffer.from('1234'));expect(await adapter.get('products/one.webp',{maxBytes:4})).toEqual(Buffer.from('1234'));});
 it('küçük dosya varsayılan limit kadar belleği tutmaz',async()=>{const adapter=new LocalStorage(folder);await adapter.put('products/small.webp',Buffer.from('1234'));const result=await adapter.get('products/small.webp');expect(result.buffer.byteLength).toBeLessThanOrEqual(65536);});
 it('büyük yerel dosyayı döndürmeden reddeder',async()=>{const adapter=new LocalStorage(folder);await adapter.put('products/large.webp',Buffer.alloc(5));await expect(adapter.get('products/large.webp',{maxBytes:4})).rejects.toMatchObject({status:413});});
 it.each(['../secret','/absolute.webp','https://foreign.example/pic','products/../../secret','C:\\secret.webp'])('güvenilmeyen nesne anahtarını reddeder: %s',async key=>{await expect(new LocalStorage(folder).get(key)).rejects.toMatchObject({status:400});});
 it('kökten dışarı çıkan yerel bağlantıyı izlemez',async()=>{const root=path.join(folder,'root'),outside=path.join(folder,'outside');await mkdir(root);await mkdir(outside);await writeFile(path.join(outside,'secret.webp'),'secret');await symlink(outside,path.join(root,'escape'),'junction');await expect(new LocalStorage(root).get('escape/secret.webp')).rejects.toMatchObject({status:400});});
 it('güvensiz limit ve süre değerlerini reddeder',async()=>{const adapter=new LocalStorage(folder);for(const options of [{maxBytes:0},{maxBytes:Infinity},{maxBytes:1.5},{timeoutMs:0},{timeoutMs:Infinity}])await expect(adapter.get('none',options)).rejects.toMatchObject({status:400});});
 it('S3 Range göz ardı edilse veya uzunluk başlığı yanlış olsa da max+1 sınırında keser',async()=>{const body=Readable.from([Buffer.from('123'),Buffer.from('456')]);let signal:AbortSignal|undefined;const send=vi.spyOn(S3Client.prototype,'send');send.mockImplementation(async(_command,options)=>{signal=(options as {abortSignal?:AbortSignal})?.abortSignal;return {Body:body,ContentLength:3,$metadata:{}} as never;});await expect(s3().get('products/large.webp',{maxBytes:4})).rejects.toMatchObject({status:413});expect(signal?.aborted).toBe(true);expect(body.destroyed).toBe(true);expect(send.mock.calls[0][0].input).toMatchObject({Range:'bytes=0-4'});});
 it('S3 boşta kalan stream için zaman aşımı ve abort uygular',async()=>{const body=new Readable({read(){}});let signal:AbortSignal|undefined;vi.spyOn(S3Client.prototype,'send').mockImplementation(async(_command,options)=>{signal=(options as {abortSignal?:AbortSignal})?.abortSignal;return {Body:body,$metadata:{}} as never;});await expect(s3().get('products/slow.webp',{maxBytes:4,timeoutMs:20})).rejects.toMatchObject({status:504});expect(signal?.aborted).toBe(true);expect(body.destroyed).toBe(true);});
 it('S3 bağlantısının kendisi takılırsa da sonlanır',async()=>{let signal:AbortSignal|undefined;vi.spyOn(S3Client.prototype,'send').mockImplementation(async(_command,options)=>{signal=(options as {abortSignal?:AbortSignal})?.abortSignal;return new Promise<never>(()=>{});});await expect(s3().get('products/slow.webp',{timeoutMs:20})).rejects.toMatchObject({status:504});expect(signal?.aborted).toBe(true);});
});
