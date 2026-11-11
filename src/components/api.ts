"use client";
/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/components/api.ts
 * Açıklama   : Özel JSON isteklerini dil, hata ve durum kodlarıyla istemciye iletir.
 */
export class ApiError extends Error {
 constructor(message:string,readonly status:number,readonly code?:string){super(message);this.name='ApiError';}
}
export class ApiResponseError extends ApiError {
 constructor(message:string,status=0){super(message,status,'RESPONSE_UNCONFIRMED');this.name='ApiResponseError';}
}
export type ApiOptions<T>=RequestInit&{validate?:(data:unknown)=>T};
function isAbort(error:unknown){return !!error&&typeof error==='object'&&'name'in error&&error.name==='AbortError';}
export async function api<T>(path:string, init?:ApiOptions<T>):Promise<T> {
 const language=typeof window!=="undefined"&&/^\/en(?:\/|$)/.test(window.location.pathname)?"en":"tr";
 const unconfirmed=language==='en'?'The server response could not be verified. Check the operation result and try again.':'Sunucu yanıtı doğrulanamadı. İşlemin sonucunu kontrol edip yeniden deneyin.';
 const {validate,...options}=init??{};let response:Response;
 try{response=await fetch(path,{...options,cache:"no-store",headers:{"Accept-Language":language,...(options.body?{"Content-Type":"application/json"}:{}),...options.headers}});}catch(error){if(isAbort(error))throw error;throw new ApiResponseError(unconfirmed);}
 let data:unknown;
 try{data=await response.json();}catch(error){if(isAbort(error))throw error;throw new ApiResponseError(unconfirmed,response.status);}
 if(!response.ok){const envelope=data&&typeof data==='object'&&!Array.isArray(data)?data as Record<string,unknown>:{};const message=typeof envelope.error==='string'&&envelope.error.trim()?envelope.error:typeof envelope.message==='string'&&envelope.message.trim()?envelope.message:null;if(!message)throw new ApiResponseError(unconfirmed,response.status);throw new ApiError(message,response.status,typeof envelope.code==='string'?envelope.code:undefined);}
 if(validate){try{return validate(data);}catch{throw new ApiResponseError(unconfirmed,response.status);}}
 return data as T;
}
export const post=<T,>(path:string,body:unknown,options?:Pick<ApiOptions<T>,'signal'|'validate'>)=>api<T>(path,{method:"POST",body:JSON.stringify(body),...options});
