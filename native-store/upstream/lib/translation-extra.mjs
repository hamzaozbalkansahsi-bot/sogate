// Curated complete furniture specifications. Index keys refer to the fixed source worklist.
import {extraTranslationsB} from './translation-extra-b.mjs';
import {extraTranslationsC} from './translation-extra-c.mjs';
const source = {
  "320": "Beyaz-Antasit",
  "321": "Masa kontrast renkte tasarlanan çalışma yüzeyi",
  "322": "Pratik açık raf sistemi",
  "323": "Y-19 Butterfly Mekanizma",
  "324": "4D ayarlanabilir Kolçak",
  "325": "Dökme Kalıp Sünger Oturum Minderi",
  "326": "Metal Yıldız Ayak",
  "327": "Naylon+PU Tekerler",
  "328": "Modern tasarımı ve üstün ergonomisi ile dikkat çeken bu gaming/ofis koltuğu, uzun süreli kullanımda bile maksimum konfor ve destek sağlar. Özellikle oyuncular, ofis çalışanları ve evde çalışanlar için ideal olan bu koltuk, yüksek kaliteli malzemeleri ve yeni nesil ayarlanabilir mekanizma özellikleri ile öne çıkar.",
  "329": "Yüksek Ergonomi:",
  "330": "Omurga Destek Sistemi: Özel olarak tasarlanmış sırt desteği, omurganızı doğal duruş pozisyonunda destekler, böylece sırt ağrılarınızı azaltır.",
  "331": "Ayarlanabilir Bel Desteği: Bel desteği, belinizi doğru pozisyonda tutarak uzun saatler boyunca konfor sağlar.",
  "332": "Baş ve Boyun Desteği:",
  "333": "Ayarlanabilir Başlık: Başlık yüksekliği ve açısı ayarlanabilir, bu sayede boyun bölgeniz rahat eder ve doğru pozisyonda desteklenir.",
  "334": "Nefes Alabilir Kumaş:",
  "335": "File (Mesh) Kumaş Arkalık: Yüksek kaliteli file (mesh) kumaş, hava akışını sağlar ve terlemeyi önler, uzun süreli oturmalarda serin kalmanıza yardımcı olur.",
  "336": "Çok Yönlü Kolçaklar:",
  "337": "3D Ayarlanabilir Kolçaklar: Kolçaklar, yükseklik, ileri-geri, sağ-sol ve dönme açılarıyla tam ayarlanabilir, bu sayede kol ve omuzlarınızı doğru pozisyonda tutar.",
  "338": "Konforlu Oturma Yeri:",
  "339": "Yüksek Yoğunluklu Sünger: Kaliteli ve yoğun sünger yapısı ile uzun süreli oturmalarda bile çökme yapmaz, sürekli konfor sağlar.",
  "340": "Dayanıklı ve yüksek kaliteli kumaş kaplaması ile üst seviye rahatlık sunar.",
  "341": "Eğim ve Yatış Fonksiyonu:",
  "342": "Yeni Nesil Senkronize Eğilim Mekanizması: Sırtlık ve oturma yeri senkronize şekilde hareket eder, farklı eğim açılarında kilitlenebilir, bu sayede rahatça dinlenebilirsiniz.",
  "343": "120 Derece Yatış: Koltuk, 120 dereceye kadar yatabilir, bu da kısa şekerlemeler veya dinlenme anları için mükemmeldir.",
  "344": "Sırt bölümünde bulunan 2 adet V kol dayama bölümü arkanıza yaslanıp kollarınızı yaslayıp dinlenmenizi ve devamında benzersiz bir kullanım deneyimi sunar.",
  "345": "Dayanıklı Tekerlekler ve Metal Ayak:",
  "346": "Sessiz ve Pürüzsüz Tekerlekler: Yüksek kaliteli geniş ölçü tekerlekler, sessiz ve pürüzsüz bir hareket sağlar, zemine zarar vermez.",
  "347": "Güçlü Özel Tasarım Ayak: Dayanıklı dökme plastik ve özel kaplama boyası ile koltuğa estetik katar ve uzun ömürlü kullanım sunar. Uç kısımlardaki 45 derece eğim ile ayaklarınızı ergonomik olarak destekler ve dinlendirmenize yardımcı olur.",
  "348": "Ofis Kullanımında: Yoğun çalışma günlerinde dahi rahatlık sunar, odaklanmanızı ve verimliliğinizi artırır.",
  "349": "Gaming Kullanımda: Uzun süreli oyun seanslarında optimum konfor ve destek sağlar, performansınızı artırır.",
  "350": "Ev: Evde çalışma, dinlenme veya eğlence aktivitelerinizde mükemmel bir yardımcıdır.",
  "351": "Neden Bu Koltuğu Tercih Etmelisiniz?",
  "352": "Yeni Nesil Ergonomik Tasarım: Benzersiz yeni nesil oturum ve sırt yaslanma mekanizması ile uzun süreli kullanımda sağlığınızı korur ve konfor sağlar.",
  "353": "Yüksek Kaliteli Malzeme: Dayanıklı ve uzun ömürlü kullanım sunar.",
  "354": "Çok Yönlü Ayarlanabilir Mekanizma: Kişisel ihtiyaçlarınıza ve vücut yapınıza uygun ayarlamalar yapabilirsiniz.",
  "355": "Estetik ve Modern Görünüm: Her türlü ofis veya ev ortamına şıklık katar.",
  "356": "Türkiye’de ilk ve Tek sadece Adore Mobilyada.",
  "357": "Adore Mobilya TGIF Türkiye Ana Distribütörü",
  "358": "TGIF – The Game Is Forever - Yeni Nesil Ergonomik Gaming ve Ofis Koltuğu",
  "359": "Tuürkiye’de İlk ve Tek",
  "360": "Handy Mate Bella Ahşap Askılık, modern görünümü ve şık tasarımıyla her mekâna rahatlıkla uyum sağlar. Dayanıklı yapısıyla, ev ve ofis ortamınızı düzenli tutmanıza yardımcı olurken doğal ahşap görünümü ile ortama zarif bir dokunuş katar. Genişliği, yüksekliği ve derinliği ile kıyafet, çanta gibi çeşitli eşyalarınızı düzenlemek için ideal bir seçimdir. Kaymayan askı kısımları ile eşyaların düşmesini önler, hafif bir yapıya sahip olmasıyla çok yer kaplamaz. Beyaz rengin verdiği sade ve temiz hatlar minimalist tarzın vazgeçilmez unsurudur. Bu nedenle kullanıldığı mobilyalarda çağdaş bir görünüm sunar. Doğal görünümdeki ahşaplarla da entegre edildiğinde sıcak ve samimi bir enerji yaratır.",
  "361": "Zemine zarar vermeyen geniş ve estetik pabuçlar",
  "362": "Kapaklı, dikey formda çok amaçlı dolap",
  "363": "Hareketli raflar ile kişiselleştirilebilir dolap içi tasarım",
  "364": "Açılabillir özellikli fonksiyonel mutfak masası",
  "365": "Açıldığında 4-6 kişilik yemek masası haline dönüşebilir",
  "366": "Karyolalarımızla uyumlu yatak ölçüleri 90 cm - 190 cm' dir.",
  "367": "Kolçaklarda bardak tutucu",
  "368": "Aletsiz tek kişi ile kurulum özelliği",
  "369": "Yüksek kaliteli Teddy kumaştan yapılmış özel tasarım çalışma sandalyesi",
  "370": "Teddy kumaş kaplama kolçaklar",
  "371": "Ayarlanabilir oturum yüksekliği",
  "372": "Estetik ve dayanıklı metal ayaklar",
  "373": "Ürün yumuşak dokulu teddy kumaş ile üretilmiştir. Alt iskelet ve ayaklar statik boyalı dayanıklı metalden üretilmiştir.",
  "374": "Özel kapak bölmesi, raf ve çekmecesi ile ergonomik kullanım özelliği",
  "375": "Banyo, mutfak, ofis vb. mobil tekerler sayesinde kolay taşınabilme özelliği",
  "376": "Kumaş kaplama karyola başlığı",
  "377": "Ürün ile uyumlu yatak ölçüsü 160 * 200 cm'dir.",
  "378": "Zemine zarar vermeyecek estetik pabuçlar",
  "379": "Eşyalarınızı kolayca organize edebileceğiniz 6 çekmeceli depolama alanı",
  "380": "Eşyalarınızı kolayca organize edebileceğiniz 4 çekmeceli depolama alanı",
  "381": "Şık ve modern tasarım.",
  "382": "Dayanıklı ve uzun ömürlü malzeme.",
  "383": "Kolay temizlenebilen mat yüzey.",
  "384": "Dar alanlar için ideal boyutlar.",
  "385": "2 adet askılık içeren fonksiyonel iç tasarım",
  "386": "Çoklu raf düzeni içeren fonksiyonel iç tasarım",
  "387": "Fonksiyonel iç tasarım",
  "388": "Şık, metal kulplar",
  "389": "Sağlam, plastik siyah ayaklar",
  "390": "Gövde ile uyumlu karyola başlığı",
  "391": "1 adet monitör rafı",
  "392": "Hem ev ,hem ofis kullanımına uygunluk",
  "393": "Özel tasarım retro metal ayaklar",
  "394": "Zemine zarar vermeyen papuçlar",
  "395": "Pembe ve beyaz rengin modern uyumu",
  "396": "2 adet masa üst bölmesi",
  "397": "Geniş çalışma alanı",
  "398": "2 adet çok amaçlı bölme",
  "399": "Masa üstü kablo kanalı",
  "400": "Yüksek kaliteli teddy kumaş",
  "401": "Geriye doğru yatabilen sırt mekanizması",
  "402": "Özel tasarım yüksek retro ayaklar",
  "403": "Hem ev, hem ofis kullanımına uygunluk",
  "404": "Yüksek retro metal ayaklar",
  "405": "Ev, ofis, balkon ve benzeri alanlarda kullanıma uygun çok amaçlı masa",
  "406": "Günlük eşyaları kolayca gizleyebileceğiniz pratik çekmece tasarımı",
  "407": "2 adet bölme",
  "408": "Günlük eşyaları kolayca gizleyebileceğiniz 2 kapaklı depolama alanı",
  "409": "Modern ve şık kompozit ayaklar",
  "410": "Ürün, 1. kalite dayanıklı ve silinebilir şönil kumaş kaplama, dayanıklı açılır mekanizma ve yaylardan oluşmaktadır.",
  "411": "Dayanıklı ve özel tasarım siyah çelik gövde ve yükseklik denge ayarı",
  "412": "Geniş ve ergonomik mouse pad",
  "413": "C tipi masa üstü kablo kanalı ve 2'li USB şarj girişi",
  "414": "Masa ayaklarında yükseklik ve denge ayarları",
  "415": "Adore Mobilya patentli özel tasarımıdır",
  "416": "Dayanıklı ve Özel Tasarım Siyah Çelik Gövde ve Yükseklik Denge Ayarı",
  "417": "Adore Mobilya patentli özel tasarımıdır.",
  "418": "C tipi masa üstü kablo kanalı ve 2'li USB şarj giriş",
  "419": "Hem işlevsel hem de görsel olarak dikkat çeker.",
  "420": "Dergi, gazete ve kitaplarınızı düzenlemek için ideal bir ürün",
  "421": "Yüksek kaliteli malzeme kullanımı",
  "422": "Küçük alanlarda bile kolayca yerleştirilebilir",
  "423": "Gazeteler, dergiler, kitaplar ve diğer basılı materyallerin düzenli bir şekilde depolanmasını sağlar.",
  "424": "Zarif ve şık tasarımı, her ortamda dikkat çekici bir aksesuara dönüşür.",
  "425": "Yüksek kaliteli malzemelerden üretilmiş olup uzun yıllar boyunca güvenle kullanılabilir.",
  "426": "Küçük alanlarda bile rahatça yerleştirilebilecek kompakt boyutları sayesinde her türlü odada kullanılabilir.",
  "427": "Florida Meşe / Karışık Renkli",
  "428": "Florida Meşe gövde ve renkli başlık uyumu",
  "429": "Florida Meşe / Karışık",
  "430": "Florida Meşe - Karışık Renkli",
  "431": "1 adet kablo kanalı",
  "432": "Kompozit ayaklar",
  "433": "Açık Ölçü: Yatak açıkken toplam 199 x 117 x 32 cm (Uzunluk x Genişlik x Yükseklik)",
  "434": "Kapalı Ölçü: Koltuk kapalıyken toplam 117 x 86,5 x 81 cm (Uzunluk x Genişlik x Yükseklik)",
  "435": "Açık Ölçü: Yatak açıkken toplam 199 x 76 x 32 cm (Uzunluk x Genişlik x Yükseklik)",
  "436": "Kapalı Ölçü: Koltuk kapalıyken toplam 76 x 85 x 81 cm (Uzunluk x Genişlik x Yükseklik)",
  "437": "Şık ve Modern tasarı",
  "438": "1 adet geniş alt raf",
  "439": "%100 Polyester kumaş kullanılmıştır.",
  "440": "Masif İskelet ile üretilmiştir.",
  "441": "35 DNS sünger kullanılmıştır.",
  "442": "%30 Pamuk + %30 Keten + %40 Polyester kumaş",
  "443": "Kayın ağacından üretilmiş doğal görünümlü yüksek ayak",
  "444": "Aynalı Kapak",
  "445": "Yavaşlatıcılı menteşe",
  "446": "10 Adet Bölme",
  "447": "3 Adet Renkli Asimetrik Kapak",
  "448": "Oyun performansınızı zirveye taşımaya hazır mısınız? Adore Gaming Maestro X, yükseklik ayarlı tasarımı sayesinde kişisel konforunuza göre özelleştirilebilir ve uzun saatler boyunca sırt, bilek ve boyun ağrılarını en aza indirir.",
  "449": "Kablo yönetim sistemi ile masanız düzensiz kablo karmaşasından kurtulacak.",
  "450": "Kupa tutucu ve kulaklık askısı, oyun sırasında maksimum rahatlık sağlar.",
  "451": "Yüksek taşıma kapasitesi, güçlü ve güvenilir bir kullanım sunar.",
  "452": "72-117 cm arası çalışma yüksekliğine sahiptir.",
  "453": "Çalışma Voltaji: AC100-240V Frekans 50/60 Hz",
  "454": "Çalışma Ortam Sıcaklığı: -10 / +40 Santigrat Derece",
  "455": "Bu masa en fazla 60 kg yük kaldırabilir. Daha fazla yük koymaktan, üzerine oturmayınız, yükselti aracı veya merdiven amacı ile üzerine çıkmayınız ve bu amaçla kesinlikle kullanmayınız.",
  "456": "Kullanmadan önce lütfen tüm elektrik kablolarının doğru şekilde takıldığından ve sağlam olduğunu kontrol ediniz.",
  "457": "Kullanmadan önce çevreyi kontrol edin ve masanın üstünde veya altında herhangi bir engel olmadığından emin olunuz.",
  "458": "Bu ürün 9 yaş altı çocukların tek başlarına kullanmaları için uygun değildir. Çocuklar kullanırken yetişkin gözetimi olması gereklidir.",
  "459": "Kullanmadan önce tüm elektrik aksamları ve kabloları kontrol ediniz. Herhangi bir arıza ve hasar söz konusu olursa ürünü kullanmayınız.",
  "460": "Ürün düz bir zemin üzerinde sabit durumda kullanılmalıdır. Ayaklar yere tam basmıyorsa ve ürün hareket ediyorsa kullanmayınız. Ürünü hareket ettirmeniz gerekiyorsa lütfen tüm kablo bağlantılarını elektrik prizinden çektiğinizden emin olunuz ve en az 2 kişi yardımı ile taşıyınız.",
  "461": "Masa yükselmeye ve alçalmaya başladığında hafif bir titreme olması normaldir. Bu ürünün kullanım ömrünü olumsuz etkileyen bir durum değildir.",
  "462": "Yumuşak dokuma kumaşı, şık bir görünüme katkıda bulunur.",
  "463": "Zarif Koyu Vizon (Koyu Bej) renk tonuyla her türlü dekorasyona uyum sağlar.",
  "464": "Düğme detaylı sırt ve oturum minderi, sofistike bir dokunuş katmaktadır.",
  "465": "Button Çalışma Koltuğu, hem konfor hem de şıklığı bir araya getiren modern bir tasarıma sahiptir. Ofis ve çalışma ortamlarınızı hem ergonomik hem de estetik açıdan zenginleştirmek için tasarlanmıştır. Bu koltuk, uzun süreli çalışma deneyimlerinizi daha rahat hale getirecek birçok özelliği sunar. Button Çalışma Koltuğu hem günlük kullanımda hem de yoğun iş temposunda size en iyi konforu sunmayı hedefler. Modern ofislerinize ya da ev çalışma alanlarınıza şıklık katmak için mükemmel bir seçimdir.",
  "466": "Yumuşak suni deri oturum ve sırt kaplamasıyla, şık bir görünüme katkıda bulunur.",
  "467": "Zarif Hardal (Kahve) renk tonuyla her türlü dekorasyona uyum sağlar.",
  "468": "Geleneksel Siyah renk tonuyla her türlü dekorasyona uyum sağlar.",
  "469": "Zarif Vizon – Bej renk tonuyla her türlü dekorasyona uyum sağlar.",
  "470": "Düğme detaylı sırt kısmı, sofistike bir dokunuş katmaktadır.",
  "471": "Button Çalışma Koltuğu, hem konfor hem de şıklığı bir araya getiren modern bir tasarıma sahiptir. Ofis ve çalışma ortamlarınızı hem ergonomik hem de estetik açıdan zenginleştirmek için tasarlanmıştır. Bu koltuk, uzun süreli çalışma deneyimlerinizi daha rahat hale getirecek birçok özelliği sunar. Button Çalışma Koltuğu hem günlük kullanımda hem de yoğun iş temposunda size en iyi konforu sunmayı hedefler. Modern ofislerinize ya da ev çalışma alanlarınıza şıklık katmak için mükemmel bir seçimdir",
  "472": "Ürün, Oryana GRD-1740-DD-3 / GRD-1740-OO-3 ve GRD-1722-DD-2 / GRD-1722-OO-2 modelleri için uyumludur",
  "473": "Çift kişilik yatak çerçevesi",
  "474": "Alt kısmında depolama alanı",
  "475": "\"C\" şeklindeki yapısı sayesinde kanepe, koltuk veya yatak altına kolayca yerleştirilebilir.",
  "476": "Taşınabilirliği kolaydır, evin farklı bölümlerinde rahatça kullanılabilir.",
  "477": "Ayaklarda bulunan plastik destekler zeminde çizilmeyi önler ve kaymayı engeller.",
  "478": "Üst tabla, çizilmeye ve lekelere karşı dayanıklı kaliteli melamin yonga levha malzemeden üretilmiştir.",
  "479": "Elektrostatik boyalı metal yüzey, paslanmaya ve aşınmaya karşı dayanıklıdır.",
  "480": "Daha güvenli ve sorunsuz bir kurulum için montajın 2 kişi ile yapılması tavsiye edilmektedir.",
  "481": "Uzun ömürlü kullanım için tasarlanmıştır.",
  "482": "Tekerlekli yapısı sayesinde kolayca taşınabilir ve farklı alanlarda kullanılabilir. Bu sayede sabit bir kullanım sağlanır.",
  "483": "Üst kısmında bulunan geniş çekmece, dosyalar, kırtasiye malzemeleri veya kişisel eşyalarınızı düzenli bir şekilde saklamanıza olanak tanır.",
  "484": "Alt raf bölümü, kitap, klasör veya diğer büyük eşyalar için ek bir depolama alanı sunar.",
  "485": "Küçük boyutları sayesinde dar alanlarda bile rahatça kullanılabilir. Masa altına yerleştirilebilir ya da bağımsız bir yan sehpa olarak kullanılabilir.",
  "486": "Gövde ve çekmece bölümü, dayanıklı melamin yonga levha ve metal malzemelerden üretilmiştir.",
  "487": "Ürün masa tablası üzerinde iki parçadan oluşan yükseltme raf bulunmaktadır.",
  "488": "Raflar masanın sağına ve soluna ayrı ayrı takılabileceği gibi, masanın orta bölümüne birleştirilerek de takılabilir.",
  "489": "Masa tablasının yan köşelerinde RGB ışıklandırma vardır.",
  "490": "Masa tablası ön kısımlarda tablet, telefon vs. takacak bölüm vardır.",
  "491": "C tipi ve standart usb şarj girişi mevcuttur.",
  "492": "Masa altı kablo toplayıcı bölme",
  "493": "Ayak ucu ayarlanabilir pabuç",
  "494": "Kulaklık ve bardak tutucu",
  "495": "Geniş mousepad",
  "496": "Kompakt tasarım",
  "497": "Modern yaşam alanları için şık ve tamamlayıcı görünüm",
  "498": "Nemli bir bezle temizlenebilir. Deterjan gerektirmez. Su ve sıcak ile uzun süreli temasından kaçınılmalıdır.",
  "499": "1 adet iç çekmece",
  "500": "Yavaşlatıcılı menteşeler",
  "501": "Baş Destekliği: Ayarlanabilir baş yastığı, boyun bölgesine tam destek sağlayarak uzun süreli oturmalarda konfor sunar.",
  "502": "Bel Desteği: Bel kısmı vücut ağırlığınıza göre tepki vererek omurga sağlığınızı korur ve doğal duruşunuzu destekler.",
  "503": "Ayarlanabilir Kolçaklar: Yumuşak yüzey dolgusu ve yükseklik ayarıyla kollarınızın ideal pozisyonda durmasını sağlar.",
  "504": "Fileli Sırtlık: Yüksek kaliteli file kumaş, terlemeyi önler ve uzun süreli kullanımda serin bir oturma deneyimi sunar.",
  "505": "Yumuşak Sünger Oturma Alanı: Kaliteli malzemeden üretilmiş oturma minderi, çökme yapmaz ve uzun ömürlüdür.",
  "506": "Oyun ve Çalışma Koltuğu: Hem ofis ortamında uzun saatler boyunca çalışmak hem de oyun oynarken üstün konfor sağlamak için idealdir.",
  "507": "Şık Tasarım: Minimalist ve modern çizgiler, ofislerden ev oyun odalarına kadar her ortamla uyum sağlar.",
  "508": "Yükseklik Ayarı: Dayanıklı amortisör ve mekanizma sayesinde koltuğun yüksekliği kolayca ayarlanabilir, böylece masa yüksekliğine ve kullanıcının boyuna uyum sağlar.",
  "509": "Koltuk Açısı: Geri yaslanma özelliği, çalışırken veya dinlenirken farklı oturma pozisyonları sağlar.",
  "510": "Eğim Mekanizması: Oturma pozisyonunuza uygun şekilde koltuğun eğimini ayarlayabilirsiniz.",
  "511": "360 Derece Dönüş: Hareket özgürlüğü sunarak verimliliğinizi artırır.",
  "512": "Dayanıklı Tekerlekler : Sessiz ve pürüzsüz hareket sağlayan tekerlekler ile sağlam metal demonte yıldız ayak uzun yıllar güvenle kullanım imkânı sunar.",
  "513": "Koltuğun yan panellerinde entegre RGB led ışık şeritleri bulunur. Çok farklı ışık modlarına sahip, isteğinize göre renk geçişlerini ve efektleri ayarlayabilirsiniz.",
  "514": "Uzaktan Kumanda ile ışıkları kolayca kontrol edebilir, oyun tarzınıza uygun atmosfer yaratabilirsiniz.",
  "515": "USB bağlantı noktası ile güç kaynağına bağlanır ve enerji tasarrufu sağlar.",
  "516": "Yüksek yoğunluklu sünger dolgu; Vücut yapınızı destekleyerek uzun süreli konfor sağlar.",
  "517": "Yüksek sırt desteği, çıkarılabilir bel ve boyun yastıkları.",
  "518": "2D ayarlanabilir eğimli kolçaklar.",
  "519": "Yüksekliği istediğiniz seviyeye ayarlayabileceğiniz güçlü amortisör.",
  "520": "90-135° yatabilir sırt mekanizması.",
  "521": "360° dönebilen metal ayak, sessiz ve parke, halı gibi yüzeylerde iz bırakmayan tekerlekler.",
  "522": "Ergonomik Tasarım:",
  "523": "Koltuğumuz, vücut yapısına uyum sağlayarak omurga sağlığını destekleyen bir yapıya sahiptir. Yüksek sırt desteği, sırtınızı doğal bir duruşta tutmanıza yardımcı olur.",
  "524": "Bel desteği, bel bölgesine ekstra destek sağlayarak doğru oturma pozisyonunu korumanıza katkıda bulunur.",
  "525": "Ayarlanabilir Başlık:",
  "526": "Uzun süreli çalışmalarda boyun ve omuz bölgesini rahatlatmak amacıyla ayarlanabilir başlık ile donatılmıştır.",
  "527": "Bu özellik sayesinde, koltuk her kullanıcıya göre kolayca uyarlanabilir.",
  "528": "Kol Desteği ve Ayarlanabilir Kollar:",
  "529": "Kol dayama kısımlarının üzeri yumuşak PU malzeme ile kaplanmıştır, böylece kollarınızın konforlu bir şekilde desteklenmesini sağlar.",
  "530": "Ayarlanabilir yapısı sayesinde farklı yükseklik ve pozisyonlarda kullanılabilir, bilekleriniz ve dirsekleriniz üzerindeki baskıyı azaltır.",
  "531": "Nefes Alabilir File Sırt Yapısı:",
  "532": "Sırt kısmında kullanılan file malzeme, hava sirkülasyonunu sağlayarak terlemeyi azaltır ve uzun süreli oturmalarda rahatlık sunar.",
  "533": "Hem dayanıklı hem de şık bir görünüm sunarak ofis ortamında modern bir estetik yaratır.",
  "534": "Yüksek Kalite Malzeme ve Dayanıklılık:",
  "535": "Sağlam yapısı ve kaliteli malzemeleri sayesinde uzun ömürlü bir kullanım sunar.",
  "536": "Metal yıldız ayaklar ile hareket kabiliyeti sağlar ve ofis içi yer değişikliklerini kolaylaştırır.",
  "537": "Özel Kalıp Dökme Sünger ile Geniş ve Yumuşak Oturma Alanı:",
  "538": "Oturum minderi, özel kalıp dökme süngerden üretilmiştir. Bu, minderin şeklini uzun süre korumasını ve kullanıcıya konforlu bir deneyim sunmasını sağlar.",
  "539": "Oturum minderi ileri geri hareket edebilir, bu da oturma alanının kullanıcıya göre ayarlanabilmesini mümkün kılar.",
  "540": "Yumuşak minderli oturma alanı, konforlu bir deneyim sunarken doğru oturma pozisyonunu destekler.",
  "541": "Yeni Nesil Kablo Kontrol Oturum Mekanizması:",
  "542": "Yeni nesil kablo kontrol oturum mekanizması ile koltuğunuzu istediğiniz yükseklik ve oturum açısına kolayca ayarlayabilirsiniz.",
  "543": "Vücut ağırlığınıza duyarlı sırt yaslanma sertlik ayarını düzenleyebilir, istediğiniz yaslanma açısında sabitleyebilirsiniz.",
  "544": "Oturum minderini bacak boyunuza uygun şekilde ileri ve geri kaydırabilirsiniz.",
  "545": "Oturum yüksekliğini kendinize en uygun seviyede sabitleyebilirsiniz.",
  "546": "3 adet metal file raf ve 1 adet yonga levha raf",
  "547": "Metal file kapak",
  "548": "Hem ev ,hem ofis kullanımına uygundur",
  "549": "Modern tasarım",
  "550": "Yatak başucunda kullanım için ideal ölçüler",
  "551": "Teleskopik raylı sistem ile yumuşak kapanır çekmeceler",
  "552": "Vizon Gövde / Zebra Çekmece Önü Detayı",
  "553": "5 adet geniş ve kullanışlı çekmece",
  "554": "Dar alanlarda bile rahat kullanım",
  "555": "Geniş iç hacim sayesinde düzenli depolama",
  "556": "Vizon Gövde / Zebra Başlık Detayı",
  "557": "Çift kişilik yatak alanına uygun",
  "558": "Destekleyici orta ayak sistemi",
  "559": "Başlık kısmında dekoratif zebra desen",
  "560": "Kolay kurulum ve dayanıklı yapı",
  "561": "Vizon Gövde / Zebra Çekmece Önleri",
  "562": "Modern ve işlevsel tasarım",
  "563": "Estetik kulp detayları",
  "564": "Vizon Gövde / Zebra Kapak",
  "565": "Derin ve kullanışlı iç tasarım",
  "566": "2 kapaklı sürgü sistem",
  "567": "Askılık ve raf düzeni",
  "568": "2 adet sürgülü kapak sistemi",
  "569": "Geniş iç hacim ve bölmeli raf düzeni",
  "570": "Sessiz ve dayanıklı sürgü mekanizması",
  "571": "2 adet temperli bronz cam kapak",
  "572": "Sadece Milano Gardırop serisi ile uyumludur",
  "573": "Sağlam ve şık görünüm sağlayan çerçeve yapısı",
  "574": "Milano gardırop gövdeleri ile tam uyumlu",
  "575": "Yalnızca 1 adet kapak",
  "576": "1 adet dikey ara bölme",
  "577": "2 adet kapak paneli",
  "578": "Yalnızca Milano Gardırop serisi ile uyumludur",
  "579": "Sağ ve sol kapak olarak kullanım için uygundur",
  "580": "Ürün yalnızca kapaklardan oluşmaktadır; gardırop gövdesi dahil değildir",
  "581": "2 kapak takılabilir gövde yapısı",
  "582": "Geniş iç hacim",
  "583": "4 kapak takılabilir gövde yapısı",
  "584": "Kapak hariç, sadece gardırop gövdesidir",
  "585": "Bronz cam yüzey",
  "586": "Tek kapak (uyumlu gardırop gövdesine takılmak üzere)",
  "587": "Ürünlerimiz, yüksek kalite melamin yüzeye sahip yonga levha çerçeve ve birinci sınıf cam kullanılarak üretilmektedir.",
  "588": "Cam, temperli (dayanıklı) cam özelliklerine sahiptir. Tüm bileşenler, Avrupa Birliği sağlık normlarına uygun, E1 sertifikalı malzemelerden üretilmiştir.",
  "589": "Şık ve Modern tasarım",
  "590": "8 bölmeli modüler çekmece içi organizer",
  "591": "Dayanıklı metal ayak",
  "592": "Masa üst tablası temperli camdır.",
  "593": "1 adet metal elbise askılığı",
  "594": "Ürün ile uyumlu yatak ölçüsü 90*190 cm'dir.",
  "595": "Renk kartelası mevcuttur.",
  "596": "Salon,Oturma Odası, Otel Vb. kullanım alanları",
  "597": "Dolgulu sırt / Soft oturum / Yerden yüksek",
  "598": "Çelik lama destekli gürgen gövde malzemesi",
  "599": "Oturum Malzemesi : 30 Soft Sünger / Zigzag Yay",
  "600": "Sırt Minderi : 57*45 cm (1 adet)",
  "601": "Oturum Derinliği : 55 cm",
  "602": "Oturum Genişliği : 55 cm",
  "603": "Oturum Yüksekliği : 45 cm",
  "604": "Ergonomik kol dayama minderleri",
  "605": "Işığa karşı dayanıklılık",
  "606": "Kol Genişliği : 12 cm",
  "607": "Sağlam Metal Ayaklar",
  "608": "Ayak Yüksekliği : 17 cm",
  "609": "Ayak Kalınlığı : 4 cm'e 2 cm",
  "610": "Ayak Rengi : Siyah",
  "611": "Ağırlık : 95 Kg",
  "612": "Yerden yüksek",
  "613": "Robot süpürgeye uygunluk",
  "614": "Sadece Mağazalarımızdan Ulaşılabilir.",
  "615": "Gürgen ve kontra plak gövde malzemesi",
  "616": "Geriye doğru hareketli mekanizma",
  "617": "Oturum Malzemesi : 30 DNS Sünger / Zigzag Yay",
  "618": "Oturum Derinliği : 62 cm",
  "619": "Oturum Genişliği : 180 cm",
  "620": "Kırlent Ölçüsü : 50*50 (2 adet)",
  "621": "Derinlik : 95 cm",
  "622": "Kol Genişliği : 20 cm",
  "623": "Sağlam Ahşap Ayaklar",
  "624": "Ayak yüksekliği : 17 cm",
  "625": "Ayak kalınlığı : 4 cm",
  "626": "Ağırlık : 73 Kg",
  "627": "Geriye doğru sırt mekanizması",
  "628": "Oturum Derinliği : 65 - 145 cm",
  "629": "Oturum Genişliği : 240 cm",
  "630": "Oturum Yüksekliği : 43 cm",
  "631": "Kırlent Ölçüsü : 35*50 (1 adet)",
  "632": "Derinlik : 100 cm",
  "633": "Kol Genişliği : 18 cm",
  "634": "CSS (Dönen iç arka)",
  "635": "Oturum Derinliği : 60 cm",
  "636": "Oturum Genişliği : 200 cm",
  "637": "Oturum Yüksekliği : 46 cm",
  "638": "Kol Genişliği : 15 cm",
  "639": "Ayak yüksekliği : 14 cm",
  "640": "Ayak kalınlığı : 5 cm*6 mm",
  "641": "Ağırlık : 70 Kg",
  "642": "Yumuşak Dokulu Modern Kumaş",
  "643": "Ergonomik Gövde Tasarımı",
  "644": "Sabit Kolçaklı Tek Parça Gövde",
  "645": "Yükseklik Ayarlı Mekanizma",
  "646": "Sağlam 5 Kollu Tekerlekli Ayak",
  "647": "Minimalist tasarımı ve yumuşak dokulu kumaşıyla öne çıkan Milano Çalışma Koltuğu, estetikten ödün vermeden rahat bir oturum sunar. Ev-ofislerden butik çalışma alanlarına kadar her ortamda şıklığı ve işlevselliği bir araya getirir.",
  "648": "Home office alanlar",
  "649": "Giyinme odası ve makyaj köşeleri",
  "650": "Butik ofisler ve danışma masaları",
  "651": "Estetik stüdyo ortamları",
  "652": "Kolçaklara kadar bütünleşmiş yuvarlak sırt ve kol yapısı",
  "653": "Açık tonlu, naturel kumaş kaplama",
  "654": "Kolayca ayarlanabilen amortisör sistemi",
  "655": "Bilek hizasında destek sağlayan kavisli kolçaklar",
  "656": "5 Kollu Tekerlekli Ayak",
  "657": "Ürün yumuşak dokulu kumaş döşemedir.",
  "658": "Kaliteli Suni Deri Döşeme",
  "659": "Ergonomik Sırt ve Kol Yapısı",
  "660": "Tek Parça Şık Gövde",
  "661": "Ultra Kalın Minderler",
  "662": "Yumuşak ve kalın yaylı oturum minderi, uzun süreli oturumlarda bile vücut basıncını azaltır, destek sağlar. Dolgun ve vücudu kavrayan sırt minderi.",
  "663": "Ayarlanabilir Baş Yaslama Minderi",
  "664": "En rahat ve konforlu çalışma şeklini ayarlamak için baş yaslama minderi ileri ve geri farklı açılarda sabitlenebilir.",
  "665": "Yatar Mekanizma & Ayak Uzatma Ünitesi",
  "666": "Geriye yatabilen, farklı açılarda sabitlenebilen sırt yaslanma ve açılır kapanır ayak uzatma minderi sayesinde kısa molalarınızı adeta bir dinlenme seansına dönüştürür.",
  "667": "Yumuşak Kumaş Döşeme",
  "668": "Modern görünümü tamamlayan kaliteli kumaş döşemesi, hava alabilir yapısıyla terlemeyi önler ve gün boyu konfor sunar.",
  "669": "Ergonomik Kolçaklar",
  "670": "Yumuşak dolgulu sünger üzeri kumaş kaplamalı sabit kolçaklar, diresek ve kollarınızı destekleyerek ergonomik oturuş pozisyonu sağlar.",
  "671": "Dayanıklı Metal Ayak & Tekerlek Sistemi",
  "672": "360 derece dönebilen sessiz tekerlekler ve güçlü metal ayak yapısı, güvenli ve uzun ömürlü kullanım sunar.",
  "673": "Ev ofisleri",
  "674": "Profesyonel çalışma ortamları",
  "675": "Oyun ve dinlenme alanları",
  "676": "Yumuşak dolgulu sünger üzeri kumaş kaplamalı sabit kolçaklar, dirsek ve kollarınızı destekleyerek ergonomik oturuş pozisyonu sağlar.",
  "677": "Modern metal tarzıyla mekanlara şıklık katar",
  "678": "Yüksek kalite yonga levhadan üretilmiştir. Ayak ve destek parçaları mat siyah metal yapıya sahiptir.",
  "679": "Tüm bileşenler Avrupa Birliği sağlık normlarına uygun E1 sertifikalı malzemeler içerir, zararlı madde bulundurmaz.",
  "680": "Ürün toplamda 1 koliden oluşmaktadır.",
  "681": "Yumuşacık teddy kumaş kaplamaAyarlanabilir oturum yüksekliği",
  "682": "360 derece döner mekanizma",
  "683": "Dayanıklı metal taban ve sessiz tekerlekler",
  "684": "Genç, çocuk ve ev ofis kullanımı için ideal",
  "685": "Ürün, yumuşak dokulu teddy kumaş ile kaplanmış, yüksek yoğunluklu sünger dolgulu ergonomik yapıya sahiptir. Alt iskelet ve ayaklar statik boyalı dayanıklı metalden üretilmiştir.",
  "686": "Yumuşacık teddy kumaş kaplama",
  "687": "Yaylı oturum minderi ile uzun süreli konfor",
  "688": "Ayarlanabilir yükseklikli amortisör sistemi",
  "689": "360° döner metal taban ve sağlam tekerlekler",
  "690": "Retro görünümlü, ergonomik sırt ve kolçak yapısı",
  "691": "Deri görünümlü yeni teknoloji kumaş döşeme",
  "692": "Ürün, dayanıklı suni deri kaplama ile üretilmiştir. Oturum kısmı yay sistemi ve yüksek yoğunluklu sünger dolgulu yapıdadır. Ayaklar ve iskelet sağlam metal malzemeden oluşur.",
  "693": "3 fonksiyonlu kullanım: Puf, koltuk ve tek kişilik yatak",
  "694": "Ayarlanabilir sırt ve ayak pozisyonu",
  "695": "Yüksek yoğunluklu sünger dolgulu döşeme",
  "696": "Dayanıklı metal iç iskelet",
  "697": "Kolay katlanır ve yerden tasarruf sağlar",
  "698": "Ürün, kaliteli döşemelik kumaş kaplama, yüksek yoğunluklu sünger dolgulu oturum alanı ve dayanıklı metal iskeletten oluşmaktadır. Ayak yapısı sağlam metal desteklidir.",
  "699": "Ürün dörtlü set halinde satılmaktadır.",
  "700": "Modern kapitone kumaş döşeme",
  "701": "Ergonomik sırt ve oturum tasarımı",
  "702": "Mat siyah metal ayaklar",
  "703": "Dayanıklı ve sağlam yapı",
  "704": "Nötr renk paleti ile çok yönlü uyum",
  "705": "Kapitone kumaş ve metal ayaklar bir arada kullanılmıştır.",
  "706": "Avrupa Birliği E1 standartlarına uygun malzeme içerir.",
  "707": "Nemli bezle silinebilir. Kimyasal temizleyiciler kullanılmamalıdır.",
  "708": "Ürün 1 koliden oluşur, koli içinde 2 adet sandalye yer alır.",
  "709": "Karbon fiber desenli geniş masa yüzeyi",
  "710": "RGB aydınlatmalı oyuncu dostu tasarım",
  "711": "Kulaklık ve bardaklık aparatı dahil",
  "712": "Kablo çıkış bölmeleri ve klavye rafı",
  "713": "X form metal ayaklar ile sağlam yapı",
  "714": "Ürün, melamin yüzeye sahip yonga levha tabla ve elektrostatik boyalı metal iskeletten oluşmaktadır. Tabla yüzeyi karbon fiber görünümlüdür.",
  "715": "Tüm malzemeler E1 sertifikalı olup, insan sağlığına zararlı madde içermez.",
  "716": "Gizli RGB aydınlatmalı üst monitör rafı",
  "717": "USB A ve C girişli şarj ünitesi",
  "718": "Kulaklık askısı ve bardak tutucu aparatlar",
  "719": "Kablo düzenleyici arka metal raf",
  "720": "160 cm geniş masa yüzeyi",
  "721": "Ryze Castle Gaming Masası çizilmeye karşı dayanıklı özel kaplama yüzeye ve sağlam metal iskelet yapıya sahiptir. Üst tabla karbon fiber dokulu görünümüyle hem estetik hem de işlevseldir.",
  "722": "100 x 76 cm (Çap x Yükseklik)",
  "723": "Yuvarlak 100 cm genişliğinde masa tablası",
  "724": "Statik boyalı sağlam metal ayaklar",
  "725": "4 kişilik ergonomik kullanım",
  "726": "Kompakt ve yer tasarrufu sağlayan tasarım",
  "727": "Kolay temizlenebilir yüzey",
  "728": "Katlanabilir tabla yapısıyla yerden tasarruf sağlar.",
  "729": "Çok amaçlı kullanım: mutfak, ofis, balkon ve çalışma alanları için uygundur.",
  "730": "Modern tasarım, metal ayaklar ve ceviz renk kombinasyonu ile şık görünüm.",
  "731": "Tabla ve gövde kısmı melamin yüzeye sahip yonga levhadan üretilmiştir. Ayak ve destek parçaları dayanıklı siyah metal yapıya sahiptir.",
  "732": "Nemli bezle silinebilir. Deterjan gerekmez. Su ve sıcakla uzun süre temasından kaçınılmalıdır.",
  "733": "Yüksek ayaklı masa ve 2 adet tabureli raflı yapı",
  "734": "Kompakt raflı tasarım sayesinde düzen sağlar",
  "735": "Ev, mutfak, ofis ve balkon gibi farklı alan kullanımına uygun",
  "736": "Modern retro tarzıyla mekânlara şıklık katar",
  "737": "Ürün, beyaz renkli yüksek kalite melamin yüzeye sahip yonga levha tabla ve beyaz statik boyalı metal ayaklardan oluşur. Raflı masa bölümü kullanışlı depolama alanı sunar.",
  "738": "Yüksek ayaklı masa ve 2 adet tabureli yapı",
  "739": "Masa ve tabure tablası yüksek kalite yonga levhadan üretilmiştir. Ayak ve destek parçaları mat beyaz metal yapıya sahiptir.",
  "740": "Nemli bezle silinebilir. Deterjan gerekmez. Su ve sıcak ile uzun süre temasından kaçınılmalıdır.",
  "741": "Ürün toplamda 2 koliden oluşmaktadır.",
  "742": "6 adet açık bölmeli geniş depolama alanı",
  "743": "Alt bölümde 2 kapaklı kapalı alan",
  "744": "Ceviz ve siyah uyumuyla modern görünüm",
  "745": "Salon, çalışma odası veya ofis kullanımı için ideal",
  "746": "Ürün, melamin yüzeye sahip yonga levha tabla ve metal ayaklardan oluşmaktadır. Kapak menteşeleri dayanıklı ve uzun ömürlüdür.",
  "747": "2 adet kullanışlı çekmece",
  "748": "2 adet geniş hacimli çekmece",
  "749": "Şık metal ayak yapısı ve altın detaylar",
  "750": "Ceviz renk tabla ve siyah çekmece kontrastı",
  "751": "Dayanıklı ve stabil yapı",
  "752": "8-15 yaş grubu için özel ergonomik tasarım",
  "753": "Yükseklik ayarlanabilir mekanizma",
  "754": "Oturum ve sırt yaslanma bölümünün tüm çevresinde RGB LED ışıklandırma",
  "755": "Yetişkin oyuncu koltuklarıyla aynı kalite ve konfor",
  "756": "Mekanizma ve ayak bileşenleri dayanıklı metal yapıya sahiptir.",
  "757": "Kumaş yüzey deri görünümlü, kaliteli ve yeni teknoloji dayanıklı kumaştan üretilmiştir.",
  "758": "Ürün demonte gönderilir, montaj için gerekli tüm parçalar kutuda bulunur.",
  "759": "Montaj için sadece tornavida yeterlidir; parçalarda numaralandırma mevcut.",
  "760": "Kolay ve hızlı kurulum için sağlam ve sade yapı sunulur.",
  "761": "2 kişi ile sorunsuz şekilde kurulum yapılabilir.",
  "762": "8-15 yaş grubu için ergonomik tasarım",
  "763": "Sırt kısmında RGB LED ışıklandırma",
  "764": "Şık, tasarım kulplar",
  "765": "5 adet askı bölmesi",
  "766": "Geniş kullanışlı, açılır kapanır bölme",
  "767": "Dekoratif makyaj aynası",
  "768": "3 bölmeli masa üstü raf",
  "769": "Dayanıklı ve Ergonomik Tasarım:",
  "770": "Çelik iskelet ve 125 dereceye kadar arakaya yaslanma mekanizması, sağlam ve dayanıklı bir yapı sunar.",
  "771": "Ergonomik tasarımı ve benzersiz ayak uzatma eki uzun oyun seansları boyunca mükemmel konfor sağlar.",
  "772": "Uzun Süre Oturuma Uygun Yüksek Yoğunlukta Sünger:",
  "773": "Temizlenebilir ve uzun ömürlü yüksek kaliteli özel tasarım Sentetik Deri kaplaması ile şıklığı bir araya getirir.",
  "774": "Ayarlanabilir Özellikler:",
  "775": "Yukarı aşağı yükseklik ayarı ve arkaya yaslanma kilit kontrolü ile kişisel konforunuzu ayarlayın.",
  "776": "Ayak uzatma ileri-geri ayarı, 360 derece dönebilme özelliği ve 4 farklı renk seçeneği ile kişiselleştirme imkanları sınırsız.",
  "777": "Ergonomik Tasarımlı Kolçaklar:",
  "778": "2D (yukarı-aşağı ve ileri-geri) yumuşak yüzey kaplamalı ergonomik tasarımlı kolçaklar, kollarınızı doğru destekleyerek oyun performansınızı artırır.",
  "779": "Ekstra Konfor Özellikleri:",
  "780": "İsteğe göre takılıp çıkartılabilir bel ve boyun yastıkları, kişisel tercihlerinize göre konforu özelleştirme fırsatı sunar.",
  "781": "Yüksek Kalite ve Güvenilirlik:",
  "782": "3. sınıf uzun ömürlü yükseklik ayar amortisörü ve dayanıklı 35 cm çapında çelik yıldız ayak, ProX modelimizin kalitesini vurgular.",
  "783": "Naylon kaplama 5cm çapında sessiz çalışan tekerler, zeminlere zarar vermeden sorunsuz hareket sağlar.",
  "784": "Adore Gaming ProX Oyuncu Koltuğu, dayanıklılık, konfor ve şıklığı bir araya getirerek oyun dünyasında yeni bir standart belirliyor. Bu muhteşem koltukla, oyun deneyiminizin tadını çıkarın!",
  "785": "Modern ve şık retro tasarım",
  "786": "2 adet geniş ve kullanışlı raf",
  "787": "Sürgü kapaklı yapı ile pratik kullanım",
  "788": "Ev ve ofis kullanımına uygundur",
  "789": "Konforlu tasarımı ve zarif detaylarıyla Boston Yönetici Koltuğu, ofis yaşamına kalite ve şıklık katar. Uzun çalışma saatlerinde ergonomik destek sunarken, dayanıklı malzemeleriyle de yıllarca kullanım sağlar.",
  "790": "Kumanda kontrolü ile kalkış desteği",
  "791": "Kullanışlı cep (kitap, dergi, telefon vb. için)",
  "792": "120 dereceye kadar geriye yatma özelliği",
  "793": "Ürün; yırtılmalara, aşınmaya ve solmaya karşı dayanıklı, nem emilimi yüksek ve silinebilir kumaş ve dayanıklı açılır mekanizma ve yaylardan oluşmaktadır.",
  "794": "Yırtılmalara, aşınmaya ve solmaya karşı dayanıklı, nem emilimi yüksek ve silinebilir kumaş.",
  "795": "1. kalite dayanıklı açılır mekanizma ve yaylar",
  "796": "Ürün kurulumu için 1 kişi tavsiye edilmektedir.",
  "797": "Oturma yüksekliği, kullanıcının ihtiyaçlarına göre kolayca ayarlanabilir.",
  "798": "360 derece dönebilen yapısı ve sessiz, dayanıklı tekerlekleri sayesinde özgürce hareket edebilirsiniz.",
  "799": "Yüksek kaliteli metal ayaklık ve dayanıklı ekose kumaş döşeme malzemesi.",
  "800": "Siyah metal ayaklar, sağlamlık ve denge sağlarken modern bir dokunuş katar.",
  "801": "Üst kısımda yer alan açık raf bölümleri, kitaplar, defterler, kırtasiye malzemeleri ve dekoratif eşyalar için ideal bir alan sunar.",
  "802": "Kablolar için özel bir çıkış bölmesi, düzenli bir görünüm sağlar ve kablo karmaşasını önler.",
  "803": "Masanın altındaki çapraz metal destekler, ekstra sağlamlık sağlar ve uzun süreli dayanıklılık sunar.",
  "804": "Metal ayakların uçlarındaki vidalı pabuçlar zemin eğriliklerine karşı masanızı dengeli durmasına yardımcı olur ve parke gibi sert yüzeyleri çizmez.",
  "805": "Doğal ahşap ve siyah metal kombinasyonu, modern, minimalist ve endüstriyel dekorasyon tarzlarına uyum sağlar.",
  "806": "Kompakt yapısı, dar alanlarda dahi düzenli ve verimli bir çalışma alanı oluşturmanıza olanak tanır.",
  "807": "Bel Destek Sistemi: Sırt kısmındaki özel bel desteği, omurgayı doğal kıvrımında tutarak bel ağrısı riskini en aza indirir. Özellikle uzun oturma sürelerinde vücut duruşunu korumaya yardımcı olur.",
  "808": "Baş Desteği: Ayarlanabilir başlık, boyun ve baş bölgesine destek sağlayarak konforu artırır ve doğru oturma pozisyonunu destekler.",
  "809": "Nefes Alabilir Kumaş: Hava akışını sağlayan file kumaş, terlemeyi önler ve uzun süreli kullanımlarda serin bir deneyim sunar.",
  "810": "Dayanıklılık: Yüksek kaliteli file malzeme, uzun ömürlü bir kullanım için tasarlanmıştır ve deformasyona karşı dayanıklıdır.",
  "811": "Yüksek Yoğunluklu Sünger: Geniş ve yumuşak oturma yüzeyi, ağırlığı eşit şekilde dağıtarak rahat bir oturma deneyimi sunar.",
  "812": "Ergonomik Tasarım: Yastığın ön kısmındaki hafif eğim, bacaklara baskıyı azaltır ve kan dolaşımını destekler.",
  "813": "Koltuk Açısı: Geri yaslanma özelliği, çalışırken veya dinlenirken farklı oturma pozisyonları sağlar.Geri yaslanma özelliği açılıp kapatılabilir.",
  "814": "Katlanabilir ve Ayarlanabilir Kollar: Kullanıcının rahatlığına göre kolları yukarıya kaldırarak veya aşağıya indirerek ergonomik bir çalışma alanı oluşturabilirsiniz.",
  "815": "360 Derece Dönüş: Koltuğun tabanı tam tur dönebilecek şekilde tasarlanmıştır, böylece hareket kabiliyetinizi artırır.",
  "816": "Sessiz ve Dayanıklı Tekerlekler: Zemin üzerinde çizik bırakmadan hareket eder, ahşap, halı veya seramik gibi farklı zemin tiplerine uygundur.",
  "817": "Sağlam Yıldız Ayak: Sağlam ve dayanıklı 5 kollu kalıp metal ayak yapısı,",
  "818": "Fileli Sırtlık:",
  "819": "Koltuk Minderi:",
  "820": "Ayarlanabilir Fonksiyonlar:",
  "821": "Kollar:",
  "822": "Geniş ve Dayanıklı Yıldız Ayak:",
  "823": "Sağlam Yıldız Ayak: Sağlam ve dayanıklı 5 kollu kalıp metal ayak yapısı.",
  "824": "Sırt kısmında terletmeyen file kumaş",
  "825": "Özel tasarım estetik görünümlü ve ergonomik bel desteği, estetik görünümlü katlanabilir kolçaklar",
  "826": "Dayanıklı, özel kalıp yüksek dansite oturum minderi",
  "827": "Kilitlenebilir yükseklik ve geriye yaslanma mekanizması",
  "828": "1. Kalite uzun ömürlü yükseklik ayar amortisörü",
  "829": "Estetik, çizilmelere karşı dayanıklı metal yıldız ayak",
  "830": "Uzun ömürlü, zemin çizmeyen sessiz tekerler",
  "831": "Kolay ve hızlı kurulum özelliği",
  "832": "Elektrikli recliner mekanizması ile sırt yaslama ve ayak uzatma fonksiyonu",
  "833": "Kumanda ile tek tuşla kolay ve zahmetsiz kullanım",
  "834": "Şarjlı pil veya elektrik kablosu ile kullanım imkanı",
  "835": "Yumuşak dokulu, dayanıklı ve uzun ömürlü döşemelik kumaş",
  "836": "Vücudu destekleyen ergonomik sırt ve oturum yapısı",
  "837": "Geniş ve konforlu kol dayama alanları",
  "838": "Sağlam metal iskelet ve dayanıklı mekanizma yapısı",
  "839": "Konfor ve Uyarlanabilirlik:",
  "840": "Yukarı aşağı yükseklik ayarı, bel destek yukarı-aşağı ayarı",
  "841": "İş gününüzü en iyi şekilde geçirebilmeniz için tasarlanmış bir oturma deneyimi",
  "842": "Estetik ve Şık Tasarım:",
  "843": "Modern ve profesyonel bir atmosfer oluşturan estetik sırt tasarımı",
  "844": "Başlık Ayarı ve Ekstra Destek:",
  "845": "Başlık yaslama yukarı-aşağı ayarı ile ekstra destek ve rahatlık",
  "846": "Bel ve sırt destek ayarı ile ergonomik oturuş pozisyonunu destekleyen özellikler",
  "847": "Dayanıklı Tekerlekler:",
  "848": "Sessiz ve pürüzsüz hareket sağlayan tekerlekler ile sağlam metal demonte yıldız ayak uzun yıllar güvenle kullanım imkânı sunar.",
  "849": "Kolay Bakım ve Temizlik:",
  "850": "Yumuşak yüzey kaplamalı malzemeler, kolay temizlik ve bakım sağlar",
  "851": "Ofis ortamında temiz ve düzenli bir görünümü sürdürmek için ideal malzemeler",
  "852": "Profesyonellik ve Performans:",
  "853": "İş performansınıza olumlu bir etki sağlayarak verimliliğinizi artırır",
  "854": "Ayarlanabilir Yükseklik Ayarı:",
  "855": "Yukarı aşağı yükseklik ayarı",
  "856": "Arkaya yaslanma sertlik ayarı, gününüzü koltuğunuzun size özel konforunu ayarlamakla geçirebilmenizi sağlar",
  "857": "Yumuşak Yüzey Kaplamalı Kolçaklar:",
  "858": "Estetik ve ergonomik yumuşak yüzey kaplamalı kolçaklar, çalışma süresince rahat bir destek sunar",
  "859": "Kolay temizlenebilir malzemeler, koltuğunuzun uzun ömürlü ve bakımlı kalmasını sağlar",
  "860": "Dayanıklı Tekerlerler:",
  "861": "360 Derece Hareket Kabiliyeti:",
  "862": "360 derece hareket kabiliyeti, ofis içinde özgürce iletişim kurabilmenize yardımcı olur",
  "863": "İşlevselliği ve kolay kullanımı ile Base Çalışma Sandalyesi, hem evde hem de işte yaşamınızı kolaylaştırır",
  "864": "3 adet askı bölmesi",
  "865": "2 adet fonksiyonel geniş çekmece",
  "866": "Polimer Kompozit Ayak",
  "867": "2 adet makine bölmesi",
  "868": "Sürgülü tabla sistemi",
  "869": "Dayanıklı gövde yapısı",
  "870": "Hem ev hem ofis kullanımına uygunluk",
  "871": "Su ve sıcak ile uzun süreli temasından kaçının. Nemli bir bezle temizlenebilir.",
  "872": "Uzun süreli kullanıma uygun kaliteli döşeme",
  "873": "4 adet geniş ve kullanışlı raf",
  "874": "İki kapaklı yapı ile pratik kullanım",
  "875": "Kapak içi bölme",
  "876": "Estetik metal kulp",
  "877": "5 adet metal askı",
  "878": "Oval köşeli tasarım",
  "879": "Metal destek aparatı",
  "880": "10 adet raf bölmesi",
  "881": "4 adet metal askı",
  "882": "1 adet askı üstü raf",
  "883": "Minderli oturma alanı",
  "884": "3 adet estetik ve sağlam metal askı aparatı",
  "885": "3 bölmeli alt dolap",
  "886": "1 adet açık bölme",
  "887": "Şerit led aydınlatma",
  "888": "Estetik kulp",
  "889": "2 adet kullanışlı raf",
  "890": "Zemine zarar vermeyecek MDF malzemeye uyumlu profil ayak",
  "891": "10 adet bölme",
  "892": "Metal estetik kulp",
  "893": "2 adet metal askı",
  "894": "Çizilmelere ve darbelere dayanıklı metal ayak",
  "895": "Çok bölmeli depolama alanı",
  "896": "Geniş üst yüzey",
  "897": "5 geniş bölme",
  "898": "2 askı",
  "899": "Özel tasarım metal kulp",
  "900": "Geniş alt raf ile ekstra depolama alanı",
  "901": "Dayanıklı ve sağlam ayak yapısı",
  "902": "İki renkli modern tasarım",
  "903": "Geniş ve kullanışlı yüzey",
  "904": "Köşe kullanımına uygun fonksiyonel tasarım",
  "905": "1 adet aynalı kapak",
  "906": "5 adet raf alanı",
  "907": "2 ayrı elbise askı bölümü",
  "908": "Üst ve alt bölümlerde askılık alanı",
  "909": "Geniş ve kullanışlı iç hacim",
  "910": "Vücut Ağırlığına Duyarlı Mekanizma: Yeni nesil mekanizma, kullanıcının vücut ağırlığına göre sırt yaslanma direncini dengeler ve daha kontrollü bir oturma deneyimi sunar.",
  "911": "Kademeli Kilitlenebilir Sırtlık: Sırt yaslanma mekanizması farklı kademelerde kilitlenerek çalışma ve dinlenme sırasında tercih edilen oturma pozisyonunun ayarlanmasını sağlar.",
  "912": "Yüksek Dansite Oturum Süngeri: Ergonomik ve dayanıklı yüksek dansite sünger, uzun süreli kullanımlarda konforlu bir oturma alanı sunar ve formunu korumaya yardımcı olur.",
  "913": "Nefes Alabilen File Sırtlık: Dayanıklı file yüzey, hava dolaşımını destekleyerek uzun süreli kullanımlarda daha ferah bir oturma deneyimi sağlar.",
  "914": "Ayarlanabilir Bel Desteği: Kullanıcının oturma pozisyonuna göre ayarlanabilen bel desteği, sırt ve bel bölgesinin desteklenmesine yardımcı olur.",
  "915": "Ayarlanabilir Kolçaklar: Yumuşak PU yüzeye sahip kolçaklar yukarı ve aşağı yönde ayarlanarak kolların çalışma alanına uygun konumlandırılmasını sağlar.",
  "916": "Dayanıklı Metal Yıldız Ayak: Sağlam metal yıldız ayak yapısı, koltuğun dengeli ve güvenli bir şekilde kullanılmasına yardımcı olur.",
  "917": "Sessiz ve Parke Dostu Tekerlekler: Dayanıklı tekerlekler sessiz ve akıcı hareket sağlarken parke gibi hassas zeminlerde çizilme riskini azaltmaya yardımcı olur.",
  "918": "Ergonomik Tasarım ve Konfor:",
  "919": "Vücut yapısına uyum sağlayan ergonomik sırt tasarımı ve ayarlanabilir bel desteği ile konforlu bir oturma deneyimi sunar. Uzun süreli çalışma saatlerinde sırt ve bel bölgesini destekler.",
  "920": "Ayarlanabilir Başlık Desteği:",
  "921": "Yukarı-aşağı ve ileri-geri ayarlanabilir başlık mekanizması sayesinde baş ve boyun bölgesine kişiselleştirilmiş destek sağlar.",
  "922": "Çok Fonksiyonlu Kolçaklar:",
  "923": "Farklı oturma pozisyonlarına uyum sağlayan çok fonksiyonlu kolçaklar, kolların rahat bir şekilde konumlandırılmasına yardımcı olur.",
  "924": "Ayarlanabilir Bel Desteği:",
  "925": "Ayarlanabilir bel desteği sayesinde kişisel ihtiyaçlara uygun ergonomik oturma pozisyonu oluşturulabilir.",
  "926": "Çok Fonksiyonlu Mekanizma:",
  "927": "Çok fonksiyonlu yeni nesil mekanizma, oturma pozisyonunun kişisel tercihlere göre ayarlanmasına olanak tanır. Yukarı-aşağı mandallı kontrol sistemi ile koltuk yüksekliği kolayca ayarlanabilir.",
  "928": "Oturum Minderi Ayarı:",
  "929": "İleri-geri ayarlanabilir oturum minderi sayesinde oturma derinliği kişisel ihtiyaçlara göre düzenlenebilir. Farklı vücut yapılarına uyum sağlayarak oturma konforunu artırır.",
  "930": "Sırt Yaslanma ve Kilitleme Sistemi:",
  "931": "Sırt yaslanma sertlik ayarı ile yaslanma direnci kişisel tercihlere göre düzenlenebilir. Sırt geri yaslanma kilidi sayesinde istenilen pozisyonda sabitlenebilir.",
  "932": "Sessiz ve Estetik Tekerlekler:",
  "933": "Geniş ve estetik tasarımlı sessiz tekerlekler sayesinde çalışma alanında rahat ve akıcı hareket imkânı sunar.",
  "934": "Modern çizgileri, zarif renk uyumu ve fonksiyonel detaylarıyla ofis ve ev çalışma alanlarına estetik bir görünüm kazandırır.",
  "935": "Ergonomik Tasarım ve Üstün Konfor:",
  "936": "Tam ergonomik yapısı, birbirinden bağımsız ayarlanabilir sırt ve bel desteği sayesinde vücut yapısına uyum sağlayarak konforlu bir oturma deneyimi sunar. Uzun süreli çalışma saatlerinde rahatlığı destekler.",
  "937": "Elektrikli Bel Masajı Özelliği:",
  "938": "Bel desteğine entegre elektrikli masaj ünitesi sayesinde çalışma sırasında ekstra konfor sağlar. Masaj fonksiyonunun kullanılabilmesi için ürünün prize bağlanması gerekmektedir.",
  "939": "Ayarlanabilir Sırt ve Bel Desteği:",
  "940": "Birbirinden bağımsız ayarlanabilen sırt ve bel destekleri, kişisel oturma alışkanlıklarına uyum sağlar. Nefes alabilen file sırtlık ve ayarlanabilir bel desteği ile ergonomik oturma pozisyonunu destekler.",
  "941": "Yeni Nesil Yaslanma Mekanizması:",
  "942": "Ayarlanabilir ve kilitlenebilir geriye yaslanma mekanizması sayesinde farklı oturma pozisyonlarına kolayca geçiş yapılabilir. Kullanıcının tercih ettiği pozisyonda sırtlık sabitlenebilir.",
  "943": "Ayarlanabilir Kolçaklar:",
  "944": "Yumuşak PU yüzeye sahip yukarı-aşağı ayarlanabilir kolçaklar, kolların rahatça konumlandırılmasına yardımcı olur. Farklı çalışma masası yüksekliklerine uyum sağlar.",
  "945": "Dayanıklı ve Konforlu Oturum Süngeri:",
  "946": "Ergonomik yapıya sahip dayanıklı yüksek dansiteli oturum süngeri, uzun süreli kullanımlarda konforlu bir oturma alanı sunar.",
  "947": "Nefes Alabilen File Sırtlık:",
  "948": "Dayanıklı ve hava geçirgenliği sağlayan file sırtlık tasarımı, hava dolaşımını destekleyerek uzun çalışma saatlerinde ferah bir kullanım deneyimi sunar.",
  "949": "Estetik ve Dayanıklı Naylon Yıldız Ayak:",
  "950": "Modern tasarıma sahip dayanıklı naylon yıldız ayak, koltuğa sağlam bir temel oluştururken ofis ve ev çalışma alanlarına şık bir görünüm kazandırır.",
  "951": "Sessiz ve Parke Çizmeyen Tekerlekler:",
  "952": "Sessiz hareket sağlayan, parke yüzeyleri çizmeye karşı tasarlanmış dayanıklı tekerlekler sayesinde çalışma alanında rahat ve akıcı hareket imkânı sunar.",
  "953": "Modern ve Fonksiyonel Tasarım:",
  "954": "Şık görünümü, ergonomik detayları ve fonksiyonel özellikleriyle hem profesyonel ofislerde hem de ev çalışma ortamlarında konfor ve estetiği bir araya getirir."
};
const curated=[];
const add=(index,en,ru,ar)=>{const tr=source[index];if(!tr)throw new Error('Unknown source index '+index);curated.push({tr,en,ru,ar});};

// CURATED_ROWS
add(546,'3 metal mesh shelves and 1 particleboard shelf','3 полки из металлической сетки и 1 полка из ДСП','3 رفوف شبكية معدنية ورف واحد من الخشب الحبيبي');
add(547,'Metal mesh door','Дверца из металлической сетки','باب شبكي معدني');
add(548,'Suitable for both home and office use','Подходит для дома и офиса','مناسب للاستخدام المنزلي والمكتبي');
add(549,'Modern design','Современный дизайн','تصميم عصري');
add(550,'Ideal dimensions for bedside use','Размеры, подходящие для размещения у кровати','أبعاد مثالية للاستخدام بجانب السرير');
add(551,'Soft-closing drawers on telescopic runners','Ящики с плавным закрыванием на телескопических направляющих','أدراج بإغلاق ناعم على سكك تلسكوبية');
add(552,'Mink-coloured body / Zebra drawer-front detail','Корпус цвета норки / фасад ящика Zebra','هيكل بلون المنك / تفصيل واجهة درج بنقش Zebra');
add(553,'5 spacious practical drawers','5 вместительных удобных ящиков','5 أدراج واسعة وعملية');
add(554,'Convenient even in small spaces','Удобно даже в небольших помещениях','استخدام مريح حتى في المساحات الصغيرة');
add(555,'Spacious interior for organised storage','Вместительное внутреннее пространство для аккуратного хранения','مساحة داخلية واسعة للتخزين المنظم');
add(556,'Mink-coloured body / Zebra headboard detail','Корпус цвета норки / изголовье Zebra','هيكل بلون المنك / تفصيل لوح رأس بنقش Zebra');
add(557,'Suitable for a double-bed sleeping area','Подходит для двуспального места','مناسب لمساحة نوم مزدوجة');
add(558,'Supportive centre-leg system','Система центральных опорных ножек','نظام أرجل وسطية داعمة');
add(559,'Decorative zebra pattern on the headboard','Декоративный узор зебры на изголовье','نقش حمار وحشي زخرفي على لوح الرأس');
add(560,'Easy assembly and durable construction','Простая сборка и прочная конструкция','تركيب سهل وبنية متينة');
add(561,'Mink-coloured body / Zebra drawer fronts','Корпус цвета норки / фасады ящиков Zebra','هيكل بلون المنك / واجهات أدراج بنقش Zebra');
add(562,'Modern functional design','Современный функциональный дизайн','تصميم عصري وعملي');
add(563,'Attractive handle details','Красивые детали ручек','تفاصيل مقابض أنيقة');
add(564,'Mink-coloured body / Zebra door','Корпус цвета норки / дверца Zebra','هيكل بلون المنك / باب بنقش Zebra');
add(565,'Deep practical interior','Глубокое удобное внутреннее пространство','مساحة داخلية عميقة وعملية');
add(566,'2-door sliding system','Раздвижная система с 2 дверцами','نظام انزلاق ببابين');
add(567,'Clothes rails and shelving layout','Организация пространства со штангами и полками','تنظيم بقضبان تعليق ورفوف');
add(568,'2 sliding doors','2 раздвижные дверцы','بابان منزلقان');
add(569,'Spacious interior with compartmentalised shelving','Вместительное внутреннее пространство с разделёнными полками','مساحة داخلية واسعة مع رفوف مقسمة');
add(570,'Quiet durable sliding mechanism','Тихий долговечный раздвижной механизм','آلية انزلاق هادئة ومتينة');
add(571,'2 tempered bronze-glass doors','2 дверцы из закалённого бронзового стекла','بابان من زجاج برونزي مقسّى');
add(572,'Compatible only with the Milano wardrobe series','Совместимо только с серией шкафов Milano','متوافق فقط مع سلسلة خزائن الملابس Milano');
add(573,'Frame construction for strength and style','Рамная конструкция для прочности и стильного вида','بنية إطار توفر المتانة والأناقة');
add(574,'Fully compatible with Milano wardrobe bodies','Полностью совместимо с корпусами шкафов Milano','متوافق تماماً مع هياكل خزائن الملابس Milano');
add(575,'1 door only','Только 1 дверца','باب واحد فقط');
add(576,'1 vertical divider','1 вертикальная перегородка','فاصل رأسي واحد');
add(577,'2 door panels','2 дверные панели','لوحا باب');
add(578,'Compatible only with the Milano wardrobe series','Совместимо только с серией шкафов Milano','متوافق فقط مع سلسلة خزائن الملابس Milano');
add(579,'Suitable for use as a right-hand or left-hand door','Подходит для установки справа или слева','مناسب للاستخدام كباب أيمن أو أيسر');
add(580,'Doors only; the wardrobe body is not included','Только дверцы; корпус шкафа не входит в комплект','المنتج أبواب فقط؛ هيكل خزانة الملابس غير مشمول');
add(581,'Body designed to accept 2 doors','Корпус для установки 2 дверей','هيكل مصمم لتركيب بابين');
add(582,'Spacious interior','Вместительное внутреннее пространство','مساحة داخلية واسعة');
add(583,'Body designed to accept 4 doors','Корпус для установки 4 дверей','هيكل مصمم لتركيب 4 أبواب');
add(584,'Wardrobe body only; doors excluded','Только корпус шкафа, без дверей','هيكل خزانة الملابس فقط، دون الأبواب');
add(585,'Bronze-glass surface','Поверхность из бронзового стекла','سطح زجاجي برونزي');
add(586,'Single door for fitting to a compatible wardrobe body','Одна дверца для установки на совместимый корпус шкафа','باب منفرد للتركيب على هيكل خزانة ملابس متوافق');
add(587,'Made with a high-quality melamine-faced particleboard frame and first-class glass.','Изготовлено из качественной ДСП с меламиновым покрытием и первоклассного стекла.','مصنوع بإطار من خشب حبيبي عالي الجودة مكسو بالميلامين وزجاج من الدرجة الأولى.');
add(588,'The glass is tempered for strength. All components use E1-certified materials meeting European Union health standards.','Используется прочное закалённое стекло. Все компоненты изготовлены из материалов с сертификатом E1, соответствующих санитарным нормам Европейского союза.','الزجاج مقسّى لزيادة المتانة. جميع المكونات من مواد معتمدة بمعيار E1 ومتوافقة مع المعايير الصحية للاتحاد الأوروبي.');
add(589,'Stylish modern design','Стильный современный дизайн','تصميم عصري أنيق');
add(590,'Modular drawer organiser with 8 compartments','Модульный органайзер для ящика с 8 отделениями','منظم أدراج معياري يضم 8 حجرات');
add(591,'Durable metal legs','Прочные металлические ножки','أرجل معدنية متينة');
add(592,'Tempered-glass tabletop.','Столешница из закалённого стекла.','سطح الطاولة من زجاج مقسّى.');
add(593,'1 metal clothes rail','1 металлическая штанга для одежды','قضيب معدني واحد لتعليق الملابس');
add(594,'Compatible mattress size: 90 × 190 cm','Подходящий размер матраса: 90 × 190 см','مقاس المرتبة المتوافق: 90 × 190 سم');
add(595,'A colour chart is available.','Доступна карта цветов.','تتوفر لوحة ألوان.');
add(596,'For lounges, living rooms, hotels and similar settings','Для гостиных, жилых комнат, гостиниц и подобных помещений','للصالات وغرف المعيشة والفنادق وما شابه');
add(597,'Padded back / Soft seat / Raised off the floor','Мягкая спинка / мягкое сиденье / высокая посадка над полом','ظهر مبطن / مقعد ناعم / مرتفع عن الأرض');
add(598,'Hornbeam frame reinforced with steel flat bars','Каркас из граба, усиленный стальными полосами','هيكل من خشب النير مدعم بشرائح فولاذية');
add(599,'Seat material: 30 Soft foam / Zigzag springs','Материал сиденья: пеноматериал 30 Soft / пружины «змейка»','مادة المقعد: إسفنج 30 Soft / نوابض متعرجة');
add(600,'Back cushion: 57 × 45 cm (1 piece)','Подушка спинки: 57 × 45 см (1 шт.)','وسادة الظهر: 57 × 45 سم (قطعة واحدة)');
add(601,'Seat depth: 55 cm','Глубина сиденья: 55 см','عمق المقعد: 55 سم');
add(602,'Seat width: 55 cm','Ширина сиденья: 55 см','عرض المقعد: 55 سم');
add(603,'Seat height: 45 cm','Высота сиденья: 45 см','ارتفاع المقعد: 45 سم');
add(604,'Ergonomic armrest cushions','Эргономичные подушки подлокотников','وسائد مساند ذراعين مريحة');
add(605,'Light resistance','Светостойкость','مقاومة للضوء');
add(606,'Armrest width: 12 cm','Ширина подлокотника: 12 см','عرض مسند الذراع: 12 سم');
add(607,'Sturdy metal legs','Прочные металлические ножки','أرجل معدنية متينة');
add(608,'Leg height: 17 cm','Высота ножек: 17 см','ارتفاع الأرجل: 17 سم');
add(609,'Leg cross-section: 4 cm × 2 cm','Сечение ножек: 4 см × 2 см','مقطع الأرجل: 4 سم × 2 سم');
add(610,'Leg colour: Black','Цвет ножек: чёрный','لون الأرجل: أسود');
add(611,'Weight: 95 kg','Вес: 95 кг','الوزن: 95 كغ');
add(612,'Raised off the floor','Приподнято над полом','مرتفع عن الأرض');
add(613,'Suitable for robot vacuum cleaners','Подходит для уборки роботом-пылесосом','مناسب للتنظيف بالمكنسة الروبوتية');
add(614,'Available only from our stores.','Доступно только в наших магазинах.','متوفر في متاجرنا فقط.');
add(615,'Hornbeam and plywood frame','Каркас из граба и фанеры','هيكل من خشب النير والخشب الرقائقي');
add(616,'Rearward-moving mechanism','Механизм перемещения назад','آلية تحريك للخلف');
add(617,'Seat material: 30 DNS foam / Zigzag springs','Материал сиденья: пеноматериал 30 DNS / пружины «змейка»','مادة المقعد: إسفنج 30 DNS / نوابض متعرجة');
add(618,'Seat depth: 62 cm','Глубина сиденья: 62 см','عمق المقعد: 62 سم');
add(619,'Seat width: 180 cm','Ширина сиденья: 180 см','عرض المقعد: 180 سم');
add(620,'Scatter cushion size: 50 × 50 (2 pieces)','Размер декоративной подушки: 50 × 50 (2 шт.)','مقاس وسادة الزينة: 50 × 50 (قطعتان)');
add(621,'Depth: 95 cm','Глубина: 95 см','العمق: 95 سم');
add(622,'Armrest width: 20 cm','Ширина подлокотника: 20 см','عرض مسند الذراع: 20 سم');
add(623,'Sturdy wooden legs','Прочные деревянные ножки','أرجل خشبية متينة');
add(624,'Leg height: 17 cm','Высота ножек: 17 см','ارتفاع الأرجل: 17 سم');
add(625,'Leg thickness: 4 cm','Толщина ножек: 4 см','سماكة الأرجل: 4 سم');
add(626,'Weight: 73 kg','Вес: 73 кг','الوزن: 73 كغ');
add(627,'Rearward-moving backrest mechanism','Механизм перемещения спинки назад','آلية تحريك مسند الظهر للخلف');
add(628,'Seat depth: 65–145 cm','Глубина сиденья: 65–145 см','عمق المقعد: 65–145 سم');
add(629,'Seat width: 240 cm','Ширина сиденья: 240 см','عرض المقعد: 240 سم');
add(630,'Seat height: 43 cm','Высота сиденья: 43 см','ارتفاع المقعد: 43 سم');
add(631,'Scatter cushion size: 35 × 50 (1 piece)','Размер декоративной подушки: 35 × 50 (1 шт.)','مقاس وسادة الزينة: 35 × 50 (قطعة واحدة)');
add(632,'Depth: 100 cm','Глубина: 100 см','العمق: 100 سم');
add(633,'Armrest width: 18 cm','Ширина подлокотника: 18 см','عرض مسند الذراع: 18 سم');
add(634,'CSS (rotating inner back)','CSS (поворотная внутренняя спинка)','CSS (ظهر داخلي دوّار)');
add(635,'Seat depth: 60 cm','Глубина сиденья: 60 см','عمق المقعد: 60 سم');
add(636,'Seat width: 200 cm','Ширина сиденья: 200 см','عرض المقعد: 200 سم');
add(637,'Seat height: 46 cm','Высота сиденья: 46 см','ارتفاع المقعد: 46 سم');
add(638,'Armrest width: 15 cm','Ширина подлокотника: 15 см','عرض مسند الذراع: 15 سم');
add(639,'Leg height: 14 cm','Высота ножек: 14 см','ارتفاع الأرجل: 14 سم');
add(640,'Leg thickness: 5 cm × 6 mm','Толщина ножек: 5 см × 6 мм','سماكة الأرجل: 5 سم × 6 مم');
add(641,'Weight: 70 kg','Вес: 70 кг','الوزن: 70 كغ');
add(642,'Modern soft-touch fabric','Современная мягкая на ощупь ткань','قماش عصري ناعم الملمس');
add(643,'Ergonomic body design','Эргономичная конструкция корпуса','تصميم هيكل مريح');
add(644,'One-piece body with fixed armrests','Цельный корпус с неподвижными подлокотниками','هيكل من قطعة واحدة بمساند ذراعين ثابتة');
add(645,'Height-adjustable mechanism','Механизм регулировки высоты','آلية لضبط الارتفاع');
add(646,'Sturdy 5-arm base with castors','Прочная 5-лучевая опора с роликами','قاعدة متينة ذات 5 أذرع وعجلات');
add(647,'The Milano desk chair combines minimalist design and soft-touch fabric for comfortable seating with style. It brings elegance and function to home offices and boutique workspaces alike.','Рабочее кресло Milano сочетает минималистичный дизайн и мягкую на ощупь ткань для комфортного и стильного сидения. Оно добавляет элегантность и функциональность как домашнему офису, так и небольшим рабочим пространствам.','يجمع كرسي المكتب Milano بين التصميم البسيط والقماش الناعم لجلوس مريح وأنيق. ويضيف الأناقة والوظائف العملية إلى المكاتب المنزلية ومساحات العمل الصغيرة المميزة.');
add(648,'Home-office spaces','Домашние офисы','مساحات العمل المكتبي المنزلي');
add(649,'Dressing rooms and makeup corners','Гардеробные и зоны для макияжа','غرف الملابس وزوايا المكياج');
add(650,'Boutique offices and reception desks','Небольшие офисы и стойки приёма','المكاتب الصغيرة المميزة ومكاتب الاستقبال');
add(651,'Stylish studio spaces','Стильные студии','مساحات الاستوديو الأنيقة');
add(652,'Rounded back and arm structure integrated through to the armrests','Округлая спинка, плавно переходящая в подлокотники','بنية مستديرة للظهر والجوانب متكاملة حتى مساند الذراعين');
add(653,'Light-toned natural-look fabric upholstery','Тканевая обивка светлого натурального оттенка','كسوة قماشية فاتحة بلون طبيعي');
add(654,'Easy-adjust gas lift system','Газлифт с простой регулировкой','نظام مكبس غازي سهل التعديل');
add(655,'Curved armrests supporting the wrists','Изогнутые подлокотники с опорой на уровне запястий','مساند ذراعين منحنية تدعم عند مستوى المعصم');
add(656,'5-arm base with castors','5-лучевая опора с роликами','قاعدة ذات 5 أذرع وعجلات');
add(657,'Soft-touch fabric upholstery.','Обивка из мягкой на ощупь ткани.','كسوة قماشية ناعمة الملمس.');
add(658,'Quality faux-leather upholstery','Качественная обивка из искусственной кожи','كسوة من جلد صناعي عالي الجودة');
add(659,'Ergonomic back and arm structure','Эргономичная конструкция спинки и подлокотников','بنية ظهر ومساند ذراعين مريحة');
add(660,'Stylish one-piece body','Стильный цельный корпус','هيكل أنيق من قطعة واحدة');
add(661,'Extra-thick cushions','Особо толстые подушки','وسائد فائقة السماكة');
add(662,'A soft, thick sprung seat cushion reduces pressure and provides support even during long periods of sitting. A full, body-hugging back cushion.','Мягкая толстая подушка сиденья с пружинами снижает давление на тело и поддерживает его даже при длительном сидении. Объёмная подушка спинки повторяет контуры тела.','تخفف وسادة المقعد الناعمة والسميكة المزودة بنوابض ضغط الجسم وتوفر الدعم حتى أثناء الجلوس الطويل. ووسادة ظهر ممتلئة تحتضن الجسم.');
add(663,'Adjustable head-support cushion','Регулируемая подушка под голову','وسادة دعم رأس قابلة للتعديل');
add(664,'The head-support cushion adjusts forwards and backwards and locks at different angles for a comfortable working position.','Подушка под голову регулируется вперёд и назад и фиксируется под разными углами для удобной работы.','يمكن تحريك وسادة دعم الرأس للأمام والخلف وتثبيتها بزوايا مختلفة لاختيار وضعية عمل مريحة.');
add(665,'Reclining mechanism & extending footrest','Механизм откидывания и выдвижная подставка для ног','آلية استلقاء ووحدة تمديد القدمين');
add(666,'A reclining backrest that locks at different angles and an extending footrest cushion turn short breaks into relaxing rest sessions.','Откидывающаяся спинка с фиксацией под разными углами и выдвижная мягкая подставка для ног превращают короткие перерывы в полноценный отдых.','يحول مسند الظهر المائل القابل للتثبيت بزوايا مختلفة ووسادة تمديد القدمين القابلة للفتح والإغلاق الاستراحات القصيرة إلى فترات استرخاء.');
add(667,'Soft fabric upholstery','Мягкая тканевая обивка','كسوة قماشية ناعمة');
add(668,'Quality fabric upholstery complements the modern look; its breathable structure helps prevent sweating and provides all-day comfort.','Качественная тканевая обивка дополняет современный вид; дышащая структура помогает предотвратить потение и обеспечивает комфорт весь день.','تكمل الكسوة القماشية عالية الجودة المظهر العصري، وتساعد بنيتها القابلة للتنفس على منع التعرق وتوفير الراحة طوال اليوم.');
add(669,'Ergonomic armrests','Эргономичные подлокотники','مساند ذراعين مريحة');
add(670,'Fixed armrests with soft foam padding and fabric upholstery support the elbows and arms for an ergonomic sitting position.','Неподвижные подлокотники с мягким пенным наполнителем и тканевой обивкой поддерживают локти и руки для эргономичной посадки.','تدعم مساند الذراعين الثابتة ذات الحشو الإسفنجي الناعم والكسوة القماشية المرفقين والذراعين لجلوس مريح.');
add(671,'Durable metal base & castor system','Прочная металлическая опора и ролики','قاعدة معدنية متينة ونظام عجلات');
add(672,'Quiet 360-degree swivelling castors and a strong metal base provide safe, long-lasting use.','Тихие поворотные ролики на 360 градусов и прочная металлическая опора обеспечивают безопасную долгую эксплуатацию.','توفر العجلات الهادئة الدوارة 360 درجة والقاعدة المعدنية القوية استخداماً آمناً وطويل الأمد.');
add(673,'Home offices','Домашние офисы','المكاتب المنزلية');
add(674,'Professional workspaces','Профессиональные рабочие пространства','بيئات العمل المهنية');
add(675,'Gaming and relaxation areas','Зоны для игр и отдыха','مناطق اللعب والاسترخاء');
add(676,'Fixed armrests with soft foam padding and fabric upholstery support the elbows and arms for an ergonomic sitting position.','Неподвижные подлокотники с мягким пенным наполнителем и тканевой обивкой поддерживают локти и руки для эргономичной посадки.','تدعم مساند الذراعين الثابتة ذات الحشو الإسفنجي الناعم والكسوة القماشية المرفقين والذراعين لجلوس مريح.');
add(677,'Modern metal styling adds elegance to interiors','Современный металлический стиль придаёт интерьеру элегантность','يضفي الطراز المعدني العصري أناقة على المكان');
add(678,'Made from high-quality particleboard. Legs and support parts are matt black metal.','Изготовлено из качественной ДСП. Ножки и опорные детали — матовый чёрный металл.','مصنوع من خشب حبيبي عالي الجودة. الأرجل وأجزاء الدعم من معدن أسود مطفي.');
add(679,'All components use E1-certified materials meeting European Union health standards and contain no harmful substances.','Все компоненты изготовлены из материалов с сертификатом E1, соответствующих санитарным нормам Европейского союза, и не содержат вредных веществ.','جميع المكونات من مواد معتمدة بمعيار E1 ومتوافقة مع المعايير الصحية للاتحاد الأوروبي وخالية من المواد الضارة.');
add(680,'1 package in total.','Всего 1 упаковка.','عبوة واحدة إجمالاً.');
add(681,'Extra-soft teddy fabric upholstery; adjustable seat height','Особо мягкая обивка «тедди»; регулируемая высота сиденья','كسوة تيدي فائقة النعومة؛ ارتفاع مقعد قابل للتعديل');
add(682,'360-degree swivel mechanism','Механизм поворота на 360 градусов','آلية دوران 360 درجة');
add(683,'Durable metal base and quiet castors','Прочная металлическая опора и тихие ролики','قاعدة معدنية متينة وعجلات هادئة');
add(684,'Ideal for young people, children and home offices','Подходит для подростков, детей и домашнего офиса','مثالي للشباب والأطفال والمكاتب المنزلية');
add(685,'An ergonomic structure with soft teddy upholstery and high-density foam filling. The lower frame and legs are durable powder-coated metal.','Эргономичная конструкция с мягкой обивкой «тедди» и наполнителем из пеноматериала высокой плотности. Нижний каркас и ножки — прочный металл с порошковым покрытием.','بنية مريحة بكسوة تيدي ناعمة وحشو إسفنجي عالي الكثافة. الهيكل السفلي والأرجل من معدن متين مطلي بالبودرة.');
add(686,'Extra-soft teddy fabric upholstery','Особо мягкая обивка из ткани «тедди»','كسوة تيدي فائقة النعومة');
add(687,'Sprung seat cushion for lasting comfort','Пружинная подушка сиденья для длительного комфорта','وسادة مقعد بنوابض لراحة طويلة');
add(688,'Height-adjustable gas lift system','Газлифт с регулировкой высоты','نظام مكبس غازي قابل لضبط الارتفاع');
add(689,'360° swivel metal base and sturdy castors','Металлическая опора с поворотом на 360° и прочные ролики','قاعدة معدنية دوارة 360 درجة وعجلات متينة');
add(690,'Retro-style ergonomic back and armrests','Эргономичные спинка и подлокотники в стиле ретро','ظهر ومساند ذراعين مريحة بطراز ريترو');
add(691,'New-technology fabric upholstery with a leather look','Тканевая обивка нового поколения с видом кожи','كسوة قماشية بتقنية جديدة ومظهر جلدي');
add(692,'Durable faux-leather upholstery. The seat has springs and high-density foam filling. Legs and frame are strong metal.','Прочная обивка из искусственной кожи. Сиденье оснащено пружинами и наполнителем из пеноматериала высокой плотности. Ножки и каркас изготовлены из прочного металла.','كسوة من جلد صناعي متين. يحتوي المقعد على نظام نوابض وحشو إسفنجي عالي الكثافة. الأرجل والهيكل من معدن قوي.');
add(693,'3 functions: Pouffe, armchair and single bed','3 функции: пуф, кресло и односпальная кровать','3 استخدامات: مقعد بوف وكرسي وسرير فردي');
add(694,'Adjustable back and footrest positions','Регулируемое положение спинки и подставки для ног','وضعيتا ظهر وقدمين قابلتان للتعديل');
add(695,'Upholstery with high-density foam filling','Обивка с наполнителем из пеноматериала высокой плотности','كسوة بحشو إسفنجي عالي الكثافة');
add(696,'Durable internal metal frame','Прочный внутренний металлический каркас','هيكل داخلي معدني متين');
add(697,'Folds easily to save space','Легко складывается и экономит место','سهل الطي ويوفر المساحة');
add(698,'Quality upholstery fabric, a high-density foam seat and a durable metal frame. The legs have strong metal supports.','Качественная обивочная ткань, сиденье из пеноматериала высокой плотности и прочный металлический каркас. Ножки усилены прочными металлическими опорами.','قماش تنجيد عالي الجودة ومقعد بحشو إسفنجي عالي الكثافة وهيكل معدني متين. بنية الأرجل مدعمة بمعدن قوي.');
add(699,'Sold as a set of four.','Продаётся комплектом из четырёх предметов.','يباع كمجموعة من أربع قطع.');
add(700,'Modern quilted fabric upholstery','Современная стёганая тканевая обивка','كسوة قماشية مبطنة بتصميم عصري');
add(701,'Ergonomic back and seat design','Эргономичная конструкция спинки и сиденья','تصميم ظهر ومقعد مريح');
add(702,'Matt black metal legs','Матовые чёрные металлические ножки','أرجل معدنية سوداء مطفية');
add(703,'Durable sturdy construction','Прочная надёжная конструкция','بنية متينة وقوية');
add(704,'Neutral colour palette for versatile coordination','Нейтральные цвета для разнообразных сочетаний','ألوان محايدة لتنسيق متعدد الخيارات');
add(705,'Quilted fabric combined with metal legs.','Сочетание стёганой ткани и металлических ножек.','قماش مبطن مع أرجل معدنية.');
add(706,'Contains materials meeting European Union E1 standards.','Содержит материалы, соответствующие стандартам E1 Европейского союза.','يحتوي على مواد متوافقة مع معايير E1 للاتحاد الأوروبي.');
add(707,'Wipe with a damp cloth. Do not use chemical cleaners.','Протирайте влажной тканью. Не используйте химические чистящие средства.','يُنظف بقطعة قماش رطبة. لا تستخدم المنظفات الكيميائية.');
add(708,'1 package containing 2 chairs.','1 упаковка, содержащая 2 стула.','عبوة واحدة تحتوي على كرسيين.');
add(709,'Spacious desktop with a carbon-fibre pattern','Просторная столешница с узором под углеволокно','سطح مكتب واسع بنقش ألياف الكربون');
add(710,'Gamer-friendly design with RGB lighting','Удобная для игроков конструкция с RGB-подсветкой','تصميم مناسب للاعبين مع إضاءة RGB');
add(711,'Headphone and cup holders included','Держатели для наушников и стакана входят в комплект','يشمل حامل السماعات وحامل الكوب');
add(712,'Cable openings and keyboard shelf','Отверстия для кабелей и полка для клавиатуры','فتحات للكابلات ورف لوحة مفاتيح');
add(713,'X-shaped metal legs for a sturdy structure','X-образные металлические ножки для прочности','أرجل معدنية بشكل X لبنية متينة');
add(714,'Melamine-faced particleboard top and powder-coated metal frame. The top has a carbon-fibre appearance.','Столешница из ДСП с меламиновым покрытием и металлический каркас с порошковой окраской. Столешница имеет вид углеволокна.','سطح من خشب حبيبي مكسو بالميلامين وهيكل معدني مطلي بالبودرة. السطح بمظهر ألياف الكربون.');
add(715,'All materials are E1-certified and contain no substances harmful to human health.','Все материалы имеют сертификат E1 и не содержат веществ, вредных для здоровья человека.','جميع المواد معتمدة بمعيار E1 ولا تحتوي على مواد ضارة بصحة الإنسان.');
add(716,'Upper monitor shelf with concealed RGB lighting','Верхняя полка для монитора со скрытой RGB-подсветкой','رف شاشة علوي بإضاءة RGB مخفية');
add(717,'Charging unit with USB-A and USB-C ports','Зарядный блок с портами USB-A и USB-C','وحدة شحن بمنافذ USB-A وUSB-C');
add(718,'Headphone hook and cup holder fittings','Крепления для наушников и стакана','ملحقات لتعليق السماعات وحمل الكوب');
add(719,'Rear metal shelf for cable organisation','Задняя металлическая полка для кабелей','رف معدني خلفي لتنظيم الكابلات');
add(720,'160 cm wide desktop','Столешница шириной 160 см','سطح مكتب بعرض 160 سم');
add(721,'The Ryze Castle gaming desk has a special scratch-resistant surface and a strong metal frame. The carbon-fibre-look top combines style and function.','Игровой стол Ryze Castle оснащён специальной устойчивой к царапинам поверхностью и прочным металлическим каркасом. Столешница с текстурой под углеволокно сочетает стиль и функциональность.','يتميز مكتب الألعاب Ryze Castle بسطح خاص مقاوم للخدوش وهيكل معدني قوي. ويجمع سطحه بمظهر ألياف الكربون بين الأناقة والوظائف العملية.');
add(722,'100 × 76 cm (Diameter × Height)','100 × 76 см (диаметр × высота)','100 × 76 سم (القطر × الارتفاع)');
add(723,'Round tabletop, 100 cm across','Круглая столешница диаметром 100 см','سطح طاولة دائري بعرض 100 سم');
add(724,'Sturdy powder-coated metal legs','Прочные металлические ножки с порошковым покрытием','أرجل معدنية متينة مطلية بالبودرة');
add(725,'Comfortably seats 4 people','Удобное размещение 4 человек','استخدام مريح لـ 4 أشخاص');
add(726,'Compact space-saving design','Компактная конструкция для экономии места','تصميم مدمج يوفر المساحة');
add(727,'Easy-clean surface','Поверхность, которую легко чистить','سطح سهل التنظيف');
add(728,'Folding tabletop saves space.','Складная столешница экономит место.','يوفر السطح القابل للطي المساحة.');
add(729,'Multipurpose use: Suitable for kitchens, offices, balconies and workspaces.','Многофункциональное использование: подходит для кухни, офиса, балкона и рабочего пространства.','متعددة الاستخدامات: مناسبة للمطبخ والمكتب والشرفة ومساحات العمل.');
add(730,'Modern design with metal legs and a walnut colour combination for a stylish appearance.','Современный дизайн с металлическими ножками и цветом ореха для стильного вида.','تصميم عصري بأرجل معدنية وتنسيق لون الجوز لمظهر أنيق.');
add(731,'Top and body are made from melamine-faced particleboard. Legs and support parts are durable black metal.','Столешница и корпус изготовлены из ДСП с меламиновым покрытием. Ножки и опорные детали — прочный чёрный металл.','السطح والهيكل من خشب حبيبي مكسو بالميلامين. الأرجل وأجزاء الدعم من معدن أسود متين.');
add(732,'Wipe with a damp cloth. No detergent is required. Avoid prolonged contact with water or heat.','Протирайте влажной тканью. Моющие средства не требуются. Избегайте длительного контакта с водой и теплом.','يُنظف بقطعة قماش رطبة دون الحاجة إلى منظف. تجنب التعرض المطول للماء والحرارة.');
add(733,'Tall table with shelving and 2 stools','Высокий стол с полками и 2 табуретами','طاولة مرتفعة برفوف ومقعدين مرتفعين');
add(734,'Compact shelving design keeps things organised','Компактная конструкция с полками помогает поддерживать порядок','يساعد التصميم المدمج المزود برفوف على التنظيم');
add(735,'Suitable for homes, kitchens, offices, balconies and other spaces','Подходит для дома, кухни, офиса, балкона и других помещений','مناسب للمنزل والمطبخ والمكتب والشرفة وغيرها');
add(736,'Modern retro styling adds elegance to interiors','Современный стиль ретро придаёт интерьеру элегантность','يضفي طراز الريترو العصري أناقة على المكان');
add(737,'White high-quality melamine-faced particleboard top and white powder-coated metal legs. The table’s shelving provides practical storage.','Столешница из качественной белой ДСП с меламиновым покрытием и белые металлические ножки с порошковой окраской. Полки стола обеспечивают удобное хранение.','سطح أبيض من خشب حبيبي عالي الجودة مكسو بالميلامين وأرجل معدنية بيضاء مطلية بالبودرة. يوفر قسم الرفوف بالطاولة تخزيناً عملياً.');
add(738,'Tall table and 2 stools','Высокий стол и 2 табурета','طاولة مرتفعة ومقعدان مرتفعان');
add(739,'Tabletop and stool seats are high-quality particleboard. Legs and support parts are matt white metal.','Столешница и сиденья табуретов изготовлены из качественной ДСП. Ножки и опорные детали — матовый белый металл.','سطح الطاولة والمقاعد من خشب حبيبي عالي الجودة. الأرجل وأجزاء الدعم من معدن أبيض مطفي.');
add(740,'Wipe with a damp cloth. No detergent is required. Avoid prolonged contact with water or heat.','Протирайте влажной тканью. Моющие средства не требуются. Избегайте длительного контакта с водой и теплом.','يُنظف بقطعة قماش رطبة دون الحاجة إلى منظف. تجنب التعرض المطول للماء والحرارة.');
add(741,'2 packages in total.','Всего 2 упаковки.','عبوتان إجمالاً.');
add(742,'Spacious storage with 6 open compartments','Вместительное хранение с 6 открытыми отделениями','مساحة تخزين واسعة تضم 6 حجرات مفتوحة');
add(743,'Enclosed lower section with 2 doors','Нижнее закрытое отделение с 2 дверцами','قسم سفلي مغلق ببابين');
add(744,'Modern look combining walnut and black','Современное сочетание цвета ореха и чёрного','مظهر عصري بتناسق لون الجوز والأسود');
add(745,'Ideal for living rooms, studies or offices','Подходит для гостиной, кабинета и офиса','مثالي لغرفة المعيشة أو الدراسة أو المكتب');
add(746,'Melamine-faced particleboard top with metal legs. The door hinges are durable and long-lasting.','Столешница из ДСП с меламиновым покрытием и металлические ножки. Петли дверей прочные и долговечные.','سطح من خشب حبيبي مكسو بالميلامين وأرجل معدنية. مفصلات الأبواب متينة وطويلة العمر.');
add(747,'2 practical drawers','2 удобных ящика','درجان عمليان');
add(748,'2 spacious drawers','2 вместительных ящика','درجان واسعان');
add(749,'Stylish metal legs with gold details','Стильные металлические ножки с золотистыми деталями','أرجل معدنية أنيقة بتفاصيل ذهبية');
add(750,'Walnut-coloured top contrasts with black drawers','Столешница цвета ореха контрастирует с чёрными ящиками','سطح بلون الجوز مع أدراج سوداء متباينة');
add(751,'Durable stable construction','Прочная устойчивая конструкция','بنية متينة وثابتة');
add(752,'Special ergonomic design for ages 8–15','Особая эргономичная конструкция для возраста 8–15 лет','تصميم مريح خاص للأعمار من 8 إلى 15 سنة');
add(753,'Height-adjustable mechanism','Механизм регулировки высоты','آلية لضبط الارتفاع');
add(754,'RGB LED lighting around the entire seat and backrest','RGB-светодиодная подсветка по всему периметру сиденья и спинки','إضاءة LED RGB حول كامل محيط المقعد ومسند الظهر');
add(755,'The same quality and comfort as adult gaming chairs','Качество и комфорт как у игровых кресел для взрослых','نفس جودة وراحة كراسي الألعاب للكبار');
add(756,'Mechanism and base components are durable metal.','Механизм и компоненты опоры изготовлены из прочного металла.','الآلية وأجزاء القاعدة مصنوعة من معدن متين.');
add(757,'The leather-look surface is made from a quality, durable new-technology fabric.','Поверхность с видом кожи изготовлена из качественной прочной ткани нового поколения.','السطح ذو المظهر الجلدي مصنوع من قماش متين وعالي الجودة بتقنية جديدة.');
add(758,'Supplied unassembled; all assembly parts are in the box.','Поставляется в разобранном виде; все детали для сборки находятся в коробке.','يأتي مفككاً، وجميع قطع التركيب موجودة في الصندوق.');
add(759,'Only a screwdriver is needed for assembly; parts are numbered.','Для сборки нужна только отвёртка; детали пронумерованы.','يلزم مفك براغٍ فقط للتركيب، والأجزاء مرقمة.');
add(760,'A strong, simple construction for quick and easy assembly.','Простая прочная конструкция для быстрой удобной сборки.','بنية قوية وبسيطة لتركيب سهل وسريع.');
add(761,'Can be assembled smoothly by 2 people.','Для удобной сборки достаточно 2 человек.','يمكن تركيبه بسهولة بواسطة شخصين.');
add(762,'Ergonomic design for ages 8–15','Эргономичная конструкция для возраста 8–15 лет','تصميم مريح للأعمار من 8 إلى 15 سنة');
add(763,'RGB LED lighting in the back','RGB-светодиодная подсветка спинки','إضاءة LED RGB في قسم الظهر');
add(764,'Stylish designer handles','Стильные дизайнерские ручки','مقابض بتصميم أنيق');
add(765,'5 hanging compartments','5 отделений для подвешивания','5 حجرات للتعليق');
add(431,'1 cable duct','1 кабель-канал','مجرى كابلات واحد');
add(432,'Composite feet','Композитные ножки','أرجل من مادة مركبة');
add(433,'Open dimensions: 199 × 117 × 32 cm overall when unfolded as a bed (Length × Width × Height)','Размеры в разложенном виде: 199 × 117 × 32 см, общие размеры спального места (длина × ширина × высота)','الأبعاد عند الفتح كسرير: إجمالي 199 × 117 × 32 سم (الطول × العرض × الارتفاع)');
add(434,'Closed dimensions: 117 × 86,5 × 81 cm overall when folded as a chair (Length × Width × Height)','Размеры в сложенном виде: 117 × 86,5 × 81 см, общие размеры кресла (длина × ширина × высота)','الأبعاد عند الإغلاق ككرسي: إجمالي 117 × 86,5 × 81 سم (الطول × العرض × الارتفاع)');
add(435,'Open dimensions: 199 × 76 × 32 cm overall when unfolded as a bed (Length × Width × Height)','Размеры в разложенном виде: 199 × 76 × 32 см, общие размеры спального места (длина × ширина × высота)','الأبعاد عند الفتح كسرير: إجمالي 199 × 76 × 32 سم (الطول × العرض × الارتفاع)');
add(436,'Closed dimensions: 76 × 85 × 81 cm overall when folded as a chair (Length × Width × Height)','Размеры в сложенном виде: 76 × 85 × 81 см, общие размеры кресла (длина × ширина × высота)','الأبعاد عند الإغلاق ككرسي: إجمالي 76 × 85 × 81 سم (الطول × العرض × الارتفاع)');
add(437,'Stylish modern design','Стильный современный дизайн','تصميم عصري أنيق');
add(438,'1 wide lower shelf','1 широкая нижняя полка','رف سفلي واسع واحد');
add(439,'100% polyester fabric','Ткань: 100% полиэстер','قماش من البوليستر بنسبة 100%');
add(440,'Solid-wood frame','Каркас из массива дерева','هيكل من الخشب المصمت');
add(441,'35 DNS foam','Пеноматериал 35 DNS','إسفنج بكثافة 35 DNS');
add(442,'Fabric: 30% cotton + 30% linen + 40% polyester','Ткань: 30% хлопок + 30% лён + 40% полиэстер','القماش: 30% قطن + 30% كتان + 40% بوليستر');
add(443,'Tall beechwood legs with a natural appearance','Высокие ножки из бука с естественным видом','أرجل مرتفعة من خشب الزان بمظهر طبيعي');
add(444,'Mirrored door','Зеркальная дверца','باب بمرآة');
add(445,'Soft-close hinge','Петля с доводчиком','مفصلة بإغلاق هادئ');
add(446,'10 compartments','10 отделений','10 حجرات');
add(447,'3 coloured asymmetric doors','3 цветные асимметричные дверцы','3 أبواب ملونة غير متماثلة');
add(448,'Ready to take your gaming performance further? Adore Gaming Maestro X adjusts in height to suit your comfort and help minimise back, wrist and neck pain during long sessions.','Готовы улучшить игровые результаты? Высота Adore Gaming Maestro X регулируется для индивидуального комфорта и уменьшения боли в спине, запястьях и шее при длительном использовании.','هل أنت مستعد لرفع مستوى أدائك في اللعب؟ يتيح تصميم Adore Gaming Maestro X القابل لضبط الارتفاع تخصيص الراحة ويساعد على تقليل ألم الظهر والمعصم والرقبة أثناء الاستخدام الطويل.');
add(449,'Cable management keeps your desk free of tangled cables.','Система организации кабелей избавляет стол от спутанных проводов.','يحافظ نظام تنظيم الكابلات على خلو المكتب من تشابك الأسلاك.');
add(450,'A cup holder and headphone hook provide convenience during gaming.','Подстаканник и крючок для наушников обеспечивают удобство во время игры.','يوفر حامل الكوب وخطاف السماعات الراحة أثناء اللعب.');
add(451,'High load capacity for strong, reliable use.','Высокая грузоподъёмность для прочности и надёжности.','قدرة تحمل عالية لاستخدام متين وموثوق.');
add(452,'Working height: 72–117 cm','Рабочая высота: 72–117 см','ارتفاع العمل: 72–117 سم');
add(453,'Operating voltage: AC100–240V; frequency: 50/60 Hz','Рабочее напряжение: AC100–240V; частота: 50/60 Гц','جهد التشغيل: AC100–240V؛ التردد: 50/60 هرتز');
add(454,'Operating ambient temperature: −10 / +40 degrees Celsius','Температура окружающей среды при работе: −10 / +40 градусов Цельсия','درجة حرارة بيئة التشغيل: −10 / +40 درجة مئوية');
add(455,'Maximum table load: 60 kg. Do not exceed this load, sit on the table or climb on it as a platform or ladder; never use it for these purposes.','Максимальная нагрузка на стол: 60 кг. Не превышайте её, не садитесь на стол и не вставайте на него для подъёма или вместо лестницы; такое использование запрещено.','أقصى حمل للطاولة: 60 كغ. لا تتجاوز هذا الحمل ولا تجلس على الطاولة أو تصعد عليها كمنصة أو سلم، ولا تستخدمها مطلقاً لهذه الأغراض.');
add(456,'Before use, check that all electrical cables are properly connected and undamaged.','Перед использованием проверьте правильность подключения и целостность всех электрических кабелей.','قبل الاستخدام، تحقق من توصيل جميع الكابلات الكهربائية بشكل صحيح وسلامتها.');
add(457,'Before use, check the surroundings and ensure there are no obstructions above or below the table.','Перед использованием проверьте пространство вокруг стола и отсутствие препятствий над ним и под ним.','قبل الاستخدام، افحص المكان وتأكد من عدم وجود عوائق فوق الطاولة أو تحتها.');
add(458,'This product is unsuitable for unsupervised use by children under 9. Adult supervision is required when children use it.','Изделие не предназначено для самостоятельного использования детьми младше 9 лет. При использовании детьми необходим присмотр взрослых.','هذا المنتج غير مناسب للاستخدام الفردي للأطفال دون 9 سنوات. يلزم إشراف شخص بالغ عند استخدام الأطفال له.');
add(459,'Check all electrical components and cables before use. Do not use the product if any fault or damage is present.','Перед использованием проверьте все электрические компоненты и кабели. При неисправности или повреждении не используйте изделие.','افحص جميع الأجزاء الكهربائية والكابلات قبل الاستخدام. لا تستخدم المنتج في حال وجود أي عطل أو تلف.');
add(460,'Use the product stationary on a level floor. Do not use it if the feet do not fully contact the floor or the product moves. To relocate it, unplug all cables from the mains and carry it with at least 2 people.','Используйте изделие неподвижно на ровном полу. Не используйте его, если ножки не полностью стоят на полу или изделие качается. Перед перемещением отключите все кабели от розетки; переносить должны не менее 2 человек.','يجب استخدام المنتج ثابتاً على أرض مستوية. لا تستخدمه إذا لم تلامس الأرجل الأرض بالكامل أو كان المنتج يتحرك. وعند نقله، افصل جميع الكابلات من المقبس واحمله بمساعدة شخصين على الأقل.');
add(461,'Slight vibration when the table starts moving up or down is normal and does not adversely affect its service life.','Небольшая вибрация в начале подъёма или опускания стола нормальна и не сокращает срок его службы.','الاهتزاز الخفيف عند بدء ارتفاع الطاولة أو انخفاضها طبيعي ولا يؤثر سلباً في عمر استخدامها.');
add(462,'Soft woven fabric adds an elegant appearance.','Мягкая ткань придаёт элегантный вид.','يسهم القماش المنسوج الناعم في المظهر الأنيق.');
add(463,'An elegant dark mink (dark beige) shade suits any décor.','Элегантный тёмный оттенок норки (тёмно-бежевый) сочетается с любым интерьером.','يناسب لون المنك الداكن الأنيق (البيج الداكن) مختلف أنماط الديكور.');
add(464,'Button detailing on the back and seat cushions adds a sophisticated touch.','Пуговичная отделка подушек спинки и сиденья придаёт утончённость.','تضفي تفاصيل الأزرار على وسادتي الظهر والمقعد لمسة راقية.');
add(465,'The Button desk chair combines comfort and style in a modern design. Designed to improve both the ergonomics and appearance of offices and workspaces, it offers features that make long working sessions more comfortable. It aims to provide comfort in everyday use and during busy workdays, adding elegance to modern offices and home workspaces.','Рабочее кресло Button сочетает комфорт и стиль в современном дизайне. Оно улучшает эргономику и внешний вид офиса или рабочего места и предлагает функции для комфорта при длительной работе. Кресло предназначено для удобства как в повседневном использовании, так и при интенсивной работе и придаёт элегантность современным офисам и домашним рабочим зонам.','يجمع كرسي المكتب Button بين الراحة والأناقة في تصميم عصري. صُمم لتحسين راحة الجلوس والمظهر في المكاتب ومساحات العمل، ويقدم مزايا تجعل فترات العمل الطويلة أكثر راحة. ويهدف إلى توفير الراحة في الاستخدام اليومي وأيام العمل المكثفة، مع إضافة الأناقة للمكاتب العصرية ومساحات العمل المنزلية.');
add(466,'Soft faux-leather upholstery on the seat and back adds an elegant appearance.','Мягкая обивка сиденья и спинки из искусственной кожи придаёт элегантный вид.','تضفي كسوة الجلد الصناعي الناعمة على المقعد والظهر مظهراً أنيقاً.');
add(467,'An elegant mustard (brown) shade suits any décor.','Элегантный горчичный (коричневый) оттенок сочетается с любым интерьером.','يناسب اللون الخردلي الأنيق (البني) مختلف أنماط الديكور.');
add(468,'A classic black shade suits any décor.','Классический чёрный цвет сочетается с любым интерьером.','يناسب اللون الأسود التقليدي مختلف أنماط الديكور.');
add(469,'An elegant mink–beige shade suits any décor.','Элегантный оттенок норки — бежевый — сочетается с любым интерьером.','يناسب لون المنك–البيج الأنيق مختلف أنماط الديكور.');
add(470,'Button detailing on the backrest adds a sophisticated touch.','Пуговичная отделка спинки придаёт утончённость.','تضفي تفاصيل الأزرار على الظهر لمسة راقية.');
add(471,'The Button desk chair combines comfort and style in a modern design. Designed to improve both the ergonomics and appearance of offices and workspaces, it offers features that make long working sessions more comfortable. It aims to provide comfort in everyday use and during busy workdays, adding elegance to modern offices and home workspaces.','Рабочее кресло Button сочетает комфорт и стиль в современном дизайне. Оно улучшает эргономику и внешний вид офиса или рабочего места и предлагает функции для комфорта при длительной работе. Кресло предназначено для удобства как в повседневном использовании, так и при интенсивной работе и придаёт элегантность современным офисам и домашним рабочим зонам.','يجمع كرسي المكتب Button بين الراحة والأناقة في تصميم عصري. صُمم لتحسين راحة الجلوس والمظهر في المكاتب ومساحات العمل، ويقدم مزايا تجعل فترات العمل الطويلة أكثر راحة. ويهدف إلى توفير الراحة في الاستخدام اليومي وأيام العمل المكثفة، مع إضافة الأناقة للمكاتب العصرية ومساحات العمل المنزلية.');
add(472,'Compatible with Oryana GRD-1740-DD-3 / GRD-1740-OO-3 and GRD-1722-DD-2 / GRD-1722-OO-2 models','Совместимо с моделями Oryana GRD-1740-DD-3 / GRD-1740-OO-3 и GRD-1722-DD-2 / GRD-1722-OO-2','متوافق مع طرازات Oryana GRD-1740-DD-3 / GRD-1740-OO-3 وGRD-1722-DD-2 / GRD-1722-OO-2');
add(473,'Double-bed frame','Каркас двуспальной кровати','إطار سرير مزدوج');
add(474,'Storage space underneath','Место хранения снизу','مساحة تخزين في الأسفل');
add(475,'Its C-shaped structure slides easily under a sofa, armchair or bed.','С-образная конструкция легко задвигается под диван, кресло или кровать.','يسهل إدخال هيكله على شكل C تحت الأريكة أو الكرسي أو السرير.');
add(476,'Easy to move and use in different parts of the home.','Легко переносить и использовать в разных частях дома.','يسهل نقله واستخدامه في أماكن مختلفة من المنزل.');
add(477,'Plastic supports on the feet prevent floor scratches and slipping.','Пластиковые накладки на ножках предотвращают царапины на полу и скольжение.','تمنع الدعامات البلاستيكية بالأرجل خدش الأرضية والانزلاق.');
add(478,'The top is high-quality melamine-faced particleboard resistant to scratches and stains.','Столешница изготовлена из качественной ДСП с меламиновым покрытием, устойчивым к царапинам и пятнам.','السطح العلوي من خشب حبيبي عالي الجودة مكسو بالميلامين ومقاوم للخدوش والبقع.');
add(479,'The powder-coated metal surface resists rust and wear.','Металлическая поверхность с порошковым покрытием устойчива к ржавчине и износу.','يقاوم السطح المعدني المطلي بالبودرة الصدأ والتآكل.');
add(480,'Assembly by 2 people is recommended for safer, trouble-free installation.','Для безопасной сборки без затруднений рекомендуется участие 2 человек.','يوصى بالتركيب بواسطة شخصين لضمان تركيب أكثر أماناً وسهولة.');
add(481,'Designed for long-lasting use.','Рассчитано на длительное использование.','مصمم لاستخدام طويل الأمد.');
add(482,'Castors make it easy to move and use in different areas, allowing stable positioning.','Ролики облегчают перемещение и использование в разных местах, позволяя устойчиво установить изделие.','تسهل العجلات نقله واستخدامه في أماكن مختلفة مع إتاحة وضعه بثبات.');
add(483,'The spacious upper drawer stores files, stationery or personal belongings neatly.','Вместительный верхний ящик позволяет аккуратно хранить документы, канцелярию и личные вещи.','يتيح الدرج العلوي الواسع تخزين الملفات والقرطاسية والمقتنيات الشخصية بانتظام.');
add(484,'The lower shelf provides extra storage for books, folders or other large items.','Нижняя полка обеспечивает дополнительное место для книг, папок и других крупных предметов.','يوفر الرف السفلي مساحة تخزين إضافية للكتب والمجلدات والأغراض الكبيرة الأخرى.');
add(485,'Compact dimensions suit even small spaces. Place it under a desk or use it as a standalone side table.','Компактные размеры подходят даже для небольших помещений. Можно поставить под стол или использовать как отдельный приставной столик.','تناسب أبعاده الصغيرة حتى المساحات الضيقة. يمكن وضعه تحت المكتب أو استخدامه كطاولة جانبية مستقلة.');
add(486,'The body and drawer are made from durable melamine-faced particleboard and metal.','Корпус и ящик изготовлены из прочной ДСП с меламиновым покрытием и металла.','الهيكل والدرج مصنوعان من خشب حبيبي متين مكسو بالميلامين ومن المعدن.');
add(487,'The desktop has a two-piece raised shelf.','На столешнице предусмотрена надставная полка из двух частей.','يوجد على سطح المكتب رف مرتفع مكون من قطعتين.');
add(488,'The shelves can be fitted separately on the right and left, or joined in the centre of the desk.','Полки можно установить отдельно справа и слева либо соединить в центре стола.','يمكن تركيب الرفين منفصلين يمين المكتب ويساره، أو جمعهما في الوسط.');
add(489,'RGB lighting at the side corners of the desktop.','RGB-подсветка на боковых углах столешницы.','إضاءة RGB عند الزوايا الجانبية لسطح المكتب.');
add(490,'The front of the desktop has a slot for a tablet, phone and similar devices.','В передней части столешницы предусмотрен держатель для планшета, телефона и подобных устройств.','يحتوي الجزء الأمامي من سطح المكتب على موضع لوضع جهاز لوحي أو هاتف وما شابه.');
add(491,'USB-C and standard USB charging ports.','Зарядные порты USB-C и стандартный USB.','منافذ شحن USB-C وUSB قياسي.');
add(492,'Under-desk cable organiser compartment','Отделение для кабелей под столом','حجرة تنظيم الكابلات أسفل المكتب');
add(493,'Adjustable levelling feet','Регулируемые опоры для выравнивания','قواعد أرجل قابلة للتعديل للاستواء');
add(494,'Headphone and cup holder','Держатели для наушников и стакана','حامل للسماعات والكوب');
add(495,'Large mouse pad','Большой коврик для мыши','لوحة فأرة كبيرة');
add(496,'Compact design','Компактная конструкция','تصميم مدمج');
add(497,'A stylish complementary look for modern living spaces','Стильное дополнение современного жилого пространства','مظهر أنيق مكمل للمساحات المعيشية العصرية');
add(498,'Wipe with a damp cloth. No detergent is required. Avoid prolonged contact with water or heat.','Протирайте влажной тканью. Моющие средства не требуются. Избегайте длительного контакта с водой и теплом.','يُنظف بقطعة قماش رطبة دون الحاجة إلى منظف. تجنب التعرض المطول للماء والحرارة.');
add(499,'1 internal drawer','1 внутренний ящик','درج داخلي واحد');
add(500,'Soft-close hinges','Петли с доводчиками','مفصلات بإغلاق هادئ');
add(501,'Head support: An adjustable head cushion fully supports the neck for comfort during prolonged sitting.','Поддержка головы: регулируемая подушка полностью поддерживает шею для комфорта при длительном сидении.','دعم الرأس: تدعم وسادة الرأس القابلة للتعديل الرقبة بالكامل لتوفير الراحة أثناء الجلوس الطويل.');
add(502,'Lumbar support: Responds to your body weight to support spinal health and natural posture.','Поясничная опора: реагирует на вес тела, поддерживая здоровье позвоночника и естественную осанку.','دعم قطني: يستجيب لوزن الجسم لدعم صحة العمود الفقري والوضعية الطبيعية.');
add(503,'Adjustable armrests: Soft padding and height adjustment keep your arms in an ideal position.','Регулируемые подлокотники: мягкая обивка и регулировка высоты обеспечивают удобное положение рук.','مساند ذراعين قابلة للتعديل: يحافظ الحشو الناعم وضبط الارتفاع على وضع الذراعين المثالي.');
add(504,'Mesh backrest: High-quality mesh helps prevent sweating and keeps seating cool during extended use.','Сетчатая спинка: качественная сетка помогает предотвратить потение и сохраняет прохладу при длительном использовании.','مسند ظهر شبكي: تساعد الشبكة عالية الجودة على منع التعرق والحفاظ على الانتعاش أثناء الاستخدام الطويل.');
add(505,'Soft foam seat: The quality seat cushion resists sagging and lasts well.','Мягкое сиденье из пеноматериала: качественная подушка не проседает и служит долго.','مقعد إسفنجي ناعم: تقاوم وسادة المقعد عالية الجودة الهبوط وتدوم طويلاً.');
add(506,'Gaming and office chair: Suitable for long office work sessions and comfortable gaming.','Игровое и рабочее кресло: подходит для длительной офисной работы и комфортной игры.','كرسي ألعاب وعمل: مناسب للعمل المكتبي لساعات طويلة وللعب براحة عالية.');
add(507,'Stylish design: Modern minimalist lines suit offices and home gaming rooms alike.','Стильный дизайн: современные минималистичные линии подходят и для офиса, и для домашней игровой комнаты.','تصميم أنيق: تلائم الخطوط العصرية البسيطة المكاتب وغرف الألعاب المنزلية.');
add(508,'Height adjustment: A durable gas lift and mechanism adjust the seat easily to the desk height and the user’s height.','Регулировка высоты: прочный газлифт и механизм позволяют легко подстроить кресло под высоту стола и рост пользователя.','ضبط الارتفاع: يتيح المكبس الغازي والآلية المتينان ضبط ارتفاع الكرسي بسهولة وفق ارتفاع المكتب وطول المستخدم.');
add(509,'Chair angle: The reclining function offers different sitting positions for work or rest.','Угол кресла: откидывание обеспечивает разные положения для работы и отдыха.','زاوية الكرسي: تتيح وظيفة الإمالة للخلف أوضاع جلوس مختلفة للعمل أو الاستراحة.');
add(510,'Tilt mechanism: Adjust the tilt to suit your seating position.','Механизм наклона: настройте наклон в соответствии с положением сидения.','آلية الإمالة: اضبط ميل الكرسي وفق وضعية جلوسك.');
add(511,'360-degree swivel: Freedom of movement helps productivity.','Поворот на 360 градусов: свобода движения повышает продуктивность.','دوران 360 درجة: حرية الحركة تساعد على زيادة الإنتاجية.');
add(512,'Durable castors: Quiet, smooth-running castors and a sturdy detachable metal star base provide reliable use for years.','Прочные ролики: тихие ролики с плавным ходом и прочная разборная металлическая крестовина обеспечивают надёжность на многие годы.','عجلات متينة: توفر العجلات الهادئة والسلسة والقاعدة النجمية المعدنية المتينة القابلة للفك استخداماً موثوقاً لسنوات.');
add(513,'Integrated RGB LED strips in the chair’s side panels offer multiple lighting modes, adjustable colour transitions and effects.','В боковые панели кресла встроены RGB-светодиодные ленты с различными режимами, настраиваемыми цветовыми переходами и эффектами.','تحتوي الألواح الجانبية للكرسي على شرائط LED RGB مدمجة مع أوضاع إضاءة متعددة وانتقالات ألوان وتأثيرات قابلة للضبط.');
add(514,'Control the lighting easily with the remote to create an atmosphere matching your gaming style.','Пульт позволяет легко управлять подсветкой и создавать атмосферу под свой игровой стиль.','يمكن التحكم بالإضاءة بسهولة عبر جهاز التحكم عن بُعد لخلق أجواء تناسب أسلوب اللعب.');
add(515,'Connects to power through USB and saves energy.','Подключается к источнику питания через USB и экономит энергию.','يتصل بمصدر الطاقة عبر USB ويوفر الطاقة.');
add(516,'High-density foam filling supports your body for lasting comfort.','Наполнитель из пеноматериала высокой плотности поддерживает тело для длительного комфорта.','يدعم حشو الإسفنج عالي الكثافة الجسم لراحة تدوم طويلاً.');
add(517,'High back support with removable lumbar and neck cushions.','Высокая спинка со съёмными подушками для поясницы и шеи.','دعم ظهر مرتفع مع وسادتي أسفل ظهر ورقبة قابلتين للإزالة.');
add(518,'2D-adjustable angled armrests.','Наклонные подлокотники с регулировкой 2D.','مساند ذراعين مائلة قابلة للتعديل 2D.');
add(519,'Strong gas lift adjusts the seat to your preferred height.','Прочный газлифт регулирует сиденье на нужную высоту.','مكبس غازي قوي لضبط المقعد على الارتفاع المطلوب.');
add(520,'Backrest reclines from 90–135°.','Спинка откидывается на 90–135°.','يميل مسند الظهر من 90 إلى 135 درجة.');
add(521,'360° swivel metal base with quiet castors that leave no marks on parquet, carpets and similar surfaces.','Металлическая опора с поворотом на 360° и тихими роликами, не оставляющими следов на паркете, коврах и подобных поверхностях.','قاعدة معدنية تدور 360 درجة مع عجلات هادئة لا تترك علامات على الباركيه والسجاد والأسطح المشابهة.');
add(522,'Ergonomic design:','Эргономичный дизайн:','تصميم مريح:');
add(523,'The chair adapts to the body to support spinal health. Its high back support helps keep your back in a natural posture.','Кресло подстраивается под телосложение и поддерживает здоровье позвоночника. Высокая спинка помогает сохранять естественное положение спины.','يتكيف الكرسي مع بنية الجسم لدعم صحة العمود الفقري. ويساعد مسند الظهر المرتفع على إبقاء الظهر بوضعه الطبيعي.');
add(524,'Lumbar support provides extra lower-back support and helps maintain a correct sitting posture.','Поясничная опора дополнительно поддерживает поясницу и помогает сохранять правильное положение сидя.','يوفر الدعم القطني دعماً إضافياً لأسفل الظهر ويساعد على الحفاظ على وضعية جلوس صحيحة.');
add(525,'Adjustable headrest:','Регулируемый подголовник:','مسند رأس قابل للتعديل:');
add(526,'An adjustable headrest helps relax the neck and shoulders during long working sessions.','Регулируемый подголовник помогает расслабить шею и плечи при длительной работе.','يساعد مسند الرأس القابل للتعديل على إراحة الرقبة والكتفين أثناء العمل الطويل.');
add(527,'This feature allows easy adaptation to each user.','Эта функция позволяет легко настроить кресло под каждого пользователя.','تتيح هذه الميزة تكييف الكرسي بسهولة مع كل مستخدم.');
add(528,'Arm support and adjustable armrests:','Опора для рук и регулируемые подлокотники:','دعم الذراعين ومساند قابلة للتعديل:');
add(529,'Armrest tops are covered with soft PU material for comfortable arm support.','Мягкое ПУ-покрытие подлокотников обеспечивает комфортную опору для рук.','تُغطى أسطح مساند الذراعين بمادة PU ناعمة لدعم الذراعين براحة.');
add(530,'Adjusts to different heights and positions to reduce pressure on wrists and elbows.','Регулировка высоты и положения уменьшает давление на запястья и локти.','يتيح التعديل إلى ارتفاعات وأوضاع مختلفة تخفيف الضغط على المعصمين والمرفقين.');
add(531,'Breathable mesh back:','Дышащая сетчатая спинка:','ظهر شبكي يسمح بمرور الهواء:');
add(532,'The mesh back allows air circulation, reduces sweating and adds comfort during prolonged sitting.','Сетчатая спинка обеспечивает циркуляцию воздуха, уменьшает потение и повышает комфорт при длительном сидении.','يسمح الظهر الشبكي بدوران الهواء ويقلل التعرق ويوفر الراحة أثناء الجلوس الطويل.');
add(533,'Combines durability and an elegant appearance for a modern office aesthetic.','Прочность и стильный вид придают офису современную эстетику.','يجمع بين المتانة والمظهر الأنيق لإضفاء طابع عصري على المكتب.');
add(534,'Quality materials and durability:','Качественные материалы и долговечность:','مواد عالية الجودة ومتانة:');
add(535,'Strong construction and quality materials provide long-lasting use.','Прочная конструкция и качественные материалы обеспечивают долгий срок службы.','توفر البنية المتينة والمواد عالية الجودة استخداماً طويل الأمد.');
add(536,'Metal star legs provide mobility and make moving around the office easy.','Металлическая крестовина обеспечивает мобильность и облегчает перемещение по офису.','توفر القاعدة النجمية المعدنية سهولة الحركة والتنقل داخل المكتب.');
add(537,'Wide, soft seat with specially moulded foam:','Широкое мягкое сиденье из специально формованного пеноматериала:','مقعد واسع وناعم بإسفنج مصبوب خصيصاً:');
add(538,'The seat cushion is made from specially moulded foam, helping it retain its shape and provide lasting comfort.','Подушка сиденья изготовлена из специально формованного пеноматериала, который долго сохраняет форму и обеспечивает комфорт.','وسادة المقعد مصنوعة من إسفنج مصبوب خصيصاً، مما يساعدها على الاحتفاظ بشكلها وتوفير الراحة لفترة طويلة.');
add(539,'The seat cushion slides forwards and backwards to adjust the seating area to the user.','Подушка сиденья перемещается вперёд и назад для настройки посадки под пользователя.','تنزلق وسادة المقعد إلى الأمام والخلف لضبط مساحة الجلوس وفق المستخدم.');
add(540,'The soft cushioned seat provides comfort and supports a correct sitting posture.','Мягкое сиденье обеспечивает комфорт и поддерживает правильную посадку.','يوفر المقعد المبطن الناعم الراحة ويدعم وضعية الجلوس الصحيحة.');
add(541,'New-generation cable-controlled seat mechanism:','Механизм сиденья нового поколения с тросовым управлением:','آلية مقعد من الجيل الجديد بتحكم سلكي:');
add(542,'The new-generation cable-controlled mechanism easily adjusts the chair to the desired height and seat angle.','Механизм нового поколения с тросовым управлением позволяет легко настроить нужную высоту и угол сиденья.','تتيح الآلية ذات التحكم السلكي من الجيل الجديد ضبط الكرسي بسهولة على الارتفاع وزاوية الجلوس المطلوبين.');
add(543,'Adjust the body-weight-sensitive backrest tension and lock the backrest at your preferred angle.','Отрегулируйте сопротивление спинки с учётом веса тела и зафиксируйте её под нужным углом.','اضبط مقاومة إمالة الظهر المتجاوبة مع وزن الجسم وثبّت المسند بالزاوية المطلوبة.');
add(544,'Slide the seat cushion forwards or backwards to suit your leg length.','Сдвигайте подушку сиденья вперёд и назад в соответствии с длиной ног.','حرّك وسادة المقعد للأمام والخلف بما يناسب طول الساقين.');
add(545,'Lock the seat height at the level most comfortable for you.','Зафиксируйте высоту сиденья на наиболее удобном уровне.','ثبّت ارتفاع المقعد على المستوى الأنسب لك.');
add(320,'White / Anthracite','Белый / антрацит','أبيض / أنثراسيت');
add(321,'Desk worktop in a contrasting colour','Рабочая поверхность стола контрастного цвета','سطح عمل المكتب بلون متباين');
add(322,'Practical open shelving system','Практичная система открытых полок','نظام رفوف مفتوحة عملي');
add(323,'Y-19 Butterfly mechanism','Механизм Y-19 Butterfly','آلية Y-19 Butterfly');
add(324,'4D-adjustable armrests','Подлокотники с регулировкой 4D','مساند ذراعين قابلة للتعديل بتقنية 4D');
add(325,'Moulded-foam seat cushion','Подушка сиденья из формованного пеноматериала','وسادة مقعد من إسفنج مصبوب');
add(326,'Metal star base','Металлическая крестовина','قاعدة نجمية معدنية');
add(327,'Nylon + PU castors','Ролики из нейлона и ПУ','عجلات من النايلون والبولي يوريثان PU');
add(328,'This gaming/office chair combines modern design and advanced ergonomics with comfort and support during prolonged use. Designed for gamers, office staff and home workers, it features high-quality materials and a new generation of adjustable mechanisms.','Это игровое/офисное кресло сочетает современный дизайн и продуманную эргономику с комфортом и поддержкой при длительном использовании. Оно предназначено для игроков, офисных сотрудников и работы дома и отличается качественными материалами и регулируемыми механизмами нового поколения.','يجمع كرسي الألعاب والمكتب هذا بين التصميم الحديث وبيئة الجلوس المريحة مع توفير الراحة والدعم للاستخدام الطويل. وهو مناسب للاعبين وموظفي المكاتب والعاملين من المنزل، ويتميز بمواد عالية الجودة وآليات قابلة للتعديل من الجيل الجديد.');
add(329,'Advanced ergonomics:','Продуманная эргономика:','راحة جلوس متقدمة:');
add(330,'Spinal support: The specially designed backrest supports the spine in its natural posture to help reduce back pain.','Поддержка позвоночника: специальная спинка поддерживает естественное положение позвоночника и помогает уменьшить боль в спине.','دعم العمود الفقري: يدعم مسند الظهر المصمم خصيصاً العمود الفقري في وضعيته الطبيعية للمساعدة على تخفيف ألم الظهر.');
add(331,'Adjustable lumbar support: Keeps the lower back correctly positioned for comfort over long hours.','Регулируемая поясничная опора: поддерживает правильное положение поясницы для комфорта в течение многих часов.','دعم قطني قابل للتعديل: يحافظ على الوضع الصحيح لأسفل الظهر لراحة تدوم ساعات طويلة.');
add(332,'Head and neck support:','Поддержка головы и шеи:','دعم الرأس والرقبة:');
add(333,'Adjustable headrest: Its height and angle adjust to support the neck comfortably in the correct position.','Регулируемый подголовник: высота и угол наклона регулируются для удобной поддержки шеи в правильном положении.','مسند رأس قابل للتعديل: يمكن تعديل الارتفاع والزاوية لدعم الرقبة براحة في الوضع الصحيح.');
add(334,'Breathable fabric:','Дышащая ткань:','قماش يسمح بمرور الهواء:');
add(335,'Mesh backrest: High-quality mesh allows airflow and helps prevent sweating, keeping you cool during extended sitting.','Сетчатая спинка: качественная сетка обеспечивает циркуляцию воздуха и помогает предотвратить потение при длительном сидении.','مسند ظهر شبكي: تسمح الشبكة عالية الجودة بتدفق الهواء وتساعد على منع التعرق والحفاظ على الانتعاش أثناء الجلوس الطويل.');
add(336,'Multidirectional armrests:','Подлокотники с многосторонней регулировкой:','مساند ذراعين متعددة الاتجاهات:');
add(337,'3D-adjustable armrests: Height, forward/backward, side-to-side and rotational adjustments position the arms and shoulders correctly.','Подлокотники с регулировкой 3D: регулировка высоты, вперёд-назад, вправо-влево и угла поворота обеспечивает правильное положение рук и плеч.','مساند ذراعين قابلة للتعديل 3D: يمكن تعديل الارتفاع والتحريك للأمام والخلف ولليمين واليسار وزاوية الدوران لوضع الذراعين والكتفين بشكل صحيح.');
add(338,'Comfortable seat:','Удобное сиденье:','مقعد مريح:');
add(339,'High-density foam: Quality dense foam resists sagging during prolonged sitting and provides lasting comfort.','Пеноматериал высокой плотности: качественный плотный наполнитель не проседает при длительном сидении и обеспечивает постоянный комфорт.','إسفنج عالي الكثافة: يقاوم الإسفنج الكثيف عالي الجودة الهبوط أثناء الجلوس الطويل ويوفر راحة مستمرة.');
add(340,'Durable, high-quality fabric upholstery provides superior comfort.','Прочная качественная тканевая обивка обеспечивает высокий уровень комфорта.','توفر الكسوة القماشية المتينة عالية الجودة مستوى عالياً من الراحة.');
add(341,'Tilt and recline function:','Наклон и откидывание:','وظيفة الإمالة والاستلقاء:');
add(342,'New-generation synchronised tilt mechanism: The backrest and seat move together and lock at different tilt angles for comfortable relaxation.','Синхронный механизм наклона нового поколения: спинка и сиденье движутся согласованно и фиксируются под разными углами для удобного отдыха.','آلية إمالة متزامنة من الجيل الجديد: يتحرك مسند الظهر والمقعد معاً ويمكن تثبيتهما بزوايا مختلفة للاستراحة براحة.');
add(343,'120-degree recline: The chair reclines up to 120 degrees, ideal for short naps or rest.','Наклон на 120 градусов: кресло откидывается до 120 градусов для короткого сна или отдыха.','استلقاء حتى 120 درجة: يميل الكرسي حتى 120 درجة، وهو مناسب للقيلولة القصيرة أو الاستراحة.');
add(344,'The back section has 2 V-shaped arm supports for leaning back and resting your arms, offering a distinctive seating experience.','В спинке предусмотрены 2 V-образные опоры для рук, позволяющие откинуться и расслабить руки для особого комфорта.','يحتوي قسم الظهر على مسندي ذراعين على شكل V عدد 2، يتيحان الاتكاء وإراحة الذراعين لتجربة جلوس مميزة.');
add(345,'Durable castors and metal base:','Прочные ролики и металлическая опора:','عجلات متينة وقاعدة معدنية:');
add(346,'Quiet, smooth castors: High-quality large castors move quietly and smoothly without damaging the floor.','Тихие ролики с плавным ходом: качественные крупные ролики двигаются тихо и плавно, не повреждая пол.','عجلات هادئة وسلسة: تتحرك العجلات الكبيرة عالية الجودة بهدوء وسلاسة دون إتلاف الأرضية.');
add(347,'Strong specially designed base: Durable moulded plastic and a special paint finish add style and longevity. The 45-degree slope at the tips ergonomically supports and rests your feet.','Прочная опора особой конструкции: долговечный формованный пластик со специальным лакокрасочным покрытием придаёт креслу стильный вид. Наклон концов на 45 градусов обеспечивает эргономичную опору и отдых для ног.','قاعدة متينة بتصميم خاص: يضفي البلاستيك المصبوب المتين والطلاء الخاص مظهراً أنيقاً وعمر استخدام طويل. وتوفر النهايات المائلة بزاوية 45 درجة دعماً مريحاً للقدمين وإراحتهما.');
add(348,'Office use: Provides comfort even on busy workdays, helping concentration and productivity.','Для офиса: обеспечивает комфорт даже в напряжённые рабочие дни, помогая сосредоточиться и работать продуктивнее.','للمكتب: يوفر الراحة حتى في أيام العمل المكثفة ويساعد على التركيز والإنتاجية.');
add(349,'Gaming use: Provides optimal comfort and support during long gaming sessions, helping performance.','Для игр: обеспечивает оптимальный комфорт и поддержку во время длительных игровых сеансов, способствуя результативности.','للألعاب: يوفر الراحة والدعم أثناء جلسات اللعب الطويلة ويساعد على تحسين الأداء.');
add(350,'Home use: A convenient companion for working, relaxing or entertainment at home.','Для дома: удобно для работы, отдыха и развлечений дома.','للمنزل: مناسب للعمل والاسترخاء والأنشطة الترفيهية في المنزل.');
add(351,'Why choose this chair?','Почему стоит выбрать это кресло?','لماذا تختار هذا الكرسي؟');
add(352,'New-generation ergonomic design: Its distinctive seat and backrest mechanism supports health and comfort during prolonged use.','Эргономика нового поколения: особый механизм сиденья и спинки поддерживает здоровье и комфорт при длительном использовании.','تصميم مريح من الجيل الجديد: تدعم آلية المقعد ومسند الظهر المميزة الصحة والراحة أثناء الاستخدام الطويل.');
add(353,'High-quality materials: Durable and designed for long-lasting use.','Качественные материалы: прочность и длительный срок службы.','مواد عالية الجودة: متينة ومصممة لاستخدام طويل الأمد.');
add(354,'Multidirectional adjustable mechanism: Adjust to your personal needs and body shape.','Многосторонняя регулировка: настройка под индивидуальные потребности и телосложение.','آلية متعددة الاتجاهات قابلة للتعديل: اضبطها وفق احتياجاتك وبنية جسمك.');
add(355,'Stylish modern appearance: Adds elegance to any office or home.','Современный стильный вид: украшает любой офис или дом.','مظهر عصري أنيق: يضفي الأناقة على أي مكتب أو منزل.');
add(356,'First and exclusive in Türkiye, only at Adore Mobilya.','Впервые и эксклюзивно в Турции, только в Adore Mobilya.','لأول مرة وحصرياً في تركيا، لدى Adore Mobilya فقط.');
add(357,'Adore Mobilya — TGIF main distributor in Türkiye','Adore Mobilya — основной дистрибьютор TGIF в Турции','Adore Mobilya — الموزع الرئيسي لـ TGIF في تركيا');
add(358,'TGIF – The Game Is Forever — New-generation ergonomic gaming and office chair','TGIF – The Game Is Forever — эргономичное игровое и офисное кресло нового поколения','TGIF – The Game Is Forever — كرسي ألعاب ومكتب مريح من الجيل الجديد');
add(359,'First and exclusive in Türkiye','Впервые и эксклюзивно в Турции','لأول مرة وحصرياً في تركيا');
add(360,'The Handy Mate Bella wooden coat stand suits any space with its modern, elegant design. Its durable construction helps organise homes and offices, while its natural wood appearance adds warmth. Its width, height and depth provide space for clothes and bags. Non-slip hanging sections help prevent items from falling, and its lightweight construction takes up little space. The clean lines and simplicity of white complement minimalist interiors and give furniture a contemporary appearance. Combined with natural-looking wood, it creates a warm, welcoming atmosphere.','Деревянная вешалка Handy Mate Bella с современным изящным дизайном подходит для любого помещения. Прочная конструкция помогает поддерживать порядок дома и в офисе, а естественный вид дерева добавляет тепла. Размеры подходят для одежды и сумок. Нескользящие элементы удерживают вещи, а лёгкая конструкция занимает мало места. Простота белого цвета и чистые линии дополняют минималистичный интерьер и придают мебели современный вид. В сочетании с натуральной текстурой дерева создаётся тёплая уютная атмосфера.','تتناسب شماعة الملابس الخشبية Handy Mate Bella مع مختلف المساحات بتصميمها العصري الأنيق. تساعد بنيتها المتينة على تنظيم المنزل والمكتب، ويضيف مظهر الخشب الطبيعي لمسة دافئة. وتوفر أبعادها مكاناً للملابس والحقائب. تساعد أجزاء التعليق المانعة للانزلاق على منع سقوط الأغراض، كما أن بنيتها الخفيفة لا تشغل مساحة كبيرة. وتنسجم بساطة اللون الأبيض وخطوطه النظيفة مع الأسلوب البسيط وتضفي مظهراً معاصراً على الأثاث. وعند دمجه مع الخشب ذي المظهر الطبيعي يخلق أجواء دافئة ومرحبة.');
add(361,'Wide, attractive floor-safe feet','Широкие аккуратные опоры, не повреждающие пол','قواعد عريضة أنيقة لا تضر بالأرضية');
add(362,'Tall multipurpose cabinet with doors','Высокий многофункциональный шкаф с дверцами','خزانة متعددة الاستخدامات بتصميم رأسي وأبواب');
add(363,'Adjustable shelves for a customisable cabinet interior','Регулируемые полки для индивидуальной организации шкафа','رفوف قابلة للتعديل لتنظيم داخل الخزانة وفق احتياجاتك');
add(364,'Functional extendable kitchen table','Функциональный раздвижной кухонный стол','طاولة مطبخ عملية قابلة للتمديد');
add(365,'Extends into a dining table for 4–6 people','Раскладывается в обеденный стол на 4–6 человек','تتحول عند تمديدها إلى طاولة طعام لـ 4–6 أشخاص');
add(366,'Compatible mattress size: 90 cm × 190 cm','Подходящий размер матраса: 90 см × 190 см','مقاس المرتبة المتوافق: 90 سم × 190 سم');
add(367,'Cup holders in the armrests','Подстаканники в подлокотниках','حاملات أكواب في مساند الذراعين');
add(368,'Tool-free assembly by one person','Сборка одним человеком без инструментов','تركيب دون أدوات بواسطة شخص واحد');
add(369,'Specially designed desk chair made with high-quality teddy fabric','Рабочий стул особой конструкции с качественной тканью «тедди»','كرسي مكتب بتصميم خاص وقماش تيدي عالي الجودة');
add(370,'Teddy-fabric-covered armrests','Подлокотники с обивкой из ткани «тедди»','مساند ذراعين مكسوة بقماش تيدي');
add(371,'Adjustable seat height','Регулируемая высота сиденья','ارتفاع مقعد قابل للتعديل');
add(372,'Attractive, durable metal legs','Красивые прочные металлические ножки','أرجل معدنية أنيقة ومتينة');
add(373,'Soft teddy fabric upholstery. The lower frame and legs are durable metal with a powder-coated finish.','Мягкая обивка из ткани «тедди». Нижний каркас и ножки изготовлены из прочного металла с порошковым покрытием.','كسوة من قماش تيدي ناعم الملمس. الهيكل السفلي والأرجل من معدن متين مطلي بالبودرة.');
add(374,'Practical use with a dedicated enclosed compartment, shelf and drawer','Удобство использования благодаря отдельному закрытому отделению, полке и ящику','استخدام عملي بفضل حجرة خاصة بباب ورف ودرج');
add(375,'For bathrooms, kitchens, offices and similar spaces; castors make it easy to move','Для ванной, кухни, офиса и других помещений; ролики облегчают перемещение','للحمام والمطبخ والمكتب وما شابه؛ تسهل العجلات نقله');
add(376,'Fabric-upholstered headboard','Изголовье с тканевой обивкой','لوح رأس سرير مكسو بالقماش');
add(377,'Compatible mattress size: 160 × 200 cm','Подходящий размер матраса: 160 × 200 см','مقاس المرتبة المتوافق: 160 × 200 سم');
add(378,'Attractive floor-safe feet','Красивые опоры, не повреждающие пол','قواعد أنيقة لا تضر بالأرضية');
add(379,'Storage with 6 drawers for easy organisation','Место хранения с 6 ящиками для удобного порядка','مساحة تخزين تضم 6 أدراج لسهولة تنظيم الأغراض');
add(380,'Storage with 4 drawers for easy organisation','Место хранения с 4 ящиками для удобного порядка','مساحة تخزين تضم 4 أدراج لسهولة تنظيم الأغراض');
add(381,'Stylish modern design.','Стильный современный дизайн.','تصميم عصري أنيق.');
add(382,'Durable, long-lasting material.','Прочный долговечный материал.','مادة متينة وطويلة العمر.');
add(383,'Easy-clean matt surface.','Матовая поверхность, которую легко чистить.','سطح مطفي سهل التنظيف.');
add(384,'Ideal dimensions for small spaces.','Размеры, подходящие для небольших помещений.','أبعاد مثالية للمساحات الصغيرة.');
add(385,'Functional interior with 2 clothes rails','Функциональная внутренняя конструкция с 2 штангами для одежды','تنظيم داخلي عملي يضم قضيبين لتعليق الملابس');
add(386,'Functional interior with multiple shelves','Функциональная внутренняя конструкция с несколькими полками','تنظيم داخلي عملي يضم رفوفاً متعددة');
add(387,'Functional interior design','Функциональная внутренняя конструкция','تنظيم داخلي عملي');
add(388,'Stylish metal handles','Стильные металлические ручки','مقابض معدنية أنيقة');
add(389,'Sturdy black plastic feet','Прочные чёрные пластиковые ножки','أرجل بلاستيكية سوداء متينة');
add(390,'Headboard matching the bed frame','Изголовье в тон каркаса кровати','لوح رأس متناسق مع هيكل السرير');
add(391,'1 monitor shelf','1 полка для монитора','رف شاشة واحد');
add(392,'Suitable for both home and office use','Подходит для дома и офиса','مناسب للاستخدام المنزلي والمكتبي');
add(393,'Specially designed retro metal legs','Металлические ножки в стиле ретро особой конструкции','أرجل معدنية بتصميم ريترو خاص');
add(394,'Floor-safe feet','Опоры, не повреждающие пол','قواعد لا تضر بالأرضية');
add(395,'Modern combination of pink and white','Современное сочетание розового и белого','تناغم عصري بين الوردي والأبيض');
add(396,'2 desktop compartments','2 настольных отделения','حجرتان أعلى الطاولة');
add(397,'Spacious work area','Просторная рабочая поверхность','مساحة عمل واسعة');
add(398,'2 multipurpose compartments','2 многофункциональных отделения','حجرتان متعددتا الاستخدامات');
add(399,'Desktop cable duct','Кабель-канал на столешнице','مجرى كابلات على سطح المكتب');
add(400,'High-quality teddy fabric','Качественная ткань «тедди»','قماش تيدي عالي الجودة');
add(401,'Reclining backrest mechanism','Механизм откидывания спинки','آلية إمالة مسند الظهر للخلف');
add(402,'Specially designed tall retro legs','Высокие ножки в стиле ретро особой конструкции','أرجل ريترو مرتفعة بتصميم خاص');
add(403,'Suitable for both home and office use','Подходит для дома и офиса','مناسب للاستخدام المنزلي والمكتبي');
add(404,'Tall retro metal legs','Высокие металлические ножки в стиле ретро','أرجل معدنية مرتفعة بتصميم ريترو');
add(405,'Multipurpose table suitable for homes, offices, balconies and similar spaces','Многофункциональный стол для дома, офиса, балкона и других помещений','طاولة متعددة الاستخدامات مناسبة للمنزل والمكتب والشرفة والمساحات المشابهة');
add(406,'Practical drawer design for concealing everyday items','Практичный ящик для скрытого хранения повседневных вещей','درج عملي لإخفاء الأغراض اليومية');
add(407,'2 compartments','2 отделения','حجرتان');
add(408,'Storage with 2 doors to conceal everyday items','Место хранения с 2 дверцами для повседневных вещей','مساحة تخزين ببابين لإخفاء الأغراض اليومية');
add(409,'Stylish modern composite feet','Стильные современные композитные ножки','أرجل مركبة عصرية أنيقة');
add(410,'Made with first-class durable, wipe-clean chenille upholstery, a durable unfolding mechanism and springs.','Изготовлено с прочной шенилловой обивкой первого сорта, допускающей влажную очистку, долговечным механизмом раскладывания и пружинами.','مصنوع بكسوة شينيل متينة من الدرجة الأولى قابلة للمسح وآلية فتح متينة ونوابض.');
add(411,'Durable specially designed black steel frame with height and levelling adjustment','Прочный чёрный стальной каркас особой конструкции с регулировкой высоты и выравниванием','هيكل فولاذي أسود متين بتصميم خاص مع ضبط الارتفاع والاستواء');
add(412,'Large ergonomic mouse pad','Большой эргономичный коврик для мыши','لوحة فأرة واسعة ومريحة');
add(413,'C-type desktop cable duct and 2 USB charging ports','Кабель-канал типа C на столешнице и 2 зарядных USB-порта','مجرى كابلات على سطح المكتب من النوع C ومنفذا شحن USB');
add(414,'Table legs with height and levelling adjustments','Ножки стола с регулировкой высоты и выравниванием','أرجل طاولة مع ضبط الارتفاع والاستواء');
add(415,'A patented exclusive Adore Mobilya design','Запатентованный эксклюзивный дизайн Adore Mobilya','تصميم خاص حاصل على براءة اختراع من Adore Mobilya');
add(416,'Durable specially designed black steel frame with height and levelling adjustment','Прочный чёрный стальной каркас особой конструкции с регулировкой высоты и выравниванием','هيكل فولاذي أسود متين بتصميم خاص مع ضبط الارتفاع والاستواء');
add(417,'A patented exclusive Adore Mobilya design.','Запатентованный эксклюзивный дизайн Adore Mobilya.','تصميم خاص حاصل على براءة اختراع من Adore Mobilya.');
add(418,'C-type desktop cable duct and 2 USB charging ports','Кабель-канал типа C на столешнице и 2 зарядных USB-порта','مجرى كابلات على سطح المكتب من النوع C ومنفذا شحن USB');
add(419,'Combines practical functionality with visual appeal.','Сочетает практичность и привлекательный вид.','يجمع بين الوظائف العملية والمظهر الجذاب.');
add(420,'Ideal for organising magazines, newspapers and books','Подходит для хранения журналов, газет и книг','مثالي لتنظيم المجلات والصحف والكتب');
add(421,'Made with high-quality materials','Изготовлено из качественных материалов','مصنوع من مواد عالية الجودة');
add(422,'Fits easily even in small spaces','Легко размещается даже в небольших помещениях','يسهل وضعه حتى في المساحات الصغيرة');
add(423,'Keeps newspapers, magazines, books and other printed materials neatly stored.','Позволяет аккуратно хранить газеты, журналы, книги и другие печатные материалы.','يتيح تخزين الصحف والمجلات والكتب وغيرها من المطبوعات بشكل منظم.');
add(424,'Its elegant, stylish design makes it an eye-catching accessory in any setting.','Благодаря изящному стильному дизайну становится заметным аксессуаром в любом помещении.','يجعله تصميمه الأنيق إكسسواراً لافتاً في مختلف الأماكن.');
add(425,'Made from high-quality materials for reliable use over many years.','Качественные материалы обеспечивают надёжное использование на протяжении многих лет.','مصنوع من مواد عالية الجودة للاستخدام الموثوق لسنوات طويلة.');
add(426,'Compact dimensions allow convenient placement in any room, even small spaces.','Компактные размеры позволяют удобно разместить изделие в любой комнате, даже небольшой.','تسمح أبعاده المدمجة بوضعه بسهولة في أي غرفة حتى في المساحات الصغيرة.');
add(427,'Florida Oak / Multicolour','Дуб Florida / разноцветный','بلوط Florida / متعدد الألوان');
add(428,'Florida Oak frame with a coordinated coloured headboard','Корпус цвета дуба Florida с гармонирующим цветным изголовьем','هيكل بلون بلوط Florida مع لوح رأس ملون متناسق');
add(429,'Florida Oak / Mixed','Дуб Florida / комбинированный','بلوط Florida / مختلط');
add(430,'Florida Oak / Multicolour','Дуб Florida / разноцветный','بلوط Florida / متعدد الألوان');

export const extraTranslations=[...extraTranslationsB,...curated,...extraTranslationsC];
const key=text=>String(text??'').normalize('NFKC').replace(/\s+/g,' ').trim().toLocaleLowerCase('tr-TR');
const lookup=new Map(extraTranslations.map(row=>[key(row.tr),row]));
export function extraTranslate(text,locale){if(locale==='tr')return String(text??'');return lookup.get(key(text))?.[locale]??String(text??'');}
export function extraTranslationIsComplete(text,locale){return locale==='tr'||Boolean(lookup.get(key(text))?.[locale]);}
