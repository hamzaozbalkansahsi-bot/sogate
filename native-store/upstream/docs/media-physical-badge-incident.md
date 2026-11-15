# Fiziksel marka baskısı olayı — 1 Kasım 2026

Studia 510 ürününün `3547:5` fotoğrafındaki Adore plakası önceki OCR/küçük plaka taramasından sıfır eşleşmeyle geçmiş ve kaynak dosya değiştirilmeden onaylanmıştı. Kullanıcının gösterdiği baskı kaynakta mevcuttu; sorun önbellek değildi. Kaynak SHA-256: `52cc037d836992eca6e674ca69d41b35fa4569da16cd86955f2e4c6af29b10be`.

## Düzeltme kapsamı

Beş Studia 510 renk galerisinin tamamı incelendi. Ceviz ve Florida meşe galerilerindeki 16 dosya düzeltildi. Ek tarama ve kardeş ürün galerisi incelemesi; KTP, SHC, SFN, CMS, RAF, RSH, RKM/RMS, GRD, SWD ve TMU ailelerinde, bazı yaşam alanı fotoğraflarının arka planındaki mobilyalarda ve çok ürünlü montajlarda başka baskılar da buldu.

Bu olayda **308 ek görsel referansı** düzeltildi. Önceki 244 düzeltmeyle güncel seçim **552 temizlenmiş / 4577 değiştirilmemiş**, toplam **5129 katalog referansı**dır. Her yeni seçimin kaynak/çıktı hashleri, baskı maskeleri, tam ürün ve büyütülmüş alan incelemesi, reddedilen/yenilenen adayları ve son seçim makbuzu saklandı. Bir fotoğraftaki birden fazla baskı ayrı alanlar olarak ele alındı.

Orijinaller değiştirilmedi. Çıktıların boyutu, yönü, ICC profili ve alfa kanalı korundu. Maske dışındaki çözülmüş RGB birebir aynı kaldı; tamamen saydam piksellerin görünmeyen RGB değerleri de değişmedi. Saydam kenarlardaki görünür baskı pikselleri için alfa >0 alanında dar rötuşa izin verildi; alfa değişikliği ve tamamen görünmeyen piksele taşan maske testlerle reddedilir.

## Tekrarını engelleyen kontroller

- `data/media-brand-incidents.json` 308 doğrulanmış kaynağın URL anahtarını, SHA-256 değerini ve baskı alanını tutar. Bilinen hatalı kaynak baytları, otomatik tarama boş dönse bile çıktı olarak yeniden onaylanamaz; aynı baytları kullanan diğer URL kayıtları da kapsanır.
- `scripts/media-physical-badge-audit.py` 21 gerçek plaka örneğiyle tarar. `scripts/media-complete-badge-audit.py` yedi ek gerçek çıplak/gri/kırmızı/ahşap yazı örneğini ekler ve önceki sonuçları yalnız aynı dosya, kare ve rapor hashleriyle devralır. Kanonik 28 örnek ve son tarama sürümü `data/media-audit-policy.json` içindedir.
- Bir karede dört eşleşmeden sonra durulmaz. Bütün kaynak ve güncel çıktılar; animasyonların her karesi ve saydam görsellerin siyah/beyaz bileşimleri taranır. Son envanter **5427 farklı kaynak/çıktı dosyasını**, 5129 kaynak ve 5129 güncel çıktı referansını kapsar.
- Görsel kararlar tam dosya/kare/bileşim/alan kimliğiyle bağlıdır. Önceki kararlar yalnız aynı rapor veya aynı gerçekten incelenmiş raster alanı için devralınır. Fiziksel/yazı taramasında 701, alev taramasında 4109 son eşleşmenin kararı vardır; güncel çıktıda gerçek marka eşleşmesi yayını durdurur.
- Yayın kanıtı güncel durumları, kaynak/çıktı hashlerini, aday/seçim makbuzlarını, bütün rapor baytlarını ve eşleşme kararlarını kapsar. Eski `publicationReady: true` tek başına kullanılamaz. Node derleme/Drive ve Python yükleme/yayın yolları eksik/eski kanıtı reddeder. Paket katalog medya sürümü ile yayın medya sürümü eşleşmelidir.

Sıfır otomatik eşleşme, değişmemiş bütün görsellerin insan tarafından tek tek incelendiği veya bilinmeyen her marka baskısının mutlak olarak yakalanacağı anlamına gelmez. İnceleme kayıtları yalnız gerçekten görülen alan/hashler ve birebir aynı raster alanı için geçerlidir.

## Denetim kayıtları

Çalışma kanıtları `artifacts/media-badge-incident/` altındadır: sekiz seçim grubu, kaynak/çıktı yakın planları ve tam ürün sayfaları, koordinat ızgaraları, tarama logları ve son eşleşme kararları. `extra` ve `round2`…`round7` grupları ilk Studia grubunu izler.

Geliştirme sırasında yanlış varsayılan eşleştiriciyle üretilen 39 ara rapor yayımdan önce durdurulup karantinaya alındı; bunlardan türemiş ek tarama raporu yoktu. Hepsi doğru sabit eşleştiriciyle yeniden tarandı ve son tam CLI taramasıyla kapsandı. Kayıt: `invalid-checkpoint-reports.json` ve `invalid-checkpoint-quarantine/`. Animasyon taraması aynı sabit kare eşleştiricisiyle paralel yürütüldü; iki gerçek örnek karesinde sıralı/paralel rapor eşitliği doğrulandı. Ara taramalar kapsam makbuzu üretmez; son CLI envanterin tamamını doğrular.

## Yerel ve canlı kabul

Son yayın kapısı geçti ve `publicationReady: true` üretildi. Üretim derlemesi, **158 Node testi (0 başarısız/0 atlanan)**, 81 Python medya testi, 18 cPanel testi ve 9 yükleme testi geçti. Son politika ile finalizer 18 ve tarayıcı eşleştirici 8 testi ayrıca yeniden geçti. Mevcut paket dosya listesinin gerisinde kalmış bir test beklentisi, dört mevcut özel PHP dosyasını da hash denetimine alacak şekilde güncellendi; hesap uygulaması değiştirilmedi.

İzole pakette Chromium masaüstü/mobil 16 ve WebKit mobil 8 ürün/dil/boyut birleşimi geçti: 216 galeri görüntüsü için hash kontrolü, büyütme, TR/EN/RU/AR, RTL, taşma ve hata yanıtı denetimleri. Bildirilen 6/11 fotoğrafının ekran görüntüleri gerçekten incelendi. İlk yerel sağlık isteğinde soğuk kasa kontrolü istemci zaman aşımına takıldı; denetim istemcisinin bekleme süresi artırılıp kontrol tamamlandı. Mobil senaryo, gizli küçük resimler yerine görünür galeri kontrollerini kullanacak şekilde düzeltildi. Bunlar ürün arayüzü değişiklikleri değildir.

**Yerel kabul: PASS. Canlı kabul: PASS.** 1 Kasım 2026 tarihinde medya düzeltmesi yedekli olarak yayımlandı.

- Yayın: `02efc3db7efcdc592c1e887900b6dbfcf3470a741ae026bc7179dfd9e48f4e70`.
- Medya sürümü: `557e3ba73d5bf21426518dd2be426a613a97767d742a1f7f248e9ec8b109260a`.
- 308/308 değişen canlı görselin HTTPS gövdesi, boyutu, MIME türü, SHA-256 başlığı ve ETag değeri beklenen çıktı ile eşleşti. Bildirilen `3547:5` için eski sürüm parametresi ve eski ETag ile yapılan istek de yeni temiz dosyayı döndürdü.
- `nodenohome.com`, `www.nodenohome.com`, `nodenohome.com.tr`, `www.nodenohome.com.tr` aynı yeni sürümü ve aynı temiz görseli verdi; ziyaretçinin alan adı korundu.
- Canlı Chromium masaüstü/mobil 16, WebKit mobil 8 birleşim geçti: toplam 216 galeri görüntüsü için hash kontrolü, büyütme, dört dil, RTL ve taşma/hata denetimleri. Bildirilen fotoğrafın masaüstü/mobil büyütme görüntüleri ve ilgili diğer dil/renk ekranları gerçekten incelendi.
- Yayın sonrasında 27 genel varlık ve iki giriş dosyasının baytları tabanla aynı bulundu. Yedi özel paket dosyası doğrulandı: küçük metinler kimlik UTF-8 okumasıyla, katalog ham API gövdesiyle, onaylı medya manifesti baytları doğrulanmış PHP çalışma zamanının zorunlu SHA-256 kontrolü ve sağlık yanıtıyla karşılaştırıldı. Hesap kodu/yapılandırma aynı kaldı; veri deposu ve kasa kökleri korundu.
- Yedek: `20261101T022718Z-02efc3db7efc-be896f`. Uzak silme veya mevcut kullanıcı verisi üzerine yazma yapılmadı.

Son kanıtlar: `artifacts/media-badge-incident/delivery-record.json`, `live-media-verification.json`, `live-health-after.json`, `remote-base-check-after.json` ve `browser-{local,local-webkit,live,live-webkit}/report.json`.

Kabul senaryosundaki iki varsayım da gerçek sözleşmeye göre düzeltildi: katalog yanıtı `public, max-age=300` kullanırken uygulama katalog isteğini `cache: no-cache` ile yeniden doğrular; canlı uygulama dosyasının hash ve bu istek davranışı kontrol edildi. Bu hostun metin okuma API'si 1 MB üstündeki dosyaları reddeder ve varsayılan HTML karakter kodlama dönüşümü meta etiketini yeniden düzenler; küçük dosyalar açık UTF-8/HTML dönüşümü kapalı, büyük JSON dosyaları yukarıdaki ham gövde/çalışma zamanı hash yollarıyla doğrulandı. Üretim dosyaları bu kontroller için değiştirilmedi.

Medya paketi canlı sürüm `33a750d6c4b199c8222b236ceaa0a68d8f78272126b423d87f7fdda3589825ee` tabanından hazırlandı. İlk `f0836a66…` sürümü çalışma sırasında başka geliştirmelerce değiştirilmiştir; geri yüklenmez. Yalnız özel katalog medya sürümü, onaylı medya JSON'u ve yayın manifesti değişti. Genel varlıklar, hesap kodu, yapılandırma, ürün/kategori verileri ve fiyatlar tabanla aynı kalır. Hesap deposu ve medya kasası sürüm dizini dışında korunur.
