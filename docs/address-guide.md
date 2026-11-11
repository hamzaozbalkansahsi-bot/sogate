# Ülke adres profilleri

Ülke kaydı ve o ülkenin adres alanları ayrı yönetilir. Adres profilinin onaylanması ülkeyi satışa açmaz; ürün, yaş, ödeme, taşıyıcı, vergi ve hukuk uygunluğu ayrıca gerekir. Bu ekran ülkelerin güncel adresleme kurallarını kendiliğinden doğrulamaz; kaynak incelemesini işletme yapmalıdır.

## Yönetim adımları

1. Yönetici hesabıyla giriş yapın ve mevcut oturumun iki adımlı doğrulamasını tamamlayın. **Ülkeler ve satış → Ülkelere göre adres alanları** bölümünü açın. Diğer roller profil değiştiremez.
2. Ülke adı veya iki harfli koduyla arayın. Liste, sunucudaki kayıtlı ülkelerden 25 sonuç verir. Ülke profillerini seçili ülkeye göre filtreleyebilir, sürümleri 25 kayıtlık sayfalarda inceleyebilirsiniz. Yeni bir ülke önce ülke yönetiminde kaydedilmelidir.
3. **Yeni adres profili** ile teslimat ülkesini seçin. Ad soyad, açık adres ve şehir her profilde bulunur ve zorunludur. Telefon, il/bölge, ilçe/semt ve posta kodu alanlarını kaynak kuralına göre ekleyin.
4. Her kullanılan alan için Türkçe ve İngilizce etiketi, zorunluluğu, alt/üst karakter sınırını ve biçimi belirleyin. Sistem tavanları ad soyad 120, telefon 30, açık adres 300, şehir/bölge/ilçe 100, posta kodu 20 karakterdir. Ad soyad/şehir en az 2, açık adres en az 5 karakter ister. Bunlar teknik sınırdır; ülkeye özgü gerçek sınır ve zorunluluğu siz belirlemelisiniz. Boşluk/kısa çizgi harf-rakam biçiminde kullanılabilir; yalnız rakam biçimi farklıdır.
5. **Adres alanı önizlemesi** bölümünde Türkçe/İngilizce etiketleri ve düzeni kontrol edin. Önizleme boştur; gerçek adres toplamaz veya kaydetmez. Kaynak ve inceleme referansını girerek **Taslağı kaydet** düğmesine basın. Taslak müşteriye uygulanmaz.
6. Sürüm kartından **İncele** ile tüm etiketleri, sınırları, kaynağı ve önizlemeyi okuyun. **Sürümü onayla** adımında gerekçeyi ve yönetici parolanızı yeniden girin. İşlem başarılıysa ülkenin önceki onaylı sürümü arşivlenir; yeni sürüm adres doğrulamasında kullanılır.
7. Değişiklik için **Yeni sürüme kopyala** kullanın. Eski sürüm yerinde düzenlenmez. Yeni kaynak referansı girin ve yeni taslağı ayrıca inceleyip onaylayın. Sürüm numarasını sunucu verir.
8. **Sürümü arşivle** gerekçe ve parola doğrulaması ister. Eski sürüm kendiliğinden açılmaz. Kullanılabilir onaylı profil kalmazsa yeni adres ve sipariş işlemleri engellenebilir. Yeni bir onaylı sürüm hazırlamadan mevcut sürümü arşivlemeyi operasyon açısından değerlendirin.

Yerel geliştirme/test ortamında oluşturulan profiller örnek olarak işaretlenir. Production bu sürümleri kullanmaz; canlı kuralları onaylı kaynaklarla ilgili ortamda ayrıca oluşturmak gerekir. Geliştirici/tasarımcı bilgileri satıcı veya adres kuralını onaylayan işletme yerine geçmez.

## Teknik bağlantı

- `GET /api/admin/address-profiles?country=TR&page=1&q=...`: `country/page` sürüm listesini filtreler; `q` yalnız ülke seçeneklerinde arar. Yanıt: `rows`, `total`, `page`, `countries`. Arayüz bu ayrımı korur.
- `POST /api/admin/address-profiles`: `create` için `country`, izinli `fields`, `reference`; `approve/archive` için `id`, `reason`, `password`. İzinli yedi alan dışında alan, tekrar eden tanım, eksik temel alan, geçersiz etiket veya uzunluk reddedilir.
- API yönetici + gerçek oturum MFA, mutasyonda aynı origin ve kritik işlemde yeniden parola doğrulaması uygular. Her sürüm ve olay veritabanında tutulur. Arayüz parolayı component state’inde saklamaz; form kapanınca giriş alanı kaldırılır.
- `country_address_profiles` değişmez alan tanımlarını; `country_address_events` inceleme/onay/arşiv kaydını tutar. Önceki sipariş/adres bağlantıları sürüm kimliğiyle korunur. Bu ekran ülke satış onaylarını değiştirmez.
- Form hata özeti odağa alınır, hatalı alanlara bağlantı verir; kullanılan alanların hataları etiketlerle ilişkilidir. Dialog ortak klavye/odak/Escape davranışını kullanır. Country ve sayfa istekleri değişince eski yanıt ekrana uygulanmaz.

## Doğrulama durumu

`src/components/admin-address-profiles.tsx`, **Ülkeler ve satış** ekranına bağlıdır; stil `admin-address-profiles.module.css` içindedir. Alan şeması ve onaylı profil doğrulaması sunucuda ortak kaynaktan yürür.

`tests/e2e/address-profiles.spec.ts` Chromium/WebKit **2/2 PASS**: yalnız kendi kapalı yerel test ülkesinde gerçek yönetici/MFA, dört alanlı taslak, İngilizce önizleme, gerçek parola onayı, arşiv, yeni sürüme kopyalama ve ülke satışının kapalı kaldığının DB kontrolü doğrulandı. Mevcut TR profili değiştirilmedi; oluşturulan ülke/sürümler kendi kimlikleriyle temizlendi. Açık dialogda Axe ve 390/1440 px taşma kontrolleri geçti; `docs/screenshots/address-profile-{chromium,webkit}-{desktop,mobile}.png` dosyaları üretildi. Son tam koşu **94/94 E2E (47+47)**; 246 birim/232 DB ve build kanıtı [test-evidence.md](test-evidence.md), kapsam [progress.md](progress.md) içindedir. Gerçek cihaz ve yabancı adres operasyonunun saha kabulü açık kalır.

Hedefli kaynak doğrulama komutları:

```powershell
npx eslint src/components/admin-address-profiles.tsx tests/e2e/address-profiles.spec.ts
npm run typecheck
```

11 Kasım 2026: hedefli ESLint **0 hata/uyarı**, tam proje strict typecheck ve son optimize toplu tarayıcı koşusu **PASS**. Güncel kabul kaydı [test-evidence.md](test-evidence.md) içindedir; yerel sonuç gerçek adres/ülke operasyon onayı yerine geçmez.
