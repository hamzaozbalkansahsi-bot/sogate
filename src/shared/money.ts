/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/shared/money.ts
 * Açıklama   : Para alt birimlerini BigInt ile koruyarak yerel sayı düzeninde gösterir.
 */
export function formatMinorAmount(value:number|bigint,currency:string,minorDigits:number,locale:string){
 if(typeof value==='number'&&!Number.isSafeInteger(value))throw new RangeError('Para alt birimi güvenli tam sayı olmalıdır.');
 if(!/^[A-Z]{3}$/.test(currency)||!Number.isInteger(minorDigits)||minorDigits<0||minorDigits>4)throw new RangeError('Para birimi veya alt birim yapılandırması geçersiz.');
 const amount=BigInt(value),negative=amount<0n,absolute=negative?-amount:amount,base=10n**BigInt(minorDigits),whole=absolute/base;
 const fraction=new Intl.NumberFormat(locale,{useGrouping:false,minimumIntegerDigits:Math.max(1,minorDigits),maximumFractionDigits:0}).format(absolute%base);
 // -0, bir ana birimden küçük negatif tutarın yerel eksi konumunu korur.
 const signed=negative?(whole===0n?-0:-whole):whole;
 const formatter=new Intl.NumberFormat(locale,{style:'currency',currency,minimumFractionDigits:minorDigits,maximumFractionDigits:minorDigits});
 return formatter.formatToParts(signed).map(part=>part.type==='fraction'?fraction:part.value).join('');
}
