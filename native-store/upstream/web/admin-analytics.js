import {formatDate} from './date-time.js?v=20261113-r2';
export function analyticsMarkup(d,products,esc){
 const n=value=>Number.isFinite(Number(value))?Number(value):0,fmt=value=>new Intl.NumberFormat('tr-TR').format(n(value)),totals={visit:0,view:0,cart:0,favorite:0};
 for(const row of d.data||[])totals[row.event]=(totals[row.event]||0)+n(row.count);
 const sourceLabels={unknown:'Bilinmiyor',direct:'Doğrudan',search:'Arama motoru',social:'Sosyal medya',referral:'Yönlendiren site',campaign:'Kampanya bağlantısı'},deviceLabels={mobile:'Mobil',desktop:'Masaüstü'};
 const countries=new Intl.DisplayNames(['tr'],{type:'region'}),country=value=>value?countries.of(value)||value:'Bilinmiyor';
 const card=(label,value,note)=>`<article class="stat"><span class="stat-label">${esc(label)}</span><strong>${fmt(value)}</strong><small>${esc(note)}</small></article>`;
 const table=(title,headers,rows)=>`<section class="panel"><h2>${esc(title)}</h2>${rows.length?`<div class="table-scroll"><table><thead><tr>${headers.map(v=>`<th>${esc(v)}</th>`).join('')}</tr></thead><tbody>${rows.map(row=>`<tr>${row.map(v=>`<td>${esc(v)}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`:'<p class="muted">Bu dönem için ölçüm bulunmuyor.</p>'}</section>`;
 const summary=d.summary||{},byProduct=new Map(products.map(p=>[p.id,p])),daily=new Map();
 for(const row of d.daily||[]){const values=daily.get(row.day)||{visit:0,view:0,cart:0,favorite:0};values[row.event]=n(row.count);daily.set(row.day,values);}
 const stats=card('Tekil ziyaretçi',summary.visitors,'Ölçülen etkileşimlerden')+card('Ziyaretçi / gün',summary.visitorDays,'Gün başına bir ziyaret kaydı')+card('Ürün görüntüleme',totals.view,'Ürün ve ziyaretçi başına günde bir')+card('Sepete ekleme',totals.cart,'Ölçülen etkileşimler')+card('Favoriye ekleme',totals.favorite,'Ölçülen etkileşimler')+card('Ölçülen hareket',summary.events,'Yalnız analiz izni verenler');
 return `<div class="stats">${stats}</div>`+
 table('Ülkeler / seçilen pazar',['Ülke','Tekil ziyaretçi','Hareket'],(d.countries||[]).map(r=>[country(r.market),fmt(r.visitors),fmt(r.events)]))+
 table('Geliş kaynakları',['Kanal','Kaynak site','Tekil ziyaretçi','Hareket'],(d.sources||[]).map(r=>[sourceLabels[r.source]||'Bilinmiyor',r.referrer||'—',fmt(r.visitors),fmt(r.events)]))+
 table('Cihazlar',['Cihaz','Tekil ziyaretçi','Hareket'],(d.devices||[]).map(r=>[deviceLabels[r.device]||r.device,fmt(r.visitors),fmt(r.events)]))+
 table('Kullanılan diller',['Dil','Tekil ziyaretçi','Hareket'],(d.languages||[]).map(r=>[r.locale.toUpperCase(),fmt(r.visitors),fmt(r.events)]))+
 table('Günlük hareketler',['Gün (UTC)','Ziyaretçi / gün','Ürün görüntüleme','Sepet','Favori'],[...daily].slice(0,30).map(([day,r])=>[formatDate(new Date(Number(day)*86400000).toISOString().slice(0,10)),fmt(r.visit),fmt(r.view),fmt(r.cart),fmt(r.favorite)]))+
 `<section class="panel"><h2>Yaş aralığı ve cinsiyet</h2><p class="muted">Bu bilgiler henüz toplanmıyor. Tarayıcı ziyaretinden yaş veya cinsiyet tahmin edilmez. İzinli profil bilgisi ya da bu ölçümleri sağlayan bağlı bir analiz kaynağı gerekir.</p></section>`+
 table('Ürün bazında',['Ürün','İşlem','Adet'],(d.products||[]).map(r=>[byProduct.get(r.product_id)?.name||r.product_id,({view:'Ürün görüntüleme',cart:'Sepete ekleme',favorite:'Favoriye ekleme'})[r.event]||r.event,fmt(r.count)]));
}
