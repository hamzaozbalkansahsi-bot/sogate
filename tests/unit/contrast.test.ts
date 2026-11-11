/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : tests/unit/contrast.test.ts
 * Açıklama   : İlgili iş akışının doğruluk, güvenlik veya erişilebilirlik kabulünü sınar.
 */
import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';

const stylesheet=readFileSync(new URL('../../src/app/globals.css',import.meta.url),'utf8');
const tokens=new Map([...stylesheet.matchAll(/(--[a-z-]+)\s*:\s*(#[\da-f]{3,8})\b/gi)].map(match=>[match[1],match[2]]));
function token(name:string):string {
  const value=tokens.get('--'+name);if(!value)throw new Error(`CSS renk tokenı bulunamadı: ${name}`);return value;
}
function luminance(hex:string):number {
  let value=hex.replace('#','');if(value.length===3)value=[...value].map(c=>c+c).join('');
  if(!/^[\da-f]{6}$/i.test(value))throw new Error('Kontrast testi opak RGB rengi gerektirir.');
  const linear=[0,2,4].map(offset=>parseInt(value.slice(offset,offset+2),16)/255).map(channel=>channel<=0.04045?channel/12.92:((channel+0.055)/1.055)**2.4);
  return 0.2126*linear[0]+0.7152*linear[1]+0.0722*linear[2];
}
function contrast(foreground:string,background:string):number {
  const first=luminance(foreground),second=luminance(background);
  return (Math.max(first,second)+0.05)/(Math.min(first,second)+0.05);
}
function assertRatio(foreground:string,background:string,minimum:number,label:string) {
  expect(contrast(foreground,background),`${label}: ${foreground}/${background}`).toBeGreaterThanOrEqual(minimum);
}
function authoredColor(selector:string,property:'color'|'background') {
  const declaration=new RegExp(`(?:^|;)\\s*${property}\\s*:\\s*([^;]+)`);
  const rule=[...stylesheet.matchAll(/([^{}]+)\{([^{}]*)\}/g)].filter(match=>match[1].split(',').some(value=>value.trim()===selector)&&declaration.test(match[2])).at(-1);
  const value=rule&&declaration.exec(rule[2])?.[1];
  if(!value)throw new Error(`CSS renk tanımı bulunamadı: ${selector}/${property}`);
  const variable=/^var\(--([a-z-]+)\)$/.exec(value);
  return variable?token(variable[1]):value;
}
function focusColor(context:string) {
  const rules=[...stylesheet.matchAll(/([^{}]+)\{([^{}]*)\}/g)];
  const global=rules.find(match=>match[1].includes('button:focus-visible')&&match[2].includes('outline:'));
  const local=rules.filter(match=>match[1].includes(context)&&match[1].includes(':focus-visible')&&/outline(?:-color)?:/.test(match[2])).at(-1);
  const declarations=local?.[2]??global?.[2]??'';
  const variable=/outline(?:-color)?\s*:[^;]*var\(--([a-z-]+)\)/.exec(declarations);
  if(variable)return token(variable[1]);
  const literal=/outline(?:-color)?\s*:[^;]*(#[\da-f]{3,8})\b/i.exec(declarations);
  if(literal)return literal[1];
  throw new Error('Odak halkası rengi CSS içinde bulunamadı.');
}

describe('Gerçek tema renklerinin WCAG AA kontrastı',()=>{
  it.each(['surface-base','surface-card','surface-soft'])('%s üzerindeki normal metin en az 4.5:1 olur',surface=>{
    for(const text of ['text-primary','text-secondary','brand-burgundy','brand-wine','status-red'])assertRatio(token(text),token(surface),4.5,`${text}/${surface}`);
  });
  it('birincil ve hover düğmesinde beyaz normal metin en az 4.5:1 olur',()=>{
    for(const background of ['brand-burgundy','brand-wine'])assertRatio(token('surface-card'),token(background),4.5,`button/${background}`);
  });
  it.each(['surface-base','surface-card','surface-soft'])('%s üzerindeki form kontrol sınırı en az 3:1 olur',surface=>{
    assertRatio(token('border-control'),token(surface),3,`form border/${surface}`);
  });
  it('bordo kampanyada açık metin ve metal vurgu en az 4.5:1 olur',()=>{
    for(const foreground of ['surface-base','brand-rose-metal'])assertRatio(token(foreground),token('brand-burgundy'),4.5,`hero/${foreground}`);
  });
  it('açık yüzeyde klavye odak halkası en az 3:1 olur',()=>{
    for(const background of ['surface-base','surface-card','surface-soft'])assertRatio(focusColor('body'),token(background),3,`focus/${background}`);
  });
  it('koyu kampanya yüzeyinde klavye odak halkası en az 3:1 olur',()=>{
    assertRatio(focusColor('.hero'),token('brand-burgundy'),3,'hero focus');
    assertRatio(focusColor('.site-footer'),authoredColor('.site-footer','background'),3,'footer focus');
  });
  it('durum etiketi ve footer normal metni en az 4.5:1 olur',()=>{
    assertRatio(token('status-green'),authoredColor('.positive','background'),4.5,'success status');
    assertRatio(authoredColor('.footer-grid a:not(.brand)','color'),authoredColor('.site-footer','background'),4.5,'footer links');
  });
});
