# Çalışma Akışı

- Tüm tasarım, geliştirme ve değişiklikler önce yerel ortamda yapılır.
- Değişiklikler yerelde çalıştırılır, incelenir ve ilgili testlerle doğrulanır.
- Canlıya geçiş, yerel çalışma ve doğrulamalar tamamlandıktan sonra ayrı bir aşama olarak ele alınır.

- Marka adı SEXSOGATE, sloganı “Tutkunu Keşfet.”; başka işletmenin ortamına bağlanma.
- Başlangıçta docs/product-spec.md, docs/architecture.md ve docs/progress.md oku. Tasarım için docs/design-system.md esas alınır.
- İlerlemeyi ve gerçek test sonuçlarını docs/progress.md içinde güncelle. Çalıştırılmayan kontrolü başarılı sayma.
- Para ve stok kararları sunucuda, işlemsel olarak alınır. İstemciden fiyat veya yetki kabul etme.
- Yerel örnek veri production'a taşınamaz. Eksik ülke, ödeme, belge ve hukuk onaylarında satış kapalıdır.
- Gizli değerleri yazdırma veya Git'e ekleme. Push, canlı yayın, gerçek tahsilat ve DNS değişikliği bu görevde yetkili değildir.
- Geliştirici gösterimi PTYS Technoligess LLC, tasarım Hamza ÖZBALKAN; satıcı/veri sorumlusu bunlardan çıkarılamaz. Elle yazılmış yorum destekleyen kaynaklarda kullanıcı standardı Türkçe dosya başlığı kullan; üretilmiş/vendor dosyalara dokunma.
- Stripe öncelikli adaptördür; işletme, hesap ülkesi, kategori kabulü ve gerçek test olmadan canlı açılmaz. Hukuk sürümleri sipariş snapshot'ında korunur. Ana kapsamın güncel sürümü 29 bölümlük kullanıcı talimatıdır.

<!-- BEGIN:nextjs-agent-rules -->

## This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` (resolved from this file's directory; in monorepos the `next` package may not be visible from the repo root) before writing any code. Heed deprecation notices.

This block is written and re-added by `next dev` — verify at `node_modules/next/dist/server/lib/generate-agent-files.js`. Removing it from a diff only re-creates the uncommitted change; committing it with your work keeps the tree clean.

<!-- END:nextjs-agent-rules -->
