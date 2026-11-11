/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/server/order-document.ts
 * Açıklama   : Saklanan sipariş ve sözleşme özetini mali olmayan PDF olarak üretir.
 */
import PDFDocument from 'pdfkit';
import path from 'node:path';
import type {OrderSummary} from '../shared/contracts';
import {money} from '../shared/contracts';
export interface AgreementSnapshot {title:string;body:string;version:number;bodyHash:string;acceptedAt:string;}
export async function makeOrderDocument(order:OrderSummary,agreements:AgreementSnapshot[]):Promise<Buffer>{
 const document=new PDFDocument({size:'A4',margin:48,bufferPages:true,font:path.resolve('assets/fonts/SexsogateBody-Regular.ttf'),info:{Title:`Sipariş özeti ${order.number}`,Author:'SEXSOGATE',Subject:'Sipariş ve sözleşme kayıt özeti; resmî fatura değildir.'}});
 const parts:Buffer[]=[];const result=new Promise<Buffer>((resolve,reject)=>{document.on('data',(part:Buffer)=>parts.push(part));document.on('end',()=>resolve(Buffer.concat(parts)));document.on('error',reject);});
 document.registerFont('brand',path.resolve('assets/fonts/SexsogateDisplay-Regular.ttf'));document.registerFont('body',path.resolve('assets/fonts/SexsogateBody-Regular.ttf'));
 document.font('brand').fontSize(29).fillColor('#5A0A20').text('SEXSOGATE');document.moveDown(.3).font('body').fontSize(10).fillColor('#24191D').text('Tutkunu Keşfet.');
 document.moveDown(2).font('brand').fontSize(24).text('Sipariş özeti');document.moveDown(.4).font('body').fontSize(10).text(`Sipariş: ${order.number}`).text(`Tarih: ${new Date(order.createdAt).toLocaleDateString('tr-TR',{timeZone:'Europe/Istanbul'})}`);
 document.moveDown().fontSize(9).fillColor('#5A0A20').text('Bu belge resmî fatura veya e-Arşiv belgesi değildir.').fillColor('#24191D');
 document.moveDown(1.5);
 for(const item of order.items){document.fontSize(11).text(item.name);document.fontSize(9).fillColor('#716168').text(`${item.sku} · ${item.quantity} adet · ${money(item.unitMinor,order.currency)} / adet`).fillColor('#24191D');document.moveDown(.7);}
 document.moveDown().fontSize(10).text(`Ürünler: ${money(order.subtotalMinor,order.currency)}`).text(`İndirim: ${money(order.discountMinor,order.currency)}`).text(`Kargo: ${money(order.shippingMinor,order.currency)}`).text(`Tutarın içindeki vergi: ${money(order.taxMinor,order.currency)}`).moveDown(.5).fontSize(14).text(`Toplam: ${money(order.totalMinor,order.currency)}`);
 for(const agreement of agreements){document.addPage();document.font('brand').fontSize(20).text(agreement.title);document.moveDown().font('body').fontSize(8).fillColor('#716168').text(`Siparişte saklanan sürüm: ${agreement.version} · Kabul: ${new Date(agreement.acceptedAt).toLocaleString('tr-TR',{timeZone:'Europe/Istanbul'})}`).text(`İçerik SHA-256: ${agreement.bodyHash}`).fillColor('#24191D').moveDown();document.fontSize(10).text(agreement.body,{lineGap:5});}
 const pages=document.bufferedPageRange();for(let i=0;i<pages.count;i++){document.switchToPage(i);document.font('body').fontSize(8).fillColor('#716168').text(`${order.number} · ${i+1} / ${pages.count}`,48,795,{lineBreak:false});}
 document.end();return result;
}
