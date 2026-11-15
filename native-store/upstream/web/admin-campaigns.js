export function campaignStatus(row,now=Math.floor(Date.now()/1000)){
 if(!row.publishedVersion||!row.publishedData)return {label:'Yayın bekliyor',kind:'draft',status:'draft',detail:'Kaydedildi; mağazadaki fiyat henüz değişmedi.'};
 const c=row.publishedData;
 let status=!c.enabled?'disabled':now<c.startsAt?'scheduled':now>=c.endsAt?'expired':row.activity?.status==='no_eligible_products'?'no_eligible_products':'active';
 const labels={disabled:'Devre dışı',scheduled:'Başlangıcı bekliyor',expired:'Sona erdi',no_eligible_products:'Uygulanacak ürün yok',active:'Aktif'};
 const descriptions={disabled:'Yayınlandı; etkinleştirme seçeneği kapalı.',scheduled:'Yayınlandı; başlangıç tarihinde otomatik uygulanacak.',expired:'Bitiş tarihi geçti; kampanya indirimi uygulanmıyor.',no_eligible_products:'Seçilen ürünlerin görünürlüğünü ve fiyatlarını kontrol edin.',active:`${row.activity?.appliedProducts??0} üründe bu kampanyanın oranı uygulanıyor.${row.activity?.overriddenProducts?' '+row.activity.overriddenProducts+' üründe daha yüksek oranlı başka bir kampanya geçerli.':''}`};
 const pending=row.version>row.publishedVersion;
 return {label:labels[status]+(pending?' · değişiklik bekliyor':''),status,kind:status==='active'?'live':status==='no_eligible_products'?'failed':'draft',detail:descriptions[status]+(pending?' Son düzenlemeler henüz yayınlanmadı.':'')};
}
export function campaignPreview(data,products){
 const percent=Number(data.percent);if(!Number.isInteger(percent)||percent<1||percent>90)return [];
 const ids=new Set(String(data.productIds||'').split(',').map(v=>v.trim()));
 return products.filter(p=>ids.has(p.id)&&p.visible&&Number.isSafeInteger(p.campaignBaseMinor)&&p.campaignBaseMinor>0).map(p=>({id:p.id,baseMinor:p.campaignBaseMinor,priceMinor:Math.floor((p.campaignBaseMinor*(100-percent)+50)/100)}));
}
