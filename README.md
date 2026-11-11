# SEXSOGATE

Tutkunu Keşfet. Önce yerel geliştirme; canlı satış kapalı.

Gereksinimler: Node24.12.x, npm11, PostgreSQL18.6. Bu Windows çalışma alanında proje içi PostgreSQL yardımcı komutu kullanılabilir:

```powershell
npm ci
npm run setup:local
node scripts/native-postgres.mjs
npm run db:migrate
npm run db:seed
npx tsx --env-file=.env.local scripts/bootstrap-admin.ts
npx tsx --env-file=.env.local scripts/legal-drafts.ts
npm run dev
```

Mağaza http://127.0.0.1:3000, yönetim /yonetim. Yerel yönetici bilgisi `.local/admin-access.txt` içindedir; sohbete/Git'e paylaşmayın. Önce /hesap > Güvenlik bölümünde MFA kurun. Worker ayrı terminalde `npm run worker`; zamanlayıcı `npx tsx --env-file=.env.local scripts/scheduler.ts`.

```powershell
npm run lint
npm run typecheck
npm test
npm run test:integration
npx tsx --env-file=.env.local scripts/import-template-integration.ts
npx tsx --env-file=.env.local scripts/legal-drafts-integration.ts
npx tsx --env-file=.env.local scripts/security-boundary-integration.ts
npx tsx --env-file=.env.local scripts/operations-integration.ts
npx tsx --env-file=.env.local scripts/shipping-tax-integration.ts
npx tsx --env-file=.env.local scripts/staff-orders-integration.ts
npx tsx --env-file=.env.local scripts/seo-integration.ts
npx tsx --env-file=.env.local scripts/turkish-locale-integration.ts
npx tsx --env-file=.env.local scripts/lot-integration.ts
npx tsx --env-file=.env.local scripts/cms-integration.ts
npx tsx --env-file=.env.local scripts/privacy-integration.ts
npx tsx --env-file=.env.local scripts/catalog-filters-integration.ts
npx tsx --env-file=.env.local scripts/bundle-integration.ts
npx tsx --env-file=.env.local scripts/compliance-integration.ts
npx tsx --env-file=.env.local scripts/social-integration.ts
npx tsx --env-file=.env.local scripts/address-integration.ts
npx tsx --env-file=.env.local scripts/quote-integration.ts
npx tsx --env-file=.env.local scripts/purchase-lots-integration.ts
npm run build
npm run verify:artifact
npm run test:e2e
npm run backup:verify
```

Playwright için ilk kurulum: `npx playwright install chromium webkit`. Aynı test DB'sini veya Playwright çıktı dizinini eşzamanlı iki test çalıştırmasıyla paylaşmayın.

E2E öncesinde güncel `npm run build` gerekir. Playwright, boş 3000 portunda optimize standalone sürümünü başlatır; CI bunu kullanır. Yerelde açık sunucu varsa yeniden kullanılır. Başka bir standalone önizleme çalışıyorsa build öncesinde durdurun.

Optimize edilmiş yerel sürüm için geliştirme sunucusundan ayrı terminal kullanın:

```powershell
npm run build
node --env-file=.env.local scripts/start.mjs --port 3004
```

Bu yardımcı standalone çıktıya statik dosya ve PDF fontlarını ekler; development/test kimliği korunur ve gerçek tahsilat açılmaz. Yeniden `build` çalıştırmadan önce bu önizleme terminalini Ctrl+C ile kapatın; Windows çalışan standalone klasörünü kilitler. Geliştirme önbelleği `.next-local`, derleme çıktısı `.next` altındadır.

Windows'ta gözlenen Turbopack geliştirme HMR döngüsü nedeniyle `npm run dev` desteklenen Webpack modunu kullanır. Optimize build Turbopack ile doğrulanır; lint, TypeScript ve test kontrolleri iki ortamda da açıktır. Kaynak ve kontrol kanıtları docs/test-evidence.md içindedir.

[Modül durumları](docs/module-status.md), [checkout](docs/checkout-guide.md) ve [lotlu satın alma kabulü](docs/purchase-lot-guide.md) rehberleri yerel kapsamı ve eksikleri ayrı gösterir. Ortam alanları, işletme ayarları ve güvenli giriş yöntemi [configuration.md](docs/configuration.md) içinde açıklanır. Son doğrulanan kapsam ve tamamlanmayan işler [progress.md](docs/progress.md) içindedir.

Devam kaydı docs/progress.md, modül sınırları docs/architecture.md, kullanım docs/admin-guide.md, dağıtım/geri yükleme docs/deployment-and-restore.md. Kapsam ve açık işler burada kayıtlıdır; yalnız adaptör veya tablo bulunması tam modül teslimi değildir. Yerel örnek ürün/vergi/stoklar production'a taşınamaz. Gerçek katalog, işletme/hukuk ve Stripe kabulü bekleniyor.
