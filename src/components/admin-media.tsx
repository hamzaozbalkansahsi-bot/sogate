"use client";
/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/components/admin-media.tsx
 * Açıklama   : Erişilebilir müşteri veya yönetim etkileşimini sunar.
 */
// Proje: SEXSOGATE | Geliştirici: PTYS Technoligess LLC | Tasarım: Hamza ÖZBALKAN
// Dosya: src/components/admin-media.tsx | Açıklama: Kullanım hakkı kaydıyla doğrulanmış görsel yükleme ve medya seçimi.
import Image from "next/image";
import {useEffect,useState} from "react";
import {Upload,Copy,ImageIcon} from "lucide-react";
import {api} from "./api";
import {Status} from "./ui";
interface Media{id:string;url:string;mimeType:string;sizeBytes:number;rightsReference:string;createdAt:string;}
export function AdminMedia(){const [rows,setRows]=useState<Media[]>([]),[revision,setRevision]=useState(0),[error,setError]=useState(""),[message,setMessage]=useState(""),[busy,setBusy]=useState(false);useEffect(()=>{api<{rows:Media[]}>("/api/admin/media").then(d=>setRows(d.rows)).catch(e=>setError(e.message));},[revision]);return <><div className="admin-tool-intro"><ImageIcon size={30}/><div><h2>Katalog görselleri</h2><p>Yalnız kullanım hakkına sahip olduğunuz ürün görsellerini yükleyin. Kaynak veya lisans belgesi referansını her görselle birlikte kaydedin.</p></div></div><form className="card form-stack" onSubmit={async e=>{e.preventDefault();setBusy(true);setError("");const form=e.currentTarget;try{const response=await fetch("/api/admin/media",{method:"POST",body:new FormData(form)});const result=await response.json();if(!response.ok)throw new Error(result.error||"Görsel yüklenemedi.");setMessage("Görsel kullanım hakkı kaydıyla yüklendi.");setRevision(v=>v+1);form.reset();}catch(e){setError((e as Error).message);}finally{setBusy(false);}}}><label>Ürün görseli (PNG, JPEG veya WebP; en fazla 8 MB)<input type="file" name="file" accept="image/png,image/jpeg,image/webp" required/></label><label>Kullanım hakkı / kaynak referansı<input name="rightsReference" minLength={5} maxLength={1000} required placeholder="Lisans belgesi veya yetkili kaynak kaydı"/></label><button className="button" disabled={busy}><Upload size={17}/>{busy?"Yükleniyor…":"Görseli yükle"}</button></form><Status error={error} message={message}/><div className="media-grid">{rows.map(row=><article className="card media-card" key={row.id}><div className="media-preview"><Image unoptimized src={row.url} alt="Yüklenen katalog görseli" width={400} height={300}/></div><p className="small">{row.rightsReference}</p><p className="small muted">{Math.ceil(row.sizeBytes/1024)} KB · {new Date(row.createdAt).toLocaleDateString("tr-TR")}</p><label className="sr-only" htmlFor={`media-${row.id}`}>Görsel yolu</label><input id={`media-${row.id}`} readOnly value={row.url}/><button className="text-button" onClick={async()=>{try{await navigator.clipboard.writeText(row.url);setMessage("Görsel adresi kopyalandı.");}catch{setError("Görsel yolunu alandan seçip kopyalayın.");}}}><Copy size={15}/>Görsel yolunu kopyala</button></article>)}</div>{rows.length===0&&<div className="table-empty"><ImageIcon size={28}/><h2>Henüz görsel yüklenmedi</h2><p>İlk yetkili ürün görselinizi ekleyerek başlayın.</p></div>}</>;}
