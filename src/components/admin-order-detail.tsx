"use client";
/**
 * Proje      : SEXSOGATE
 * Geliştirici: PTYS Technoligess LLC
 * Tasarım    : Hamza ÖZBALKAN
 * Dosya      : src/components/admin-order-detail.tsx
 * Açıklama   : Rol sınırlı sipariş ayrıntısı, SKU doğrulaması ve manuel paket sevki formu.
 */
import {useEffect,useRef,useState,type FormEvent} from 'react';
import {PackageCheck,ScanLine,Truck,RefreshCw} from 'lucide-react';
import {api,post} from './api';
import {Busy,Status} from './ui';
import {money} from '@/shared/contracts';
import {translatedStatus} from './checkout';
import type {StaffOrderDetail} from '@/server/commerce/staff-orders';

const taskLabels:Record<string,string>={picking:'Toplanıyor',packing:'Paketleme kontrolü',packed:'Sevke hazır',shipped:'Sevk edildi',cancelled:'İptal edildi'};
export function AdminOrderDetail({orderId,onChanged}:{orderId:string;onChanged:()=>void}){
 const [detail,setDetail]=useState<StaffOrderDetail|null>(null),[error,setError]=useState(''),[message,setMessage]=useState(''),[busy,setBusy]=useState(false),[revision,setRevision]=useState(0);
 const keys=useRef(new Map<string,string>());
 useEffect(()=>{let active=true;api<StaffOrderDetail>(`/api/admin/orders/${encodeURIComponent(orderId)}`).then(d=>{if(active){setDetail(d);setError('');}}).catch(e=>{if(active)setError(e.message);});return()=>{active=false;};},[orderId,revision]);
 async function command(scope:string,body:Record<string,unknown>){setBusy(true);setError('');setMessage('');const requestKey=keys.current.get(scope)??crypto.randomUUID();keys.current.set(scope,requestKey);try{await post(`/api/admin/orders/${encodeURIComponent(orderId)}`,{...body,requestKey});keys.current.delete(scope);setRevision(v=>v+1);onChanged();setMessage('Paket hazırlığı güncellendi.');}catch(e){setError((e as Error).message);}finally{setBusy(false);}}
 function create(e:FormEvent<HTMLFormElement>){e.preventDefault();const form=new FormData(e.currentTarget);const items=detail!.items.map(i=>({variantId:i.variantId,quantity:Number(form.get(`quantity_${i.variantId}`)??0)})).filter(i=>i.quantity>0);if(!items.length){setError('Paket için en az bir ürün adedi seçin.');return;}void command('create',{action:'create',items});}
 if(!detail)return <><Status error={error}/>{!error&&<Busy/>}</>;
 return <div className="form-stack"><div className="admin-tool-intro"><div><p className="eyebrow">SİPARİŞ</p><h3>{detail.number}</h3><p>{translatedStatus(detail.status,'tr')} · {translatedStatus(detail.paymentStatus,'tr')}</p></div><button className="icon-button" aria-label="Sipariş ayrıntısını yenile" onClick={()=>setRevision(v=>v+1)}><RefreshCw size={18}/></button></div><Status error={error} message={message}/>
  {detail.address&&<section className="card"><h3>Teslimat bilgileri</h3><p><strong>{detail.address.fullName}</strong><br/>{detail.address.line1}<br/>{[detail.address.district,detail.address.city,detail.address.region,detail.address.postalCode].filter(Boolean).join(' · ')} · {detail.address.country}<br/>{detail.address.phone}</p>{detail.contact&&<p>{detail.contact.email}</p>}</section>}
  {!detail.address&&detail.contact&&<p>{detail.contact.email}</p>}
  {detail.totals&&<section className="card"><h3>Tahsilat toplamı</h3><p>{money(detail.totals.totalMinor,detail.totals.currency)}</p>{detail.payment&&<p className="small">İade edilen: {money(detail.payment.refundedMinor,detail.totals.currency)} · {translatedStatus(detail.payment.status,'tr')}</p>}</section>}
  <div className="admin-table-wrap"><table className="admin-table"><caption>Sipariş ürünleri ve sevk adetleri</caption><thead><tr><th>Ürün / stok kodu</th><th>Sipariş</th><th>Sevk</th><th>Paket hazırlığı</th><th>Kalan</th></tr></thead><tbody>{detail.items.map(i=><tr key={i.variantId}><td><strong>{i.sku}</strong><br/>{i.name}</td><td>{i.quantity}</td><td>{i.shippedQuantity}</td><td>{i.assignedQuantity}</td><td>{i.remainingQuantity}</td></tr>)}</tbody></table></div>
  {detail.canFulfill&&detail.items.some(i=>i.remainingQuantity>i.assignedQuantity)&&<form className="card form-stack" onSubmit={create} aria-label="Paket hazırlığı"><h3><PackageCheck size={19}/> Yeni paket hazırlığı</h3><p className="small muted">Bu pakete ayıracağınız adetleri seçin. Diğer paketlere ayrılan ürünler kullanılamaz.</p><div className="form-grid">{detail.items.filter(i=>i.remainingQuantity>i.assignedQuantity).map(i=><label key={i.variantId}>Paket adedi · {i.sku}<input name={`quantity_${i.variantId}`} type="number" min="0" max={i.remainingQuantity-i.assignedQuantity} defaultValue="0" inputMode="numeric"/></label>)}</div><button className="button" disabled={busy}>Paket hazırlığı oluştur</button></form>}
  {detail.tasks.map((task,index)=><section className="card form-stack" key={task.id}><div><p className="eyebrow">PAKET {detail.tasks.length-index}</p><h3>{taskLabels[task.status]??task.status}</h3></div><ul>{task.items.map(i=>{const item=detail.items.find(x=>x.variantId===i.variantId);return <li key={i.variantId}><strong>{item?.sku}</strong> · {i.quantity} adet · Toplanan {i.pickedQuantity} · Paketlenen {i.packedQuantity}</li>;})}</ul>
   {detail.canFulfill&&['picking','packing'].includes(task.status)&&<form className="form-stack" aria-label={task.status==='picking'?'Toplama doğrulaması':'Paketleme doğrulaması'} onSubmit={e=>{e.preventDefault();const form=new FormData(e.currentTarget);void command(`scan:${task.id}`,{action:task.status==='picking'?'pick':'pack',taskId:task.id,code:String(form.get('code')),quantity:Number(form.get('quantity'))});}}><p className="small"><ScanLine size={16}/> {task.status==='picking'?'Ürünü toplarken barkodu okutun veya siparişteki stok kodunu girin.':'Paket içine yerleştirirken ürünü tekrar doğrulayın.'}</p><div className="form-grid"><label>Barkod veya stok kodu<input name="code" required autoComplete="off" maxLength={100}/></label><label>Doğrulanan adet<input name="quantity" type="number" min="1" max="999" defaultValue="1" required inputMode="numeric"/></label></div><button className="button" disabled={busy}>{task.status==='picking'?'Toplamayı doğrula':'Paketlemeyi doğrula'}</button></form>}
   {detail.canFulfill&&task.status==='packed'&&<form className="form-stack" aria-label="Manuel sevkiyat" onSubmit={e=>{e.preventDefault();const form=new FormData(e.currentTarget);void command(`ship:${task.id}`,{action:'ship',taskId:task.id,carrier:String(form.get('carrier')),trackingNumber:String(form.get('trackingNumber'))});}}><p className="small"><Truck size={16}/> Taşıyıcının gerçek belgesindeki bilgileri girin.</p><label>Gerçek taşıyıcı adı<input name="carrier" required minLength={2} maxLength={100}/></label><label>Gerçek takip numarası<input name="trackingNumber" required minLength={3} maxLength={100}/></label><p className="notice">Bu işlem sevkiyat kaydını oluşturur. Ücretli etiket veya taşıyıcı API işlemi yapmaz.</p><button className="button" disabled={busy}>Manuel sevki kaydet</button></form>}
   {['picking','packing','packed'].includes(task.status)&&detail.canFulfill&&<button className="text-button" disabled={busy} onClick={()=>void command(`cancel:${task.id}`,{action:'cancel',taskId:task.id})}>Paket hazırlığını iptal et</button>}
  </section>)}
  {detail.shipments.length>0&&<section className="card"><h3>Sevkiyat kayıtları</h3>{detail.shipments.map(s=><p key={s.id}><strong>{s.carrier}</strong><br/>{s.trackingNumber} · {translatedStatus(s.status,'tr')}</p>)}</section>}
 </div>;
}
