/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/server/address-profiles.ts
 * Açıklama   : Ülke adres alanlarını sürümlü yönetici onayı ve sunucu doğrulamasıyla uygular.
 */
import {z} from 'zod';
import {query,transaction,type Connection} from './db';
import {HttpError} from './security';
import type {Principal,Locale} from '../shared/contracts';
import {addressValueSchema,parseAddressFields,validateAddressValues,type AddressProfile} from '../shared/address-fields';
const local=()=>['development','test'].includes(process.env.APP_ENV??'');
function authorize(principal:Principal){if(principal.role!=='admin'||!principal.mfa)throw new HttpError(403,'Adres kurallarını yalnız doğrulanmış yönetici değiştirebilir.');}
function parse<T>(schema:z.ZodType<T>,input:unknown):T{const result=schema.safeParse(input);if(!result.success)throw new HttpError(400,'Adres kuralı alanlarını kontrol edin.','ADDRESS_PROFILE_INVALID');return result.data;}
const country=z.string().regex(/^[A-Z]{2}$/),id=z.string().min(1).max(100),note=z.string().trim().min(10).max(2000);
export async function manageAddressProfile(input:unknown,principal:Principal){
 authorize(principal);const data=parse(z.discriminatedUnion('action',[
  z.object({action:z.literal('create'),country,fields:z.unknown(),reference:note}).strict(),
  z.object({action:z.enum(['approve','archive']),id,reason:note}).strict()
 ]),input);
 if(data.action==='create'){
  let fields;try{fields=parseAddressFields(data.fields);}catch{throw new HttpError(400,'Adres alanları, çeviriler veya uzunluk sınırları geçersiz.','ADDRESS_PROFILE_INVALID');}
  return transaction(async connection=>{
   await query("SELECT pg_advisory_xact_lock(hashtext('country-address:'||$1))",[data.country],connection);
   const [exists]=await query('SELECT code FROM country_rules WHERE code=$1',[data.country],connection);if(!exists)throw new HttpError(400,'Önce ülke kaydını oluşturun.');
   const [row]=await query("INSERT INTO country_address_profiles(country,version,fields,reference,created_by,fixture) SELECT $1,coalesce(max(version),0)+1,$2,$3,$4,$5 FROM country_address_profiles WHERE country=$1 RETURNING id,version",[data.country,JSON.stringify(fields),data.reference,principal.id,local()],connection);
   await record(principal,row.id,'create',data.reference,connection);return {id:String(row.id),version:Number(row.version)};
  });
 }
 return transaction(async connection=>{
  const [target]=await query('SELECT country FROM country_address_profiles WHERE id=$1',[data.id],connection);if(!target)throw new HttpError(404,'Adres profili bulunamadı.');
  await query("SELECT pg_advisory_xact_lock(hashtext('country-address:'||$1))",[target.country],connection);
  const [row]=await query('SELECT * FROM country_address_profiles WHERE id=$1 FOR UPDATE',[data.id],connection);
  if(data.action==='approve'){
   if(row.status!=='draft')throw new HttpError(409,'Yalnız yeni taslak sürüm onaylanabilir.');
   if(row.fixture&&!local())throw new HttpError(409,'Örnek adres profili bu ortamda onaylanamaz.');
   parseAddressFields(row.fields);
   await query("UPDATE country_address_profiles SET status='archived' WHERE country=$1 AND status='approved'",[row.country],connection);
   await query("UPDATE country_address_profiles SET status='approved',approved_by=$2,approved_at=now() WHERE id=$1",[row.id,principal.id],connection);
  }else{
   if(row.status==='archived')return {id:String(row.id),version:Number(row.version)};
   await query("UPDATE country_address_profiles SET status='archived' WHERE id=$1",[row.id],connection);
  }
  await record(principal,row.id,data.action,data.reason,connection);return {id:String(row.id),version:Number(row.version)};
 });
}
async function record(principal:Principal,profileId:string,action:string,reference:string,connection:Connection){
 await query('INSERT INTO country_address_events(profile_id,actor_id,action,note) VALUES($1,$2,$3,$4)',[profileId,principal.id,action,reference],connection);
 await query("INSERT INTO audit_log(actor_id,action,resource,resource_id) VALUES($1,$2,'address_profiles',$3)",[principal.id,`address_profile_${action}`,profileId],connection);
}
export async function loadAddressProfile(code:string,connection?:Connection){
 const [row]=await query("SELECT id,country,version,fields FROM country_address_profiles WHERE country=$1 AND status='approved' AND approved_by IS NOT NULL AND($2 OR fixture=false) FOR SHARE",[code,local()],connection);
 if(!row)throw new HttpError(409,'Bu ülke için teslimat adresi kuralları henüz hazır değil.','ADDRESS_PROFILE_REQUIRED');
 let fields;try{fields=parseAddressFields(row.fields);}catch{throw new HttpError(503,'Teslimat adresi kuralları şu anda kullanılamıyor.');}
 return {id:String(row.id),country:String(row.country),version:Number(row.version),fields};
}
export async function validateCountryAddress(input:unknown,connection?:Connection,locale:Locale='tr'){
 const result=addressValueSchema.safeParse(input);if(!result.success)throw new HttpError(400,locale==='en'?'Check the delivery address fields.':'Teslimat adresi alanlarını kontrol edin.','ADDRESS_INVALID');
 const profile=await loadAddressProfile(result.data.country,connection),validated=validateAddressValues(result.data,profile.fields);
 if(!validated.success){const label=profile.fields.find(field=>field.id===validated.field)?.label[locale]??(locale==='en'?'Address':'Adres');throw new HttpError(400,locale==='en'?`Check the ${label.toLocaleLowerCase('en-GB')} field for this delivery country.`:`Bu teslimat ülkesi için ${label} alanını kontrol edin.`,'ADDRESS_INVALID');}
 return {profileId:profile.id,profileVersion:profile.version,values:{...validated.values,fullName:result.data.fullName,line1:result.data.line1,city:result.data.city,country:result.data.country}};
}
export async function publicAddressProfile(code:string):Promise<AddressProfile>{
 parse(country,code);const {getMarkets}=await import('./markets');const markets=await getMarkets();if(!markets.markets.some(market=>market.countryCode===code))throw new HttpError(409,'Bu ülkeye teslimat şu anda açık değil.','COUNTRY_NOT_APPROVED');
 const profile=await loadAddressProfile(code);return {country:profile.country,version:profile.version,fields:profile.fields};
}
export async function listAddressProfiles(principal:Principal,filter:{country?:string;page?:number;q?:string}={}){
 authorize(principal);const page=filter.page??1;if(!Number.isInteger(page)||page<1||page>100000)throw new HttpError(400,'Sayfa numarası geçersiz.');
 if(filter.country)parse(country,filter.country);
 const search=`%${(filter.q??'').slice(0,100).replace(/[\\%_]/g,'\\$&')}%`;
 const rows=await query("SELECT p.id,p.country,c.name,p.version,p.fields,p.status,p.fixture,p.reference,p.approved_by,p.approved_at,p.created_at FROM country_address_profiles p JOIN country_rules c ON c.code=p.country WHERE($1::text IS NULL OR p.country=$1) ORDER BY p.country,p.version DESC LIMIT 25 OFFSET $2",[filter.country??null,(page-1)*25]);
 const [count]=await query('SELECT count(*) total FROM country_address_profiles WHERE($1::text IS NULL OR country=$1)',[filter.country??null]);
 const countries=await query('SELECT code,name FROM country_rules WHERE sg_search_normalize(name) LIKE sg_search_normalize($1) OR code ILIKE $1 ORDER BY code LIMIT 25',[search]);
 return {rows,total:Number(count.total),page,countries};
}
