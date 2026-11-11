/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : tests/unit/compliance.test.ts
 * Açıklama   : Belge girdisini ve yalnız açık teknik alanlardan oluşan müşteri projeksiyonunu sınar.
 */
import {describe,it,expect} from 'vitest';
import {validateComplianceInput,publicProductTechnical,publicVariantTechnical} from '../../src/server/compliance';
const command={idempotencyKey:'compliance-unit-command',reason:'Gerçek kaynağa göre yerel kontrol'};
describe('SKU belge ve teknik alan sınırı',()=>{
 it('gerçek SKU, ülke, belge türü, referans ve tarihleri korur',()=>{
  expect(validateComplianceInput({action:'document.create',variantId:'sku-id',country:'TR',kind:'üretici-belgesi',reference:'Üretici Arşivi / 2026-42',modelReference:'Özgün Model',validFrom:'2026-01-01',validUntil:'2027-01-01',...command})).toMatchObject({modelReference:'Özgün Model',reference:'Üretici Arşivi / 2026-42'});
 });
 it('tarihi ters belgeyi, eksik referansı, kontrol karakterini ve bilinmeyen alanı reddeder',()=>{
  const base={action:'document.create',variantId:'sku-id',country:'TR',kind:'belge',reference:'Kaynak 42',validFrom:'2026-01-01',...command};
  for(const extra of [{validUntil:'2025-01-01'},{reference:''},{reference:'Kimlik\u0000'},{country:'TUR'},{reviewed:true},{rawPdf:'base64'}])expect(()=>validateComplianceInput({...base,...extra})).toThrow();
 });
 it('teknik alanda gerçekte verilmeyen sertifika, maliyet ve onayı kabul etmez',()=>{
  for(const extra of [{costMinor:10},{approved:true},{waterproof:true},{certified:true}])expect(()=>validateComplianceInput({action:'technical',variantId:'sku-id',...command,...extra})).toThrow();
 });
 it('public ürün alanlarına maliyet, tedarikçi ve özel belge notlarını kopyalamaz',()=>{
  const dto=publicProductTechnical({origin:'Türkiye',attributes:{warranty:'Üretici garanti koşulları',privateNote:'GİZLİ'},translations:{en:{warranty:'Manufacturer warranty terms'}},cost_minor:999,supplier_id:'private',reference:'private-doc'} as never);
  expect(dto).toEqual({origin:'Türkiye',warranty:'Üretici garanti koşulları',warrantyEn:'Manufacturer warranty terms'});expect(JSON.stringify(dto)).not.toContain('GİZLİ');
 });
 it('gerçek teknik bilgileri ve barkodun baştaki sıfırlarını korur',()=>{
  expect(publicVariantTechnical({barcode:'0012345678905',weightGrams:120,packageDimensions:{lengthCm:10,widthCm:5,heightCm:3},batteryType:'Şarjlı USB-C',batteryCapacityMah:500,measurements:'Ölçü: 12 cm',ingredients:'Üretici içerik listesi',hygieneSealed:true,liquid:true})).toEqual({barcode:'0012345678905',weightGrams:120,packageDimensions:{lengthCm:10,widthCm:5,heightCm:3},batteryType:'Şarjlı USB-C',batteryCapacityMah:500,measurements:'Ölçü: 12 cm',ingredients:'Üretici içerik listesi',hygieneSealed:true,liquid:true});
 });
 it('bilinmeyen ağırlığı, kapasiteyi ve boş alanları sıfır iddiasına dönüştürmez',()=>{
  expect(publicVariantTechnical({weightGrams:0,batteryCapacityMah:0,batteryType:null,barcode:null,packageDimensions:{lengthCm:0,widthCm:1,heightCm:1},costMinor:700,supplier:'private'} as never)).toEqual({});
 });
 it('onaysız üretici/sorumlu kişi iletişimini yayımlamaz',()=>{
  expect(publicProductTechnical({contact_profile:{reviewed:false,manufacturerAddress:'Gizli taslak adres',responsibleName:'Taslak kişi'}} as never)).toEqual({});
  expect(publicProductTechnical({contact_profile:{reviewed:true,manufacturerAddress:'Üretici iş adresi',manufacturerEmail:'bilgi@example.invalid',responsibleName:'Sorumlu İşletme',responsibleAddress:'İş adresi',responsibleCountry:'DE',sourceReference:'GİZLİ'}} as never)).toEqual({manufacturerContact:{address:'Üretici iş adresi',email:'bilgi@example.invalid'},responsiblePerson:{name:'Sorumlu İşletme',address:'İş adresi',country:'DE'}});
 });
});
