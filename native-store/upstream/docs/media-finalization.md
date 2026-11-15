# Son görsel seçimi ve yayın kapısı

`scripts/finalize-media.py` yalnız yerelde çalışır; ağ veya uzak yükleme yapmaz. Varsayılan `--plan` hiçbir dosyayı değiştirmez. `--apply`, açıkça seçilen son dosya hashlerini birleştirir ve `publicationReady:false` bırakır. Ayrı `--publish` işlemi bütün son kanıtları doğruladıktan sonra kapıyı atomik olarak açar. Araç, ilk OCR onayını görsel/yapısal kabul olarak kullanmaz.

Kanonik katalog, indirme manifesti ve ana manifest aynı 5.129 referansı kapsamalıdır. Her kaynak URL ve orijinal dosyanın SHA-256 değeri, boyutu, MIME türü ve boyutları doğrulanır. Başlangıç pipeline kimliği `37fbdbdb594cb9d366fec3cb7f2662a694d4497ea7545607d471d23c3a9ecbd9` olmalıdır. İlk manifestin tam baytları ve bütün eski raporların hash bağları `frozen37fb` altında korunur; bu kanıtlar sonradan değişirse işlem durur.

Root görsel seçimi için örnek makbuz:

```json
{
  "schemaVersion": 1,
  "basePipelineVersion": "37fbdbdb594cb9d366fec3cb7f2662a694d4497ea7545607d471d23c3a9ecbd9",
  "selections": {
    "URL_SHA256": {
      "candidateSha": "SON_DOSYANIN_SHA256_DEGERI",
      "reviewer": "incelemeyi yapan",
      "notes": "Tam görsel ve yakın planda eğri, plaka/dikiş, renk ve artık baskı kontrolü",
      "structureReview": true
    }
  }
}
```

İlk otomatik `approved_cleaned` durumundaki 123 görsel dahil her değişmiş görsel böyle bir seçim ister. Yeni bir aday makbuzunda bulunan, önceden otomatik değiştirilmemiş kabul edilmiş görsel de açık seçim olmadan onaylı kalamaz. Önceki sayfa veya önizleme için verilen kabul başka SHA değerine taşınmaz. Aday makbuzları liste veya URL hashine göre sözlük biçiminde olabilir; `--candidates` tekrarlanabilir. Aynı kaynak için birden fazla yöntem bulunabilir; son dosya hashini seçim belirler.

```powershell
& './artifacts/media-tools/Scripts/python.exe' scripts/finalize-media.py --plan `
  --candidates artifacts/media-review/candidates.json `
  --candidates artifacts/media-ink-margin/candidates.json `
  --candidates artifacts/media-ink-margin/manual-corrections.json `
  --candidates artifacts/media-review-special/candidates.json `
  --selections artifacts/media-finalization/root-selections.json
```

Plan incelendikten sonra aynı girdilerle `--apply` kullanılır. Bu işlem başka dosyalara yazılacak bir genel onay değildir; yalnız makbuzdaki son SHA değerleri seçilir. Başarısız, çözümlenmemiş, artık marka tespiti pozitif veya son OCR/template kontrolü bulunmayan aday reddedilir. Kaynak ve çıktı gerçek decode sonrasında aynı boyutta olmalıdır. Maskeler ikili ve en çok kare alanının %5'i büyüklüğünde olabilir. Maske dışındaki RGB değerleri ile tüm alpha değerleri birebir aynı olmalıdır; maske saydam piksellerle kesişemez. GIF/WebP süreleri ve loop bilgisi korunur; ancak aynı zaman çizgisini ve dış pikselleri koruyan ardışık kare birleştirmesi kabul edilir. Bu sayısal kontroller, maske içindeki ürün geometrisinin doğru olduğuna dair görsel incelemenin yerine geçmez.

Seçilen çıktı `artifacts/media-cleaned/OUTPUT_SHA.uzanti` adına değiştirilmeden kopyalanır. Var olan içerik adresli bir dosya farklı baytlarla değiştirilemez. Orijinaller, eski pipeline çıktıları ve raporları silinmez. Seçim ve aday makbuzlarının tam baytları içerik adresli ayrı kanıt dosyalarına arşivlenir; taslak makbuzun daha sonra genişletilmesi eski kabul kanıtını değiştirmez. Ana manifest yalnız tüm yerel kontrollerden sonra, başlangıç dosya hashinin hâlâ aynı olduğu kontrol edilerek atomik değiştirilir.

Birleştirme tamamlandığında kaynakların tamamını ve **son seçilmiş çıktıları** kapsayan iki frozen tarama ailesi de yeniden çalıştırılmalıdır. Flame ailesinin `passVersion` değeri tam olarak `65506c85586787cd33916d83b7f978e08f94e2d6ac401faaf461d8a1a018a71d` ve iki bilinen flame referansının hashleri sabit sözleşmeyle eşleşmelidir. Küçük yazılı plaka ailesinin sürümü `b5f2f3ed18e09a9d94a1de57d564204cf68b1aa0d437525ddb49420da814c117` ve beş referansı (`adore-physical-badge.png`, `catalog-thin-adore-badge.png`, `tiny-real-badge.png`, `tiny-oblique-word.png`, `tiny-collapsed-word.png`) ayrı sabit hashlerle eşleşmelidir. Önceki sürümler son beş gerçek kaynak kalibrasyonunun tamamını karşılamadığı için kabul edilmez. Aileler birbirinin yerine geçemez; tek aileyle kapı açılamaz.

Kaynak ve son çıktının ICC profil baytları da aynı kalmalıdır. Görüntü yönü EXIF alanında korunur; eksik, `0` ve `1` aynı döndürmesiz davranıştır. Piksel eşitliği tek başına tarayıcıdaki renk ve yön eşitliğini kanıtlamaz. Profil veya yön değişen aday, görsel seçim kaydı olsa da reddedilir.

Eski dosya hashleri önbellekten kullanılabilir; değişen dosya hashleri yeniden taranır. Her ailenin son makbuzunda her 5.129 kaynak ve her 5.129 son çıktı hashine bağlı rol bulunmalıdır. Araç sayaçlara güvenmek yerine bu kapsamı türetir. Her dosyanın bütün kareleri ve gereken beyaz/siyah alpha kompozitleri, frozen tarayıcının şekil/dtype ve RGB baytlarıyla oluşturduğu hash biçiminde doğrulanır. Aşağıdaki hit değerlendirme makbuzu her aile için ayrı hazırlanır; başka ailenin hit kimlikleri veya makbuz hashleri kullanılamaz.

Hit değerlendirme makbuzu:

```json
{
  "schemaVersion": 1,
  "basePipelineVersion": "37fbdbdb594cb9d366fec3cb7f2662a694d4497ea7545607d471d23c3a9ecbd9",
  "passVersion": "SON_TARAMANIN_PASS_VERSION_DEGERI",
  "receiptSha256": "SON_TARAMA_RECEIPT_DOSYASININ_SHA256_DEGERI",
  "hits": {
    "TAM_HIT_ID": {
      "fileSha256": "TARANAN_DOSYANIN_SHA256_DEGERI",
      "reportSha256": "HIT_RAPOR_DOSYASININ_SHA256_DEGERI",
      "visualReview": true,
      "reviewer": "incelemeyi yapan",
      "notes": "Bu tam hit için görülen gerekçe",
      "disposition": "false_positive"
    }
  }
}
```

Bir kaynakta gerçek marka bulunduysa `disposition` değeri `true_brand_cleaned` olur ve `cleanedOutputs` sözlüğü, o kaynak hashine bağlı bütün URL hashlerini son temiz çıktı hashlerine eşler. Bu çıktılar onaylı, değişmiş ve son taramada kapsanmış olmalıdır. **Son çıktıdaki gerçek marka hiti kapıyı daima kapatır.** Son çıktıda kalan her aday hit, tam kimliği ve rapor hashine bağlı açık görsel false-positive değerlendirmesi ister. Bilinmeyen, eski makbuza ait veya eksik hit kimlikleri kabul edilmez.

```powershell
& './artifacts/media-tools/Scripts/python.exe' scripts/finalize-media.py --publish `
  --symbol-receipt artifacts/media-symbol-audit/receipt.json `
  --symbol-dispositions artifacts/media-finalization/root-symbol-dispositions.json `
  --small-badge-receipt artifacts/media-small-badge-audit/receipt.json `
  --small-badge-dispositions artifacts/media-finalization/root-small-badge-dispositions.json
```

Bu komut açık onay durumları, seçim makbuzları, değişmez eski kanıtlar, son dosyalar ve iki ailenin son hit değerlendirmeleri tamamlanmadan `publicationReady:true` yazamaz. Aile doğrulayıcısı ortak kodu kullanır; her birinin sürüm/referans pinleri, kapsamı ve disposition makbuzu bağımsız denetlenir. Son tarama ve hit değerlendirme makbuzlarının tam baytları ayrıca arşivlenir. Üretim derleme/yükleme ve gerçek web/tarayıcı kabulü sonraki ayrı doğrulamalardır.

Sınırlı fixture testleri:

```powershell
& './artifacts/media-tools/Scripts/python.exe' -m unittest discover -s tests -p media_finalize_test.py
```
