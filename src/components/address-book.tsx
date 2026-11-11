"use client";
/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/components/address-book.tsx
 * Açıklama   : Hesaba ait adresleri ülke kurallarıyla ekler, düzenler ve güvenle kaldırır.
 */
import {useEffect,useRef,useState} from 'react';
import {MapPin} from 'lucide-react';
import {api,post} from './api';
import {useStore} from './store-context';
import {AddressFields,useAddressProfile} from './address-fields';
import {Busy,Modal,Status} from './ui';
import type {AddressValues} from '@/shared/address-fields';
export type SavedAddress=AddressValues&{id:string;label:string;country:string};
export function AddressBook(){
 const {locale,t}=useStore(),en=locale==='en';
 const generation=useRef(0);
 const [rows,setRows]=useState<SavedAddress[]|null>(null),[editing,setEditing]=useState<SavedAddress|null|false>(false),[removing,setRemoving]=useState<SavedAddress|null>(null),[error,setError]=useState(''),[message,setMessage]=useState(''),[busy,setBusy]=useState(false),[writing,setWriting]=useState(false);
 useEffect(()=>{let active=true;const version=++generation.current;api<{addresses:SavedAddress[]}>('/api/addresses').then(data=>{if(active&&version===generation.current)setRows(data.addresses);}).catch(error=>{if(active&&version===generation.current)setError(error.message);});return()=>{active=false;};},[]);
 return <><div className="section-heading"><h2>{t('addressBook')}</h2><button className="button button-outline" disabled={writing||busy} onClick={()=>{setEditing(null);setError('');}}>{t('addAddress')}</button></div><Status error={error} message={message}/>{rows===null&&!error?<Busy/>:!rows?.length&&editing===false?<p className="muted">{t('noAddress')}</p>:null}
 <div className="address-grid">{rows?.map(address=><article className="card" key={address.id}><MapPin size={22}/><h3>{address.label}</h3><p>{address.fullName}</p><p style={{whiteSpace:'pre-wrap'}}>{address.line1}</p><p>{[address.district,address.city,address.region,address.postalCode].filter(Boolean).join(' · ')}</p><p>{address.country}</p><div className="summary-row"><button className="text-button" disabled={writing||busy} onClick={()=>{setEditing(address);setError('');}}>{en?'Edit':'Düzenle'}</button><button className="text-button" disabled={writing||busy} onClick={event=>{event.currentTarget.focus();setRemoving(address);setError('');}}>{en?'Remove':'Kaldır'}</button></div></article>)}</div>
 {editing!==false&&<AddressEditor key={editing?.id??'new'} address={editing} onBusyChange={setWriting} onCancel={()=>setEditing(false)} onSaved={addresses=>{generation.current++;setRows(addresses);setEditing(false);setMessage(t('saved'));}}/>}
 <Modal open={!!removing} onClose={()=>{if(!busy)setRemoving(null);}} title={en?'Remove saved address':'Kayıtlı adresi kaldır'}>{removing&&<form className="form-stack" onSubmit={async event=>{event.preventDefault();setBusy(true);setError('');try{const data=await post<{addresses:SavedAddress[]}>('/api/addresses',{action:'remove',id:removing.id});generation.current++;setRows(data.addresses);setRemoving(null);setMessage(t('saved'));}catch(error){setError((error as Error).message);}finally{setBusy(false);}}}><p>{removing.label}</p><p>{en?'This removes the address from your address book. Addresses already saved with orders remain unchanged.':'Bu kayıt adres defterinizden kaldırılır. Siparişlere kaydedilmiş adresler değişmez.'}</p><Status error={error}/><button className="button" disabled={busy}>{en?'Remove address':'Adresi kaldır'}</button></form>}</Modal></>;
}
function AddressEditor({address,onSaved,onCancel,onBusyChange}:{address:SavedAddress|null;onBusyChange:(value:boolean)=>void;onSaved:(addresses:SavedAddress[])=>void;onCancel:()=>void}){
 const {user,country:chosenCountry,locale,markets,marketsLoading,t}=useStore(),[country,setCountry]=useState(address?.country??chosenCountry),[busy,setBusy]=useState(false),[error,setError]=useState(''),en=locale==='en';
 const {profile,loading,error:profileError}=useAddressProfile(country);
 return <form className="card form-stack" aria-label={en?'Address details':'Adres bilgileri'} onSubmit={async event=>{event.preventDefault();if(!profile||loading||busy)return;setBusy(true);onBusyChange(true);setError('');try{const body=Object.fromEntries(new FormData(event.currentTarget));const result=await post<{addresses:SavedAddress[]}>('/api/addresses',{...body,country,...(address?{action:'update',id:address.id}:{action:'create'})});onSaved(result.addresses);}catch(error){setError((error as Error).message);}finally{setBusy(false);onBusyChange(false);}}}>
 <h3>{address?(en?'Edit address':'Adresi düzenle'):(en?'Add an address':'Yeni adres')}</h3><label>{en?'Address label':'Adres başlığı'}<input name="label" required minLength={1} maxLength={60} defaultValue={address?.label??''}/></label>
 <label>{t('country')}<select value={country} onChange={event=>setCountry(event.target.value)} disabled={marketsLoading}>{!markets.some(market=>market.countryCode===country)&&<option value={country} disabled>{country} — {en?'Delivery unavailable':'Teslimat açık değil'}</option>}{markets.map(market=><option key={market.countryCode} value={market.countryCode}>{market.name}</option>)}</select></label>
 <Status error={error||profileError}/>{loading?<Busy/>:profile&&<div className="form-grid" key={country+'|'+profile.version}><AddressFields profile={profile} values={address??{fullName:user?.name??''}}/></div>}
 <div className="summary-row"><button type="button" className="text-button" disabled={busy} onClick={onCancel}>{en?'Cancel':'Vazgeç'}</button><button className="button" disabled={busy||loading||!profile}>{busy?t('loading'):t('save')}</button></div>
 </form>;
}
