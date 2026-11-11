# Yapılandırma ve güvenli giriş

Yerel değerler `npm run setup:local` ile Git dışında `.env.local` içine oluşturulur. Sırları sohbete, ekran görüntüsüne veya kaynak koda yazmayın. Canlı/staging değerleri ayrı secret manager üzerinden web, worker ve scheduler süreçlerine verilir. `.env.example` yalnız alan isimleri ve açıklamalar içerir. Ortam dosyasının bulunması sağlayıcı erişimini veya işletme kabulünü kanıtlamaz.

## Çalışan kodun kullandığı alanlar

| Tam alan adı | Kullanım yeri ve koşul |
| --- | --- |
| `APP_ENV` | development/test/staging/production ayrımı; örnek veri ve test ödeme kapıları. NODE_ENV ile aynı kavram değildir. |
| `APP_URL`, `BETTER_AUTH_URL` | Mutasyon origin kontrolü, güvenli dönüş URL'leri, oturum ve SEO taban adresi. |
| `APP_BIND_HOST` | `scripts/start.mjs` ağ bind adresi; varsayılan 127.0.0.1. |
| `DATABASE_URL`, `TEST_DATABASE_URL` | Uygulama ve izole test PostgreSQL veritabanları. Test komutları localhost ve *_test koruması kullanır. |
| `BETTER_AUTH_SECRET` | Better Auth, özel bağlantı HMAC'ı, ağ kota anahtarı ve e-posta iş payload şifrelemesi; ayrıca amaç ayrımlı HMAC ile beş dakikalık sepet toplamı tokenı ve özel ekonomik parmak izi. En az 32 karakter gerekir. Rotasyon oturumları, bağlantıları ve mevcut teklifleri etkiler; planlanmalıdır. |
| `PAYMENT_PROVIDER` | Yerelde test; kabul ve anahtar doğrulandığında stripe. Başka ad gerçek adaptör oluşturmaz. |
| `PAYMENT_WEBHOOK_SECRET` | Yalnız yerel test ödeme HMAC doğrulaması. Stripe imza sırrı ayrıdır. |
| `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET` | `src/server/providers/stripe.ts`, imzalı `/api/payments/stripe` ve worker. Testte sk_test; production'da sk_live ve kabul kapıları gerekir. |
| `STRIPE_BUSINESS_APPROVED`, `LIVE_SALES_ENABLED` | Teknik kapılar. Kanıtlı kategori/işletme kabulü ve bütün canlı koşullar sağlanmadan true yapılmaz. |
| `TRUSTED_PROXY_ENABLED`, `TRUSTED_CLIENT_IP_HEADER` | `src/server/abuse.ts`. Üretimde yalnız güvenilir proxy'nin yeniden yazdığı x-real-ip; origin private ağ/firewall ile sınırlandırılmalıdır. |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM` | Worker'ın hesap/sipariş e-postaları. Eksik bağlantı kalıcı işte yeniden deneme/hata üretir; gönderim başarı sayılmaz. Ürün adı konuya eklenmez. |
| `STORAGE_PROVIDER`, `STORAGE_LOCAL_PATH` | Local/S3 seçimi; local dosya alanı production'da reddedilir. |
| `S3_ENDPOINT`, `S3_REGION`, `S3_BUCKET`, `S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY` | Özel S3 uyumlu medya adaptörü; endpoint AWS için isteğe bağlıdır. Gerçek servis erişimi henüz test edilmedi. |
| `BACKUP_ENCRYPTION_KEY` | `scripts/backup-verify.ts`, 32 bayt hex AES-256-GCM anahtarı; arşivden ayrı saklanır. |
| `ADMIN_SETUP_EMAIL`, `ADMIN_SETUP_PASSWORD` | Yalnız yerel bootstrap hesabı. `.local/admin-access.txt` bilgisini paylaşmadan açın, /hesap > Güvenlik üzerinden MFA kurun. |
| `LOCAL_DB_PASSWORD`, `PG_BIN` | Yerel PostgreSQL/Compose ve pg_dump/pg_restore dizini. PG_BIN verilmezse proje içi native dizin kullanılır. |

`NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` mevcut hosted Checkout yönlendirmesinde kullanılmaz; ödeme formu/tokenizasyonu eklenirse yeniden değerlendirilir. `PAYMENT_API_KEY`, `PAYMENT_MERCHANT_ID`, `SHIPPING_PROVIDER`, `SHIPPING_API_KEY`, `INVOICE_PROVIDER`, `INVOICE_API_KEY` gelecekteki bağlantılar için ayrılmıştır; bugün bu alanları doldurmak gerçek API entegrasyonunu etkinleştirmez. Manuel sevk ve dış fatura referansı uygulama kayıtlarından yönetilir.

## İşletme ve onay alanları

MFA doğrulanmış yönetici `/yonetim/settings` üzerinden aşağıdaki tam anahtarları düzenleyebilir. Kredi satırındaki geliştirici adı bu alanlara otomatik taşınmaz.

| Anahtar | İçerik |
| --- | --- |
| `seller.name` | Belgelerle doğrulanan hukuki satıcı unvanı |
| `seller.taxNumber` | Gerçek vergi numarası |
| `seller.address` | Hukuki işletme adresi |
| `seller.supportEmail`, `seller.phone` | Gerçek destek kanalları |
| `seller.bankAccount` | Doğrulanmış işletme banka hesabı |
| `launch.backupVerified`, `launch.securityReviewed`, `launch.legalApproved`, `launch.catalogVerified`, `launch.providerApproved` | Boolean kapılar; onay için kanıt referansı açıklaması zorunludur. Tek başına hukuki/operasyonel kabul değildir. |

Veri sorumlusu ve SKU belge yönetimi panelde ayrı akışlardır; gerçek işletme/ürün kanıtları henüz sağlanmadı. Geliştiricinin resmî unvan belgesi, sağlayıcı ülkeleri ve tam saklama/aktarım envanteri açık kalır. Bunları satıcı alanından varsaymayın. Hukuk taslakları gerçek bilgiler ve yetkili inceleme olmadan yürürlüğe alınmaz. Ülke, vergi ve SKU belgeleri ayrıca kontrol edilir; genel kapıların doldurulması bu denetimleri kaldırmaz.

## Veri sorumlusu ve başvuru yapılandırması

`/yonetim/privacy` yönetici MFA ve yeniden parola doğrulaması ister. Yeni kimlik sürümü alanları: `legalName`, `address`, `email`, `evidence`, `approve`; bunlar `privacy_controllers` tablosuna yazılır, `seller.*` ayarlarını değiştirmez. Süre/saklama sürümü alanları: `country`, `unit`, `count`, `timeZone`, `source`, `evidence`, `retentionNote`, `approve`; `privacy_policies` tablosuna yazılır. Development/test kayıtları fixture olarak işaretlenir. Sohbete belge/kimlik/secret yapıştırmadan yetkili yerel panel veya gerçek secret yöneticisi kullanılır. Üretimde doğrulanmış veri sorumlusu ve etkin ülke kuralları olmadan canlı kapı açılmaz. Detay: [privacy-guide.md](privacy-guide.md).

## SKU, set, sosyal şablon ve ülke adresi

Bu modüller yeni gizli ortam değişkeni istemez. `/yonetim/compliance`: SKU/ülke/tür/ref/tarih ve yönetici incelemesi, ayrı ülke uygunluk kararı; `/yonetim/variants`: sürümlü set bileşen önizleme ve kayıt; `/yonetim/social`: dil/para/SKU/CMS kaydından indirme. Dışa yayın işlemi yoktur. Sosyal çıktı için aynı özel StorageProvider, sınırlandırılmış okuma ve hak kaynağı kullanılır. Resmî belge incelemesi yerine bir dosya adı veya ref girilmesi yeterli değildir.

`/yonetim/countries` içindeki adres profili `country`, `fields` (id, label.tr/en, required, minLength, maxLength, format), `reference` alanlarıyla yeni taslak sürüm oluşturur. `approve`/`archive` işlemi `id`, `reason`, mevcut yönetici `password` alanlarını ister. Parola kaydedilmez; tekrar doğrulanır. Profil onayı satış kapılarını açmaz. Üretimde fixture profil kullanılamaz. Ayrıntılı kullanım [address-guide.md](address-guide.md), [compliance-guide.md](compliance-guide.md), [bundle-guide.md](bundle-guide.md), [social-guide.md](social-guide.md).
