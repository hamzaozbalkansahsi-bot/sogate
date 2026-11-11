/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : tests/unit/api-response.test.ts
 * Açıklama   : Okunamayan başarı yanıtının ve geçersiz sonuç sözleşmesinin kesin başarı sayılmasını engeller.
 */
import {afterEach,describe,it,expect,vi} from 'vitest';
import {api,post,ApiError} from '../../src/components/api';
import {purchaseReceiptResultSchema} from '../../src/shared/purchase-receipts';
afterEach(()=>vi.unstubAllGlobals());
function reply(body:string,status=200){const fetch=vi.fn().mockImplementation(async()=>new Response(body,{status,headers:{'Content-Type':'application/json'}}));vi.stubGlobal('fetch',fetch);return fetch;}
describe('İstemci API yanıtı ve belirsiz işlem sonucu',()=>{
 it.each(['<html>upstream</html>','{"id":"receipt"'])('2xx okunamayan gövdeyi başarı yerine belirsiz sonuç yapar: %s',async body=>{reply(body);await expect(api('/api/admin/purchases')).rejects.toMatchObject({name:'ApiResponseError',status:200,code:'RESPONSE_UNCONFIRMED'});});
 it.each([{id:'receipt',status:'partially_received'},[{id:'row'}],null])('doğrulayıcı istenmeyen geçerli JSON sözleşmesini korur: %j',async value=>{reply(JSON.stringify(value));expect(await api('/api/example')).toEqual(value);});
 it('başarılı gövdedeki sözleşme hatasını belirsiz sonuç olarak korur',async()=>{reply('{"status":"received"}');const validate=vi.fn(()=>{throw new Error('private contract detail');});await expect(api('/api/admin/purchases',{validate})).rejects.toMatchObject({name:'ApiResponseError',status:200,code:'RESPONSE_UNCONFIRMED'});expect(validate).toHaveBeenCalledTimes(1);});
 it('doğrulayıcı sonucunu döndürür, özel doğrulayıcıyı fetch seçeneklerine taşımaz',async()=>{const fetch=reply('{"id":"receipt"}');const validate=vi.fn(()=>({verified:true}));expect(await post('/api/admin/purchases',{action:'receive'},{validate})).toEqual({verified:true});expect(validate).toHaveBeenCalledWith({id:'receipt'});expect(fetch.mock.calls[0][1]).not.toHaveProperty('validate');expect(fetch.mock.calls[0][1]).toMatchObject({method:'POST',cache:'no-store'});});
 it('JSON iş hatasının gerçek HTTP durumunu ve kodunu korur',async()=>{reply('{"error":"Kalan miktar aşıldı.","code":"OVER_RECEIPT"}',409);await expect(api('/api/admin/purchases')).rejects.toMatchObject({name:'ApiError',status:409,code:'OVER_RECEIPT',message:'Kalan miktar aşıldı.'});});
 it.each(['<html>Forbidden</html>','null','[]','"denied"'])('JSON olmayan veya nesne olmayan hata zarfı sonucu kesinleştirmeden HTTP durumunu korur: %s',async body=>{reply(body,403);await expect(api('/api/admin/purchases')).rejects.toBeInstanceOf(ApiError);await expect(api('/api/admin/purchases')).rejects.toMatchObject({name:'ApiResponseError',status:403,code:'RESPONSE_UNCONFIRMED',message:'Sunucu yanıtı doğrulanamadı. İşlemin sonucunu kontrol edip yeniden deneyin.'});});
 it('bağlantı hatasında ham ağ ayrıntısını sızdırmaz; sonuç hâlâ belirsizdir',async()=>{vi.stubGlobal('fetch',vi.fn().mockRejectedValue(new TypeError('secret upstream URL')));await expect(api('/api/admin/purchases')).rejects.toMatchObject({name:'ApiResponseError',status:0,code:'RESPONSE_UNCONFIRMED',message:'Sunucu yanıtı doğrulanamadı. İşlemin sonucunu kontrol edip yeniden deneyin.'});});
 it('kasıtlı iptali çağıranın yaşam döngüsü kontrolüne aynen bırakır',async()=>{const abort=new DOMException('This operation was aborted','AbortError');vi.stubGlobal('fetch',vi.fn().mockRejectedValue(abort));await expect(api('/api/example')).rejects.toBe(abort);});
 it('İngilizce sayfada bozuk başarı yanıtı doğal İngilizce hata verir',async()=>{vi.stubGlobal('window',{location:{pathname:'/en/odeme'}});reply('not json');await expect(api('/api/checkout')).rejects.toMatchObject({message:'The server response could not be verified. Check the operation result and try again.'});});
 it.each([{id:'receipt',status:'received'},{id:'receipt',status:'partially_received'},{id:'receipt',duplicate:true}])('yeni kabul veya eski idempotent tekrar gerçek sözleşmesi kabul edilir: %j',async value=>{reply(JSON.stringify(value));expect(await post('/api/admin/purchases',{action:'receive'},{validate:input=>purchaseReceiptResultSchema.parse(input)})).toEqual(value);});
 it.each([{status:'received'},{id:'receipt'},{id:'receipt',duplicate:false},{id:'receipt',status:'ordered'},{id:'',duplicate:true}])('eksik veya yanlış kabul sonucu başarı göstermez; aynı anahtarla tekrar belirsiz kalır: %j',async value=>{reply(JSON.stringify(value));await expect(post('/api/admin/purchases',{action:'receive'},{validate:input=>purchaseReceiptResultSchema.parse(input)})).rejects.toMatchObject({name:'ApiResponseError',status:200,code:'RESPONSE_UNCONFIRMED'});});
});
