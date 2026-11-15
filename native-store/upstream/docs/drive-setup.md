# NODENO ürün görsellerini özel Google Drive hesabına taşıma

**Güncel karar:** Kullanıcı Drive aşamasını erteledi. Yayının görselleri doğrudan Turhost'ta barındırılır. Aşağıdaki adımlar ileride Drive aktarımına dönülmesi içindir; mevcut yayının tamamlanma koşulu değildir. Belirlenen gelecek hedef hesap `nodenohome@gmail.com` adresidir.

Yeni hedef Google hesabı ve klasörü bu değişiklikte bağlanmadı; gerçek Drive yazımı yapılmadı. Aktarım aracı yalnız onaylanmış **yerel temiz görselleri** yükler. Ham tedarikçi CDN'sinden indirme veya eksik dosya için kaynağa geri dönüş yoktur. Mevcut üretim görsel kasası Turhost'tadır; Drive aktarımı ve canlı Drive bağlantısı ayrı tamamlanma koşullarıdır.

Kataloğun tüm 5.129 görsel referansı onaylanmadan, `artifacts/media-cleanup.json` içindeki `publicationReady` tam olarak `true` olmadan ve gerçek dosyaların SHA256/ölçüleri doğrulanmadan yükleme kapalıdır. `--limit 1` bu kapıyı aşmaz: önce tüm katalog denetlenir, ardından seçilen yükleme kapsamı uygulanır.

## Hesap ve klasör

1. NODENO için kullanılacak bireysel Google hesabını siz oluşturun ve iki adımlı doğrulamayı açın.
2. Bu hesapta `NODENO Ürün Görselleri` adında yeni bir **paylaşılmamış My Drive klasörü** oluşturun. Klasörü veya görselleri “bağlantıya sahip herkes” erişimine açmayın. Araç, paylaşılmış klasörü ve ortak Drive'ı reddeder.
3. Google Cloud projesinde Drive API'yi etkinleştirin; kendinize ait OAuth uygulamasını yapılandırın. Masaüstü istemcisi kullanırken sistem tarayıcısında izin verin; uygulama PKCE ve loopback dönüş adresiyle yetkilendirilmelidir. Google'ın [masaüstü OAuth kılavuzunu](https://developers.google.com/identity/protocols/oauth2/native-app) izleyin.
4. Uygulamanın erişeceği dosyalar için Google'ın önerdiği `drive.file` kapsamını kullanın. Önceden tarayıcıdan oluşturulmuş klasörü bu kapsamla kullanmak için aynı OAuth uygulamasının Google Picker akışından klasörü seçerek uygulamaya izin vermeniz gerekir. Bu seçim yapılmazsa klasör API'de bulunamayabilir. Sırf bu hatayı aşmak için tüm Drive'a erişen `drive` kapsamına geçmeyin. Ayrıntılar: [Drive kapsamları](https://developers.google.com/workspace/drive/api/guides/api-specific-auth).
5. Erişim belirtecini yalnız çalıştırılan işlemin ortam değişkenine verin. Hedef yeni hesabın adresi ve hedef klasör kimliği açıkça belirtilmelidir. Araç ilk Google isteği olarak [Drive `about.get`](https://developers.google.com/workspace/drive/api/reference/rest/v3/about/get) üzerinden `user.emailAddress` değerini okuyup hedef hesapla karşılaştırır; eşleşmeden klasör işlemi veya dosya oluşturma yapılmaz. Parola, access token, refresh token ve istemci sırrını sohbete, komut satırı argümanlarına, kaynak koda veya Git'e yazmayın.

| Ortam değişkeni | Kullanım |
| --- | --- |
| `GOOGLE_ACCESS_TOKEN` | Yalnız `--apply` / `--upload` için gerekli, kısa ömürlü OAuth erişim belirteci. |
| `GOOGLE_DRIVE_FOLDER_ID` | Kullanıcının seçtiği hedef klasörün gerçek kimliği; `--folder ID` ile de verilebilir. |
| `GOOGLE_DRIVE_ACCOUNT_EMAIL` | Zorunlu açık hedef hesap adresi; `--account-email EMAIL` ile de verilebilir. |
| `GOOGLE_EXPECTED_EMAIL` | Eski çağrılar için hedef hesap adresi takma adı; yeni alan veya seçenek verilmemişse kullanılır. |

Araç OAuth hesabı veya hedef klasör oluşturmaz, yetki kapsamını yükseltmez ve belirteçleri saklamaz. Önceden bağlı başka bir Google hesabı, yeni hedef hesabın yetkisi yerine kullanılamaz. Klasör mevcut hesapça sahip olunan, yalnız sahibine izin veren, paylaşılmamış, yazılabilir bir My Drive klasörü olmalıdır; sahiplik/izin bilgisi eksikse işlem durur. Süresi biten belirteçte aktarım durur. Aynı hesap ve **aynı OAuth istemcisiyle** yeni belirteç alıp aynı manifestle devam edin; `appProperties` uygulamaya özeldir.

## Önce kuru çalışma

Proje dizininden Node.js 22 veya daha yenisiyle çalıştırın:

```powershell
node scripts/drive-migrate.mjs --dry-run
```

Bu komut katalogdaki her ürün/görseli sayar ve yerel onay durumunu raporlar. Son onay hazırsa tüm kaynak/çıktı dosyalarının yerel bütünlüğünü de denetler. Google'a bağlanmaz, kimlik bilgisi ortam değişkenlerini okumaz, görsel indirmez, yükleme yapmaz veya manifest yazmaz. `--apply` veya eski adı `--upload` verilmedikçe varsayılan davranış budur.

Rapordaki `approval.status` değeri `pending` ise son onay beklenir; `invalid` ise kapsam/dosya/özet/ölçü tutarsızlığı vardır. Yalnız `verified`, `publicationReady:true` ve tüm görsellerin yerel doğrulaması yükleme ön koşulunu karşılar. Kuru çalışmanın çıkış kodu `0` olması tek başına yayın onayı veya Google yetkisi değildir.

Tüm onaylar tamamlanıp **doğru yeni hesap ve özel klasör için erişim açıkça verildikten sonra**, önce tek görselle gerçek hesap/klasör denemesi yapın:

```powershell
node scripts/drive-migrate.mjs --apply --limit 1
```

Drive arayüzünde dosyanın doğru yeni hesapta, doğru özel klasörde ve doğru görüntüyle oluştuğunu kontrol edin. Ardından tam aktarım:

```powershell
node scripts/drive-migrate.mjs --apply --concurrency 2
```

Diğer seçenekler:

```powershell
node scripts/drive-migrate.mjs --help
node scripts/drive-migrate.mjs --dry-run --catalog data/catalog-source.json
```

Varsayılan manifest `artifacts/drive-manifest.json` dosyasıdır. Bu dosyayı yedekleyin; web istemcisine veya açık Git deposuna koymayın. İşlem çalışırken manifesti değiştirmeyin. `--manifest` ile başka manifest seçebilirsiniz, ancak ilk aktarımın kimliklerini kaybetmeyin. Normal çalışmada kilit dosyası otomatik silinir. İşletim sistemi beklenmedik biçimde kapanırsa `.lock` dosyası kalabilir; ilgili PID'nin çalışmadığını doğruladıktan sonra yalnız bu kilidi kaldırın. Manifesti silmek aktarım kurtarma kayıtlarını kaybettirir.

## Doğrulama ve devam etme

- `artifacts/media-download.json` ve `artifacts/media-cleanup.json`, bütün katalogdaki `productId:index` anahtarlarını ve URL SHA256 eşlemelerini tam karşılamalıdır. Tek bir eksik, onaysız, karantinadaki veya `testOnly` kayıt yüklemeyi durdurur. Manifestteki toplam sayaç tek başına kanıt sayılmaz.
- Kaynak URL'nin HTTPS ve izinli alan adı, yalnız özel provenance kaydı olarak doğrulanır; bu URL'ye ağ isteği yapılmaz. Kaynak dosya özeti, temizleme kaydındaki `sourceSha`, gerçek çıktı `outputSha`, boyut ve ölçüler derlemeyle aynı `lib/media-approvals.mjs` denetiminden geçer.
- Yükleme baytları yalnız `artifacts/media-cleaned/` altındaki manifest yolundan okunur. Dizin dışına çıkan yol ve sembolik bağlantı reddedilir. `approved_cleaned` ve `approved_unmodified` durumları kabul edilir; ikincisinde çıktı orijinal baytlarla da eşit olmalıdır. Her dosya yüklenmeden hemen önce yerel özet ve ölçü yeniden kontrol edilir; değişmiş dosya CDN'den tamamlanmaz.
- JPEG, PNG, WebP, GIF ve AVIF gerçek dosya imzası/ölçüsüyle tanınır. HTML/SVG ve 20.000.000 bayt üstü içerik reddedilir. Drive MIME türü ve dosya uzantısı onaylı gerçek çıktı biçiminden gelir; kaynak URL uzantısı kullanılmaz.
- Eşdeğer içerik SHA-256 özetiyle tek Drive dosyasına bağlanır; farklı ürünler aynı dosyayı kullanabilir.
- Dosya oluşturmadan önce Google'dan dosya kimliği alınır ve manifestte saklanır. Bağlantı kesildiğinde aynı kimlikle devam edilir; sonucu belirsiz bir yükleme ikinci dosyaya dönüştürülmez. Google [önceden kimlik üretimini](https://developers.google.com/workspace/drive/api/reference/rest/v3/files/generateIds) destekler.
- Yüklemeden sonra Drive'dan dosya yeniden okunur; klasör, MIME türü, boyut, SHA-256 özelliği ve Google'ın MD5 özeti karşılaştırılır. Yalnız doğrulanan kayıt `uploaded` olur.
- Varsayılan tek aktarım işçisi vardır, en fazla üç olabilir. Kota ve geçici ağ hataları sınırlı artan beklemeyle yeniden denenir. Yetki hataları gizlenmez ve ham API mesajları/belirteçleri yazdırılmaz. [Google hata işleme kılavuzu](https://developers.google.com/workspace/drive/api/guides/handle-errors) temel alınmıştır.
- Çıkış kodu `0`: seçilen kapsam başarılı veya kuru çalışma; `2`: bazı görseller başarısız; `1`: başlangıç/kimlik/manifest gibi aktarımı durduran hata. `--limit 1` başarısı tüm kataloğun tamamlandığı anlamına gelmez.

## Sunucu bağlantısı sözleşmesi

Manifest biçimi `version: 1` ve `images` haritasıdır. Her anahtar katalog ürün kimliği ve görsel sırasının `productId:index` birleşimidir. Başarılı kayıt aşağıdaki alanları içerir; dosya kimlikleri Google API'den gelir, tahmin edilmez:

```text
images[productId + ':' + index] → {
  productId, index, sourceUrl, folderId, fileId,
  sha256, md5, mimeType, extension, size, status: 'uploaded', verifiedAt,
  localPath, approvalState, sourceSha, outputSha, width, height
}
```

`sha256` ve `outputSha` yüklenen temiz çıktı baytlarının özetidir; `sourceSha` özel kaynak kaydının özetidir. `sourceUrl` yalnız özel yerel provenance olarak kalır; Drive dosya metadatasına veya kamuya açık istemciye aktarılmaz. Drive dosyasında `nodeno_source: approved-local-v1` ve gerçek çıktı özeti tutulur. Eski ham görsel aktarım kaydı, temiz çıktı özetiyle eşleşmedikçe devam kaydı olarak kullanılamaz.

Mağaza sunucusu yalnız `uploaded` ve doğrulanmış kayıtları eşlemeli; Drive dosyasını OAuth ile sunucudan okuyup ziyaretçiye kendi `/media/...` adresinden iletmelidir. Google erişim belirteci, refresh token veya özel Drive bağlantısı tarayıcıya verilmez. Drive API [blob içeriğini `alt=media` ile indirmeyi](https://developers.google.com/workspace/drive/api/guides/search-files) destekler.

Canlıda sürekli erişim için kısa ömürlü access token tek başına yeterli değildir. Aynı OAuth uygulamasının `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET` ve `GOOGLE_DRIVE_REFRESH_TOKEN` değerleri yalnız hosting'in gizli ortam değişkenlerinde tutulmalı; sunucudaki yenileme akışı doğrulanmalıdır. İşçi ayrıca kısa ömürlü `GOOGLE_DRIVE_ACCESS_TOKEN` değerini destekler. Bunlar canlı sunucu adlarıdır; yerel aktarım aracının access token adı `GOOGLE_ACCESS_TOKEN` olarak kalır. Bu belge bu sırların girildiği veya canlı Drive bağlantısının çalıştığı iddiasında bulunmaz.

Google Drive arşiv sahipliğini sağlar; herkese açık görsel CDN hizmeti veya sınırsız trafik garantisi değildir. Sunucu önbelleği, Google kota/storage sınırları, hesap güvenliği ve geri yükleme denemesi yayından sonra izlenmelidir. Ekranda gösterilen bir görselin kopyalanmasını teknik olarak tamamen engellemek mümkün değildir; sağ tık ve sürükleme sınırlamaları yalnız kolay kopyalamayı azaltır, ekran görüntüsünü engellemez.

## Yerel doğrulama

`node --test tests/drive-migrate.test.mjs` sahte Google API sınırında gerçek yerel temiz PNG baytlarının gönderildiğini, ham CDN çağrısı bulunmadığını, onaysız/eksik/değişmiş/test girdinin ve ölçü hatasının Google isteğinden önce durduğunu doğrular. Tam ön denetimden sonra değişen çıktı da tekrar reddedilir. Açık hesap adresi zorunluluğu, yanlış hesapta klasör okunmaması, özel klasör izinleri, içerik tekilleştirme, önceden ayrılan kimlikle devam etme ve Drive içerik doğrulaması aynı test kapsamındadır. Bu testler gerçek Drive hesabına erişmez ve canlı aktarım kabulü yerine geçmez.
