"use client";
/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/components/admin-taxes.tsx
 * Açıklama   : Erişilebilir müşteri veya yönetim etkileşimini sunar.
 */
// Proje: SEXSOGATE | Geliştirici: PTYS Technoligess LLC | Tasarım: Hamza ÖZBALKAN
// Dosya: src/components/admin-taxes.tsx | Açıklama: Kaynak ve yürürlük tarihleriyle ürün ve teslimat vergi kurallarını yönetir.
import {useEffect,useState} from "react";
import {Plus,FileCheck2} from "lucide-react";
import {api,post} from "./api";
import {Busy,Modal,Status} from "./ui";

interface TaxRule{id:string;kind:"product"|"shipping";country:string;productClass:string;rateBps:number;validFrom:string;validUntil:string|null;reference:string;}
const dates=new Intl.DateTimeFormat("tr-TR",{dateStyle:"short",timeStyle:"short"});
const percent=new Intl.NumberFormat("tr-TR",{maximumFractionDigits:2});
export function AdminTaxes(){
 const [rows,setRows]=useState<TaxRule[]>([]),[total,setTotal]=useState(0),[revision,setRevision]=useState(0),[loadedRevision,setLoadedRevision]=useState(-1),[open,setOpen]=useState(false),[kind,setKind]=useState<"product"|"shipping">("product"),[error,setError]=useState(""),[message,setMessage]=useState(""),[busy,setBusy]=useState(false);
 useEffect(()=>{let active=true;api<{rows:TaxRule[];total:number}>("/api/admin/taxes").then(data=>{if(active){setRows(data.rows);setTotal(data.total);setError("");}}).catch(e=>{if(active)setError(e.message);}).finally(()=>{if(active)setLoadedRevision(revision);});return()=>{active=false;};},[revision]);
 async function submit(event:React.FormEvent<HTMLFormElement>){
  event.preventDefault();setError("");setBusy(true);const values=Object.fromEntries(new FormData(event.currentTarget));
  const [whole,fraction=""]=String(values.percent).split(".");
  const rateBps=Number(whole)*100+Number((fraction+"00").slice(0,2));
  try{
   await post("/api/admin/taxes",{kind,country:String(values.country).toUpperCase(),rateBps,effectiveFrom:new Date(String(values.effectiveFrom)).toISOString(),...(values.effectiveUntil?{effectiveUntil:new Date(String(values.effectiveUntil)).toISOString()}:{}),...(kind==="product"?{productClass:String(values.productClass)}:{}),reference:String(values.reference)});
   setOpen(false);setRevision(value=>value+1);setMessage("Vergi kuralı kaynak bilgisiyle kaydedildi.");
  }catch(e){setError((e as Error).message);}finally{setBusy(false);}
 }
 return <><div className="admin-tool-intro"><FileCheck2 size={29}/><div><h2>Kaynağı doğrulanmış vergi kuralları</h2><p>Ürün ve teslimat vergisini ayrı yönetin. Oran, ülke, ürün sınıfı ve yürürlük tarihlerini yalnız yetkili mali incelemeyle doğrulanmış bir kaynağa dayanarak girin. Bu ekran hukuki veya mali görüş yerine geçmez.</p></div><button className="button" onClick={()=>{setKind("product");setError("");setOpen(true);}}><Plus size={16}/>Yeni vergi kuralı</button></div>
 <p className="notice">Uygulanabilir vergi kuralı eksikse sipariş oluşturulmaz. Yeni kuralın mevcut bir yürürlük dönemiyle çakışmasına izin verilmez. Sıfır oran da doğrulanmış kaynak ve onay gerektirir.</p><Status error={error} message={message}/>
 {loadedRevision!==revision?<Busy/>:<><p className="small muted">{total} vergi kuralı</p><div className="admin-table-wrap"><table className="admin-table"><thead><tr><th>Vergi türü</th><th>Ülke</th><th>Ürün sınıfı</th><th>Oran</th><th>Yürürlük başlangıcı</th><th>Yürürlük sonu</th><th>Kaynak / onay referansı</th></tr></thead><tbody>{rows.map(row=><tr key={row.id}><td>{row.kind==="shipping"?"Teslimat vergisi":"Ürün vergisi"}</td><td>{row.country}</td><td>{row.kind==="shipping"?"Teslimat":row.productClass==="*"?"Tüm ürün sınıfları":row.productClass}</td><td>%{percent.format(Number(row.rateBps)/100)}</td><td>{dates.format(new Date(row.validFrom))}</td><td>{row.validUntil?dates.format(new Date(row.validUntil)):"Bitiş tanımlanmadı"}</td><td>{row.reference}</td></tr>)}</tbody></table>{rows.length===0&&<div className="table-empty"><h2>Henüz vergi kuralı tanımlanmadı</h2><p>Doğrulanmış oran ve yürürlük kaynağını hazırladıktan sonra ilk kuralı ekleyin.</p></div>}</div></>}
 <Modal open={open} onClose={()=>setOpen(false)} title="Yeni vergi kuralı"><form className="form-stack" onSubmit={submit}><label>Vergi türü<select value={kind} onChange={e=>setKind(e.target.value as "product"|"shipping")}><option value="product">Ürün vergisi</option><option value="shipping">Teslimat vergisi</option></select></label><div className="form-grid"><label>Ülke kodu<input name="country" required minLength={2} maxLength={2} pattern="[A-Za-z]{2}" defaultValue="TR" autoCapitalize="characters"/></label><label>Vergi oranı (%)<input name="percent" type="number" required min="0" max="100" step="0.01" inputMode="decimal"/></label></div>{kind==="product"&&<label>Ürün sınıfı<input name="productClass" required defaultValue="*" maxLength={100}/><span className="small muted">Tüm sınıfları kapsayan onaylı bir kural için * kullanılır. Belirli sınıf onayını genel kurala dönüştürmeyin.</span></label>}<label>Yürürlük başlangıcı<input type="datetime-local" name="effectiveFrom" required/></label><label>Yürürlük sonu (isteğe bağlı)<input type="datetime-local" name="effectiveUntil"/></label><label>Doğrulanmış kaynak ve onay referansı<textarea name="reference" required minLength={10} maxLength={2000} rows={4} placeholder="Kaynak belgesi, yetkili inceleme ve karar referansı"/></label><Status error={error}/><button className="button" disabled={busy}>{busy?"Kaydediliyor…":"Vergi kuralını kaydet"}</button></form></Modal></>;
}
