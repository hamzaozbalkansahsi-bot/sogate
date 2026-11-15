const KEY='nodeno.analytics.consent.v1',LIFETIME=90*86400000;
const OPTIONAL_KEYS=['nodeno.recent.v1','nodeno.searches.v1'];
let generation=0;
function browserStorage(){try{return globalThis.localStorage;}catch{return null;}}
function browserTarget(){return typeof window==='undefined'?null:window;}
function notify(target,detail){try{target?.dispatchEvent(new CustomEvent('nodeno:privacy-change',{detail}));}catch{}}
export function clearOptionalPersonalization(storage=browserStorage()){
 for(const key of OPTIONAL_KEYS)try{storage?.removeItem(key);}catch{}
}
export function savePrivacyPreference(granted,{storage=browserStorage(),eventTarget=browserTarget(),now=Date.now()}={}){
 if(typeof granted!=='boolean')throw new TypeError('privacy_choice_required');
 const record={schema:3,granted,decidedAt:now,expiresAt:now+LIFETIME};
 if(!granted)clearOptionalPersonalization(storage);
 try{storage?.setItem(KEY,JSON.stringify(record));}catch{}
 notify(eventTarget,{granted,expiresAt:record.expiresAt});return granted;
}
export function readPrivacyPreference(storage=browserStorage(),now=Date.now()){
 let raw;try{raw=storage?.getItem(KEY);}catch{return null;}
 if(raw==null){clearOptionalPersonalization(storage);return null;}
 let value;try{value=JSON.parse(raw);}catch{}
 // An old unversioned acceptance does not prove consent to the current purposes or its age.
 if(value===false){savePrivacyPreference(false,{storage,now});return false;}
 if((value?.schema===3||(value?.schema===2&&value.granted===false))&&typeof value.granted==='boolean'&&Number.isSafeInteger(value.decidedAt)&&Number.isSafeInteger(value.expiresAt)&&value.decidedAt<=now&&value.expiresAt===value.decidedAt+LIFETIME&&now<value.expiresAt)return value.granted;
 try{storage?.removeItem(KEY);}catch{}clearOptionalPersonalization(storage);
 notify(browserTarget(),{granted:false,expiresAt:null,expired:true});return null;
}
export function optionalPersonalizationAllowed(storage=browserStorage(),now=Date.now()){
 return readPrivacyPreference(storage,now)===true;
}
async function consentRequest(path,body){
 const response=await fetch(path,{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
 if(!response.ok)throw new Error('insights_unavailable');return response.json();
}
export async function setOptionalPreference(granted,{storage=browserStorage(),eventTarget=browserTarget(),now=Date.now(),request=consentRequest}={}){
 if(typeof granted!=='boolean')throw new TypeError('privacy_choice_required');
 const own=++generation;
 // Refusal takes effect locally even while offline; a grant waits for the server acknowledgement.
 if(!granted)savePrivacyPreference(false,{storage,eventTarget,now});
 const result=await request('/api/insights/consent',{granted});
 if(own!==generation)return readPrivacyPreference(storage,now);
 if(result?.granted!==granted)throw new Error('insights_consent_unconfirmed');
 if(granted)savePrivacyPreference(true,{storage,eventTarget,now});
 return granted;
}
