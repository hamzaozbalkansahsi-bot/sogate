# NODENO rehber ve kalıcı yayın sistemi

Kullanıcı en az 250 farklı, özgün, resimli, SEO altyapısıyla bütünleşik rehber ve bilgisayardan bağımsız günde iki yayın istedi. Hazır içerik bankası anahtarsız çalışır. Ücretli abonelik açılmaz; katalog, müşteri ve ödeme kayıtları değiştirilmez. Aynı çalışma alanındaki ürün/firma editörü korunur.

Blog `/blog` altında sunucuda HTML olarak sunulur. Kategori ve arama yayınlanmış içerikleri filtreler; taslaklar, gelecek tarihler ve yönetim verisi genel yanıta girmez. Makalelerde açıklayıcı özgün SVG çizimler, gerçek yayın tarihi, kaynak dayanakları, ilişkili rehberler ve kullanım amacına uygun alan/boya/renk aracı bulunur. Çizimler ürün fotoğrafı veya üretici renk kartelası gibi sunulmaz. Doğrulanmış ürünler yalnız gerçek katalog kimliğiyle ilişkilendirilir.

İçerik 125 yaşam alanı, 125 boya/yenileme rehberidir. Her yazı ayrı karar sorununu çözer; dört veya daha fazla konuya özgü bölüm, uygulanabilir kontrol listesi ve açıklayıcı görsel taşır. Sayısal örnekler varsayımlarıyla açıklanır. Üretici teknik özellikleri yalnız resmi kaynakla desteklenirse yazılır. Başlık değiştirerek şablon çoğaltılmaz.

Kanonik içerik Türkçedir. Gerçek çeviri bulunan sürümler ayrı `lang` URL, dil etiketi ve hreflang ile sunulur; eksik çeviriye sahte hreflang verilmez. Dört çekirdek dilin arayüzü ve Arapça RTL tamamlanır; diğer hedef diller mevcut mağaza yönlendirmeleriyle korunur. Kaynak ve çeviri alanları birbirinden ayrılır.

Kalıcı `storageRoot/blog.sqlite` içerik kimliği, plan, yayın durumu ve olay kayıtlarını saklar. Saat dilimi Europe/Istanbul, günlük slotlar 09:30/18:30. Cron her beş dakikada web kökü dışındaki CLI runner'ı çağırır. Kilit, benzersiz kayıt kimliği, transaction, gerçek yayın anı, sınırlı telafi, yeniden deneme ve başarısız kuyruk gerekir. Yönetici mevcut oturum ve CSRF kurallarıyla duraklatma, sürdürme, yeniden deneme ve izleme yapar. Banka sonludur: 250 içerik 125 günlük yayın sağlar; bitiş yaklaşımı panelde görünür, makale yeniden yayımlanmaz.

SEO: gerçek yayınlar için BlogPosting ve BreadcrumbList, liste için CollectionPage, canonical, yayınlanmış URL sitemap'i, ana sitemap bağlantısı, dahili kategori/araç/ürün bağlantıları ve RSS. Arama sonuçları noindex olur. Arama motoruna gönderim mevcut gerçek bağlantı üzerinden yapılabiliyorsa kullanılır; yetkisiz servis veya anahtar var sayılmaz.

Arayüz mevcut NODENO Sans ve marka paletini kullanır: lacivert #172D38, fildişi #F5F2E9, açık yeşil #D8EC81, ikincil #536770, çizgi #DADDD6, beyaz #FFFFFF. Tipografi başlık 40–64, gövde 17–19, not 14–16 px. İmza öğe, makale yanında çalışan ölçü/boya deneme defteridir. Yeni font veya marka rengi eklenmez. Mobilde tek sütun; fotoğraf/çizim esnetilmez, tüm form alanları etiketli ve klavyeyle erişilebilirdir.

Yayın öncesi gerçek canlı releaseHash yeniden okunur ve o sürümdeki tüm değişiklikler korunur. Yalnız blog delta paketi hazırlanır; cPanel ortak deployment lease altında eski işaretçi/yazılacak dosyalar yedeklenir, özel sürüm hazırlanır, byte/hash doğrulanır, işaretçi çevrilir; hatada geri alınır. Kalıcı hesap ve görsel kasaları korunur. Yerel test ve canlı kabul ayrı raporlanır.
