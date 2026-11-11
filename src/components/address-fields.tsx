"use client";
/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/components/address-fields.tsx
 * Açıklama   : Onaylı ülke profilinin erişilebilir adres alanlarını özgün metinle gösterir.
 */
import {useEffect,useState} from 'react';
import {api} from './api';
import {useStore} from './store-context';
import type {AddressProfile,AddressValues} from '@/shared/address-fields';
export function useAddressProfile(country:string){
 const {locale}=useStore(),key=country+'|'+locale;
 const [record,setRecord]=useState<{key:string;profile?:AddressProfile;error?:string}|null>(null);
 useEffect(()=>{let active=true;api<AddressProfile>('/api/address-profile?country='+encodeURIComponent(country)).then(profile=>{if(active)setRecord({key,profile});}).catch(error=>{if(active)setRecord({key,error:error.message});});return()=>{active=false;};},[country,locale,key]);
 return {profile:record?.key===key?record.profile:null,error:record?.key===key?record.error:'',loading:record?.key!==key};
}
const autocomplete={fullName:'name',phone:'tel',line1:'street-address',city:'address-level2',region:'address-level1',district:'address-level3',postalCode:'postal-code'};
export function AddressFields({profile,values={}}:{profile:AddressProfile;values?:AddressValues}){
 const {locale}=useStore();
 return <>{profile.fields.map(field=>{
  const common={name:field.id,required:field.required,minLength:field.minLength,maxLength:field.maxLength,autoComplete:autocomplete[field.id],defaultValue:values[field.id]??''};
  return <label key={field.id} className={field.id==='line1'?'span-2':undefined}>{field.label[locale]}{field.id==='line1'?<textarea {...common} rows={3}/>:<input {...common} type={field.id==='phone'?'tel':'text'} inputMode={field.format==='digits'?'numeric':undefined} pattern={field.format==='digits'?'[\\p{Nd}]+':undefined}/>}</label>;
 })}</>;
}
