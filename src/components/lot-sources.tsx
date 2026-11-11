"use client";
/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/components/lot-sources.tsx
 * Açıklama   : Lotun gerçek mal kabulü kaynaklarını finans alanları olmadan gösterir.
 */
import {useEffect,useState} from 'react';
import Link from 'next/link';
import {Search} from 'lucide-react';
import type {PurchaseLotSources} from '@/shared/purchase-receipts';
import {api} from './api';
import {Busy,Status} from './ui';
import {useStore} from './store-context';
import styles from './lot-sources.module.css';

const readableRoles=['admin','catalog','warehouse','finance'];

export function LotSources({lotId,lotNumber,sku}:{lotId:string;lotNumber:string;sku:string}){
 const {user}=useStore(),authorized=readableRoles.includes(user?.role??'')&&user?.mfaVerified===true;
 const [search,setSearch]=useState(''),[query,setQuery]=useState(''),[page,setPage]=useState(1),[revision,setRevision]=useState(0);
 const key=JSON.stringify([user?.id,user?.role,authorized,lotId,query,page,revision]);
 const [record,setRecord]=useState<{key:string;data?:PurchaseLotSources;error?:string}|null>(null),current=record?.key===key?record:null;
 useEffect(()=>{
  if(!authorized)return;
  let active=true;const controller=new AbortController(),params=new URLSearchParams({view:'sources',lotId,q:query,page:String(page)});
  api<PurchaseLotSources>(`/api/admin/lots?${params}`,{signal:controller.signal}).then(data=>{if(active)setRecord({key,data});}).catch(error=>{if(active)setRecord({key,error:(error as Error).message});});
  return()=>{active=false;controller.abort();};
 },[authorized,key,lotId,page,query]);
 if(!authorized)return <p className="notice">Mal kabulü kaynaklarını görmek için yetkili hesabınızın iki adımlı doğrulamasını tamamlayın.</p>;
 return <section className={styles.panel} aria-label="Lotun mal kabulü kaynakları">
  <div className={styles.identity}><span>Üretici lotu</span><strong>{lotNumber}</strong><span>Stok kodu: {sku}</span></div>
  <p className="notice">Aynı lot birden fazla mal kabulünden oluşabilir. Bu kayıtlar, satılan her adedin hangi satın almadan geldiğini belirlemez.</p>
  {['admin','catalog','warehouse'].includes(user?.role??'')&&<Link className="text-link" href="/yonetim/purchases">Satın almadan mal kabulü</Link>}
  <form className={styles.search} onSubmit={event=>{event.preventDefault();setQuery(search.trim());setPage(1);}}>
   <label>Mal kabulü kaynaklarında ara<input type="search" maxLength={100} value={search} onChange={event=>setSearch(event.target.value)} placeholder="Tedarikçi, kayıt veya belge referansı"/></label>
   <button className="button button-outline" type="submit"><Search size={17}/>Ara</button>
  </form>
  <Status error={current?.error}/>
  {!current?<Busy/>:current.error?<button className="button button-outline" type="button" onClick={()=>setRevision(value=>value+1)}>Yeniden dene</button>:<>
   <p className={styles.count} role="status">{current.data?.total??0} mal kabulü kaydı</p>
   {current.data?.rows.length?<ol className={styles.list}>{current.data.rows.map(source=><li key={source.id}><article className={styles.card}>
    <div className={styles.heading}><h3>{source.kind==='purchase'?'Satın alma mal kabulü':'Satın alma dışı mal kabulü'}</h3><time dateTime={source.receivedAt}>{new Date(source.receivedAt).toLocaleString('tr-TR',{dateStyle:'medium',timeStyle:'short',timeZone:'Europe/Istanbul'})}</time></div>
    <dl className={styles.details}>
     {source.kind==='purchase'&&<><div className={styles.full}><dt>Tedarikçi</dt><dd>{source.supplierName??'Kaynak kaydında belirtilmedi'}</dd></div><div className={styles.full}><dt>Satın alma kaydı</dt><dd><code>{source.purchaseId??'Kaynak ilişkisi bulunmuyor'}</code></dd></div><div className={styles.full}><dt>Mal kabul kaydı</dt><dd><code>{source.receiptId??'Kaynak ilişkisi bulunmuyor'}</code></dd></div></>}
     <div><dt>Kabul adedi</dt><dd>{source.quantity.toLocaleString('tr-TR')}</dd></div><div><dt>Karantinaya alınan</dt><dd>{source.quarantineQuantity.toLocaleString('tr-TR')}</dd></div>
     {source.kind==='purchase'&&<div className={styles.full}><dt>Teslimat belgesi</dt><dd>{source.receiptSourceReference??'Teslimat referansı kayıtlı değil'}</dd></div>}
     <div className={styles.full}><dt>Kaynak belge referansı</dt><dd>{source.sourceReference??'Kaynak referansı kayıtlı değil'}</dd></div>
    </dl>
   </article></li>)}</ol>:<div className="table-empty"><p>{query?'Bu aramaya uyan mal kabulü kaynağı bulunmuyor.':'Bu lot için kayıtlı mal kabulü kaynağı bulunmuyor.'}</p></div>}
   <div className={styles.pagination}><button className="button button-outline" type="button" disabled={page<=1} onClick={()=>setPage(value=>value-1)}>Önceki</button><span>{page}. sayfa</span><button className="button button-outline" type="button" disabled={page*(current.data?.pageSize??25)>=(current.data?.total??0)} onClick={()=>setPage(value=>value+1)}>Sonraki</button></div>
   <p className={styles.caption}>Karantina adedi, kabul adedinin içindedir. Tarihler Türkiye saatine göre gösterilir.</p>
  </>}
 </section>;
}
