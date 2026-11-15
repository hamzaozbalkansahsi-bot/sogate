# Native ürün yükleme ve yaş ekranı — 15 Kasım 2026

<!-- BEGIN NATIVE_FIRST_PAINT_DELIVERY_20261115 -->
## Güncel test durumu

Etkin sürüm554e78f543311a4d7e250b89. Önceki62d yalnız adaydı; güncel sürümde aynı veri incelemesi ile ilk HTML düzeltmesi birlikte yayımlandı. 2.194 yönetim kaydının468'i görünür,1.726'sı taslak. Mağazada6 ana+44 alt tanım,18 dolu alt kategori var; boş kategoriler çoğaltılmaz. Kaynak172 kategori özel inceleme ekranındadır. Yerel, önizleme ve yayın sonrası gerçek katalog kabulü geçti; 12 görünür medya orijinal hash ile ayrıca karşılaştırıldı.

Önceki bölümdeki ilk18 kapak, ilk aktarım aşamasının tarihsel sayısıdır. Güncel sayımlar `native-catalog-report.json` ve `native-deployment-report.json` içindedir. Katalog doluluğu bütün zorunlu olguların doğrulandığı veya gerçek tahsilatın açıldığı anlamına gelmez.
<!-- END NATIVE_FIRST_PAINT_DELIVERY_20261115 -->

Kullanıcı bu görevde mevcut üç tedarikçinin ürünlerinin yeni yönetim paneline, ürün alanları ve SEO bilgileriyle yüklenmesini istedi. İlk fiyat **kaynak kamu fiyatı ×1,30**, kuruşa en yakın yuvarlamadır; maliyet diye kaydedilmez. Sonraki aktarım yönetici fiyatını ezmez. Üç kaynağın fotoğraf/içerik yayın izni kullanıcı tarafından bu sohbet içinde beyan edildi; yazılı sözleşme varmış gibi kayıt tutulmaz. Bu beyan ürün sertifikası, ülke/taşıyıcı veya ödeme kabulü değildir.

1. Mevcut 2.194 kaynak kaydını orijinal yanıt hash'iyle oku; Liona form seçeneklerini ve Sistina kamu `pageSpecificData` alanlarını geri kazan. Gerçek barkod/SKU/üretici/belge yoksa uydurma; eksik ve uygulanmayan alanları ayır.
2. Hak beyanına dayanan orijinal fotoğrafları değiştirmeden, HTTPS/host/IP/boyut/MIME/hash denetimiyle özel yerel depoya al. Tekil içerik dosyaları ve ürün bağlantılarını kaydet. Bayi miktarı/fiziksel depo bakiyesi oluşturma.
3. Korunmuş NODENO kaynağını değiştirmeden, kaynak katalog ve alan sözleşmesini SEXOGATE derlemesine bağla. Ürün/SEO editörü aynı yönetim kabuğunu kullanır; kaynak, teknik bilgi, fiyat ve eksikler görünürdür. Yönetimden ürüne git bağlantısı bulunur.
4. MFA/CSRF/rol/idempotency denetimli yönetim aktarımı; sayım, mükerrer kayıt, %30 fiyat, Türkçe, SEO/API/SSR tutarlılığı, fotoğraf, tekrar aktarımda yönetici fiyatını koruma testleri.
5. 18+ ekranı: mevcut krem/bordo ve serif kimlik korunur. İmza hareketi, kapı kemerinin çizimi ve kadife ışık geçişidir; hafif giriş/çıkış, düğme geri bildirimi vardır. İlk çerçevede içerik okunur; azaltılmış hareket, klavye odağı ve misafir erişimi korunur. Yeni paket yerelde ve sunucu önizlemesinde doğrulanır.
6. Yalnız `/test` yayını; ana site ve diğer sohbetlerin kaynakları korunur. Gerçek tahsilat kapalıdır. Fotoğraf/ürün/satış onayları ayrı tutulur; teknik boşlukları doldurmak için yanlış bilgi üretilmez.

Gerçek sonuçlar bu belgeye ve `docs/progress.md` içine iş tamamlandıkça eklenir; bu plan tamamlanma kanıtı değildir.

## Yönetimde kullanım

`/test/yonetim` adresinde mevcut MFA hesabıyla girin. **Ürünler → Ürünleri yükle** kaynak sayısını ve ilk fiyat kuralını gösterir. **Yüklemeyi başlat** 40 kayıtlık işlemlerle ilerler; bağlantı kesilirse güvenle yeniden denenebilir. Aynı işlem ikinci kayıt/sürüm üretmez; başka yönetici yeniden yüklediğinde de mevcut fiyat ve içerik korunur. **Kaynak kategoriler** 172 kaynağı tedarikçisiyle aratır; müşteriye yönelik sınıflandırma altı SEXOGATE ana grubu ve ürün türlerine bağlı alt kategorilerden oluşur. Kaynak kategoriler bağımsız 172 yayımlanmış mağaza kategorisi gibi gösterilmez.

**Düzenle** içinde 11 dilin ad, açıklama ve SEO alanları; mağaza stok kodu, marka, gerçek barkod, üretici/menşe, malzeme, ölçü/beden/renk, pil, ağırlık/paket, içerik, bakım, güvenlik, garanti ve belge referansları yer alır. Kaynak URL, fiyat, gözlem zamanı, varyantlar, izin dayanağı ve bulunmayan bilgiler ayrıca salt okunur görünür. Kaynak kamu fiyatı alış maliyeti değildir. **Ürüne git** görünür ürünü vitrinde, taslağı yetkili özel önizlemede açar. Sipariş/tahsilat açmaz.

Kapak ve incelenen görsel sıraları sıfırdan başlar. `0` ilk karedir; `0,2` yalnız incelenmiş birinci/üçüncü kareyi gösterir. İncelenmemiş galeri müşteriye açılmaz. Bu alanı değiştirmek gerçek görsel incelemesi yerine geçmez. Görsel onayı, mali/hukuki/ülke/ödeme onayı değildir.

## Kaynak ve açık eksikler

- 2.194 gerçek kayıt; 2.151 fiyat,43 eksik fiyat;39 kayıtta kullanılabilir kaynak rasteri yok. Eksik fiyat ücretsiz ürün olarak yayımlanmaz. Fiziksel stok, maliyet veya tedarikçi miktarı üretilmedi.
- 9.498 ayrı kaynak URL'sinin9.494'ü kabul edildi;4 animasyonlu GIF desteklenen JPEG/PNG/WebP denetiminde dışarıda kaldı. Hash ile tekilleştirilmiş8.546 orijinal dosya vardır. Fotoğraflar Git'e girmez; özel depoda tutulur.
- İlk35 kapak görsel olarak incelendi. Son kullanıcı yönlendirmesiyle tedarikçi rozeti veya ambalaj içeriği ayrıca değerlendirme gerektiren6 kapak daha beklemeye alındı;18 temiz kapak test vitrini için seçildi. Diğer2.176 ürün yönetimde taslaktır; bütün galeriler incelendi denmez.
- Kullanıcı xShopum gizleme rozetlerinin kendi simgemizle değiştirilmesini istedi. Yerleşik görsel düzenleme aracı tek yetkili örnek denemesini `moderation_blocked/sexual` ile reddetti. Başka yöntemle aynı işlemi aşma denenmedi; bu rozet değişimi **tamamlanmadı**. Tedarikçiden temiz izinli orijinaller alınmalı. Gerçek üretici/model/ambalaj bilgileri değiştirilmez. Orijinal dosyalar korunur.
- Kaynakların hiçbirinde doğrulanmış barkod, üretici, menşe veya uygunluk belgesi bulunmadı. Bunlar açık eksik olarak kalır; alanın varlığı verinin doğrulandığı anlamına gelmez.
- Türkçe gerçek açıklama2.167 kayıtta geri kazanıldı;629 kayıtta varyant metadatası vardır. Diğer diller gerçek marka/kod/kategori/özelliklere dayanan otomatik özetlerdir; insan çevirisi veya tam hukuki dil onayı değildir. Ayrı varyant stok/satış kaydı oluşmadı.
- Slug alanı düzenlenebilir; özgün motorun ürün bağlantısı halen `?product=...&lang=...` biçimindedir. Teknik SEO testleri fiyat/schema/canonical tutarlılığını doğrular; indeks/sıralama garantisi değildir. Gerçek yorum/puan eklenmez.
- Kaynak taslaklarında aynı başlığı kullanan119 Türkçe SEO başlık grubu vardır; diğer10 dilin her birinde1 grup bulunur. Alanların doldurulması editoryal benzersizlik onayı değildir. Yinelenen başlıkların gerçek model/kodla ayrıştırılması ve insan çevirisi incelemesi açık iştir; toplu kaynak aktarımı sonradan düzenlenen başlığı ezmez. Sayımlar `docs/native-catalog-report.json` içindedir.
- Katalog büyüklüğünün yönetim yanıtı128 MB PHP sınırını aştığı yerel testte yakalandı; uygulama başlangıcında sınırlı256 MB bütçesi istenir. Hosting kabul testleri ayrıca zorunludur. Bellek bütçesini sınırsız yapma veya kontrol kapatma uygulanmadı.

18+ ekranındaki açıklama üst başlığı ve nokta son kullanıcı kararıyla kaldırıldı. İmza hareketi bordo perdelerin açılışı, kemer çizgisi ve kadife ışığıdır; ayrı hareket ayarı arayüzü bulunmaz. Yaş onayından sonra üyelik gerekmez. Son test/yayın durumu ilerleme kaydındadır.

## 15 Kasım — genişletilen test kataloğu

İlk18 kapağın ardından640 aday kapak ayrıca incelendi. Yeni aday62d6c5ffd241a891832db8f1,2.194 yönetim kaydından468 ürünü görünür yapıyor;1.726 taslak kalıyor. Altıana+44alt olmak üzere50 kategori tanımı,bu ürünlerle dolu18 alt kategori var. Boş alt kategoriler vitrinde gösterilmez. Kaynak172 kategori özel inceleme ekranında korunur. Yönetim yükleme penceresindeki “Vitrin450”,bu işlemde yeni yayımlanan sayısıdır;önceden yayımlanan18 ile toplam468 olur.

Yeni veri sürümü yüklenirken yalnız ilk kaydından beri değişmemiş sürüm1 taslağın kapak onayı yükseltilir. Elle değiştirilen fiyat/metin ve sonradan gizlenen ürünler korunur. Önizleme/aktif test aynı veritabanını kullanır; ürün yükleme veri değişikliğidir, uygulama giriş rollback'i bunu geri almaz. Önceki şifreli veritabanı yedeği ayrıca saklanır. Son kanıt/yayın durumu [katalog genişletme kaydı](native-catalog-expansion.md) ve [ilerlemededir](progress.md). Yeni adayın bütün tedarikçi,üretici,belge,galeri ve satış kabulü tamamlandı denmez.
