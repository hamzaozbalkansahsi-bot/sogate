# NODENO alışveriş deneyimi

Çalışma tarihi: 1 Kasım 2026. Canlı kabul tamamlandığında sürüm ve sonuçlar bu dosyanın sonuna eklenir. Tasarım sözleşmesi: [alışveriş deneyimi tasarımı](superpowers/specs/2026-11-01-shopping-experience-design.md).

## Referans incelemesi ve sınırlar

Trendyol'un [mobilya kategorisi](https://www.trendyol.com/mobilya-x-c1119), [işlem rehberi](https://www.trendyol.com/yardim/islem-rehberi) ve kullanıcı tarafından sağlanan mobil ürün/kategori ekranları incelendi. Resmî kategoride genişlik, malzeme, kategori ve fiyat gibi daraltma alanları; işlem rehberinde üyelik, misafir alışverişi, adres, ödeme ve iade aşamaları görülebiliyor. İndekslenmiş kamuya açık içerik erişilebilirken normal otomatik tarayıcıyla ana sayfa, mobilya ve yardım sayfaları 403 döndürdü. Üye hesabı, kişisel öneri motoru, gerçek sipariş, ödeme ve iade işlemlerinin Trendyol tarafında uçtan uca çalıştırıldığı iddia edilmez. Bu erişim sınırı aşılmadı.

Karşılaştırma ve alan uyumu araçları NODENO mobilya alışverişi için geliştirildi; Trendyol'da birebir aynı araçların bulunduğu iddia edilmez. Görsel dil NODENO'nun kanonik marka paketiyle korunur. Pazar yerlerindeki kampanya, satıcı puanı, satış sıralaması, teslimat sayacı ve kişisel öneri iddiaları gerçek işletme verisi bulunmadan eklenmez.

| Yolculuk | NODENO'daki somut davranış | Doğrulama |
| --- | --- | --- |
| Ana sayfa ve keşif | Daha kısa vitrin, gerçek oda fotoğrafları, ilk ürün rafına daha erken erişim; ana raflar arasında model tekrarı azaltılır | Gerçek fotoğrafla masaüstü/mobil görsel kontrol |
| Arama | Çok kelimeli sıralama, Türkçe karakter eşleme, bitişik ürün kodu, kontrollü tek harf hatası, kategoriler, temizlenebilir son aramalar, klavye seçimleri | Saf fonksiyonlar ve tarayıcı |
| Listeleme | Kategori/fiyat/renk filtrelerine açık kaynak ölçülerinden en fazla genişlik/yükseklik/derinlik eklenir; URL ve kaldırılabilir filtreler | Saf fonksiyonlar ve dört dilde tarayıcı |
| Ürün kartı | Gerçek renkle hızlı inceleme, adet, sepete ekleme, karşılaştırma, koleksiyona ekleme | Tarayıcı |
| Ürün ayrıntısı | Mevcut gerçek galeri/renk/teknik bilgi/SSS korunur; alan uyumu ve alışveriş araçları eklenir | Tarayıcı, eski galeri kabulü tekrar çalıştırılır |
| Karar verme | En çok dört gerçek SKU, fiyat/kod/renk/ölçü/malzeme/kapsam/özellik tablosu, yalnız farklar, paylaşılabilir seçim URL'si | Saf fonksiyonlar ve iki motor |
| Koleksiyon | Misafir yerel listeleri; üyede özel, kalıcı, sürümlü kayıt; açık talep ile misafir aktarımı; oluşturma/yeniden adlandırma/onaylı silme/ürün kaldırma/sepete ekleme | Gerçek PHP/SQLite, CSRF/sahiplik/CAS, iki motorlu üye arayüz testi |
| Sepet | Aynı modelde renk değiştirme, mevcut renkle adetleri güvenle birleştirme, 99 üstünde sessiz kısma olmadan ret, silme/temizleme sonrası 8 saniye geri alma | Saf fonksiyonlar ve iki motor |
| Favoriler ve son bakılanlar | Koleksiyonlarla bağlantılı sekmeler; favorileri toplu eklerken mevcut adetleri koruma; temizlenebilir cihaz geçmişi | Tarayıcı ve sınır testleri |
| Misafir, hesap ve sonrası | Mevcut ödeme öncesi adres/iletişim/bilgi kontrolü, üyelik, adresler, sipariş görünümü ve yardım korunur | Mevcut mağaza testleri |

## Ölçü ve veri sözleşmesi

Eksen sırası yalnız açık kaynak `GxYxD` veya eşdeğer etiketlerden okunur. Sayıların yerlerine bakıp eksen tahmini yapılmaz. Filtreler, ayarlanabilir ölçünün üst ucunu kullanır; girilen eksenin ölçüsü olmayan ürün o filtrede gösterilmez. Alan uyumu; sığar, büyük, ayarlanabilir ölçü ayrıca kontrol edilmeli ve yeterli bilgi yok sonuçlarını ayırır. Kapak açılma boşluğu, taşıma yolu, montaj veya duvar bağlantısı için uygunluk garantisi vermez.

Koleksiyon sınırları: hesap başına 20 liste, liste başına 100 ürün ve toplam 1.000 ürün. Ürünler mevcut kanonik kimliklerle doğrulanır. Misafir aktarımı giriş sırasında otomatik yapılmaz. Özel hesap koleksiyonları localStorage'a yazılmaz. PUT sürüm uyuşmazlığında 409 döner; başka cihazın kaydı ezilmez. Birleştirme atomiktir; hesap birleştirmede kapasite aşılırsa sepet ve kimlikler dahil işlem geri alınır.

Sepet geri alma, ilgili hesap/oturum ve sepetin işlem sonrası tam hali ile sınırlıdır. Arada başka değişiklik yapılırsa eski sepet geri yazılmaz. Koleksiyonlar, sepet ve kullanıcı veritabanı yayın klasörünün dışındaki mevcut kalıcı depoda tutulur.

Ödeme, sipariş oluşturma, ödeme kuruluşu ve gerçek Google/Apple sağlayıcı etkinleştirmesi kullanıcının önceki kararıyla beklemektedir. Yeni koleksiyonların sosyal hesap birleştirmesinde korunması hazırlandı; sağlayıcı kabulü yapılmış sayılmaz.

## Edinilen beceriler ve tedarik kaydı

Kullanıcının açık kurulum talebiyle iki resmî kaynak incelendi, sabit Git revizyonundan güvenilir yerel skill installer kullanılarak kuruldu. Depoya veya canlı pakete üçüncü taraf bir mağaza teması ya da çalışma zamanı bağımlılığı eklenmedi.

| Beceri | Birincil kaynak ve incelenen revizyon | Kullanım |
| --- | --- | --- |
| web-design-guidelines | [Vercel Agent Skills](https://github.com/vercel-labs/agent-skills/tree/1a2c79d4e6c4a2283dc2c614b6538cbe1ed5ca62/skills/web-design-guidelines) | Semantik kontroller, erişilebilir adlar, odak, taşma, azaltılmış hareket, form ve görsel yerleşimi |
| webapp-testing | [Anthropic Skills](https://github.com/anthropics/skills/tree/ca45fc496a3436251f191354091d557da31c15b5/webapp-testing) | Gerçek Python Playwright senaryoları, önce DOM/ağ incelemesi, sonra kullanıcı eylemleri |

Kurulu SKILL.md SHA256 değerleri sırasıyla `f4647ca866a3accf763777f83e7682954f0187cd6bea7eea0399796652414e8f` ve `51b7349e77ec63b7744a6f63647e7566a0b4d2e301121cc10e8c2113af6556a2`. Yönergeler kurulum öncesi okunan dosyalarla eşleşti. Vercel'in [güncel arayüz kuralları](https://github.com/vercel-labs/web-interface-guidelines/blob/main/command.md) son incelemede yeniden okundu. Marka/dil/kopya için kullanıcı kuralları önceliklidir. Beceri kataloğu sonraki turda yeniden keşfedilir; bu tur yönergeler okunarak uygulandı.

Python Playwright 1.64.1 yalnız `artifacts/commerce-qa-python` sanal ortamına kuruldu; mevcut yerel Chromium ve Windows WebKit çalıştırıcıları kullanılır. Araştırma, test görüntüleri ve ham sonuçlar `artifacts/commerce-research` ve `artifacts/shopping-experience` altındadır. Yerel kaynak önizlemesi açıkça test amaçlıdır; nihai kabul gerçek paket ve ardından canlı sürüm üzerinde ayrıca yapılır.

## Kabul kaydı

**YAYINLANDI VE CANLIDA DOĞRULANDI.** Kabul: `2026-11-01T07:28:22.293383+00:00`. Turhost sürümü `a44faa2a8a4c9823e8b25bafe75c043efbbb313f3905330ea9f553672b2654c3`, uygulama kaynak kaydı `b1687b6`. 174 kaynak testi, 18 dağıtım testi; gerçek pakette ve canlıda ayrı ayrı 18 yeni alışveriş, 20 genel mağaza, 40 ürün sayfası, 32 galeri ve 4 bildirim çakışma kontrolü geçti. İki motorlu özel hesap ve sepet durum testleri de geçti. Dört güvenilir HTTPS alan adı, 35 varlık hash değeri, 13 mevcut özel yol ve üç ek koleksiyon yolu doğrulandı. 15 medya örneği birebir eşleşti; katalog/fiyat/medya sürümü aynı kaldı. Yedek: `/home/nodenoho/nodeno-backups/20261101T072245Z-a44faa2a8a4c-fcd592`. Makine kaydı: `artifacts/shopping-experience/delivery-record.json`; güncel genel kayıt `artifacts/qa/production-release.json`. Gerçek ödeme, Google/Apple sağlayıcı kabulü ve fiziksel iPhone testi iddia edilmez.
