/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : scripts/verify-order-document.ts
 * Açıklama   : Yerel kurulum, doğrulama veya operasyon komutunu yürütür.
 */
import {makeOrderDocument} from '../src/server/order-document';
import type {OrderSummary} from '../src/shared/contracts';
import {mkdir,writeFile} from 'node:fs/promises';
const order:OrderSummary={id:'local',number:'SG-LOCAL',status:'confirmed',paymentStatus:'succeeded',fulfillmentStatus:'unfulfilled',currency:'TRY',subtotalMinor:12345,shippingMinor:1000,taxMinor:2058,discountMinor:0,totalMinor:13345,createdAt:'2026-11-10T12:00:00Z',items:[{variantId:'v',name:'İç Giyim · Ölçü ve Özellikler',sku:'LOCAL',quantity:1,unitMinor:12345}],shipments:[]};
const pdf=await makeOrderDocument(order,[{title:'Güvenli Alışveriş',body:'Hamza ÖZBALKAN · İstanbul · İzmir · Iğdır · Şişli · Çeşme.\nı İ i I ş Ş ğ Ğ ü Ü ö Ö ç Ç.\nBu içerik yalnız yerel belge doğrulama örneğidir.',version:1,bodyHash:'a'.repeat(64),acceptedAt:'2026-11-10T12:00:00Z'}]);
await mkdir('tmp/pdf-qa',{recursive:true});await writeFile('tmp/pdf-qa/order-summary.pdf',pdf);console.log('Yerel PDF doğrulama örneği üretildi.');
