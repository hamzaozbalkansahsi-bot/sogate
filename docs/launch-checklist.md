# Canlıya hazırlık — satış kapalı

Bu belge yayın onayı değildir. Yerel testler işletme, ödeme kuruluşu veya hukuk kabulünün yerine geçmez. Kullanıcının açık talebiyle kaynaklar GitHub main dalına yüklendi. Staging/production dağıtımı, gerçek tahsilat, DNS işlemi veya alan adı satın alımı yapılmadı. GitHub CI runner'ı hesap/faturalandırma kilidi nedeniyle başlamadı; [gerçek kayıt](git-workflow.md) ayrı tutulur.

## Doğrulanan yerel hazırlık

- [x] 09:19 kontrol noktasında sahiplik/yanıt düzeltmeleri dahil lint, strict typecheck, birim, PostgreSQL entegrasyonu, Chromium/WebKit E2E, optimize build ve artefakt kontrolü geçti. Güncel kabul [test-evidence.md](test-evidence.md) ile [progress.md](progress.md) içindedir; tarihsel PASS yeni sürüme aktarılmaz.
- [x] Gerçek yerel oturum/MFA, sepet/teklif sahipliği, hesap değişiminde eski yanıt, ödeme tekrarı ve stok/kupon/lot kabul sınırları otomatik regresyonlarla doğrulandı. Test ödeme gerçek tahsilat değildir.
- [x] Lotlu PO kabulü, gerçek kaynak geçmişi ve depo rolünün maliyetsiz yanıtı yerel sunucu ve tarayıcı akışında doğrulandı; fiziksel üretici etiketi/paket kontrolü sayılmaz.
- [x] Şifreli DB yedeği yeni izole yerel DB'ye yüklendi; 33 tablo sayı/hash ve tek örnek medya SHA-256 eşleşti. Staging veya tüm medya restore kabulü değildir.
- [x] Yerel TR/EN, mobil/klavye ve Chromium/WebKit kontrolleri geçti; gerçek iOS cihazı, tam manuel WCAG ve saha performansı ayrı bekler.

Bu işaretler yalnız yeni 320 dosyalık test edilen yerel kontrol noktasına aittir; sonraki kaynak değişikliklerini kendiliğinden geçmiş saydırmaz. Aşağıdaki üretim onaylarını veya `launch.*` ayarlarını kendiliğinden açmaz.

## İşletme ve gerçek katalog

- [ ] Hukuki satıcı unvanı, sicil, vergi, adres, banka ve destek kanalları belgelendi.
- [ ] Veri sorumlusu ve veri işleyen rolleri ayrı belirlendi; geliştirici/tasarımcı kredisinden türetilmedi.
- [ ] Yayımlanan şirket/marka beyanları gerçek belgelerle karşılaştırıldı; geliştirici/tasarımcı kredisi satıcı veya veri sorumlusu gibi sunulmuyor.
- [ ] sexsogate.com sahipliği, DNS/sertifika ve marka tescili doğrulandı. Teyitsiz ® kullanılmıyor.
- [ ] Gerçek SKU, stok, fotoğraf hakları, üretici/menşe, beden, bakım ve uyarılar doğrulandı.
- [ ] Pil/sıvı/lot/son kullanma ve SKU/model belgeleri ülkeye göre incelendi; üretimde fixture kayıt sayısı sıfır.

## Ödeme, vergi, sevk ve hukuk

- [ ] Stripe hukuki işletme, hesap ülkesi, gerçek kategori, site ve hedef ülkeler için kabul kanıtı verdi; hesap tahsilat durumu kontrol edildi.
- [ ] Gerçek Stripe sandbox Checkout, webhook, tekrar/sıra değişimi, iade, itiraz, kesinti ve mutabakat testleri tamamlandı.
- [ ] Test/canlı anahtarlar ayrı secret manager üzerinden verildi. Ortam değişkeninin bulunması tek başına kabul sayılmadı.
- [ ] SKU vergi sınıfları, ülke/yürürlük kuralları, fiyat listeleri, kargo vergisi ve fatura sağlayıcısı işletme/uzman tarafından onaylandı.
- [ ] Gerçek taşıyıcı, tarife/desi, pil/sıvı kabulü, paketleme prosedürü ve etiket/takip doğrulandı.
- [ ] Her ülkenin adres alanları, güçlü yaş doğrulaması ihtiyacı, DDP/DAP bedelleri, ürün/ödeme/kargo/çeviri/vergi/hukuk kapıları tamamlandı.
- [ ] Hukuk taslakları gerçek şirket ve veri akışlarıyla dolduruldu, yetkili inceleme/sürüm/yürürlük kanıtı alındı.
- [ ] Siparişe bağlı sözleşme ve ön bilgilendirme, müşteri için kalıcı erişim/ileti yöntemiyle doğrulandı.
- [ ] KVKK başvuru, saklama, silme, anonimleştirme ve sınır ötesi aktarım süreçleri işletme tarafından devralındı.

## Üretim ortamı ve kabul

- [ ] Gerçek yönetici MFA kurdu; oturum doğrulaması, iptal/reset, kritik işlemler ve personel rolleri gerçek ortamda sınandı.
- [ ] Origin yalnız güvenilir proxy üzerinden erişilebilir; proxy istemci x-real-ip başlığını silip yeniden yazıyor. Kalıcı ağ kotası gerçek sınırda test edildi.
- [ ] Worker, scheduler, SMTP, başarısız iş takibi ve operasyon alarmları gerçek hizmetlerle çalışıyor. Uzun işlerin lease/yeniden deneme ve belirsiz dış sonuçları doğrulandı.
- [ ] DB ve tüm medya için şifreli uzak yedek, ayrı anahtar, erişim/saklama ve staging restore tatbikatı tamamlandı.
- [ ] Yerelde doğrulanan kaynak sürümü gerçek ortamda dış servis ve sınır güvenliği kabulünü geçti.
- [ ] TR/EN içerik ve URL/metaveri doğrulandı; de/ru/ar eksik yayınları kapalı. SEO taraması, sitemap, schema, yönlendirme ve görsel hakları incelendi.
- [ ] Mobil checkout, klavye/WCAG ve gerçek iOS Safari cihazı kontrol edildi. Saha Core Web Vitals yalnız gerçek kullanıcı verisiyle raporlandı.
- [ ] Remote CI çalıştı; staging web/worker/scheduler/DB/storage birlikte dağıtılıp kritik akışları geçti.
- [ ] Migration öncesi yedek/geri dönüş ve sonrasında sağlık, ödeme/stok mutabakatı ile olay prosedürü prova edildi.
- [ ] Kullanıcının açık production geçiş yetkisi alındı.

Teknik kapılar: APP_ENV=production, test ödeme/fixture seed reddi; LIVE_SALES_ENABLED=false; boş satıcı ve launch.* onayları; ülke izin listesi, ürün belgesi, taşıma ve vergi kuralları. Bu kapılar aşılmaz. Yerelde yapılmış kontrolün gerçek kapsamı docs/progress.md ve docs/test-evidence.md içindedir; bu üretim listesi yerel başarı nedeniyle kendiliğinden işaretlenmez.
