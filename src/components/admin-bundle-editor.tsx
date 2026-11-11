"use client";
/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/components/admin-bundle-editor.tsx
 * Açıklama   : Fiziksel set bileşenlerini sunucu önizlemesi ve sürüm denetimiyle düzenler.
 */
import {useEffect,useRef,useState} from 'react';
import {api,post} from './api';
import {Busy,Status} from './ui';
import type {BundleComponent,BundleEditorData,BundlePreview} from '@/shared/bundle-management';

type Candidate=Omit<BundleComponent,'variantId'|'quantity'>&{id:string};
type Candidates={rows:Candidate[];total:number;page:number};
export function AdminBundleEditor({variantId,onSaved}:{variantId:string;onSaved:()=>void}){
 const [data,setData]=useState<BundleEditorData|null>(null),[selected,setSelected]=useState<BundleComponent[]>([]),[revision,setRevision]=useState(0),[loading,setLoading]=useState(true),[error,setError]=useState('');
 const [searchRevision,setSearchRevision]=useState(0);
 const [search,setSearch]=useState(''),[query,setQuery]=useState(''),[page,setPage]=useState(1),[candidates,setCandidates]=useState<Candidates>({rows:[],total:0,page:1}),[searching,setSearching]=useState(true),[searchError,setSearchError]=useState('');
 const [preview,setPreview]=useState<BundlePreview|null>(null),[reason,setReason]=useState(''),[busy,setBusy]=useState(false);
 const generation=useRef(0),alive=useRef(true);
 useEffect(()=>{alive.current=true;return()=>{alive.current=false;};},[]);
 useEffect(()=>{
  let active=true;
  api<BundleEditorData>(`/api/admin/variants?view=bundle&id=${encodeURIComponent(variantId)}`).then(result=>{if(active){setData(result);setSelected(result.components);setError('');}}).catch(error=>{if(active)setError((error as Error).message);}).finally(()=>{if(active)setLoading(false);});
  return()=>{active=false;};
 },[variantId,revision]);
 useEffect(()=>{
  let active=true;
  api<Candidates>(`/api/admin/variants?view=bundleCandidates&exclude=${encodeURIComponent(variantId)}&q=${encodeURIComponent(query)}&page=${page}`).then(result=>{if(active){setCandidates(result);setSearchError('');}}).catch(error=>{if(active)setSearchError((error as Error).message);}).finally(()=>{if(active)setSearching(false);});
  return()=>{active=false;};
 },[variantId,query,page,revision,searchRevision]);
 function edit(rows:BundleComponent[]){generation.current++;setSelected(rows);setPreview(null);setError('');}
 function reload(){generation.current++;setLoading(true);setData(null);setPreview(null);setReason('');setRevision(value=>value+1);}
 async function requestPreview(){
  if(!data)return;const current=++generation.current;setBusy(true);setError('');setPreview(null);
  try{const result=await post<BundlePreview>('/api/admin/variants',{action:'bundlePreview',id:variantId,expectedVersion:data.version,components:selected.map(({variantId,quantity})=>({variantId,quantity}))});if(alive.current&&current===generation.current)setPreview(result);}
  catch(error){if(alive.current&&current===generation.current)setError((error as Error).message);}
  finally{if(alive.current&&current===generation.current)setBusy(false);}
 }
 async function save(event:React.FormEvent){
  event.preventDefault();if(!preview?.hasChanges||!data)return;const current=++generation.current;setBusy(true);setError('');
  try{await post('/api/admin/variants',{action:'bundle',id:variantId,expectedVersion:preview.expectedVersion,components:preview.components.map(({variantId,quantity})=>({variantId,quantity})),reason:reason.trim()});if(alive.current&&current===generation.current)onSaved();}
  catch(error){if(alive.current&&current===generation.current)setError((error as Error).message);}
  finally{if(alive.current&&current===generation.current)setBusy(false);}
 }
 if(loading)return <Busy/>;
 if(!data)return <><Status error={error}/><button type="button" className="button button-outline" onClick={reload}>Yeniden yükle</button></>;
 const editable=data.canWrite&&data.blockers.length===0;
 return <section className="form-stack" aria-label="Set bileşenleri düzenleyicisi">
  <p><strong>{data.productName}</strong> · {data.sku} · Sürüm {data.version}</p>
  <p className="notice">Fiziksel ürünleri ve her set için gereken adetleri seçin. Kaydetme ürünü yeniden incelemeye alır; ülke, belge ve taşıyıcı onayı yeniden değerlendirilir. Fiyat ve fiziksel stok bu ekranda değişmez.</p>
  {data.blockers.length>0&&<div className="feedback error" role="status"><p>Set tanımı şu anda değiştirilemiyor:</p><ul>{data.blockers.map(blocker=><li key={blocker.code}>{blocker.message}</li>)}</ul></div>}
  {!data.canWrite&&<p className="notice">Bu oturum set tanımını yalnız görüntüleyebilir.</p>}
  <div className="admin-table-wrap"><table className="admin-table"><caption>Seçili fiziksel bileşenler</caption><thead><tr><th>Ürün / stok kodu</th><th>Her sette adet</th><th>Satılabilir</th><th>İşlem</th></tr></thead><tbody>{selected.map(row=><tr key={row.variantId}><td>{row.productName}<br/><small>{row.sku} · {row.name}{row.lotTracking?' · Lot takipli':''}</small></td><td><label className="small">{row.sku} adedi<input aria-label={`${row.sku} adedi`} type="number" min="1" max="99" step="1" value={row.quantity} disabled={!editable||busy} onChange={event=>edit(selected.map(item=>item.variantId===row.variantId?{...item,quantity:Number(event.target.value)}:item))}/></label></td><td>{row.available}</td><td><button type="button" className="text-button" disabled={!editable||busy} onClick={()=>edit(selected.filter(item=>item.variantId!==row.variantId))}>Kaldır<span className="sr-only"> {row.sku}</span></button></td></tr>)}</tbody></table>{selected.length===0&&<p className="table-empty">Henüz bileşen seçilmedi.</p>}</div>
  {editable&&<>
   <form className="form-stack" onSubmit={event=>{event.preventDefault();setSearching(true);setQuery(search);setPage(1);setSearchRevision(value=>value+1);}}><label>Fiziksel ürün ara<input type="search" value={search} disabled={busy} onChange={event=>setSearch(event.target.value)} placeholder="Ürün adı veya stok kodu"/></label><button className="button button-outline" disabled={busy}>Bileşen ara</button></form>
   <Status error={searchError}/>{searching?<Busy/>:<><div className="admin-table-wrap"><table className="admin-table"><caption>Arama sonuçları · {candidates.total} fiziksel seçenek</caption><thead><tr><th>Ürün</th><th>Stok kodu</th><th>Satılabilir</th><th>İşlem</th></tr></thead><tbody>{candidates.rows.map(row=><tr key={row.id}><td>{row.productName}<br/><small>{row.name}{row.lotTracking?' · Lot takipli':''}</small></td><td>{row.sku}</td><td>{row.available}</td><td><button type="button" className="text-button" aria-label={`${row.sku} bileşenini ekle`} disabled={busy||selected.length>=20||selected.some(item=>item.variantId===row.id)} onClick={()=>edit([...selected,{variantId:row.id,quantity:1,sku:row.sku,productName:row.productName,name:row.name,active:row.active,lotTracking:row.lotTracking,available:row.available}])}>{selected.some(item=>item.variantId===row.id)?'Seçildi':'Ekle'}</button></td></tr>)}</tbody></table>{candidates.rows.length===0&&<p className="table-empty">Aramaya uygun fiziksel seçenek bulunamadı.</p>}</div><div className="pagination"><button type="button" className="button button-outline" disabled={page<=1||busy} onClick={()=>{setSearching(true);setPage(value=>value-1);}}>Önceki</button><span>{page}. sayfa</span><button type="button" className="button button-outline" disabled={page*25>=candidates.total||busy} onClick={()=>{setSearching(true);setPage(value=>value+1);}}>Sonraki</button></div></>}
   <button type="button" className="button button-outline" disabled={busy||selected.length===0||selected.some(row=>!Number.isInteger(row.quantity)||row.quantity<1||row.quantity>99)} onClick={requestPreview}>{busy?'İşleniyor…':'Değişikliği önizle'}</button>
  </>}
  {preview&&<section className="form-stack" aria-label="Set değişiklik önizlemesi"><h3>Değişiklik önizlemesi</h3><p>Mevcut stokla hazırlanabilir set: {preview.capacityBefore} → {preview.capacityAfter}. Önizleme stok ayırmaz; ödeme sırasında yeniden kontrol edilir.</p><div className="admin-table-wrap"><table className="admin-table"><thead><tr><th>Bileşen</th><th>Önceki adet</th><th>Yeni adet</th></tr></thead><tbody>{preview.changes.map(row=><tr key={row.variantId}><td>{row.productName} · {row.sku}</td><td>{row.beforeQuantity}</td><td>{row.afterQuantity}</td></tr>)}</tbody></table></div>{preview.hasChanges?<form className="form-stack" onSubmit={save}><label>Set değişikliği gerekçesi<textarea value={reason} onChange={event=>setReason(event.target.value)} required minLength={5} maxLength={500} disabled={busy}/></label><button className="button" disabled={busy||!editable||reason.trim().length<5}>{busy?'Kaydediliyor…':'Set tanımını kaydet'}</button></form>:<p>Seçilen bileşenlerde değişiklik bulunmuyor.</p>}</section>}
  <Status error={error}/><button type="button" className="text-button" onClick={reload} disabled={busy}>Güncel tanımı yükle ve taslağı sıfırla</button>
  {data.history.length>0&&<details><summary>Son 10 tanım değişikliği</summary><ol>{data.history.map(change=><li key={change.version}><strong>Sürüm {change.version}</strong> · {new Date(change.createdAt).toLocaleString('tr-TR')}<p>{change.reason}</p><span className="small">{change.before.length} bileşen → {change.after.length} bileşen</span></li>)}</ol></details>}
 </section>;
}
