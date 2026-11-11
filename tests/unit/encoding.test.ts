/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : tests/unit/encoding.test.ts
 * Açıklama   : İlgili iş akışının doğruluk, güvenlik veya erişilebilirlik kabulünü sınar.
 */
import {it,expect} from 'vitest';
import {readdir,readFile} from 'node:fs/promises';
import path from 'node:path';
async function files(root:string):Promise<string[]>{const entries=await readdir(root,{withFileTypes:true});return (await Promise.all(entries.map(entry=>entry.isDirectory()?files(path.join(root,entry.name)):Promise.resolve([path.join(root,entry.name)])))).flat();}
it('elle yazılan kaynak, arayüz, belge ve CSV UTF-8 kalır; bozuk Türkçe kodlama işaretlerini yakalar',async()=>{
 const candidates=(await Promise.all(['src','docs','public/templates'].map(files))).flat().filter(file=>/\.(tsx?|css|md|csv)$/.test(file));
 for(const file of candidates){const text=new TextDecoder('utf-8',{fatal:true}).decode(await readFile(file));expect(text,`${file} kodlama bozulması`).not.toMatch(/\uFFFD|Ã[\u0080-\u00BF]|Ä[\u0080-\u00BF]|Å[\u0080-\u00BF]/);}
 const contracts=await readFile('public/templates/product-import.csv','utf8');expect(contracts.length).toBeGreaterThan(10);
});
