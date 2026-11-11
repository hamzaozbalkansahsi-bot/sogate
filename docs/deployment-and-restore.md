# Dağıtım, geri dönüş ve geri yükleme

Öncelik yerel çalışmadır. Docker Desktop bu makinede inference listener başlangıç hatası verdi; sistem ayarları değiştirilmedi. Native PostgreSQL18.6 resmî EDB Windows arşivinden yalnız .local altına kuruldu; Unicode Windows kurulum yolu için 8.3 yol kullanılıyor, kaynak ve veri UTF-8 kalıyor. Docker/CI dosyaları yazıldı fakat çalışan Docker motoru ve remote olmadan dağıtım yapılmış sayılamaz.

## Yerel başlatma
`npm ci`, `npm run setup:local`, `node scripts/native-postgres.mjs`, `npm run db:migrate`, `npm run db:seed`, `npx tsx --env-file=.env.local scripts/bootstrap-admin.ts`, `npm run dev`. Worker ayrı terminalde `npm run worker`; zamanlayıcı `npx tsx --env-file=.env.local scripts/scheduler.ts`. Native DB yalnız127.0.0.1:55432. Durdurmak için `node scripts/native-postgres.mjs --stop`; klasör silmeyin.

Docker kullanılabilirse .env.local içine rastgele LOCAL_DB_PASSWORD yazıp `docker compose --env-file .env.local up -d postgres` ile ayrı55433 portunda DB başlatın. Container DATABASE_URL compose tarafından postgres:5432'ye yönlendirilir. İlk migration ve yerel seed: `docker compose --env-file .env.local run --rm worker node --import tsx scripts/migrate.ts` ve aynı komutta scripts/seed.ts. Sonra web/worker/scheduler başlatın. Compose yalnız yerel kullanım içindir; APP_ENV development ve satış false sabittir. Üretim için bu ayarları körlemesine değiştirmeyin.

## Staging ve production sözleşmesi
Yerel optimize önizleme: önce `npm run build`, ardından `node --env-file=.env.local scripts/start.mjs --port 3004`. Standalone yardımcısı public, statik bundle ve PDF fontlarını çıktıya kopyalar. Varsayılan bind yalnız 127.0.0.1'dir. Uygun private ağda bind adresi `APP_BIND_HOST` ile belirlenir; port açılması güvenilir proxy kanıtı değildir. Yeniden build öncesinde önizlemeyi Ctrl+C ile durdurun; aksi halde Windows EBUSY dosya kilidi verebilir. Dev `.next-local`, build `.next` kullanır. `next start` yerine bu yardımcı veya Docker'ın `node server.js` komutu kullanılır.

Farklı DB, secret, bucket, SMTP ve Stripe hesap modu; fixture seed yok. Runtime secret manager dışında anahtar bulundurmayın. S3 bucket özel, gerekli hizmet yetkileri sınırlı, şifreli yedek anahtarı ayrı. Web/worker/scheduler aynı kaynak sürümünü kullanmalı. Origin uygulama portu yalnız güvenilir reverseproxy'ye açık olmalı; proxy istemci x-real-ip başlığını silip gerçek bağlantı adresini yeniden yazmalı. Güvenli TLS ve Secure cookie şart. Network kotası bu sınır doğrulanmadan üretimde fail-closed çalışır.

Gönderim öncesi launch-checklist.md tüm kanıtları doğrulanır; açık production yetkisi olmadan dağıtım yapılmaz. Kullanıcı tarafından satın alınmamış domain veya DNS varsayılmaz.

## Migration ve geri dönüş
1. DB ve medya yedeği alın; şifreli arşiv ve ayrı anahtar erişimini doğrulayın.
2. Aynı yedeği izole staging DB'ye geri yükleyin; kritik tablo sayıları/hash ve medya hash'lerini kontrol edin.
3. Migration SQL'ini inceleyin. Çalışmış dosyanın checksum'ını değiştirmeyin. Yıkıcı değişiklik bu görevde yetkili değildir.
4. Önce staging'e migration, sonra aynı commit web/worker/scheduler. Sağlık /api/health, katalog ve yetkili test akışı.
5. Uyumlu eski uygulama sürümüne geri dönüş için önceki image/commit saklayın. Geriye uyumsuz şemada otomatik down migration yerine test edilmiş restore/forward-fix planı kullanın. Gerçek sonradan gelen tahsilatları kaybetmemek için bakım ve mutabakat gerekir.

## Ölçülen yerel geri yükleme
`npm run backup:verify` yalnız yerel *_test DB'yi kabul eder. pg_dump custom arşivini AES256GCM ile şifreler, çözerek yeni `sexsogate_restore_<zaman>_test` DB'ye pg_restore yapar, 33 kritik tablonun sayısı ve deterministik hash'ini karşılaştırır. Son yerel koşu bu kapsamla geçti. Medya için markaya ait tek örnek PNG ayrı şifrelenip SHA-256 karşılaştırılır. Yalnız bu invocation'ın oluşturduğu restore DB temizlenir; kaynak DB korunur. Düz dump finally içinde kaldırılır. Kanıt `.local/owner-backup.log`, `.local/backups/last-restore-report.json` ve [kanonik test kaydı](test-evidence.md).

Bu yerel prova gerçek production yedekleme hizmeti, tüm medya bucket'ı, uzak saklama, erişim denetimi veya düzenli restore programının çalıştığını kanıtlamaz. RPO/RTO, saklama, coğrafya ve yetkiler işletmeyle belirlenmelidir. Anahtar kaybı geri yüklemeyi engeller; arşiv yanında saklamayın.

11 Kasım genişletmesi migration kayıtları, lot/bakiye/rezervasyon lotları, CMS/rehber sürümleri, gizlilik kayıtları, set/uygunluk/ülke adres profilleri ve satın alma/kabul/lot ilişkilerini fingerprint kapsamına aldı. `purchase_orders`, `purchase_items`, `purchase_receipts`, `purchase_receipt_items`, `purchase_receipt_lots` ve `lot_operations` bu 33 tabloya dahildir. Bazı kaynak tablolar boştur; eşleşen boş tablo, dolu gerçek müşteri/lot verisinin kurtarıldığı iddiası değildir. En son rapor her tablonun gerçek sayısını gösterir. Tam bucket medyası, uzak staging, üretim saklama/erişim, RPO/RTO veya felaket kurtarma tatbikatı bu yerel provada doğrulanmadı.

## Standalone paket sınırı

`npm run build` sonrasında `npm run verify:artifact` çalıştırın. Kontrol, kökte sır/yerel DB-yedek dizini, test/trace raporu veya belge dosyası paketlenmesini reddeder; sosyal şablonların gerekli font, lisans ve logosunun route trace listesinde olduğunu doğrular. `.env*`, `.local`, Git ve test kayıtları `outputFileTracingExcludes` ile web paketinden dışlanır. Sırlar çalışma anında ayrı secret yönetiminden sağlanır. Yerel medya runtime deposudur; build içine kopyalanmaz. Worker hedefi kendi kaynak/migration dosyalarını Dockerfile'dan alır ve ayrı ortam sırlarını kullanır.

Windows'ta build öncesi kendi çalışan standalone sürecinizi durdurun. Yerel test sunucusunun açık dosyalarını zorla silmeyin. Artefakt kontrolünün geçmesi uzak CI, registry, container veya staging dağıtım kanıtı değildir.
