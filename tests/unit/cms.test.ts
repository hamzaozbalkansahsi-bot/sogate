/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : tests/unit/cms.test.ts
 * Açıklama   : İçerik bağlantılarının ve yapısal veri sınırlarının güvenliğini sınar.
 */
import {describe,it,expect} from 'vitest';
import {parseCMSPayload,publicContentHref} from '../../src/server/cms';
describe('CMS yapı ve bağlantı sınırları',()=>{
 it('aynı origin genel sayfaları kabul eder ve yerel yola indirger',()=>{
  expect(publicContentHref('/urunler?category=aksesuarlar','https://sexsogate.example')).toBe('/urunler?category=aksesuarlar');
  expect(publicContentHref('https://sexsogate.example/rehber/bakim','https://sexsogate.example')).toBe('/rehber/bakim');
 });
 it.each(['https://foreign.example/','//foreign.example/','javascript:alert(1)','/yonetim','/api/session','/hesap','/odeme','/en/hesap','/urunler?redirect=https://foreign.example','/urun/%2fsecret','/urun/../hesap'])('özel veya yabancı bağlantıyı reddeder: %s',href=>expect(()=>publicContentHref(href,'https://sexsogate.example')).toThrow());
 it('ham HTML, ek anahtar ve tekrar eden koleksiyon üyesini kabul etmez',()=>{
  const hero={kind:'hero',eyebrow:'Yeni koleksiyon',title:'Tutkunu keşfet',italic:'Kendi ritminde',description:'Koleksiyonları keşfedin.',cta:{label:'Keşfet',href:'/urunler'}};
  expect(parseCMSPayload(hero).kind).toBe('hero');expect(()=>parseCMSPayload({...hero,html:'<script/>'})).toThrow();expect(()=>parseCMSPayload({...hero,title:'<script>alert(1)</script>'})).toThrow();
  expect(()=>parseCMSPayload({kind:'collection',title:'Özel seçim',description:'Seçili aksesuarlar',image:'/media/atelier-01.svg',productIds:['a','a'],featured:true})).toThrow();
 });
 it('bozuk URL biçimini sunucu hatası yerine geçersiz girdi olarak bildirir',()=>{
  expect(()=>publicContentHref('https://[','https://sexsogate.example')).toThrowError(expect.objectContaining({status:400,code:'INVALID_CMS_LINK'}));
 });
});
