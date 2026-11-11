# SKU belgeleri, uygunluk ve teknik ürün bilgisi

Bu modül yerel geliştirme içindir. Gerçek ürün belgesi, üretici beyanı, ülke hukuku veya taşıyıcı kabulü yazılım tarafından oluşturulmaz. Canlı satış hazırlık kapıları ayrı kalır. `023_product_compliance.sql` uygulanmalıdır; son yerel optimize tarayıcı/build kabulü [test-evidence.md](test-evidence.md) içinde kaydedilmiştir.

## Yetki ve veri sınırı

`Ürün belgeleri / uygunluk` yönetim ekranının bileşeni `AdminCompliance`, API'si `/api/admin/compliance` ve iş kuralları `src/server/compliance.ts` içindedir. Yönetim menüsü ana admin kabuğuna bağlıdır. Her istekte gerçek oturum MFA'sı gerekir.

| İşlem | Katalog | Yönetici |
|---|---|---|
| SKU ara; belge ve özel referansları oku | Evet | Evet |
| Belge metadata'sı oluştur/düzenle, teknik bilgi ve kaynaklı iletişimi incelemeye sun | Evet | Evet |
| Belgeyi onayla veya onayını iptal et | Hayır | Evet |
| SKU + ülke uygunluğu ver/kaldır | Hayır | Evet |
| İşletme iletişimini yayımlanabilir olarak incele | Hayır | Evet |

Depo, müşteri hizmetleri, finans, pazarlama ve müşteri rolleri bu özel belge alanına erişemez. Liste/detayda maliyet, tedarikçi veya finansal alan dönmez. Belge referansı, kaynak notu, inceleme gerekçesi ve aktör kaydı müşteri DTO'suna girmez. API özel/no-store/noindex; mutasyon aynı origin, sınırlı JSON gövdesi ve sunucu şeması gerektirir.

## Belgeyi kaydetme ve inceleme

1. **Belge / stok kodu ara** alanından gerçek SKU'yu bulun; **SKU kaydını aç** seçin. Liste 25 kayıttır; durum filtresi inceleme bekleyen/incelenen/iptal edilen belgeli SKU'ları ayırır.
2. **Belge ekle** ile yapılandırılmış gerçek ülkeyi, üreticinin belge türünü, gerçek arşiv/doküman referansını, varsa gerçek model bilgisini ve geçerlilik tarihlerini girin. SKU bağlantısı seçili varyanttır; model, barkod, sertifika veya belge numarası üretilmez. Bitiş tarihi başlangıçtan önce olamaz.
3. Katalog kaydı inceleme bekler. Yönetici **Belgeyi incele** ile gerçek kaynağı kontrol eder, karar ve gerekçe verir. Yalnız bugün yürürlükte belge onaylanabilir. Eski `reviewed=true` kaydında aktör yoksa yeni onay gibi gösterilmez; yönetici yeniden incelemelidir.
4. **Ülke uygunluğunu yönet** ayrı yönetici kararıdır. Gerekli belge türü varsa aynı SKU/ülke/türde, referansı dolu, aktörü kayıtlı, incelenmiş ve tarihi geçerli belge aranır. Başka SKU veya ülkenin belgesi kabul edilmez. Tür alanının komutta bulunmaması mevcut gereksinimi korur; açıkça boşaltılması yeni yönetici kararıdır.
5. Yönetici ülke kararından sonra katalog/yönetici normal ürün yayın akışını kullanır. Yayın işlemi artık uygunluk satırı oluşturmaz veya onay vermez; önceki yönetici kararını doğrular. Set üst SKU'su ile her fiziksel bileşen ayrı denetlenir; bileşenin tek başına vitrinde yayımlanması gerekmez. Pasif/üretimde fixture bileşen ve iç içe set reddedilir.

Belge ekleme/değiştirme/inceleme/iptal ilgili uygunluğu ve yayını yeniden incelemeye alır; belge onayı tek başına ülke onayı veya yayın değildir. **Onayı iptal et** gerekçe ve aktörle kaydedilir, SKU/ülke ve ilişkili set uygunluğunu kapatır. Daha önce sepete alınmış ürün checkout'ta yeniden denetlenir. Ülkenin ödeme/yaş/vergi/taşıyıcı/hukuk kapıları bu kararlarla açılmaz.

Belge metadata değişiklikleri sürüm denetimlidir; eski sürüm 409 ile yeniden açma ister. Komut anahtarı aktör ve içerik hash'ine bağlıdır; aynı komut bir kez sonuç üretir. Farklı içerik veya aktör aynı anahtarı kullanamaz. Belge ve karar olayları uygulamada ekleme geçmişidir; genel audit ayrıntı hash'i saklar. Eski kayıtlara yeni onaylayan kişi uydurulmaz.

## Teknik bilgi ve üretici iletişimi

**Teknik bilgileri düzenle** formu üretici/menşe/malzeme, gerçek barkod, beden/renk/ölçü, gram ağırlık, paket U×G×Y ölçüleri, gerçek pil/güç türü ve kapasitesi, üretici içerik listesi, hijyen/sıvı işaretleri ile TR/EN garanti/bakım/uyarıları düzenler. Barkod metindir; baştaki sıfırlar korunur. Boş kapasite veya bilinmeyen varsayılan sıfır ağırlık müşteriye gerçek bir ölçü diye sunulmaz. Pil adından şarj, medikal malzeme, su geçirmezlik veya sertifika sonucu çıkarılmaz.

Teknik değişiklik ilgili belge/ülke/taşıyıcı onayını iptal eder; ürün incelemeye döner. Ürün düzeyi değişiklik aynı ürünün varyantlarını, varyant düzeyi değişiklik ilgili SKU'yu etkiler. Üretici/ürün bilgisi değişince önceki işletme iletişim incelemesi de kapanır. Fiyat/maliyet bu formun parçası değildir; sipariş anındaki snapshot yeniden yazılmaz.

**Üretici / sorumlu iletişimi** isteğe bağlı gerçek iş adresi/e-postası ve gerçek sorumlu ad/iş adresi/ülke bilgisidir. Kaynak referansı zorunludur ve özel kalır; yönetici incelemesine kadar iletişim müşteriye açılmaz. Kaynağı olmayan şirket, üretici, adres veya sorumlu kişi doldurulmaz. Bu kayıt hukuk uygunluğu veya yetki belgesi yerine geçmez.

Müşteri DTO'su açık alan listesinden oluşur: menşe, ilgili dilde garanti ve mevcut teknik varyant alanları; yalnız onaylı gerçek işletme iletişimi. Ürün detayında teknik bilgi, üretici/sorumlu, içerik, bakım, uyarı ve garanti bölümleri ayrı gösterilir. Bilinmeyen isteğe bağlı alan gizlenir. Maliyet, tedarikçi, keyfi attributes JSON'u, belge kaynağı ve özel inceleme notları döndürülmez.

## Dosya ve dış erişim durumu

Bu teslim **belge metadata'sı ve kontrollü dış sistem/arşiv referansı** yönetir. Raw PDF yükleme, dosya indirme yetkisi, doküman depolama, PDF önizleme veya malware tarama servisi yoktur. Referans düz metindir; sunucu URL'yi çekmez, tarayıcıda otomatik dış bağlantı açılmaz. Ürün görseli yüklemesi ayrı medya modülüdür ve belge yükleme sayılmaz. Gerçek üretici/arşiv erişimi ve içerik doğrulaması operasyon tarafından yapılmalıdır.

## Yerel doğrulama ve kalan kabul

- İlk birim RED: yeni compliance modülü bulunmadığından test yüklenemedi. Son hedefli birim: 7 compliance + 23 katalog + 7 kart = 37 kontrol.
- Eski publish bypass'ı veritabanında önce **Missing expected rejection** ile yakalandı; otomatik uygunluk yazımı kaldırıldıktan sonra reddedildi.
- `npx tsx --env-file=.env.local scripts/compliance-integration.ts`: yeni rastgele adlı yerel `*_test` DB, migration ve yalnız kendi fixture'ları; **18/18 kontrol**. Rol/MFA; aktörsüz eski onay; aynı SKU/ülke/tür ve tarih; stale sürüm; idempotency; teknik/taşıyıcı iptali; private/public alanlar; kaynaklı iletişim; production fixture reddi; gerçek checkout reddi ve üretici değişince eski iletişim onayının kapanmasını içerir.
- `npx vitest run tests/unit/compliance.test.ts tests/unit/catalog-display.test.ts tests/unit/catalog-filters.test.ts`: 37/37; hedefli kaynak ESLint ve strict typecheck çalıştırıldı. Bir testte SQL parametresinden sonra eksik boşluk düzeltildi. Unique DB ilk denemesinde genel seed guard'ı istisna vermiştir; guard gevşetilmeden yalnız açık test fixture'ları kuruldu. Yeni checkout adres kapısı için ayrı fixture ülke adres profili kullanıldı.
- `tests/e2e/compliance.spec.ts` Chromium/WebKit **2/2 PASS**: resmi auth fixture + gerçek HTTP MFA, katalog teknik/belge formu, yönetici ayrı kararları, Türkçe/İngilizce ürün detayı ve onayın iptali doğrulandı. 390/1440 ekranları `docs/screenshots/compliance-admin-{mobile,desktop}-{chromium,webkit}.png` altında üretildi. Son 94/94 optimize E2E (47+47), 246 birim/232 DB ve build kaydı [test-evidence.md](test-evidence.md) içindedir; güncel kapsam [progress.md](progress.md) ile birlikte değerlendirilir.

Gerçek sertifika/model eşleşmesinin içeriği, tüm ülkelerin hukuk kuralları, gerçek belge deposu/tarama, staging, gerçek cihaz ve bağımsız güvenlik kabulü açıktır. Ekran veya test verisi gerçek üretim onayı değildir.
