/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : scripts/address-integration.ts
 * Açıklama   : Ülke adres profili onayı, alan farklılıkları ve geçmiş sürüm korunmasını izole veritabanında sınar.
 */
import assert from 'node:assert/strict';
import {randomBytes} from 'node:crypto';
import pg from 'pg';
import {migrate} from './migrate';
import type {AddressField} from '../src/shared/address-fields';
const base=process.env.TEST_DATABASE_URL;if(!base)throw new Error('TEST_DATABASE_URL gerekir.');
const url=new URL(base);if(!['127.0.0.1','localhost','[::1]'].includes(url.hostname)||!url.pathname.endsWith('_test'))throw new Error('Yalnız izole yerel test DB kullanılabilir.');
const name=`sexsogate_${randomBytes(5).toString('hex')}_address_test`,control=new pg.Client({connectionString:base});await control.connect();await control.query(`CREATE DATABASE "${name}"`);url.pathname='/'+name;
process.env.DATABASE_URL=url.toString();process.env.APP_ENV='test';
const {pool,query}=await import('../src/server/db');let passed=0;
async function check(label:string,work:()=>Promise<void>){await work();console.log(`PASS ${++passed}: ${label}`);}
const fields:AddressField[]=[{id:'fullName',label:{tr:'Ad soyad',en:'Full name'},required:true,minLength:2,maxLength:120,format:'text'},{id:'line1',label:{tr:'Adres',en:'Address'},required:true,minLength:5,maxLength:300,format:'text'},{id:'city',label:{tr:'Şehir',en:'City'},required:true,minLength:2,maxLength:100,format:'text'},{id:'postalCode',label:{tr:'Posta kodu',en:'Postal code'},required:true,minLength:5,maxLength:5,format:'digits'}];
const address={fullName:'Hamza ÖZBALKAN',line1:'Çeşme Sokak, Şişli 12',city:'İstanbul',postalCode:'34000',country:'TR'};
try{
 await migrate(process.env.DATABASE_URL);const service=await import('../src/server/address-profiles');
 const admin={id:'address-admin',role:'admin' as const,mfa:true};
 await query("INSERT INTO country_rules(code,name,fixture) VALUES('TR','Türkiye',true),('US','United States',true)");
 let profileId='';
 await check('Eksik veya taslak adres profili doğrulanmış alan gibi kullanılamaz',async()=>{
  await assert.rejects(()=>service.validateCountryAddress(address));
  const draft=await service.manageAddressProfile({action:'create',country:'TR',fields,reference:'Yalnız izole test için alan tanımı'},admin);profileId=draft.id;
  await assert.rejects(()=>service.validateCountryAddress(address));
 });
 await check('Yönetici/MFA gerekir; profil onayı ülkeye satış açmaz',async()=>{
  for(const principal of [{...admin,role:'catalog' as const},{...admin,mfa:false}])await assert.rejects(()=>service.manageAddressProfile({action:'approve',id:profileId,reason:'İzole onay incelemesi'},principal));
  await service.manageAddressProfile({action:'approve',id:profileId,reason:'İzole onay; gerçek ülke veya hukuk kabulü değildir'},admin);
  assert.equal((await query("SELECT enabled FROM country_rules WHERE code='TR'"))[0].enabled,false);
  const result=await service.validateCountryAddress(address);assert.equal(result.profileId,profileId);assert.equal(result.values.fullName,address.fullName);assert.equal(result.values.city,'İstanbul');
 });
 await check('İstenmeyen veri ve ülkeye uymayan posta biçimi sunucuda reddedilir',async()=>{
  await assert.rejects(()=>service.validateCountryAddress({...address,postalCode:'AB123'}));
  await assert.rejects(()=>service.validateCountryAddress({...address,region:'Gereksiz alan'}));
 });
 await check('Adres oluşturma, sahiplik kontrollü güncelleme ve kaldırma özgün Türkçeyi korur',async()=>{
  const {addresses}=await import('../src/server/customer');const owner={id:'address-owner',role:'customer' as const,mfa:false},other={...owner,id:'address-other'};
  const created=await addresses(owner,{action:'create',label:'Şişli Ev',...address});assert.equal(created.addresses.length,1);
  const id=created.addresses[0].id;assert.equal(created.addresses[0].fullName,'Hamza ÖZBALKAN');
  assert.equal((await addresses(other)).addresses.length,0);
  await assert.rejects(()=>addresses(other,{action:'update',id,label:'Yabancı adres',...address}));
  await assert.rejects(()=>addresses(other,{action:'remove',id}));
  const updated=await addresses(owner,{action:'update',id,label:'Çeşme',...address,city:'İzmir'});assert.equal(updated.addresses[0].city,'İzmir');
  assert.equal((await query('SELECT address_profile_id FROM customer_addresses WHERE id=$1',[id]))[0].address_profile_id,profileId);
  assert.equal((await addresses(owner,{action:'remove',id})).addresses.length,0);
 });
 await check('Ülke yeni bölge alanı isteyebilir; posta kullanmayan profil boş değeri kabul eder',async()=>{
  const usFields=[...fields.filter(field=>field.id!=='postalCode'),{id:'region' as const,label:{tr:'Eyalet',en:'State'},required:true,minLength:2,maxLength:100,format:'text' as const}];
  const draft=await service.manageAddressProfile({action:'create',country:'US',fields:usFields,reference:'Yalnız izole test için farklı ülke alanları'},admin);await service.manageAddressProfile({action:'approve',id:draft.id,reason:'Yalnız izole test onayı; ülke satışı kapalı'},admin);
  await assert.rejects(()=>service.validateCountryAddress({...address,country:'US',postalCode:''}));
  const result=await service.validateCountryAddress({...address,country:'US',postalCode:'',region:'İzmir'});assert.equal(result.values.region,'İzmir');assert(!result.values.postalCode);
 });
 await check('Yeni sürüm eskisini arşivler; eski sürümün içeriği ve referansı değişmez',async()=>{
  const before=(await query('SELECT fields,reference FROM country_address_profiles WHERE id=$1',[profileId]))[0];
  const draft=await service.manageAddressProfile({action:'create',country:'TR',fields:[...fields,{id:'district',label:{tr:'İlçe',en:'District'},required:true,minLength:2,maxLength:100,format:'text'}],reference:'İkinci izole test alanı; kaynak incelemesi'},admin);
  await service.manageAddressProfile({action:'approve',id:draft.id,reason:'Yeni sürüm ayrı incelemeyle onaylandı'},admin);
  const old=(await query('SELECT fields,reference,status FROM country_address_profiles WHERE id=$1',[profileId]))[0];assert.deepEqual(old.fields,before.fields);assert.equal(old.reference,before.reference);assert.equal(old.status,'archived');
  await assert.rejects(()=>service.validateCountryAddress(address));assert.equal((await service.validateCountryAddress({...address,district:'Şişli'})).profileId,draft.id);
  await assert.rejects(()=>query("UPDATE country_address_profiles SET reference='sessiz değişiklik' WHERE id=$1",[profileId]));
  await assert.rejects(()=>service.manageAddressProfile({action:'approve',id:profileId,reason:'Arşiv sürümünü etkinleştirme denemesi'},admin));
 });
 await check('Eşzamanlı iki taslak aynı sürümü alamaz; bütün incelemeler audit edilir',async()=>{
  const result=await Promise.all([service.manageAddressProfile({action:'create',country:'TR',fields,reference:'Eşzamanlı ilk izole sürüm kaynağı'},admin),service.manageAddressProfile({action:'create',country:'TR',fields,reference:'Eşzamanlı ikinci izole sürüm kaynağı'},admin)]);
  assert.notEqual(result[0].version,result[1].version);assert((await query('SELECT id FROM country_address_events')).length>=7);
 });
 await check('Production örnek adres politikasını veya kaynak profil içeriğini kabul etmez',async()=>{
  process.env.APP_ENV='production';try{await assert.rejects(()=>service.validateCountryAddress({...address,district:'Şişli'}));}finally{process.env.APP_ENV='test';}
 });
 console.log(`Address integration: ${passed} checks passed.`);
}finally{await pool.end();await control.query('SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname=$1',[name]);await control.query(`DROP DATABASE "${name}"`);await control.end();}
