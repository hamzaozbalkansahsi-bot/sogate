/**
 * Proje      : SEXOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : native-store/storefront/public-read.js
 * Açıklama   : Yalnız kamu katalog/ayar okumasının bağlantı beklemesini sınırlar.
 */
export async function readStorefrontJson(url,init={}, {timeoutMs=20000,fetcher=(...args)=>globalThis.fetch(...args)}={}){
 if(typeof url!=='string'||!url.startsWith('/')||url.startsWith('//')||!/^\/(?:[^?#]*\/)?api\/(?:catalog|config)$/.test(url)||(init.method&&init.method!=='GET'))throw Error('public_read_scope');
 for(let attempt=0;attempt<2;attempt++){
  const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),timeoutMs);
  try{
   const response=await fetcher(url,{...init,method:'GET',signal:controller.signal});
   if(!response.ok)throw Error('public_read_failed');
   return await response.json();
  }catch(error){
   if(attempt===1||(!controller.signal.aborted&&!(error instanceof TypeError)))throw error;
  }finally{clearTimeout(timer);}
 }
}
