/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : tests/unit/money-format.test.ts
 * Açıklama   : Farklı alt birimleri yuvarlama veya hassasiyet kaybı olmadan biçimlendirmeyi sınar.
 */
import {describe,it,expect} from 'vitest';
import {formatMinorAmount} from '../../src/shared/money';
describe('Alt birim biçimlendirme',()=>{
 it('Türkçe ve İngilizce iki basamaklı tutarları korur',()=>{
  expect(formatMinorAmount(123456,'TRY',2,'tr-TR')).toBe(new Intl.NumberFormat('tr-TR',{style:'currency',currency:'TRY'}).format(1234.56));
  expect(formatMinorAmount(123456,'EUR',2,'en-GB')).toBe(new Intl.NumberFormat('en-GB',{style:'currency',currency:'EUR'}).format(1234.56));
 });
 it('Ondalık basamağı olmayan para birimi alt birimini bölmez',()=>{
  expect(formatMinorAmount(1234,'JPY',0,'en-GB')).toBe(new Intl.NumberFormat('en-GB',{style:'currency',currency:'JPY'}).format(1234));
 });
 it('Üç basamaklı para biriminde son haneyi ve sıfırları korur',()=>{
  expect(formatMinorAmount(1001,'BHD',3,'en-GB')).toContain('1.001');expect(formatMinorAmount(12340,'BHD',3,'en-GB')).toContain('12.340');
 });
 it('Bir ana birimden küçük negatif tutarın eksi işaretini korur',()=>{
  expect(formatMinorAmount(-1,'TRY',2,'tr-TR')).toContain('-');expect(formatMinorAmount(-1,'BHD',3,'en-GB')).toContain('0.001');
 });
 it('Güvenli Number aralığını aşan BigInt tutarını aynen gösterir',()=>{
  expect(formatMinorAmount(9007199254740993123n,'USD',2,'en-US')).toBe('$90,071,992,547,409,931.23');
 });
 it('Arapça sayı sisteminde kesir hanelerini de yerelleştirir',()=>{
  expect(formatMinorAmount(1001,'BHD',3,'ar-EG')).toBe(new Intl.NumberFormat('ar-EG',{style:'currency',currency:'BHD'}).format(1.001));
 });
 it('Kesirli/sonsuz/güvensiz Number ve geçersiz yapılandırmayı reddeder',()=>{
  for(const amount of [NaN,Infinity,1.01,Number.MAX_SAFE_INTEGER+1])expect(()=>formatMinorAmount(amount,'TRY',2,'tr-TR')).toThrow();
  for(const digits of [-1,1.5,5,NaN])expect(()=>formatMinorAmount(100,'TRY',digits,'tr-TR')).toThrow();
  expect(()=>formatMinorAmount(100,'wrong',2,'tr-TR')).toThrow();
 });
});
