/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/shared/bundle-management.ts
 * Açıklama   : Set düzenleyicisinin alan sözleşmesi ve deterministik değişiklik özeti.
 */
export interface BundleQuantity{variantId:string;quantity:number;}
export interface BundleComponent extends BundleQuantity{sku:string;productName:string;name:string;active:boolean;lotTracking:boolean;available:number;}
export interface BundleDifference{variantId:string;beforeQuantity:number;afterQuantity:number;}
export interface BundleBlocker{code:string;message:string;}
export interface BundleEditorData{
 id:string;sku:string;productName:string;version:number;productStatus:string;components:BundleComponent[];capacity:number;
 canWrite:boolean;blockers:BundleBlocker[];history:{version:number;before:BundleQuantity[];after:BundleQuantity[];reason:string;createdAt:string}[];
}
export interface BundlePreview{
 id:string;expectedVersion:number;components:BundleComponent[];changes:(BundleDifference&{sku:string;productName:string;name:string})[];
 capacityBefore:number;capacityAfter:number;hasChanges:boolean;
}
export function bundleDifferences(before:readonly BundleQuantity[],after:readonly BundleQuantity[]):BundleDifference[]{
 const old=new Map(before.map(row=>[row.variantId,row.quantity])),next=new Map(after.map(row=>[row.variantId,row.quantity]));
 return [...new Set([...old.keys(),...next.keys()])].sort().flatMap(variantId=>{const beforeQuantity=old.get(variantId)??0,afterQuantity=next.get(variantId)??0;return beforeQuantity===afterQuantity?[]:[{variantId,beforeQuantity,afterQuantity}];});
}
