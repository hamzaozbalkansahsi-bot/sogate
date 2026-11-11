"use client";
/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/components/privacy-request.tsx
 * Açıklama   : Gereksiz kimlik belgesi toplamadan özel başvuru alır ve yetkili durum görünümünü sunar.
 */
import {useEffect,useState} from 'react';
import {useSearchParams} from 'next/navigation';
import {useStore} from './store-context';
import {api,post} from './api';
import Link from './localized-link';
import {localePath} from '@/shared/i18n';
import {Busy,PageHeading,Status} from './ui';
type CaseStatus={id:string;reference:string;status:string;receivedAt:string;dueAt:string|null;summary?:string;type?:string;responses?:{body:string;outcome:string;created_at:string}[]};
const topics={access:['Verilerime erişim','Access my data'],correction:['Bilgi düzeltme','Correct my information'],erasure:['Silme talebi','Request erasure'],objection:['İşlemeye itiraz','Object to processing'],portability:['Veri taşınabilirliği','Data portability'],consent_withdrawal:['İzin geri alma','Withdraw permission'],other:['Diğer başvuru','Other request']} as const;
function statusLabel(value:string,en:boolean){return ({received:en?'Received':'Alındı',in_review:en?'Under review':'İnceleniyor',responded:en?'Answered':'Yanıtlandı',rejected:en?'Reasoned response provided':'Gerekçeli yanıtlandı'} as Record<string,string>)[value]??value;}
export function PrivacyRequest(){
 const {locale,user}=useStore(),en=locale==='en',params=useSearchParams(),id=params.get('case'),token=params.get('token');
 const viewKey=[id,token,user?.id??'guest'].join('|');
 const [loaded,setLoaded]=useState<{key:string;record?:CaseStatus;error?:string}|null>(null),[error,setError]=useState(''),[busy,setBusy]=useState(false),[revision,setRevision]=useState(0),[email,setEmail]=useState('');
 useEffect(()=>{if(!id)return;let active=true;api<CaseStatus>('/api/privacy?case='+encodeURIComponent(id)+(token?'&token='+encodeURIComponent(token):'')).then(value=>{if(active)setLoaded({key:viewKey,record:value});}).catch(e=>{if(active)setLoaded({key:viewKey,error:e.message});});return()=>{active=false;};},[id,token,revision,viewKey]);
 const record=loaded?.key===viewKey?loaded.record:null,loadError=loaded?.key===viewKey?loaded.error:'';
 async function submit(event:React.FormEvent<HTMLFormElement>){
  event.preventDefault();setBusy(true);setError('');const values=Object.fromEntries(new FormData(event.currentTarget)),country=String(values.country??'').trim().toUpperCase();
  try{const result=await post<{id:string;reference:string;token:string}>('/api/privacy',{email:user?.email??email,type:values.type,summary:values.summary,...(country?{country}:{}),locale});const url=new URL(localePath('/veri-basvurusu',locale),window.location.origin);url.searchParams.set('case',result.id);url.searchParams.set('token',result.token);window.location.assign(url.pathname+url.search);}catch(e){setError((e as Error).message);setBusy(false);}
 }
 return <div className="container section narrow"><PageHeading title={en?'Data privacy request':'Veri gizliliği başvurusu'} description={en?'Submit a request about your personal data.':'Kişisel verilerinizle ilgili talebinizi iletin.'}/><Status error={error||loadError}/>{id?<>{!record&&!error&&!loadError?<Busy/>:record&&<article className="card"><h2>{record.reference}</h2><p className="notice">{statusLabel(record.status,en)}</p><dl><dt>{en?'Received':'Alınma zamanı'}</dt><dd>{new Date(record.receivedAt).toLocaleString(en?'en-GB':'tr-TR')}</dd><dt>{en?'Response deadline':'Son yanıt zamanı'}</dt><dd>{record.dueAt?new Date(record.dueAt).toLocaleString(en?'en-GB':'tr-TR'):en?'The applicable response rule is under review.':'Uygulanacak yanıt süresi kuralı inceleniyor.'}</dd></dl>{record.summary&&<p style={{whiteSpace:'pre-wrap'}}>{record.summary}</p>}{record.responses?.map((response,index)=><section key={index}><h3>{en?'Response':'Yanıt'}</h3><p style={{whiteSpace:'pre-wrap'}}>{response.body}</p></section>)}<p>{en?'Keep this private status link safe. Detailed responses are shared with the verified requester through a secure channel.':'Size özel durum bağlantısını güvenli yerde saklayın. Ayrıntılı yanıtlar kimliği doğrulanmış başvuranla güvenli kanaldan paylaşılır.'}</p><button className="button button-outline" onClick={()=>setRevision(value=>value+1)}>{en?'Refresh status':'Durumu yenile'}</button></article>}</>:<form className="card form-stack" onSubmit={submit}><p>{en?'Include only the information needed to explain your request. Do not attach identity documents, card details or sensitive personal information.':'Talebinizi açıklamak için gereken bilgileri paylaşın. Kimlik belgesi, kart bilgisi veya gereksiz hassas bilgi eklemeyin.'}</p><label>{en?'Email address':'E-posta adresi'}<input name="email" type="email" required maxLength={254} autoComplete="email" value={user?.email??email} readOnly={Boolean(user)} onChange={event=>setEmail(event.target.value)}/></label><label>{en?'Request topic':'Talep konusu'}<select name="type">{Object.entries(topics).map(([value,labels])=><option key={value} value={value}>{labels[en?1:0]}</option>)}</select></label><label>{en?'Country code, if known':'Biliyorsanız ülke kodu'}<input name="country" maxLength={2} pattern="[A-Za-z]{2}" placeholder="TR" autoComplete="country"/></label><label>{en?'Your request':'Talebiniz'}<textarea name="summary" required minLength={10} maxLength={4000} rows={6}/></label><p className="small muted">{en?'An account or marketing permission is not required. Identity verification may be needed before personal information can be shared.':'Üyelik veya pazarlama izni gerekmez. Kişisel bilgi paylaşılmadan önce güvenli kimlik doğrulaması istenebilir.'} <Link className="text-link" href="/yasal/gizlilik">{en?'Privacy notice':'Aydınlatma metni'}</Link></p><button className="button" disabled={busy}>{busy?(en?'Saving…':'Kaydediliyor…'):(en?'Submit request':'Başvuruyu kaydet')}</button></form>}</div>;
}
export function PrivacyAccount(){
 const {locale}=useStore(),en=locale==='en';const [rows,setRows]=useState<{id:string;reference:string;status:string;received_at:string}[]|null>(null),[error,setError]=useState('');
 useEffect(()=>{api<{requests:{id:string;reference:string;status:string;received_at:string}[]}>('/api/privacy').then(value=>setRows(value.requests)).catch(e=>setError(e.message));},[]);
 return <section className="card"><h2>{en?'Your data privacy requests':'Veri gizliliği başvurularınız'}</h2><Status error={error}/><Link className="button button-outline" href="/veri-basvurusu">{en?'Create a request':'Yeni başvuru'}</Link>{!rows&&!error?<Busy/>:rows?.length?<ul>{rows.map(row=><li key={row.id}><Link className="text-link" href={'/veri-basvurusu?case='+encodeURIComponent(row.id)}>{row.reference} · {statusLabel(row.status,en)}</Link></li>)}</ul>:<p>{en?'You have no recorded requests.':'Kayıtlı başvurunuz bulunmuyor.'}</p>}</section>;
}
