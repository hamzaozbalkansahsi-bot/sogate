# Tedarikçi aktarımı: araştırma ve erişim durumu

Kontrol: 14 Kasım 2026. Kullanıcının son kapsamı xShopum, Liona ve Sistina'nın kategori/ürünlerini almak ve uygun ürünleri markanın kurgusal yetişkin yüzü Liora ile sunmaktır. Bu belge bağlantının çalıştığını veya ürünlerin aktarıldığını göstermez. Başka işletmenin bayi hesabı kullanılmadı; başvuru, sözleşme, evrak gönderimi veya sipariş verilmedi.

| Tedarikçi | Resmî kaynakta görülen koşul | Gerçek erişim durumu |
| --- | --- | --- |
| xShopum | Aktif bayiler için XML/API ve stok-fiyat webhook hizmetleri ücretsiz; dropshipping paketlemesi20 TL+KDV, ürün/kargo ayrıca. Ürün ekleme/silme için XML; webhook yalnız stok/fiyat. | Bayi tokenı yok. Örnek XML adresine doğrudan yerel GET yaş bildirim sayfası verdi; normal form POST403 döndü, XML alınmış sayılmaz. API doküman adresi de403 verdi. Erişim kontrolü aşılmadı. |
| Liona | XML bayiliği için ücretsiz ifadesi ve aynı sayfada tek sefer ödeme başlığı var. Referans satış fiyatının altında satışa kısıt koyuyor. Sayfanın sonunda bayi girişlerinin bir süreliğine durdurulduğu yazıyor. | Onaylı hesap/özel XML yok. Yeni bayi kabulü, mevcut hesapların feed erişimi, güncel ücret ve görsel kullanımı yazılı teyit bekliyor. |
| Sistina | `.com.tr` toptan bayilik sayfasının arama önbelleği onaylı bayilere ücretsiz XML/Excel ve içerik/görsel aktarımı sunulduğunu belirtiyor. | İlgili sayfanın doğrudan güncel açılışı başarısız; `.com.tr` ve `.com` genel katalogları açıldı. Bunların bayi/feed kapsamı ve güncel koşulları teyit bekliyor. Özel XML yok. |

Kaynaklar: [xShopum bayilik](https://www.xshopum.com/sex-shop-bayilik/), [xShopum resmî XML rehberi](https://www.xshopum.com/xml-entegrasyon-rehberi/), [Liona XML bayilik](https://www.liona.com.tr/liona-ucretsiz-fantazi-ic-giyim-dropshipping-xml-bayilik), [Sistina toptan bayilik](https://sistinaicgiyim.com.tr/ic/toptan-bayilik), [Sistina genel katalog](https://www.sistinaicgiyim.com/). Tedarikçinin iade veya pazaryeri iddiası bizim hukuk/kanal kabulümüz sayılmaz.

## Güvenli bağlantı alanları

Git dışı kök `.env.local` içine boş `XSHOPUM_XML_URL`, `LIONA_XML_URL`, `SISTINA_XML_URL` alanları hazırlandı. Mevcut sırlar değiştirilmedi veya yazdırılmadı. Kişiye özel bağlantılar/tokenlar sohbet, Git veya tarayıcıya gönderilmez. Bu alanlar henüz PHP runtime'a bağlanmış bir feed adaptörü değildir; yalnız güvenli yapılandırma yeridir. Kullanıcıya onaylı bayi hesabı/bağlantı bulunup bulunmadığı soruldu.

## Uygulanacak veri sınırı ve kalan iş

Mevcut PHP CSV/XLSX önizleme/onay akışı çalışır; XML indirme, tedarikçiye özgü eşleme, kalıcı inceleme kuyruğu ve tam katalog aktarımı **tamamlanmadı**. xShopum rehberi gerçek SKU, başlık, kategori, görsel URL, stok ve maliyet/satış fiyatının ayrı alanlarını tarif ediyor; üretici bilgisi yalnız kaynakta varsa korunacak. Ürünleri yayımlamak ayrı onaydır. Eksik feed, eksik görsel hakkı ve örnek XML gerçek tedarikçi kataloğuna dönüştürülmez.

Sonraki adım: onaylı feed örneğini özel dosyadan al; HTTPS host izin listesi, özel ağ/DNS yönlendirme engeli, boyut/zaman sınırı, XXE/DTD reddi ve akışlı XML okuma testlerini yaz; SKU ve kategori eşlemesini inceleme kaydına al. Tedarikçi fiyatı maliyet/perakende ayrımıyla korunur; stok bildirimi zaman damgalı ayrı kayıttır, fiziksel depo bakiyesi değildir. Tekrar çekme özgün yerel ürün metnini veya geçmiş siparişi değiştirmemelidir. Gerçek kategori/ürün sayısı alınmadan sayım uydurulmaz.

## Liora ürün sunumu

Kanonik kimlik [brand-face-liora.md](brand-face-liora.md) ve `public/brand/liora/identity.json` içindedir. Liora yaklaşık30 yaşında kurgusal yetişkindir. Tedarikçi ürün fotoğrafını kullanma/değiştirme hakkı ve gerçek SKU referansı henüz doğrulanmadı; Liora üzerinde gerçek ürünü gösteren yeni varlık bu aşamada üretilmedi. İzinli referans geldiğinde yüz kimliği ve gerçek ürün ayrıntıları korunarak sunum hazırlanır; özgün ürün fotoğrafı ayrı tutulur, üretilmiş sunum gerçek model çekimi veya beden/uyum kanıtı gibi sunulmaz.
