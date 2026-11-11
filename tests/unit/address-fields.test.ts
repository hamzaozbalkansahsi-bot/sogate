/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : tests/unit/address-fields.test.ts
 * Açıklama   : Ülkeye göre adres alanlarını ve özgün çok dilli metnin korunmasını sınar.
 */
import {describe,it,expect} from 'vitest';
import {parseAddressFields,validateAddressValues,type AddressField} from '../../src/shared/address-fields';
const fields:AddressField[]=[
 {id:'fullName',label:{tr:'Ad soyad',en:'Full name'},required:true,minLength:2,maxLength:120,format:'text'},
 {id:'line1',label:{tr:'Adres',en:'Address'},required:true,minLength:5,maxLength:300,format:'text'},
 {id:'city',label:{tr:'Şehir',en:'City'},required:true,minLength:2,maxLength:100,format:'text'},
 {id:'postalCode',label:{tr:'Posta kodu',en:'Postal code'},required:true,minLength:5,maxLength:5,format:'digits'},
];
const value={fullName:'Hamza ÖZBALKAN',line1:'Çeşme Sokak, Şişli 12',city:'İstanbul',postalCode:'34000'};
describe('Adres alanları',()=>{
 it('Türkçe özgün metni değiştirmez',()=>{expect(validateAddressValues(value,fields)).toEqual({success:true,values:value});});
 it('Yeni ülke bölge alanını zorunlu kılabilir',()=>{
  const state:AddressField={id:'region',label:{tr:'Eyalet',en:'State'},required:true,minLength:2,maxLength:100,format:'text'};
  expect(validateAddressValues(value,[...fields,state])).toMatchObject({success:false,field:'region',reason:'required'});
  expect(validateAddressValues({...value,region:'İzmir'},[...fields,state]).success).toBe(true);
 });
 it('Posta kodu gerektirmeyen profilde toplamaya zorlamaz',()=>{expect(validateAddressValues({...value,postalCode:''},fields.filter(field=>field.id!=='postalCode')).success).toBe(true);});
 it('İstenmeyen dolu alanı ve yanlış uzunluk/biçimi reddeder',()=>{
  expect(validateAddressValues({...value,region:'Gereksiz bilgi'},fields)).toMatchObject({success:false,field:'region',reason:'unexpected'});
  expect(validateAddressValues({...value,postalCode:'3400'},fields)).toMatchObject({success:false,field:'postalCode',reason:'length'});
  expect(validateAddressValues({...value,postalCode:'AB123'},fields)).toMatchObject({success:false,field:'postalCode',reason:'format'});
 });
 it('Kiril/Arapça ve yerel sayısal karakterleri korur',()=>{
  const data={...value,fullName:'Ирина Петрова',line1:'شارع النور ١٢',city:'دبي',postalCode:'١٢٣٤٥'};
  expect(validateAddressValues(data,fields)).toEqual({success:true,values:data});
 });
 it('Kontrol karakterlerini reddeder, açık adres satırında yeni satırı korur',()=>{
  expect(validateAddressValues({...value,city:'İstanbul\u0000'},fields).success).toBe(false);
  expect(validateAddressValues({...value,line1:'Şişli Mahallesi\nÇeşme Sokak 12'},fields).success).toBe(true);
 });
 it('Bilinmeyen/çift alan, keyfi regex ve eksik çeviriyi kabul etmez',()=>{
  for(const input of [[...fields,fields[0]],[...fields,{...fields[0],id:'birthDate'}],fields.slice(1),fields.map(field=>field.id==='fullName'?{...field,required:false}:field),fields.map(field=>({...field,pattern:'(a+)+$'})),fields.map(field=>({...field,label:{tr:'Adres'}}))])expect(()=>parseAddressFields(input)).toThrow();
 });
 it('Sınırlı profil tanımı harici bilinmeyen boyutları reddeder',()=>{
  expect(()=>parseAddressFields(fields.map(field=>({...field,maxLength:1000000})))).toThrow();
  expect(parseAddressFields(fields)).toEqual(fields);
 });
});
