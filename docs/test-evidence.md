# Test kanıtı — 11 Kasım 2026

## GitHub aktarımı ve CI durumu

Kullanıcının açık talebiyle kaynaklar `38d603d7ffab9df926d6ad0b6c4d9215b5b7e249` commit'inde GitHub main dalına yüklendi. Uzak 421 blob ile yerel commit'in bütün blob SHA'ları eşleşti; eksik/ekstra/yasak yerel dosya yok. Eski README güncel SEXSOGATE içeriğiyle değiştirildi, Git geçmişi yedeklendi ve korundu.

[42985339650 numaralı CI](https://github.com/hamzaozbalkansahsi-bot/sogate/actions/runs/42985339650), GitHub hesabının faturalandırma kilidi nedeniyle runner veya test adımları başlamadan sonlandı. Uzak test PASS/FAIL kanıtı oluşmadı; aşağıdaki sonuçlar gerçek yerel koşuya aittir. Uygulama iş kuralları değişmedi; AGENTS.md push yetkisi ve Git sonuç belgeleri güncellendi. Kontroller veya workflow kapatılmadı. Tam kayıt [git-workflow.md](git-workflow.md).

## Güncel tam kontrol noktası — 09:19 İstanbul

Ödeme öncesi teklif, oturum yarış koruması ve 025 lotlu PO kabulü dahil kaynak/test/varlık/config **320 dosya** manifesti SHA256 `53849dbe305cd6c0466dfded498e4de0c6f1e4265cdede1344720fe53866a0bc` (`.local/owner-snapshot.json`). Son genel koşudan sonra 320 dosya baytı tekrar karşılaştırıldı; değişiklik yok. Belgeler bu manifest dışında güncellenir. Şema 001–006, 010–025; uygulanmış migration değiştirilmedi. Bu yerel bayt izi commit, canlı kabul veya hukuk sertifikası değildir.

| Komut | Gerçek sonuç / yerel log |
| --- | --- |
| `npm run lint` | PASS, sıfır uyarı; `.local/owner-lint.log` |
| `npm run typecheck` | PASS, strict; `.local/owner-typecheck.log` |
| `npm test` | **246/246**, 29 dosya PASS; `.local/owner-unit.log` |
| `npm run test:integration` | 15 PASS; `.local/owner-integration.log` |
| `npx tsx --env-file=.env.local scripts/import-template-integration.ts` | 14 PASS; `.local/owner-import-template-integration.log` |
| `npx tsx --env-file=.env.local scripts/legal-drafts-integration.ts` | 6 PASS; `.local/owner-legal-drafts-integration.log` |
| `npx tsx --env-file=.env.local scripts/security-boundary-integration.ts` | 10 PASS; `.local/owner-security-boundary-integration.log` |
| `npx tsx --env-file=.env.local scripts/operations-integration.ts` | 16 PASS; `.local/owner-operations-integration.log` |
| `npx tsx --env-file=.env.local scripts/shipping-tax-integration.ts` | 11 PASS; `.local/owner-shipping-tax-integration.log` |
| `npx tsx --env-file=.env.local scripts/staff-orders-integration.ts` | 11 PASS; `.local/owner-staff-orders-integration.log` |
| `npx tsx --env-file=.env.local scripts/seo-integration.ts` | 8 PASS; `.local/owner-seo-integration.log` |
| `npx tsx --env-file=.env.local scripts/turkish-locale-integration.ts` | 5 PASS; `.local/owner-turkish-locale-integration.log` |
| `npx tsx --env-file=.env.local scripts/lot-integration.ts` | 11 PASS; `.local/owner-lot-integration.log` |
| `npx tsx --env-file=.env.local scripts/cms-integration.ts` | 16 PASS; `.local/owner-cms-integration.log` |
| `npx tsx --env-file=.env.local scripts/privacy-integration.ts` | 13 PASS; `.local/owner-privacy-integration.log` |
| `npx tsx --env-file=.env.local scripts/catalog-filters-integration.ts` | 14 PASS; `.local/owner-catalog-filters-integration.log` |
| `npx tsx --env-file=.env.local scripts/bundle-integration.ts` | 16 PASS; `.local/owner-bundle-integration.log` |
| `npx tsx --env-file=.env.local scripts/compliance-integration.ts` | 18 PASS; `.local/owner-compliance-integration.log` |
| `npx tsx --env-file=.env.local scripts/social-integration.ts` | 13 PASS; `.local/owner-social-integration.log` |
| `npx tsx --env-file=.env.local scripts/address-integration.ts` | 8 PASS; `.local/owner-address-integration.log` |
| `npx tsx --env-file=.env.local scripts/quote-integration.ts` | 13 PASS; `.local/owner-quote-integration.log` |
| `npx tsx --env-file=.env.local scripts/purchase-lots-integration.ts` | 14 PASS; `.local/owner-purchase-lots-integration.log` |
| PostgreSQL toplamı | **19 komutta 232 kontrol PASS**; korunan çekirdek test DB'si ve diğer benzersiz izole *_test DB'leri |
| `npm run build` | PASS, uyarı yok; `.local/owner-build.log` |
| `npm run verify:artifact` | PASS; özel geliştirme/test dosyaları dışarıda, sosyal font/lisans/logo runtime trace'de |
| `npm run test:e2e` | **94/94 PASS**, Chromium 47 + WebKit 47, tek worker/retry 0, 4,7 dakika; `.local/owner-e2e-94.log` |
| `npm run backup:verify` | **33 tablo** count/hash ve ayrı örnek medya SHA256 PASS; `.local/owner-backup.log`, `.local/backups/last-restore-report.json` |
| `npm audit --audit-level=low` | Sıfır bilinen açık, tüm dependency ağacı; yeni paket kurulmadı |
| `GET http://127.0.0.1:3000/api/health` | HTTP200, `{"status":"ok","sales":"closed"}` |

### İnceleme sonrası ek RED→GREEN

- Yeni sepet okuma/yazma ve checkout sahibi aynı DB snapshot/kilidi içinde doğrulanır. Anonim ön kontrolden sonra gerçek üye birleşmesi, okuma önceki snapshot, yazma önceki kilit ve iki üyenin tek sepeti talep etmesi ayrı sınanır. Eski kod anonim okuma ve aynı tutarlı teklif checkout'unda `Missing expected rejection` verdi; boundary10/quote13 yeni kaynakta geçti.
- Başka sepete birleşip anonimleşen eski sepetin `orders.user_id` alanı ayrıca denetlenir. Anonim/B eski sipariş tekrarını alamaz, doğru A aynı iş girdisiyle sürdürür. Ayrılmış üye siparişi için de gerçek ayrı RED yakalandı. Sipariş takip/PDF/JSON'un mevcut sahiplik sözleşmesi korunur.
- Ortak istemci helper'ının ilk RED koşusu 15 testte 8 PASS/7 FAIL verdi (`.local/api-response-red.log` ve `.local/api-response-red.json`); son 23 API testi nihai 29 dosya/246 PASS içindedir. Bozuk 2xx JSON başarıya dönüşmez; mal kabulünün yeni/idempotent sonuç sözleşmesi doğrulanır, abort korunur, ham ağ ayrıntısı sızmaz. Eski `{id, duplicate: true}` desteklenir.
- Genel94 içindeki PO senaryosu gerçek200 sunucu yazımından sonra ağ/kesikJSON/eksikID/eksiksonuç yanıtlarını bozar. Beş deneme aynı anahtar/gövdeyi taşır, yalnız bir kabul ve ilk stok miktarı kalır; son doğrulanmış duplicate sonucu UI'yi kapatır. Test sayısı94 değişmedi, mevcut senaryonun kapsamı genişledi.
- Hukuk bağlantıları müşteri ekranında “Aydınlatma metnini oku / Satış koşullarını oku” ve İngilizce karşılıklarıyla gösterilir. Dört CSS kaynak başlığı kullanıcı standardına eşitlendi; CSS kuralları değişmedi.

### Önceki davranışların bu sürümde regresyonu

- Teklif `REPEATABLE READ READ ONLY` içinde fiyat/kargo/vergi/kupon toplamını ve sahipliği aynı snapshot'ta okur; finansal yazım yapmaz. Anonim→üye sepet birleşmesinin iki gerçek DB sırası, başka sahibin reddi, yeni toplamın onayı ve eski teklifin sıfır finansal yazımla reddi test edildi. Teklif değişse/bitse bile aynı iş girdisinin pending/ödenmiş idempotent tekrarı ikinci sipariş üretmez.
- Geciken checkout/test ödeme yanıtı A ekranından çıkıp B ile girişten sonra yönlendirme veya özel içerik üretmez. Eski `/api/session` yanıtının yeni hesabı geri çevirdiği gerçek eski-build RED (`.local/session-refresh-red.log`) sonrasında oturum/sepet request-generation ve AbortController koruması GREEN oldu. İptal edilen HTTP isteği sunucuda oluşmuş siparişi geri almış sayılmaz.
- 025 karma normal/lotlu PO kabulü atomiktir: yanlış toplam/fazla kabul rollback, kısmi kalan, kaynak/karantina/expiry/recall, aynı anahtarla ağ belirsizliği sonrası tekrar, farklı aktör/gövde çatışması, doğrudan kabul anahtar çakışması ve maliyetsiz kaynak yetkisi test edildi. Yeni kaynak tablosu gerçek restore karşılaştırmasına dahildir.
- İlk quote genel koşusu 80 PASS/10 FAIL (`.local/quote-e2e-90.log`): erişilebilir seçici/kanonik e-posta, gerçek checkbox genişlik taşması ve yalnız özel test ülkesinin eksik vergi kuralı düzeltildi. Sonraki 88 PASS/2 FAIL giriş HTTP429 penceresiydi. Resmî 0..60 saniye retry başlığı bir kez beklenir; uygulamanın 5/60 saniye giriş kotası kapatılmadı, sahte IP veya kota sıfırlama yoktur. Hedef WebKit koşusunda gerçek 50,3 saniye bekleme ve başarı görüldü. Son09:19 sürümünün94 testi de retriesiz geçti.

### Görsel ve operasyon sınırı

Yeni checkout toplamı, adres profili ve lotlu kabul/kaynak ekranları Chromium/WebKit'te 390/1440 px görüntülendi; ilgili Axe ve yatay taşma kontrolleri geçti. Ana sayfa 360/390/430/768/1440 px genel E2E kapsamındadır. [Görsel rapor](visual-review.md) görüntüleri ve gerçek inceleme kapsamını açıklar. Klavye odağı görünür tutulur; ekran görüntüsü için odak gizlenmez.

Geri yükleme gerçek yeni yerel izole DB'ye yapılmıştır; bazı tabloların kaynak test DB'sinde boş olması ve yalnız ayrı örnek medya kontrolü nedeniyle tüm medya/staging/üretim RPO-RTO kabulü değildir. Gerçek iOS cihazı, ekran okuyucu, saha p75 performansı, Stripe sandbox/işletme kabulü, SMTP teslimi, S3, taşıyıcı/e-Fatura/kanal API'si, remote CI ve staging çalıştırılmadı. Canlı satış kapalıdır. Aşağıdaki sayılar önceki sürümlerin tarihsel kanıtıdır; güncel toplam yerine kullanılmaz.

## Son tam kontrol noktası — 08:46 İstanbul

Ödeme öncesi teklif, oturum yarış koruması ve 025 lotlu PO kabulü dahil kaynak/test/varlık/config **319 dosya** manifesti SHA256 `b48946568ebd671eea767b647f660f6c90c3a5f733e8ca14ee2b6232affebd46` (`.local/po-snapshot-final.json`). Son genel koşudan sonra 319 dosya baytı tekrar karşılaştırıldı; değişiklik yok. Belgeler bu manifest dışında güncellenir. Şema 001–006, 010–025; uygulanmış migration değiştirilmedi. Bu yerel bayt izi commit, canlı kabul veya hukuk sertifikası değildir.

| Komut | Gerçek sonuç / yerel log |
| --- | --- |
| `npm run lint` | PASS, sıfır uyarı; `.local/po-lint.log` |
| `npm run typecheck` | PASS, strict; `.local/po-typecheck.log` |
| `npm test` | **223/223**, 28 dosya PASS; `.local/po-unit.log` |
| `npm run test:integration` | 15 PASS; `.local/po-integration.log` |
| `npx tsx --env-file=.env.local scripts/import-template-integration.ts` | 14 PASS; `.local/po-import-template-integration.log` |
| `npx tsx --env-file=.env.local scripts/legal-drafts-integration.ts` | 6 PASS; `.local/po-legal-drafts-integration.log` |
| `npx tsx --env-file=.env.local scripts/security-boundary-integration.ts` | 5 PASS; `.local/po-security-boundary-integration.log` |
| `npx tsx --env-file=.env.local scripts/operations-integration.ts` | 16 PASS; `.local/po-operations-integration.log` |
| `npx tsx --env-file=.env.local scripts/shipping-tax-integration.ts` | 11 PASS; `.local/po-shipping-tax-integration.log` |
| `npx tsx --env-file=.env.local scripts/staff-orders-integration.ts` | 11 PASS; `.local/po-staff-orders-integration.log` |
| `npx tsx --env-file=.env.local scripts/seo-integration.ts` | 8 PASS; `.local/po-seo-integration.log` |
| `npx tsx --env-file=.env.local scripts/turkish-locale-integration.ts` | 5 PASS; `.local/po-turkish-locale-integration.log` |
| `npx tsx --env-file=.env.local scripts/lot-integration.ts` | 11 PASS; `.local/po-lot-integration.log` |
| `npx tsx --env-file=.env.local scripts/cms-integration.ts` | 16 PASS; `.local/po-cms-integration.log` |
| `npx tsx --env-file=.env.local scripts/privacy-integration.ts` | 13 PASS; `.local/po-privacy-integration.log` |
| `npx tsx --env-file=.env.local scripts/catalog-filters-integration.ts` | 14 PASS; `.local/po-catalog-filters-integration.log` |
| `npx tsx --env-file=.env.local scripts/bundle-integration.ts` | 16 PASS; `.local/po-bundle-integration.log` |
| `npx tsx --env-file=.env.local scripts/compliance-integration.ts` | 18 PASS; `.local/po-compliance-integration.log` |
| `npx tsx --env-file=.env.local scripts/social-integration.ts` | 13 PASS; `.local/po-social-integration.log` |
| `npx tsx --env-file=.env.local scripts/address-integration.ts` | 8 PASS; `.local/po-address-integration.log` |
| `npx tsx --env-file=.env.local scripts/quote-integration.ts` | 10 PASS; `.local/po-quote-integration.log` |
| `npx tsx --env-file=.env.local scripts/purchase-lots-integration.ts` | 14 PASS; `.local/po-purchase-lots-integration.log` |
| PostgreSQL toplamı | **19 komutta 224 kontrol PASS**; korunan çekirdek test DB'si ve diğer benzersiz izole *_test DB'leri |
| `npm run build` | PASS, uyarı yok; `.local/po-build-final.log` |
| `npm run verify:artifact` | PASS; özel geliştirme/test dosyaları dışarıda, sosyal font/lisans/logo runtime trace'de |
| `npx playwright test tests/e2e/account-privacy.spec.ts tests/e2e/checkout-quote.spec.ts tests/e2e/session-refresh-race.spec.ts tests/e2e/purchase-lots.spec.ts` | İlgili hedef 14/14 PASS, 1,7 dakika; `.local/po-ui-targeted.log`; son tam koşu aşağıdadır |
| `npm run test:e2e` | **94/94 PASS**, Chromium 47 + WebKit 47, tek worker/retry 0, 4,8 dakika; `.local/po-e2e-94-final.log` |
| `npm run backup:verify` | **33 tablo** count/hash ve ayrı örnek medya SHA256 PASS; `.local/po-backup.log`, `.local/backups/last-restore-report.json` |
| `npm audit --audit-level=low` | Sıfır bilinen açık, tüm dependency ağacı; yeni paket kurulmadı |
| `GET http://127.0.0.1:3000/api/health` | HTTP200, `{"status":"ok","sales":"closed"}` |

### Bu sürümün regresyonları

- Teklif `REPEATABLE READ READ ONLY` içinde fiyat/kargo/vergi/kupon toplamını ve sahipliği aynı snapshot'ta okur; finansal yazım yapmaz. Anonim→üye sepet birleşmesinin iki gerçek DB sırası, başka sahibin reddi, yeni toplamın onayı ve eski teklifin sıfır finansal yazımla reddi test edildi. Teklif değişse/bitse bile aynı iş girdisinin pending/ödenmiş idempotent tekrarı ikinci sipariş üretmez.
- Geciken checkout/test ödeme yanıtı A ekranından çıkıp B ile girişten sonra yönlendirme veya özel içerik üretmez. Eski `/api/session` yanıtının yeni hesabı geri çevirdiği gerçek eski-build RED (`.local/session-refresh-red.log`) sonrasında oturum/sepet request-generation ve AbortController koruması GREEN oldu. İptal edilen HTTP isteği sunucuda oluşmuş siparişi geri almış sayılmaz.
- 025 karma normal/lotlu PO kabulü atomiktir: yanlış toplam/fazla kabul rollback, kısmi kalan, kaynak/karantina/expiry/recall, aynı anahtarla ağ belirsizliği sonrası tekrar, farklı aktör/gövde çatışması, doğrudan kabul anahtar çakışması ve maliyetsiz kaynak yetkisi test edildi. Yeni kaynak tablosu gerçek restore karşılaştırmasına dahildir.
- İlk quote genel koşusu 80 PASS/10 FAIL (`.local/quote-e2e-90.log`): erişilebilir seçici/kanonik e-posta, gerçek checkbox genişlik taşması ve yalnız özel test ülkesinin eksik vergi kuralı düzeltildi. Sonraki 88 PASS/2 FAIL giriş HTTP429 penceresiydi. Resmî 0..60 saniye retry başlığı bir kez beklenir; uygulamanın 5/60 saniye giriş kotası kapatılmadı, sahte IP veya kota sıfırlama yoktur. Hedef WebKit koşusunda gerçek 50,3 saniye bekleme ve başarı görüldü. Son 94 test retriesiz geçti.

### Görsel ve operasyon sınırı

Yeni checkout toplamı, adres profili ve lotlu kabul/kaynak ekranları Chromium/WebKit'te 390/1440 px görüntülendi; ilgili Axe ve yatay taşma kontrolleri geçti. Ana sayfa 360/390/430/768/1440 px genel E2E kapsamındadır. [Görsel rapor](visual-review.md) görüntüleri ve gerçek inceleme kapsamını açıklar. Klavye odağı görünür tutulur; ekran görüntüsü için odak gizlenmez.

Geri yükleme gerçek yeni yerel izole DB'ye yapılmıştır; bazı tabloların kaynak test DB'sinde boş olması ve yalnız ayrı örnek medya kontrolü nedeniyle tüm medya/staging/üretim RPO-RTO kabulü değildir. Gerçek iOS cihazı, ekran okuyucu, saha p75 performansı, Stripe sandbox/işletme kabulü, SMTP teslimi, S3, taşıyıcı/e-Fatura/kanal API'si, remote CI ve staging çalıştırılmadı. Canlı satış kapalıdır. Aşağıdaki sayılar önceki sürümlerin tarihsel kanıtıdır; güncel toplam yerine kullanılmaz.

## 07:34 İstanbul modül kontrol noktası

Kaynak/test/varlık300 dosya manifesti SHA256 `62119dfd8a3f8e529007a63c42e10d764a6047ad12eba59137cceede8d14d1b9` (`.local/phase-snapshot-final.json`). Sonradan başlayan quote fazı bu sonuçlara dahil değildir. Şema001–006,010–024; uygulanmış SQLchecksum değişmedi. Optimize previewbuild aynı appkaynağını, son testseçicileri günceltestmanifestini kullanır.

| Komut/kontrol | Gerçek sonuç |
|---|---|
| `npm run lint` / `npm run typecheck` | PASS, uyarı yok |
| `npm test` |206/206, 25 dosya PASS |
| `npm run test:integration` |15PASS; çekirdek `.local/phase-core-db.log` |
| `npx tsx --env-file=.env.local scripts/*-integration.ts` |import14,hukuk6,ağ4,operasyon16,kargo/vergi11,personel11,SEO8,Türkçe5,lot11,CMS16,privacy13,filtre14,set16,uygunluk18,sosyal13,adres8 PASS;17 komutta 199 kontrol |
| `npm run build` |PASS,0 uyarı; `.local/phase-build-fixed.log` |
| `npm run verify:artifact` |PASS; özelgeliştirme/testdosyaları dışarıda, gerekli sosyal font/lisans/logo trace'de |
| `npm run test:e2e` |82/82PASS,Chromium 41/WebKit 41,worker 1,retry 0,3,6 dk; `.local/phase-e2e-82-final.log` |
| `npm run backup:verify` |27 tablo gerçek izole restore count/hash ve ayrı örnekmedya SHA256 PASS; `.local/phase-backup.log` |
| `npm audit --omit=dev --audit-level=low` |0bilinen açık; yeni paket kurulmadı |

E2E geçmişi: ilk74PASS/8FAIL, testler bitince kapanışta bekleyen koşu durduruldu (`phase-e2e-82.log`); ikinci78PASS/4FAIL (`phase-e2e-82-fixed.log`), hedef4/4PASS26sn (`phase-ui-targeted.log`), son82/82PASS. Yeni arama ve selectler gerçek erişilebilir searchbox/combobox rollerine bağlandı; imza/rol/kota/timeouteşikleri gevşetilmedi.

Regresyonlar: logicalsetüstSKUreceipt/PO/returnwrite RED→GREEN, stok↔setdönüşümünde iki sırada yarış ve karmaPOrollback; actorless eligibility/reviewerlessdoc reddi;26kaynaktan boş3.sayfada toplam26;8MiBüstü özelgörsel importreddi; kaynak/özeltestverisini paketleyen eski artefaktRED→yeni dar runtimeokuma+exclusionGREEN; gecikenadresGET'in yeniCRUDyanıtını gizlememesi; siparişadres/profilsürümünün sonraki değişiklikte korunması.

Yeni ekran görüntüleri docs/screenshots altındaki admin-bundles-*,compliance-admin-*,social-*-mobile,address-book-mobile-* dosyalarıdır. İki yeni sosyal/adresprofilformunda AxeWCAG2.2AA ihlali0. Otomatik tarama tam manuelWCAG/ekran okuyucu/gerçekcihaz kabulü değildir. Geri yükleme gerçekstaging/tümmedya/RPO-RTO tatbikatı değildir; bazı yeni tablolar kaynakta boş olabilir. Stripe sandbox,SMTP,S3 ve gerçekcarrierAPI çağrısı yapılmadı.

## Tarihsel çekirdek test kanıtı — 06:37 İstanbul

Bu belge canlı satış, hukuk onayı, gerçek sağlayıcı kabulü veya bütün kapsamın tamamlanması anlamına gelmez. Kaynak, geliştirme/test verileri ve optimize yerel sunucu doğrulanır. Son tam tarayıcı sonucu aşağıda ayrı belirtilir; önceki başarısız koşular PASS sayılmamıştır.

## Komutlar ve gözlenen sonuç

| Komut | Gerçek sonuç |
|---|---|
| `npm run lint` | PASS, sıfır uyarı; kurallar kapatılmadı |
| `npm run typecheck` | PASS, strict TypeScript |
| `npm test` | 162/162 PASS, 20 dosya; 06:17 İstanbul |
| `npm run test:integration` | 14/14 PASS |
| `npx tsx --env-file=.env.local scripts/import-template-integration.ts` | 14/14 PASS |
| `npx tsx --env-file=.env.local scripts/legal-drafts-integration.ts` | 6/6 PASS |
| `npx tsx --env-file=.env.local scripts/security-boundary-integration.ts` | 4/4 PASS |
| `npx tsx --env-file=.env.local scripts/operations-integration.ts` | 16/16 PASS |
| `npx tsx --env-file=.env.local scripts/shipping-tax-integration.ts` | 11/11 PASS |
| `npx tsx --env-file=.env.local scripts/staff-orders-integration.ts` | 11/11 PASS |
| `npx tsx --env-file=.env.local scripts/seo-integration.ts` | 8/8 PASS |
| `npx tsx --env-file=.env.local scripts/turkish-locale-integration.ts` | 5/5 PASS |
| `npx tsx --env-file=.env.local scripts/lot-integration.ts` | 11/11 PASS |
| `npx tsx --env-file=.env.local scripts/cms-integration.ts` | 16/16 PASS |
| `npx tsx --env-file=.env.local scripts/privacy-integration.ts` | 13/13 PASS |
| `npx tsx --env-file=.env.local scripts/catalog-filters-integration.ts` | 14/14 PASS |
| PostgreSQL toplamı | 13 komutta 143 kontrol PASS; çekirdek yalnız kendi test DB'sini, diğerleri benzersiz yeni *_test DB'lerini kullanır |
| `npm run build` | PASS, Turbopack optimize standalone + TypeScript |
| `node --env-file=.env.local scripts/start.mjs --port 3000` | Başladı; health200/salesclosed, özel HTML private/no-store/noindex |
| Playwright düzeltme hedefi | Chromium/WebKit 20/20 PASS, 1,1 dakika; gizlilik/hesap/filtre/MFA/personel |
| Hermetic checkout hedefi | Chromium/WebKit 2/2 PASS, 7,6 saniye |
| `npm run test:e2e` | 72/72 PASS, Chromium36 + WebKit36, tek worker, retry 0, 2,7 dakika (06:37 kontrol noktası) |
| Axe | Dört temel sayfa ×iki motor +mobil filtre çekmecesi ×iki motor: 10 otomatik taramada sıfır ihlal |
| `npm run backup:verify` | PASS; AES256-GCM dump→yeni izole restore DB; 17 tablo sayı/hash ve ayrı örnek PNG SHA-256 eşleşti |
| `npx tsx --env-file=.env.local scripts/scheduler.ts --once` | Çıkış0; kalıcı işler planlandı |
| `npx tsx --env-file=.env.local scripts/worker.ts --once` | Çıkış0; gerçek SMTP/Stripe olmadığı için teslimat/tahsilat iddiası yok |
| `npm audit` ve `npm audit --omit=dev` | Sıfır bilinen açık; ESLint9 uyum/EOL borcu ayrıca integrations.md içinde |
| `docker compose --env-file .env.local config --quiet` | PASS; gerçek container/dağıtım kanıtı değildir |
| Özel sipariş PDF'si | Dokuz Türkçe ifade çıkarımı ve iki sayfa render incelemesi PASS; resmî fatura değildir |
| Görev kaynaklarında `git diff --check` | PASS; orijinal OFL lisanslarının satır sonu boşluğu değiştirilmedi, lisans dosyaları bu kaynak kontrolü dışında |

DB komutlarının son tam çıktıları `.local/final-*-integration.log`, build `.local/final-build.log`, son tarayıcı koşusu `.local/final-e2e.log` içinde; bu klasör Git dışıdır. Sırlar ve gerçek müşteri bilgileri bu belgede bulunmaz. Yerel test aktörleri/ürünleri production'a taşınamaz.

## Kullanıcının 22 kabul senaryosu

| # | Senaryo ve yerel kanıt | Sınır |
|---|---|---|
| 1 | Ürün/varyant→stok→yayın→misafir sipariş: çekirdek DB ve gerçek tarayıcı checkout/PDF zinciri | Gerçek katalog/ürün belgeleri henüz sağlanmadı |
| 2 | Son adet eşzamanlı checkout; set bileşenleri ve FEFO son lot aynı transaction'da | Tek sevk deposu main; çok depo transferi yok |
| 3 | Tekrarlanan webhook: ikinci sipariş/stok hareketi/iş yok | Gerçek Stripe olayı alınmadı |
| 4 | İmzasız, yanlış tutar/para/oturum ve replay içerik uyuşmazlığı reddi | Resmî SDK imzası offline, sağlayıcı hesabı testi yok |
| 5 | Başarısız/süresi dolan ödeme rezervasyonu ve kupon kotası serbest | Üretim scheduler/worker operasyonu bekliyor |
| 6 | Geç başarılı ödeme istisnası; negatif stok ve otomatik sevk yok | Finans/sağlayıcı mutabakatı gerçek hesapta denenmedi |
| 7 | Kupon, tam sayı/BigInt dağılımı, farklı alt birim biçimlendirme | Ticarette TRY/EUR/USD/GBP; JPY/BHD yalnız formatter altyapı testi |
| 8 | Karma sınıf/kargo vergisi, kısmi iade ve değişmez indirim/vergi snapshot'ı | Gerçek vergi/fatura/ülke kuralı onaysız |
| 9 | Kısmi paket, SKU toplama/paketleme, tekrar/yanlış adet ve gerçek takip alanı | Gerçek taşıyıcı API/ücretli etiket/fiziksel cihaz testi yok |
| 10 | Açılmış mühür/karantina ve setin satılmış bileşen snapshot'ı; genel stok yolundan bypass yok | Bilinmeyen iade lotuna yeniden atıf ve fiziksel QC devri eksik |
| 11 | Ülke, SKU belgesi, setin fiziksel bileşen belgesi, pil/sıvı taşıyıcı kabulü kapıları | Gerçek uygunluk/lisans/ülke kabulü bekliyor |
| 12 | A/B/misafir sepet ve sipariş/PDF sahipliği; özel başvurunun minimum token alanı | Gerçek production sınır güvenliği ayrıca incelenmeli |
| 13 | Depo maliyet/finans/iletişim alan sınırı; pazarlama toplu müşteri erişimi reddi | Gerçek personel hesap tahsisi bekliyor |
| 14 | Production test adaptörü, örnek ürün/ülke/metin/veri sorumlusu/politika reddi | Canlı satış hâlâ kapalı |
| 15 | Kuyruk retry/dedupe; Stripe inbox, iade pending/finalize ve belirsiz eski iade POST engeli | Gerçek Stripe sandbox/kesinti/itiraz/uzun kesinti kabulü yok |
| 16 | Türkçe API/arama/ICU sıralama, CSV/XLSX, snapshot/PDF ve tarayıcı başvuru metni | Gerçek SMTP teslim/UTF-8 doğrulaması yok |
| 17 | 360/390/430/768/1440, mobil filtre ve RTL altyapı | Gerçek iOS/Android cihazı ve tam Arapça yayın yok |
| 18 | Klavye Tab/Enter/Escape, modal focus, form etiketleri ve Axe | Otomatik belirtilen ekranlar; tam manuel ekran okuyucu sertifikası değil |
| 19 | Rıza öncesi/sonrası yalnız aynı origin, reklam/analitik/replay çerezi yok | Gelecekte eklenecek araçlar yeniden incelenir |
| 20 | Siparişte hukuk body/hash/version korunur; veri başvurusunda ilk alım/süre sürümü değişmez | Gerçek satıcı/veri sorumlusu ve hukuk onayı yok |
| 21 | Ürün/rehber SSR, dil canonical/hreflang, gerçek Product/Offer, editör/redirect, parçalı ve fixture-free sitemap | Dış schema doğrulayıcısı, tam crawler ve Search Console/Bing yok |
| 22 | Şifreli dump gerçek yerel restore, 17 tablo count/hash ve örnek medya | Bazı yeni tablolar kaynakta boş; gerçek staging/tüm medya/üretim RPO-RTO tatbikatı yok |

## Bulunan hatalar ve düzeltme sınırları

- MFA'nın hesap bayrağından eski oturuma yayılması, başlıksız büyük gövde, sepet sahipliği/kota, karantina bypass, set iade snapshot'ı ve ham SDK hata sızıntısı anlamlı RED→GREEN regresyonlarıyla kapatıldı.
- Dil rewrite'ında localhost/127.0.0.1 normalizasyonu proxy'nin dış HTTP isteğine dönüşüyordu. Gerçek origin korunuyor, dil SSR doğru; farklı TR/EN alias, eksik çeviri ve yabancı alternate/query/hash testleri korundu.
- Türkçe sıralama default C yerine ICU dil collation'ı kullanıyor. Katalog stok filtresi LIMIT öncesindedir; main dışı stok satılabilir gösterilmez; lot/set ve aynı varyant AND semantiği korunur. Kart fiyatı SQL sıralamasıyla aynı minimum geçerli varyantı seçer.
- İçe aktarma önizlemesi aktör/ortam/format/satır/hatalara hash ile bağlıdır. Eksik ana depo gizlenmez; yeni SKU yalnız mevcut main'de sıfır bakiye alır. Tek dilli seçenek çevirisi uydurulmaz.
- CMS yeni kurulumda ilk revision'ı eklemiyor, planlı rehber SEO projection'da kalıyordu. İlk revision/schedule resolver, gerçek SSR/404 ve sitemap/redirect ortak yürürlük kaynağı düzeltildi.
- Başvuru politikası onayı/alımı ülke kilidini paylaşır; yönlendirme veya sonradan ilk onay daha erken deadline'ı uzatmaz. Yanıt için kimlik ve dış güvenli teslim referansı gerekir. Ekran otomatik mali kayıt silmez.
- Hesap ve yönetim state'i kullanıcı/rol/MFA sınırına key ile bağlandı; A→logout→B sırasında sipariş/adres/MFA taslağı gösterilmez. Geciken A başvuru cevabı B ekranını request-generation nedeniyle değiştiremez.
- Yeni footer bağlantısında Axe 1,3:1 kontrast buldu; açık tema tokenıyla düzeltildi. Native select testleri gerçek erişilebilir combobox adına bağlandı. Next'in route-announcer duyurusu uygulama hata alanı dışında tutulur; uygulama hataları hâlâ denetlenir. Safari'de filtre açan düğme açıkça focus alır, Escape odağı geri döndürür.
- Anonim form gerçek navigasyon yaptığından testin daha sonra POST body okuması Chromium'da geçersizdi. Gerçek201, yönlenilen ID/token, yetkili GET ve DB/hash/PII doğrulaması korunarak yarış kaldırıldı.
- MFA fixture baskısı gerçek HTTP429 olarak trace'te doğrulandı. Better Auth `/two-factor/*` path/IP başına10sn/3 kuralı değiştirilmedi. Fixture enable resmî sunucu API'siyle hazırlanır, HTTP TOTP ve oturum hook'u korunur. Yalnız resmî0..10sn retry header'ında bir kez beklenir, kod yeniden hesaplanır. Asıl Security/Account enable senaryoları HTTP/UI kalır; fixture politikasının11 birim kontrolü vardır.
- Genel seed ürünü çok sayıda E2E koşusunda tükendi. Test stoğunu artırmak yerine checkout her case'e ait benzersiz ürün/varyant/stok hareketiyle çalışır ve yalnız kendi FK ilişkilerini temizler. Yeni iki hedef geçti; tam suite sonucu üst tabloda tutulur.
- İlk optimize70 test koşusu kontrast/seçici hatalarıyla durduruldu; sonraki72 koşusu65/72, ardından70/72 oldu. Hiçbiri son kabul diye sunulmadı. Dev HMR tekrar yüklemeleri ve eski standalone Windows EBUSY kilidi için sunucu/çıktı ayrımı belgelendi; kontroller kapatılmadı.

## Görsel, performans ve gerçek dış erişim

Son laboratuvar: `docs/performance-report.json`, 390px LCP788ms/CLS0/örnek etkileşim40ms;1440px LCP168ms/CLS0/örnek24ms. Her genişlikte bir kısıtlamasız localhost navigasyonudur; saha INP/p75, gerçek cihaz veya ağ kısıtlamalı Lighthouse değildir. Yeni filtre, gizlilik ve admin masaüstü/mobil görüntüleri `docs/screenshots` altındadır. Referansın logo/kemer/boynuz/kuyruk, krem/bordo dengesi ve tipografisi görsel olarak karşılaştırıldı; birebir kaynak vektör veya lisanslı gerçek katalog fotoğrafı teslimi iddiası yok.

Gerçek Stripe sandbox/işletme-kategori kabulü; SMTP/S3; taşıyıcı/e-Fatura/kanal erişimi; gerçek satıcı/vergi/adres/banka/destek; ürün ve görsel hakları; yetkili hukuk incelemesi; remote CI/staging/production/DNS; gerçek cihaz ve tam medya restore hâlâ bekliyor. Bu eksikler yerel testlerle tamamlanmış sayılmaz.

## Dondurulmuş çekirdek sürümü

11 Kasım 2026 06:37 İstanbul: yerel260kaynak/varlık baytmanifesti SHA-256 `33217b58eac9a191d87e2cc6f20e4869935def4b87f53b8dd04116c45476cbaf`. Manifest Git dışı `.local/core-snapshot.json` ve tam72PASS logu `.local/checkpoint-core-e2e-72-pass.log` içindedir. Bu yerel bayt izi bir Git commit veya hukuk/güvenlik sertifikası değildir; satır sonu dönüşümü de hash değiştirir. Sonraki faz değişiklikleri bu manifestin test edilmiş sürümü olarak sunulmayacak; yeni kabul ayrıca yapılacaktır.
