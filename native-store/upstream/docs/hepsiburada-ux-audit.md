# Hepsiburada alışveriş deneyimi incelemesi

İnceleme: 31.10.2026. Kapsam: herkese açık web içeriği ve NODENO için uygulanabilecek alışveriş mekanikleri. Hesaba giriş, sipariş, ödeme, mesaj veya yorum işlemi yapılmadı.

## Kanıtın sınırı

Standart Playwright ile 1366×900 masaüstü ve 390×844 mobil erişim HTTP 403 güvenlik ekranıyla sonuçlandı. Koruma aşılmadı. `artifacts/reference-hb/home-desktop.png`, `home-mobile.png` ve `inspection-summary.json` bu sonucu kaydeder. Bunlar mağaza tasarımının ekran görüntüleri değildir.

Resmî sayfaların okunabilir içeriği web aracıyla incelendi. Bu yöntem içerik ve gezinme hedeflerini doğruladı; piksel yerleşimi, hover davranışı, mobil çekmeceler, arama önerilerinin etkileşimi ve oturum içi ekranlar doğrulanmadı. Aşağıdaki mobil düzen kararları NODENO önerisidir.

## Doğrulanan mekanikler

### Anasayfa ve gezinme

Arama, ana kategorilerden alt gruplara inen kapsamlı gezinme, kampanya vitrini ve farklı ürün seçkileri bulunuyor. Kartlarda ürün adı, fiyat, değerlendirme bilgisi ve koşula bağlı kampanyalar yer alıyor. Üst bağlantılar sipariş geçmişine ve desteğe erişim sağlıyor. Çok sütunlu kategori bilgi yapısı okunabilir kaynakta var; menünün fareyle açılış animasyonu gözlemlenmedi. Kaynak: [Hepsiburada anasayfa](https://www.hepsiburada.com/).

### Mobilya listesi

Liste, oda ve ürün gruplarına daraltılabiliyor; marka, satıcı, tutar aralığı, malzeme, renk ve üç boyut üzerinden filtre alanları sunuyor. Sonuç sayısı ve ürün kartları var. Doğrulanan sekiz sıralama adı: **Önerilen sıralama**, **En düşük fiyat**, **En yüksek fiyat**, **Çok satanlar**, **Çok değerlendirilenler**, **Yüksek puanlılar**, **İndirim oranı**, **Yeni eklenenler**. Kaynak: [Mobilya kategorisi](https://www.hepsiburada.com/mobilyalar-c-18021299).

### Ürün ayrıntısı

İncelenen ürün içeriğinde kategori yolu, çoklu görsel, başlık, satıcı, sepet eylemi ve teknik bilgi özeti bulunuyor. Ayrıntılar açıklama, değerlendirme, soru-cevap ve iade başlıklarıyla ayrılıyor. Değerlendirmelerde dağılım, metin arama ve filtreleme alanları var; yorum yazma koşulu satın alma ile ilişkili. Tıklama sonrası sepet sonucu gözlemlenmedi. Kaynaklar: [örnek ürün](https://www.hepsiburada.com/1-500-kelime-ilk-100-kelimem-p-HBCV00007DA0GC), [mobilya örneği](https://www.hepsiburada.com/minera-anka-montessori-ahsap-yer-kitapligi-mavi-mdf-58x34x37-cm-cocuk-odasi-kitap-ve-oyuncak-duzenleyici-pm-HBC00007CSXY9).

### Sipariş, teslimat ve destek

[Siparişlerim](https://www.hepsiburada.com/siparislerim) hedefi doğrulandı; içerik okunamadığı için sipariş ayrıntısı veya gönderi zaman çizelgesi gözlemlenmiş sayılmaz. [Yardım](https://www.hepsiburada.com/yardim), [Çözüm Merkezi](https://www.hepsiburada.com/cozummerkezi) adresine yönleniyor; dinamik yardım ekranı okunamadı.

Resmî [teslimat noktası anlatımı](https://www.hepsiburada.com/staticPage/13390), sepetten teslimat seçimine ve onaya ilerleyen süreci tarif ediyor. Bu hizmetin ürün boyutu ve kategori kısıtları var; mobilyalara otomatik uygulanamaz. Resmî [kapıdan iade anlatımı](https://www.hepsiburada.com/kapinda-iade), siparişten talep açma, teslim alma yöntemi ve randevu seçme adımlarını açıklıyor. Bunlar yardım içeriğiyle doğrulandı; hesap içi işlem yapılmadı.

## Erişim durumu

| Akış | Gözlem |
| --- | --- |
| Anasayfa, kategori, ürün içeriği | Resmî web içeriği okunabildi; canlı görsel yerleşim doğrulanmadı. |
| Masaüstü ve mobil mağaza ekranı | Her iki görünümde 403. |
| Arama otomatik önerileri, mega menü etkileşimi | Davranış gözlemlenmedi. |
| Sepet ve favori değişiklikleri | Başarı/kalıcılık akışı gözlemlenmedi; resmî teslimat anlatımı sepet adımını doğruluyor. |
| Giriş, kayıt, adres defteri | Formlar ve akışlar gözlemlenmedi; tahmini rota kullanılmadı. |
| Sipariş ve kargo ayrıntısı | Sipariş hedefi ve resmî yardım anlatımı mevcut; hesap ekranları doğrulanmadı. |
| Destek | Hedef adres doğrulandı; dinamik içerik okunamadı. |

## NODENO uygulama matrisi

Bu bölüm uygulama önerisidir; geliştirme veya canlı kabul kanıtı değildir. Marka, logo, palet, slogan ve mobilya içeriği NODENO olarak kalır.

| Alan | Masaüstü | Mobil | Gerçek veri sınırı |
| --- | --- | --- | --- |
| Başlık ve arama | Belirgin arama; hesap, favori ve sepet erişimi; oda gruplarına açılan kategori paneli. | Arama ayrı satır; dokunulabilir kategori açılımı ve kısa alt gezinme. | Öneriler 667 ürünün adı, kodu ve gerçek kategorilerinden gelir. |
| Ürün listesi | Filtre alanı, sonuç sayısı, sıralama ve düzenli kartlar. | İki sütun; filtre ve sıralama çekmecesi; seçili filtreleri temizleme. | Fiyat onaylanmadan tutar filtresi/sıralaması etkin sayılmaz. Satış, indirim ve puan verisi yoksa bunları gerektiren sıralamalar sunulmaz. |
| Ürün sayfası | Galeri ve seçim özeti; açıklama, ölçü ve kullanım bilgileri. | Kaydırılabilir galeri; kalıcı ana eylem; açılır ayrıntılar. | Kaynakta bulunmayan özellik uydurulmaz; üretici stok kaydı satış sözü yapılmaz. |
| Sepet ve favoriler | Adet, silme, kaydetme, geri dönme ve görünür toplam durumu. | Aynı kurallar; toplam ve devam eylemi erişilebilir kalır. | Onaylı fiyat ve ödeme hesabı olmadan ödeme tamamlandı veya sipariş alındı denmez; teklif listesi açıkça belirtilir. |
| Hesap ve adresler | Hesap alanı; adres oluşturma/düzenleme; sipariş listesi. | Kısa formlar ve alan doğrulaması. | Gerçek oturum, sunucu saklama ve yetkilendirme gerekir. Yerel liste hesap sistemi diye sunulmaz. |
| Sipariş ve destek | Gerçek kayıt ayrıntısı, durum ve yardım geçişi. | Aynı bilgi daha dar düzende. | Sipariş/gönderi kaydı yoksa dürüst boş durum; sahte sipariş, kargo, değerlendirme ve kampanya yok. |

Kabulte 1366, 768 ve 390 genişlik; klavye ve dokunma; dört dil ile Arapça sağdan sola düzen; arama→ürün→liste/sepet→geri dönüş; yenilemede kalıcılık ve boş/hata durumları sınanmalıdır. Haricî ödeme, e-posta ve lojistik sağlayıcısı kurulmadan bunlara bağlı işlemler çalışıyor sayılmaz.
