import {seoPage,seoDocument,seoRobots,seoSitemap} from './seo.mjs';
const MEDIA_HOSTS = new Set(['witcdn.adoremobilya.com','www.adoremobilya.com','adoremobilya.com']);
const SECURITY_HEADERS = {
 'X-Content-Type-Options':'nosniff',
 'Referrer-Policy':'strict-origin-when-cross-origin',
 'Permissions-Policy':'camera=(), microphone=(), geolocation=()',
 'Content-Security-Policy':"default-src 'self'; script-src 'self'; style-src 'self'; font-src 'self'; img-src 'self' data:; connect-src 'self'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'; object-src 'none'",
};

export function safeMediaUrl(value) {
 try { const u=new URL(value); return u.protocol==='https:' && MEDIA_HOSTS.has(u.hostname) && !u.username && !u.password && (!u.port || u.port==='443'); } catch { return false; }
}

export function productMetadata(html,catalog,url,config={}){return seoDocument(html,seoPage(catalog,config,url));}

export function createApplication(catalog, assets, media, driveManifest = {}, upstreamFetch = fetch, brand = {}, mediaProof = {}, ownerMedia = {}) {
 const publicJSON=JSON.stringify(catalog);
 const verification=typeof brand.seo?.googleVerification==='string'?brand.seo.googleVerification.trim():'';
 const googleVerification=/^[A-Za-z0-9_-]{1,200}$/.test(verification)?verification:'';
 const publicConfig=JSON.stringify({
  checkoutEnabled:false,contactEmail:brand.contact?.email||null,contactPhone:brand.contact?.phone||null,
  contactPhoneUri:brand.contact?.phoneE164?'tel:'+brand.contact.phoneE164:null,
  domain:brand.domain||null,website:brand.website||null,socialHandle:brand.socialHandle||null,socials:brand.socials||[],
  legalName:brand.legalName||null,parentCompany:brand.parentCompany||null,mode:'catalogue',brand:{name:brand.name||'NODENO',slogan:brand.slogan||catalog.brand?.slogan||{}},
  ...(googleVerification?{seo:{googleVerification}}:{})
 });
 let oauthToken=null;
 let tokenUntil=0;
 function reply(body,status=200,type='application/json; charset=utf-8',extra={}) {
  return new Response(body,{status,headers:{...SECURITY_HEADERS,'Content-Type':type,...extra}});
 }
 const error=(status,code)=>reply(JSON.stringify({error:code}),status);
 async function driveToken(env) {
  if(env.GOOGLE_DRIVE_ACCESS_TOKEN) return env.GOOGLE_DRIVE_ACCESS_TOKEN;
  if(!env.GOOGLE_DRIVE_REFRESH_TOKEN || !env.GOOGLE_OAUTH_CLIENT_ID || !env.GOOGLE_OAUTH_CLIENT_SECRET) return null;
  if(oauthToken && Date.now()<tokenUntil) return oauthToken;
  const r=await upstreamFetch('https://oauth2.googleapis.com/token',{method:'POST',body:new URLSearchParams({grant_type:'refresh_token',refresh_token:env.GOOGLE_DRIVE_REFRESH_TOKEN,client_id:env.GOOGLE_OAUTH_CLIENT_ID,client_secret:env.GOOGLE_OAUTH_CLIENT_SECRET}),signal:AbortSignal.timeout(15000)});
  if(!r.ok) return null;
  const t=await r.json();
  if(typeof t.access_token!=='string') return null;
  oauthToken=t.access_token; tokenUntil=Date.now()+Math.max(0,(Number(t.expires_in)||3600)-60)*1000;
  return oauthToken;
 }
 async function getMedia(id,index,env,requestOrigin) {
  const original=media[id]?.[index];
  if(!original) return error(404,'image_not_found');
  if(catalog.meta?.mediaVersion) {
   const expected=mediaProof[`${id}:${index}`];
   if(!/^[a-f0-9]{64}$/.test(expected||''))return error(503,'image_review_pending');
   let canonical;
   try{canonical=new URL(brand.website);}catch{return error(503,'image_unavailable');}
   if(canonical.protocol!=='https:'||canonical.hostname!==brand.domain||canonical.username||canonical.password||canonical.origin===requestOrigin)return error(503,'image_unavailable');
   const target=new URL(`/media/${encodeURIComponent(id)}/${index}`,canonical);
   target.searchParams.set('v',catalog.meta.mediaVersion);
   const reviewed=await upstreamFetch(target.href,{redirect:'error',signal:AbortSignal.timeout(20000)});
   if(!reviewed.ok)return error(502,'image_unavailable');
   const type=(reviewed.headers.get('content-type')||'').split(';')[0].toLowerCase();
   if(!['image/jpeg','image/png','image/webp','image/avif','image/gif'].includes(type)||Number(reviewed.headers.get('content-length'))>20000000)return error(502,'image_unavailable');
   const reader=reviewed.body?.getReader();if(!reader)return error(502,'image_unavailable');
   const chunks=[];let length=0;
   while(true){const {value,done}=await reader.read();if(done)break;length+=value.byteLength;if(length>20000000){await reader.cancel();return error(502,'image_unavailable');}chunks.push(value);}
   const bytes=new Uint8Array(length);let offset=0;for(const chunk of chunks){bytes.set(chunk,offset);offset+=chunk.byteLength;}
   const digest=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),b=>b.toString(16).padStart(2,'0')).join('');
   if(digest!==expected)return error(502,'image_unavailable');
   return reply(bytes,200,type,{'Cache-Control':'public, max-age=86400','Content-Disposition':'inline','Cross-Origin-Resource-Policy':'same-origin'});
  }
  const entry=driveManifest[`${id}:${index}`];
  let response;
  if(entry?.fileId) {
   const token=await driveToken(env);
   // Once a migrated file is selected, an authorization failure stays visible;
   // do not silently return an older supplier image.
   if(!token) return error(503,'image_unavailable');
   if(!/^[A-Za-z0-9_-]{8,180}$/.test(entry.fileId)) return error(503,'image_unavailable');
   response=await upstreamFetch(`https://www.googleapis.com/drive/v3/files/${encodeURIComponent(entry.fileId)}?alt=media`,{headers:{Authorization:`Bearer ${token}`},redirect:'error',signal:AbortSignal.timeout(20000)});
  } else {
   let target=original;
   for(let hops=0;hops<4;hops++) {
    if(!safeMediaUrl(target)) return error(502,'image_unavailable');
    response=await upstreamFetch(target,{headers:{'User-Agent':`NODENO-Catalog/1.0 (+${brand.website||'https://nodenohome.com'})`},redirect:'manual',signal:AbortSignal.timeout(20000)});
    if(![301,302,303,307,308].includes(response.status)) break;
    const location=response.headers.get('location');
    if(!location) return error(502,'image_unavailable');
    target=new URL(location,target).href;
    response=null;
   }
  }
  if(!response?.ok) return error(502,'image_unavailable');
  const type=(response.headers.get('content-type')||'').split(';')[0].toLowerCase();
  if(!['image/jpeg','image/png','image/webp','image/avif','image/gif'].includes(type)) return error(502,'image_unavailable');
  const contentLength=Number(response.headers.get('content-length'));
  if(contentLength>20000000) return error(502,'image_unavailable');
  return reply(response.body,200,type,{'Cache-Control':entry?.fileId?'private, max-age=3600':'public, max-age=86400','Content-Disposition':'inline','Cross-Origin-Resource-Policy':'same-origin'});
 }
 return {async fetch(request,env={},ctx={}) {
  try {
   const url=new URL(request.url);
   if(!['GET','HEAD'].includes(request.method)) return reply(JSON.stringify({error:'method_not_allowed'}),405,'application/json; charset=utf-8',{'Allow':'GET, HEAD'});
   const categoryAlias={'adore-gaming':'oyuncu-mobilyalari','adoregaming-tgif':'tgif-serisi'}[url.searchParams.get('category')];
   if(typeof categoryAlias==='string'&&['/','/index.html','/index.php'].includes(url.pathname)){url.searchParams.set('category',categoryAlias);return reply('',301,'text/html; charset=utf-8',{'Location':url.pathname+url.search,'Cache-Control':'no-store'});}
   let response;
   if(url.pathname==='/api/catalog') response=reply(publicJSON,200,'application/json; charset=utf-8',{'Cache-Control':'public, max-age=300'});
   else if(url.pathname==='/api/config') response=reply(publicConfig);
   else if(url.pathname==='/api/health') response=reply(JSON.stringify({status:'ok',brand:'NODENO',products:catalog.products.length,categories:catalog.categories.length,checkoutEnabled:false,releaseHash:catalog.meta.releaseHash||null}));
   else if(url.pathname==='/sitemap.xml'||/^\/sitemap-(products|pages)-(tr|en|ru|ar|de|az|kk|tk|uz|ky|fa)\.xml$/.test(url.pathname)){const match=/^\/sitemap-(products|pages)-(tr|en|ru|ar|de|az|kk|tk|uz|ky|fa)\.xml$/.exec(url.pathname);response=reply(seoSitemap(catalog,JSON.parse(publicConfig),match?.[1]||'index',match?.[2]||'tr'),200,'application/xml; charset=utf-8',{'Cache-Control':'public, max-age=300'});}
   else if(url.pathname.startsWith('/media/')) {
    const m=/^\/media\/([A-Za-z0-9_-]+)\/(0|[1-9]\d{0,3})$/.exec(url.pathname);
    if(m&&ownerMedia[m[1]+':'+m[2]]){
     const asset=assets[ownerMedia[m[1]+':'+m[2]]];if(!asset)return error(404,'image_not_found');
     const body=asset.encoding==='base64'?Uint8Array.from(atob(asset.body),c=>c.charCodeAt(0)):asset.body;
     return reply(request.method==='HEAD'?null:body,200,asset.type,{'Cache-Control':'public, max-age=86400'});
    }
    if(!m || !media[m[1]]?.[Number(m[2])]) return error(404,'image_not_found');
    const cacheKey=new Request(url.origin+url.pathname+(catalog.meta?.mediaVersion?'?v='+encodeURIComponent(catalog.meta.mediaVersion):''));
    const privateImage=Boolean(driveManifest[`${m[1]}:${m[2]}`]?.fileId);
    let cache=null,cached=null;
    // Dispatch namespaces disable caches.default. A named cache remains an
    // optional optimization; lack of cache support must never hide an image.
    if(!privateImage) {
     try { if(globalThis.caches?.open){cache=await globalThis.caches.open(catalog.meta?.mediaVersion?'nodeno-reviewed-media-v1':'nodeno-media-v1');cached=await cache.match(cacheKey);} } catch {cache=null;}
    }
    response=cached||await getMedia(m[1],Number(m[2]),env,url.origin);
    if(!cached && !privateImage && response.ok && cache && ctx.waitUntil) {
     try {ctx.waitUntil(Promise.resolve(cache.put(cacheKey,response.clone())).catch(()=>{}));} catch {}
    }
   } else if(url.pathname==='/robots.txt') response=reply(seoRobots(),200,'text/plain; charset=utf-8');
   else {
    const key=url.pathname==='/'||url.pathname==='/index.html'?'/':url.pathname;
    const asset=assets[key];
    if(!asset) return error(404,'not_found');
    if(key==='/') {
     const nonce=Array.from(crypto.getRandomValues(new Uint8Array(16)),value=>value.toString(16).padStart(2,'0')).join('');
     const policy=SECURITY_HEADERS['Content-Security-Policy'].replace("script-src 'self'",`script-src 'self' 'nonce-${nonce}'`);
     const detailAsset=assets['/api/supplier-products/'+url.searchParams.get('product')];const details=detailAsset?JSON.parse(detailAsset.body):null;const seoCatalog=details?{...catalog,products:catalog.products.map(p=>p.id===details.id?{...p,description:details.description}:p)}:catalog;
     const page=seoPage(seoCatalog,JSON.parse(publicConfig),url);
     response=reply(seoDocument(asset.body,page).replace(/<script\b/g,`<script nonce="${nonce}"`),page.status,asset.type,{'Cache-Control':'no-store','Content-Security-Policy':policy,'X-Robots-Tag':page.indexable?'index,follow':'noindex,follow'});
    } else if(asset.encoding==='external') {
     const match=/^\/assets\/suppliers\/([a-f0-9]{64})\.(jpg|png|webp)$/.exec(url.pathname);
     if(!match||asset.sha256!==match[1]||asset.url!=='https://nodenohome.com'+url.pathname)return error(503,'image_not_approved');
     const remote=await upstreamFetch(new Request(asset.url,{redirect:'error'}));if(!remote.ok)return error(503,'image_unavailable');
     const bytes=await remote.arrayBuffer();const hash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),n=>n.toString(16).padStart(2,'0')).join('');
     if(hash!==asset.sha256)return error(503,'image_not_approved');
     response=reply(bytes,200,asset.type,{'Cache-Control':'public, max-age=86400'});
    } else {
     const body=asset.encoding==='base64'?Uint8Array.from(atob(asset.body),character=>character.charCodeAt(0)):asset.body;
     response=reply(body,200,asset.type,{'Cache-Control':'public, max-age=300'});
    }
   }
   if(request.method==='HEAD') return new Response(null,{status:response.status,headers:response.headers});
   return response;
  } catch { return error(503,'temporarily_unavailable'); }
 }};
}
