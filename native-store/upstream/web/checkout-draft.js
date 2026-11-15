const key='nodeno.checkout-draft.v1';
const fields=['name','email','phone','country','city','district','postalCode','line1','line2','billing_name','billing_country','billing_city','billing_district','billing_postalCode','billing_line1','billing_line2','sameBilling'];
export function cleanCheckoutDraft(value){
 const details={};if(!value||typeof value!=='object')return {details,review:null};
 for(const name of fields){const v=value.details?.[name];if(name==='sameBilling'){if(typeof v==='boolean')details[name]=v;}else if(typeof v==='string'&&v.length<=1200)details[name]=v;}
 return {details,review:null};
}
export function loadCheckoutDraft(owner){try{const value=JSON.parse(sessionStorage.getItem(key));if(owner!==undefined&&(value?.owner??'guest')!==owner){clearCheckoutDraft();return cleanCheckoutDraft(null);}return cleanCheckoutDraft(value);}catch{return {details:{},review:null};}}
export function saveCheckoutDraft(value,owner='guest'){try{sessionStorage.setItem(key,JSON.stringify({...cleanCheckoutDraft(value),owner}));}catch{}}
export function clearCheckoutDraft(){try{sessionStorage.removeItem(key);}catch{}}
