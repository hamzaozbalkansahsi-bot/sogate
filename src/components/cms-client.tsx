"use client";
/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/components/cms-client.tsx
 * Açıklama   : Yalnız yayımlanmış CMS alanlarını seçili dil ve fiyat listesiyle yükler.
 */
import {useEffect,useState} from 'react';
import {useStore} from './store-context';
import {api} from './api';
import type {PublicCMS} from '@/shared/cms-types';
export function usePublicCMS(collection?:string,page=1,initialContent?:PublicCMS){
 const {locale,currency}=useStore(),key=[locale,currency,collection??'',page].join('|');
 const [content,setContent]=useState<PublicCMS|null>(initialContent??null),[error,setError]=useState(''),[loaded,setLoaded]=useState(()=>initialContent?key:'');
 useEffect(()=>{let active=true;api<PublicCMS>(`/api/cms?locale=${locale}&currency=${currency}${collection?`&collection=${encodeURIComponent(collection)}&page=${page}`:''}`).then(data=>{if(active){setContent(data);setError('');}}).catch(e=>{if(active)setError(e.message);}).finally(()=>{if(active)setLoaded(key);});return()=>{active=false;};},[locale,currency,collection,page,key]);
 return {content:loaded===key?content:null,loading:loaded!==key,error};
}
