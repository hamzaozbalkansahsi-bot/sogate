/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/server/customer.ts
 * Açıklama   : Müşteri adresleri, sepet sahipliği ve izinli hesap işlemleri.
 */
import { randomBytes, createHash } from 'node:crypto';
import { pool, transaction } from './db';
import { HttpError } from './security';
import { z } from 'zod';
import type { Principal } from '../shared/contracts';
import {addressValueSchema} from '../shared/address-fields';
import {validateCountryAddress} from './address-profiles';

export const hashToken=(value:string)=>createHash('sha256').update(value).digest('hex');
export const newToken=()=>randomBytes(32).toString('base64url');
export async function resolveCartOwner(token:string,principal:Principal|null){
 const result=await pool.query('SELECT user_id FROM carts WHERE token_hash=$1',[hashToken(token)]);
 const owner=result.rows[0]?.user_id;
 if(owner&&owner!==principal?.id)return newToken();
 return principal?mergeCustomerCart(token,principal):token;
}
export async function enforceQuota(token:string,resource:string,max=30){
 const key=hashToken(`${resource}:${token}`);
 const result=await pool.query("INSERT INTO request_limits(key,count,window_start,expires_at) VALUES($1,1,now(),now()+interval '2 minutes') ON CONFLICT(key) DO UPDATE SET count=CASE WHEN request_limits.window_start<now()-interval '1 minute' THEN 1 ELSE request_limits.count+1 END,window_start=CASE WHEN request_limits.window_start<now()-interval '1 minute' THEN now() ELSE request_limits.window_start END,expires_at=now()+interval '2 minutes' RETURNING count",[key]);
 if(result.rows[0].count>max)throw new HttpError(429,'Çok fazla istek alındı. Bir dakika sonra yeniden deneyin.');
}
export const addressSchema=addressValueSchema.extend({label:z.string().trim().min(1).max(60)}).strict();
export async function addresses(principal:Principal,input?:unknown){
  if(input!==undefined){
    const schema=z.union([
      addressSchema.extend({action:z.literal('create').optional()}),
      addressSchema.extend({action:z.literal('update'),id:z.string().min(1).max(100)}),
      z.object({action:z.literal('remove'),id:z.string().min(1).max(100)}).strict()
    ]),parsed=schema.safeParse(input);
    if(!parsed.success)throw new HttpError(400,'Adres alanlarını kontrol edin.','ADDRESS_INVALID');
    const data=parsed.data,action=data.action??'create';
    await transaction(async connection=>{
      await connection.query("SELECT pg_advisory_xact_lock(hashtextextended($1,0))",['address-book:'+principal.id]);
      if('id' in data){
        const own=await connection.query('SELECT id FROM customer_addresses WHERE id=$1 AND user_id=$2 FOR UPDATE',[data.id,principal.id]);
        if(!own.rows.length)throw new HttpError(404,'Adres bulunamadı.');
      }
      let recordId:string;
      if(data.action==='remove'){
        await connection.query('DELETE FROM customer_addresses WHERE id=$1 AND user_id=$2',[data.id,principal.id]);recordId=data.id;
      }else{
        const {label,fullName,phone,line1,city,region,district,postalCode,country}=data;
        const result=await validateCountryAddress({fullName,phone,line1,city,region,district,postalCode,country},connection);
        const snapshot={...result.values,profileVersion:result.profileVersion};
        if(data.action==='update'){
          await connection.query('UPDATE customer_addresses SET label=$1,address=$2,address_profile_id=$3 WHERE id=$4 AND user_id=$5',[label,snapshot,result.profileId,data.id,principal.id]);recordId=data.id;
        }else{
          const count=await connection.query('SELECT count(*)::int n FROM customer_addresses WHERE user_id=$1',[principal.id]);
          if(count.rows[0].n>=50)throw new HttpError(409,'En fazla 50 adres saklayabilirsiniz.');
          const created=await connection.query('INSERT INTO customer_addresses(user_id,label,address,address_profile_id) VALUES($1,$2,$3,$4) RETURNING id',[principal.id,label,snapshot,result.profileId]);recordId=created.rows[0].id;
        }
      }
      await connection.query("INSERT INTO audit_log(actor_id,action,resource,resource_id) VALUES($1,$2,'addresses',$3)",[principal.id,'address_'+action,recordId]);
    });
  }
  return {addresses:(await pool.query('SELECT id,label,address FROM customer_addresses WHERE user_id=$1 ORDER BY created_at DESC LIMIT 50',[principal.id])).rows.map(r=>({id:r.id,...r.address,label:r.label}))};
}
export async function mergeCustomerCart(token:string,principal:Principal){
  return transaction(async client=>{
    const own=(await client.query('SELECT * FROM carts WHERE token_hash=$1 FOR UPDATE',[hashToken(token)])).rows[0];
    if(!own)return token;
    if(own.user_id&&own.user_id!==principal.id) return newToken();
    await client.query('SELECT pg_advisory_xact_lock(hashtextextended($1,0))',[principal.id]);
    const other=(await client.query('SELECT id FROM carts WHERE user_id=$1 AND id<>$2 ORDER BY id FOR UPDATE',[principal.id,own.id])).rows;
    for(const old of other){
      await client.query('INSERT INTO cart_items(cart_id,variant_id,quantity) SELECT $1,variant_id,quantity FROM cart_items WHERE cart_id=$2 ON CONFLICT(cart_id,variant_id) DO UPDATE SET quantity=LEAST(99,cart_items.quantity+EXCLUDED.quantity)',[own.id,old.id]);
      await client.query('DELETE FROM cart_items WHERE cart_id=$1',[old.id]);
      await client.query('UPDATE carts SET user_id=NULL WHERE id=$1',[old.id]);
    }
    await client.query('UPDATE carts SET user_id=$1 WHERE id=$2',[principal.id,own.id]);return token;
  });
}
export async function contact(input:unknown,principal:Principal|null){
  const value=z.object({email:z.email().max(254),kind:z.enum(['support','defective','privacy','withdrawal']),message:z.string().trim().min(10).max(4000),locale:z.enum(['tr','en']).default('tr')}).strict().parse(input);
  if(value.kind==='privacy'){const {createPrivacyRequest}=await import('./privacy');return {...await createPrivacyRequest({email:value.email,type:'other',summary:value.message,locale:value.locale},principal),privacy:true};}
  const result=await pool.query('INSERT INTO contact_requests(user_id,email,kind,message,due_at) VALUES($1,$2,$3,$4,NULL) RETURNING id',[principal?.id??null,value.email,value.kind,value.message]);
  return {id:result.rows[0].id};
}
export async function adminUsers(principal:Principal,input:unknown|undefined,headers:Headers){
  if(principal.role!=='admin'||!principal.mfa)throw new HttpError(403,'Bu işlem için yönetici doğrulaması gerekir.');
  if(input){const value=z.object({userId:z.string().min(1),role:z.enum(['admin','catalog','warehouse','support','finance','marketing','customer']),password:z.string().min(12)}).strict().parse(input);
    const {getAuth}=await import('./auth');await getAuth().api.verifyPassword({body:{password:value.password},headers}).catch(()=>{throw new HttpError(403,'Parola tekrar doğrulaması başarısız.');});
    await transaction(async client=>{if(value.userId===principal.id&&value.role!=='admin')throw new HttpError(400,'Kendi yönetici yetkinizi bu işlemle kaldıramazsınız.');await client.query('UPDATE "user" SET role=$1 WHERE id=$2',[value.role,value.userId]);await client.query('INSERT INTO audit_log(actor_id,action,resource,resource_id) VALUES($1,\'role.change\',\'users\',$2)',[principal.id,value.userId]);await client.query('DELETE FROM session WHERE "userId"=$1',[value.userId]);});
  }
  return {rows:(await pool.query('SELECT id,name,email,role,"twoFactorEnabled" FROM "user" ORDER BY "createdAt" DESC LIMIT 100')).rows};
}
