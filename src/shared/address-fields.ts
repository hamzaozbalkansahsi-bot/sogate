/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/shared/address-fields.ts
 * Açıklama   : Sınırlı adres alanı sözleşmesini ve ülke profilinden veri doğrulamasını tanımlar.
 */
import {z} from 'zod';
export const addressFieldIds=['fullName','phone','line1','city','region','district','postalCode'] as const;
export type AddressFieldId=typeof addressFieldIds[number];
export type AddressField={id:AddressFieldId;label:{tr:string;en:string};required:boolean;minLength:number;maxLength:number;format:'text'|'digits'|'alphanumeric'};
export type AddressValues=Partial<Record<AddressFieldId,string>>;
export type AddressProfile={country:string;version:number;fields:AddressField[]};
const limits:Record<AddressFieldId,number>={fullName:120,phone:30,line1:300,city:100,region:100,district:100,postalCode:20};
const label=z.string().trim().min(2).max(60).refine(value=>!/[\u0000-\u001f\u007f-\u009f<>]/u.test(value));
const definition=z.array(z.object({id:z.enum(addressFieldIds),label:z.object({tr:label,en:label}).strict(),required:z.boolean(),minLength:z.number().int().min(0).max(300),maxLength:z.number().int().min(1).max(300),format:z.enum(['text','digits','alphanumeric'])}).strict()).min(3).max(7).superRefine((fields,context)=>{
 const seen=new Set<string>();
 for(const field of fields){
  const minimum=field.id==='fullName'?2:field.id==='line1'?5:field.id==='city'?2:0;
  if(seen.has(field.id)||field.maxLength>limits[field.id]||field.minLength>field.maxLength||field.minLength<minimum)context.addIssue({code:'custom',message:'Alan tekrarı veya uzunluk sınırı geçersiz.'});
  seen.add(field.id);
 }
 for(const id of ['fullName','line1','city'])if(!fields.some(field=>field.id===id&&field.required&&field.minLength>0))context.addIssue({code:'custom',message:'Temel teslimat alanları gereklidir.'});
});
export function parseAddressFields(input:unknown):AddressField[]{return definition.parse(input);}
export function validateAddressValues(input:AddressValues,fields:readonly AddressField[]):{success:true;values:AddressValues}|{success:false;field:AddressFieldId;reason:'required'|'length'|'format'|'unexpected'}{
 const values:AddressValues={};
 for(const id of addressFieldIds){
  const field=fields.find(item=>item.id===id),value=input[id]??'';
  if(!field){if(value)return {success:false,field:id,reason:'unexpected'};continue;}
  if(!value){if(field.required)return {success:false,field:id,reason:'required'};continue;}
  if(value.length<field.minLength||value.length>field.maxLength)return {success:false,field:id,reason:'length'};
  const controls=id==='line1'?/[\u0000-\u0009\u000b-\u000c\u000e-\u001f\u007f-\u009f]/u:/[\u0000-\u001f\u007f-\u009f]/u;
  if(controls.test(value)||field.format==='digits'&&!/^\p{Nd}+$/u.test(value)||field.format==='alphanumeric'&&!/^[\p{L}\p{N} -]+$/u.test(value))return {success:false,field:id,reason:'format'};
  values[id]=value;
 }
 return {success:true,values};
}
export const addressValueSchema=z.object({
 fullName:z.string().trim().min(2).max(120),phone:z.string().trim().max(30).optional(),line1:z.string().trim().min(5).max(300),city:z.string().trim().min(2).max(100),region:z.string().trim().max(100).optional(),district:z.string().trim().max(100).optional(),postalCode:z.string().trim().max(20).optional(),country:z.string().regex(/^[A-Z]{2}$/)
}).strict();
