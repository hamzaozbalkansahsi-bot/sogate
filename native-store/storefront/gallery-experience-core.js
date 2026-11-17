/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : native-store/storefront/gallery-experience-core.js
 * Açıklama   : Galeri döngüsünü ve yatay raf kenarlarını DOM’dan bağımsız hesaplar.
 */
const finite=value=>Number.isFinite(Number(value))?Number(value):0;
export function wrapGalleryIndex(index,total){const length=Math.max(0,Math.trunc(finite(total)));if(length<2)return 0;return((Math.trunc(finite(index))%length)+length)%length;}
export function railEdges({scrollLeft=0,scrollWidth=0,clientWidth=0}={}){
 const maximum=Math.max(0,finite(scrollWidth)-Math.max(0,finite(clientWidth))),position=Math.min(maximum,Math.abs(finite(scrollLeft))),overflow=maximum>4;
 return {maximum,position,overflow,previousHidden:!overflow||position<=2,nextHidden:!overflow||position>=maximum-2};
}
export function railStepDelta(step,width,direction='ltr'){return Math.sign(finite(step))*Math.max(0,finite(width))*.8*(direction==='rtl'?-1:1)||0;}
export function catalogImagePath(product,src){
 if(typeof src!=='string'||typeof product?.id!=='string')return '';
 const match=/^\/media\/([A-Za-z0-9_%-]+)\/(?:(\d+)|gallery\/([a-f0-9]{64}))$/.exec(src);
 return match&&match[0]===src&&match[1]===product.id&&(match[2]!==undefined||/^sg_ty_[a-f0-9]{16}$/.test(product.id))?src:'';
}
