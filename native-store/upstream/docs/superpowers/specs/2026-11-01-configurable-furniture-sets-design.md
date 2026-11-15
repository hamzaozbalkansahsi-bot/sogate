# Adet ve takım satışları

Kullanıcı düzeltmesi önceki paket/palet satış birimini geçersiz kılar. Toplu alım bağımsız SKU için adet, kaynaktan takım olarak satılan SKU için takım ve kullanıcının seçtiği parçalardan oluşan özel takım için takım adedidir. Koli/palet bilgisi ürün adedine dönüştürülmez. Önceki taleplerin anlık kayıtları değişmez.

## Katalog ve takım tanımı

Kaynak: `output/pdf/NODENO_Mobilya_Katalogu_2026_Paylasim_Son.pdf` (86 sayfa), mevcut doğrulanmış katalog ve kimlik eşlemesi. PDF sayfaları 3–15,17–22 üzerinde aynı isimli oda sayfaları birleşerek 17 seçilebilir oda koleksiyonu olur. Her üye SKU, PDF'deki kodla birebir eşleşmelidir; benzer isim veya fotoğrafla eklenmez. Güncel katalogda olmayan 5 benzersiz kod raporlanır ve sepete/teklife eklenemez. Takımın tüm üyelerinin alınması şart değildir. Renk alternatifleri yalnız aynı oda grubunda PDF ile doğrulanmış SKU'lardan seçilir. Gövde ve kapak gibi modüller açıkça ayrı parça olarak belirtilir; komple dolap sanılmaz. Kaynakta tek SKU ile satılan masa/tabure seti ve köşe takımları parçalanmaz.

`data/furniture-sets.json`: şema1, PDF SHA256, kaynak katalog/kimlik SHA256, kaynak sayfa/kod kanıtları, 17 grup, eksik kodlar ve 3 sabit takım SKU'su. Build fail-closed doğrular; halka açık `catalog.furnitureSets` ve SKU `saleUnit` alanları üretilir. Orijinal SKU, renk/ölçü/fiyat/görsel değişmez.

## Müşteri arayüzü

`?page=sets&set=<id>&lang=...` herkese açık, gerçek fotoğraflarla oda kartları ve seçilebilir parça listesi. Her model için dahil et/çıkar, adet ve doğrulanmış renk/SKU seçimi; tüm parçalar opsiyonel fakat en az bir seçim zorunlu. İlk durumda hiçbir parça zorla eklenmez. `1 dolap + 2 komodin + 1 şifonyer + 0 baza/karyola` gerçek kabul senaryosudur. Aktif seçimlerin kalem ve toplam fiyatı gerçek güncel perakende SKU fiyatlarıyla hesaplanır. Takım indirimi/stoğu/SKU'su uydurulmaz.

Türkiye perakende: seçilen parçalar tek atomik işlemle mevcut sepete gerçek SKU kalemleri olarak eklenir. Aynı SKU mevcutsa miktar birleştirilir. Sonuç kalem başına99 veya toplam100 kalemi aşarsa, fiyat bilinmiyorsa, SKU gizlenmişse veya hesap geçişi sürüyorsa tüm işlem reddedilir; kısmi ekleme/kırpma yapılmaz. Girişli hesabın mevcut güvenli eşitleme kuyruğu korunur. Sepette parçalar ayrı ayrı düzenlenebilir.

Toptan mod: seçilen takım içeriği teklif listesine eklenir; aynı içerik için takım sayısı belirlenir. On takım için `1 dolap+2 komodin+1 şifonyer` sunucuda `10 dolap+20 komodin+10 şifonyer` olarak açılır. Bağımsız ürünler aynı talepte adet olarak yer alabilir. Talep anındaki içeriği ve miktarları özel kayıt saklar. Toptan fiyatlar bilinmediği için perakende tutar toptan fiyatmış gibi sunulmaz. Gönderim boyunca tüm teklif düzenlemeleri kilitlenir.

## Sunucu, SEO ve yönetim

RFQ yeni gövdesi `items:[{productId,unit:piece|set,quantity}]`, `sets:[{setId,quantity,components:[{productId,quantity}]}]`, `compositionVersion`. Sunucu güncel katalog üyeliği, sürüm, tekrar/taşma, devre dışı SKU ve satış birimini doğrular. Tüm kaynak SKU miktarları hesaplanır; doğrulanmış toptan kademeler varsa toplam gerçek SKU miktarına göre değerlendirilir. Farklı para birimleri veya eksik fiyatlar yanlış toplam üretmez. Başlık/ad/fiyat istemciden alınmaz. Önceki idempotency ve özel kayıt sınırları korunur. Paket/palet POST artık satış işlemi için kabul edilmez; eski talepler okunabilir kalır.

Yönetim kayıtları yeni adet/takım dilini ve takım alt kalemlerini gösterir; hazırlanan içerikler katalog kaynak kaydı olarak korunur. Koli/palet geçmiş ayarları sevkiyat bilgisi olarak korunabilir; satış miktarı bu alanlardan türetilmez. Firma/ödeme, fiscal ve sosyal sağlayıcı açılışları beklemeye devam eder.

Dört dil TR/EN/RU/AR, RTL, NODENO marka varlıkları ve erişilebilir mobil/masaüstü. Yeni takım sayfası SSR/canonical/hreflang/site haritası ile yayımlanır; özel seçim ve toptan mod kopyaları tek canonical'a bağlanır. Teklif odaklı içerik adet/takım diline güncellenir; hayali takım Offer fiyatı oluşturulmaz.

## Kabul ve yetki

Gerçek PDF eşleşmesi, saf JS hesaplama/atomik sepet, PHP RFQ açılımı/sürüm/mahremiyet testleri RED→GREEN; gerçek paket Chromium ve Windows WebKit mobil/masaüstü/RTL, misafir/girişli sepet ve örnek 10 takım. Tek taze son inceleme, kaynak/dağıtım testleri, zorunlu medya kapısı, yedekli Turhost yayını ve canlı kabul. Üretimde test müşterisi/talep/ödeme oluşturulmaz. Yardım ve yönetim/SEO kılavuzları birlikte güncellenir. Kullanıcının geliştirme ve otomatik yayın yetkisi sürer; tekrar izin döngüsü başlatılmaz.
