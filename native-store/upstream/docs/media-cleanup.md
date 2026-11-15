# Ürün görseli marka temizleme hattı

Bu akış, katalogdaki ürün görsellerinin içine işlenmiş tedarikçi marka işaretlerini kodla topluca temizleme ve sonucu doğrulama işi için orijinalleri hazırlar. İndirme aşaması görüntüyü değiştirmez; kaynak katalog ve indirilen orijinal dosyalar temizleme aşamasının girdisi olarak korunur. Temizleme ve yayın için ayrıca temizlenmiş çıktı ve kontrol sonucu gerekir; yalnız indirme tamamlanması görsel temizliği tamamlandı anlamına gelmez.

## Kaynak ve envanter

Kaynak `data/catalog-source.json` dosyasıdır. Mevcut katalog 667 ürün, 5.129 ürün/görsel başvurusu ve 5.129 benzersiz URL içerir. URL aynı olduğunda yalnız bir dosya indirilir; tüm `ürünKimliği:görselİndeksi` eşlemeleri korunur. Kaynak dosya SHA256 özeti manifestte tutulur; katalog değişmişse eski manifestle devam edilmez.

`scripts/media-download.py` Python 3.11 veya üstü ve Pillow gerektirir. İndirme doğrulamasında OpenCV veya OCR gerekmez. İlk uygulama ortamında Python 3.12, Pillow 12.3.0 ve OpenCV headless 5.0.0.93 bulunmuştur; OCR/temizleme ortamı ayrı hazırlanır. Depoya veya sisteme genel paket/ayar değişikliği yapılmaz.

## Kullanım

Varsayılan çağrı salt plan üretir; ağ isteği veya dosya yazımı yapmaz:

```powershell
python scripts/media-download.py
```

Yetkilendirilmiş toplu indirmeyi başlatmak veya kesilen indirmeye devam etmek için:

```powershell
python -u scripts/media-download.py --apply --workers 10 --rate 8
```

`--workers` 1–12 arası eşzamanlı işçi sayısıdır. Varsayılan 10 işçi ve küresel saniyede 8 istek sınırı kullanılır; yönlendirmeler ve yeniden denemeler de aynı sınıra dahildir. `--rate` 0,5–12 aralığındadır. Yükü azaltmak için daha düşük değer seçilebilir. `--attempts` en fazla 3, bağlantı/okuma `--timeout` değeri 5–60 saniye arasındadır. Geçici hatalar en fazla 3 kez, 0,5/1 saniyelik beklemeyle denenir; sunucunun `Retry-After` değeri en fazla 5 saniyeye kadar dikkate alınır. Kalıcı MIME, görüntü veya URL hatası tekrar indirilmez. `--limit 12` yalnız ilk eksik 12 URL ile deneme yapar; manifest kalan görselleri beklemede tutar.

İndirme sonrası salt okunur denetim:

```powershell
python scripts/media-download.py --verify-only
```

Bu denetim manifestteki tamamlanmış her dosyanın SHA256 ve boyutunu yeniden hesaplar; ağ isteği veya yazma yapmaz. Tam kapsama varsa çıkış kodu `0`, eksik/bozuk dosya varsa `2` döner. `--apply` bozuk/eksik dosyaları yeniden indirir; yalnız önceden doğrulanmış ve güncel dosya özeti eşleşen kayıtlar atlanır. Başarılı ağ aktarımı daha önce Pillow tarafından doğrulandığından, aynı SHA256 eşleşmesi aynı doğrulanmış baytları yeniden kullanır.

Tüm çıktı yolları aynı deponun `artifacts/` ağacı içinde kalmak zorundadır. Kaynak katalog ile çıktı/manifest/ilerleme dosyaları çakışamaz; sembolik bağlantılı çıktı yolları reddedilir. Uygulama, sistem PATH'i, diğer projeler, site yayını veya kimlik bilgileri üzerinde değişiklik yapmaz.

## İndirme ve içerik doğrulaması

Yalnız tam `witcdn.adoremobilya.com` alan adına HTTPS üzerinden, varsayılan veya 443 portuyla erişilir. URL içinde kullanıcı/parola, parça, boşluk, kontrol karakteri veya ters eğik çizgi reddedilir. Otomatik HTTP yönlendirmesi kapalıdır; en fazla üç yönlendirme her adımda aynı kurallarla doğrulanır. Sistem güven kökleriyle TLS sertifika ve sunucu adı kontrolü zorunludur. Ortam proxy kimlik bilgileri, oturum çerezleri veya kaydedilmiş giriş bilgileri kullanılmaz.

Her dosyada hem `Content-Length` hem gerçekten okunan veri için 20.000.000 bayt sınırı uygulanır. JPEG, PNG, WebP, AVIF ve GIF kabul edilir. Bildirilen MIME ile Pillow'un belirlediği gerçek biçim eşleşmelidir. `Image.verify()` yapısal kontrolü sonrasında dosya yeniden açılır ve bütün kareler bellekte biriktirilmeden sırayla yüklenir. Kare başına 50 milyon piksel, toplam 1 milyar kare-piksel ve 1.000 kare sınırı uygulanır. Her kare öncesi ve sonrası kontrol edilen dosya başına 60 saniyelik çözme bütçesi vardır. Aynı anda en fazla iki görüntü çözülür; böylece indirme paralelliği görüntü belleğini sınırsız büyütmez. Dosya adının uzantısı URL'den değil gerçek görüntü biçiminden üretilir.

Her başarılı dosyada gerçek bayt SHA256 özeti, bayt sayısı, genişlik, yükseklik, biçim, MIME ve kare sayısı kaydedilir. Yeni doğrulama sonuçlarında `decodedFramePixels` toplam çözülmüş kare-piksel sayısını, `durationMs` animasyonun toplam kodlanmış süresini belirtir; önceki sürümün doğrulanmış kayıtlarında bu iki alan bulunmayabilir. Yarım/bozuk aktarımlar geçici `.part` dosyasından nihai dosyaya geçirilmez; başarısız geçici dosya temizlenir. Orijinal veri üzerinde kırpma, yeniden sıkıştırma veya logo kaldırma bu betikte yapılmaz.

## Çıktı sözleşmesi

- `artifacts/media-originals/{sha256(URL)}.{gerçekUzantı}`: doğrulanmış, değiştirilmemiş orijinal.
- `artifacts/media-download.json`: tüm kaynak eşlemeleri ve doğrulama durumu.
- `artifacts/media-download-progress.jsonl`: her sonuç için zaman, URL özeti, durum, deneme sayısı, bayt ve sabit hata kodu. Konsola yalnız toplu ilerleme yazılır; ham ağ hata metni, kimlik bilgisi veya URL sorgusu yazılmaz.

Manifest, en az her 25 sonuçta veya iki saniyede bir geçici dosyaya yazılıp `os.replace` ile atomik değiştirilir. Temizleme işlemi dosyayı okurken eksik JSON görmez. Çalışma sonunda son durum ayrıca kaydedilir. Beklenmedik kesinti sırasında indirilmiş ama henüz manifeste alınmamış az sayıdaki dosya sonraki çalışmada yeniden indirilebilir; doğrulanmamış dosya tamamlanmış sayılmaz.

```json
{
  "schemaVersion": 1,
  "sourceCatalogSha256": "kaynak-katalog-özeti",
  "totals": {"products":667,"references":5129,"uniqueUrls":5129,"verified":0,"failed":0,"pending":5129,"bytes":0},
  "references": {"2393:0":"url-özeti"},
  "images": {
    "url-özeti": {
      "url":"https://witcdn.adoremobilya.com/...",
      "status":"verified",
      "path":"artifacts/media-originals/url-özeti.jpg",
      "sha256":"gerçek-bayt-özeti",
      "bytes":12345,"width":1200,"height":1200,"format":"JPEG","mime":"image/jpeg","frames":1,
      "attempts":1,"lastError":null
    }
  }
}
```

`status` değeri `pending`, `verified` veya `failed` olabilir. Temizleme yalnız `verified` kayıtları ve `path` alanını kullanır; girdi özeti `sha256` ile kontrol edilir. `references` eşlemesi bütün katalog görsellerinin çıktı ile yeniden bağlanması için kullanılır. Birden fazla kare içeren GIF/WebP/AVIF dosyalarında bütün kareler ayrıca temizleme ve görsel kontrol kapsamına alınmalıdır.

## Testler

```powershell
python -m unittest tests/media_download_test.py
```

Testler ağdan bağımsız olarak tam alan adı ve yönlendirme kısıtını, gerçek veri boyutu sınırını, MIME/bozuk görüntü reddini, tam çözme metaverisini, en fazla üç denemeyi, TLS doğrulama ayarını, kaynak değişmeden deduplikasyonu, değiştirilmiş dosyanın yeniden işlenmesini, dizin dışına çıkış engelini ve atomik manifest yazımını denetler. Gerçek CDN indirmesi ayrıca TLS ve içerik doğrulamasından geçer.

Pillow'un [Image.verify / load](https://pillow.readthedocs.io/en/stable/reference/Image.html) ve Python'un [urllib.request yönlendirme davranışı](https://docs.python.org/3/library/urllib.request.html#urllib.request.HTTPRedirectHandler) belgeleri indirme doğrulamasının dayanağıdır.
