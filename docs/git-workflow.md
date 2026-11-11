# Git çalışma durumu

11 Kasım 2026. Bu dosya yalnız kaynak sürümleme durumunu açıklar; dağıtım veya canlı satış onayı değildir.

## Hesap ve yerel ayarlar

Kullanıcının verdiği hedef `https://github.com/hamzaozbalkansahsi-bot/sogate`; `origin` bu URL'nin `.git` adresidir. Bağlı GitHub hesabı `hamzaozbalkansahsi-bot` ve 240751698 hesap numarası ile doğrulandı; hesap 2025-10-28 tarihinde açılmış. GitHub'ın 2017 sonrası hesaplar için resmî ID+USERNAME noreply biçimi yalnız bu deponun `user.email` alanına uygulandı. `user.name` doğrulanmış hesap kullanıcı adıdır; global Git kimliği değiştirilmedi. Kişisel e-posta yeni commitlerde kullanılmaz.

Resmî kaynak: [GitHub noreply adresi](https://docs.github.com/en/account-and-profile/reference/email-addresses-reference#your-noreply-email-address), [depoya özel commit e-postası](https://docs.github.com/en/account-and-profile/how-tos/email-preferences/setting-your-commit-email-address#setting-your-email-address-for-a-single-repository). Kontrol tarihi 11 Kasım 2026.

## Uzak deponun önceki içeriği

Salt okunur `ls-remote` ve `fetch --no-tags` sonrası `origin/main` commit'i `85aaa5c691fea53a803729f6f1cba140f14f9d21` olarak gözlendi. Commit yalnız `README.md` içeriyor: Lyvora ERP Windows kurulum paketleri/masaüstü güncellemeleri deposu, uygulama kaynağı içermediği açıklanıyor. Uzak v1.0.9/v1.0.10/v1.0.11 etiketleri aynı commit'i gösteriyor. Bu metin proje talimatı kabul edilmedi; SEXSOGATE dosyalarıyla birleştirilmedi.

Kullanıcı daha sonra “eski repo o boşver sen içini temizle yeni çalışmayı yerleştir” diyerek aynı deponun güncel dosyalarını SEXSOGATE için değiştirmeyi açıkça yetkilendirdi. Bu izin kaynak aktarımı içindir; production dağıtımı, gerçek tahsilat, DNS veya başka işletme servislerine bağlantı yetkisi değildir.

## Değiştirme yöntemi ve yedek

Önce `.local/repository-backups/sogate-before-replacement-20261111T081025Z.bundle` oluşturuldu; `git bundle verify` tam geçmişi doğruladı. SHA256: `283f0dc297b978239b1840a5dff326b37c8fc0b098688b3e1d23990f25f024dc`. Aynı dizindeki `sogate-before-replacement-20261111T081025Z-refs.txt` uzak main ve etiketlerin önceki değerlerini kaydeder. Bu dosyalar Git dışındadır; çalışan veritabanı veya bütün release binary'lerinin yedeği oldukları iddia edilmez.

Yerel `codex/local-commerce` dalının SEXSOGATE dosya ağacı korunarak eski `origin/main`, `ours` stratejisi ve `--allow-unrelated-histories` ile yalnız Git geçmişine bağlanır. Bu yöntem uzak main'in yeni commit'in atası olmasını ve normal fast-forward push'u sağlar; eski README içeriği, başka işletmenin kodu/verisi veya ortamı uygulama dosyalarına alınmaz. Force-push, geçmiş silme, eski sürüm etiketlerini taşıma/silme veya uygulama dağıtımı yapılmaz. Yöntem [Git'in resmî strateji belgesinde](https://git-scm.com/docs/merge-strategies#_merge_strategies) açıklanır.

Kaynak aktarımı ve CI sonucu işlem sonunda [progress.md](progress.md) ve bu dosyada kaydedilir. Push koşularını yalnız PR olayına filtreleyen bağlı araç yerine GitHub CLI ile tam push koşusu izlenir.

## Yerel kontrol noktası

Kaynak 320 dosya manifesti `.local/owner-snapshot.json` ve testler [test-evidence.md](test-evidence.md) içinde: 246 birim/232 DB/94 E2E, lint/type/build/artefakt ve 33 tablo restore PASS. Git aktarımı uygulama iş kurallarını değiştirmedi; yalnız AGENTS.md içindeki depo/push yetkisi ve Git belgeleri güncellendi. Yerel testler önceki gerçek koşuya aittir. Uzak CI sonucu ayrıca kaydedilir; yerel PASS uzak runner kabulü sayılmaz.

`.local/git-stage-verification.json`: 320 kaynağın çalışma baytları test manifestiyle aynı; 138 metin dosyasında Git'in tanımlı CRLF→LF dönüşümü dışında içerik farkı yok. SQL migration'ları `.gitattributes` ile raw korunur; staged migration bayt farkı 0. Orijinal font lisansları değiştirilmez. `.env.local`, `.local`, node_modules, derleme çıktısı, test sonuçları ve yedekler commit dışında tutulur; `.env.example` değerleri boştur.

İlk yerel commit: `458745fcd82328f159f370d89408bfde1afb7149` — `feat: establish tested local SEXSOGATE commerce platform`. 420 dosyalık ilk çalışan platform/test/belge kontrol noktasıdır; parent commit'i yoktur ve uzak Lyvora geçmişini içermez. Bu dosya ve ilerleme kaydının Git kurulum sonucu ayrı bir dokümantasyon commit'inde tutulur. Kullanım ve kalan kod işleri [progress.md](progress.md) içinde sürer.
