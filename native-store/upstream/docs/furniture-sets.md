# Katalogdan seçilebilir mobilya takımları

Ürünler kendi SKU ve fiyatlarıyla bağımsız kalır. Oda takımları, müşterinin seçtiği parçalardan oluşan bir seçimdir; yeni stok/SKU veya zorunlu satın alma paketi değildir.

Kaynak PDF: `output/pdf/NODENO_Mobilya_Katalogu_2026_Paylasim_Son.pdf`. PDF SHA256: `326f3d643638e1bbf2a69f91786f1e2f03ad559d61762a3ab4551a27bcb12238`. Kaynak ürün ve kimlik hashleri `data/furniture-sets.json` içinde kayıtlıdır. `python scripts/import-furniture-sets.py` yalnız birebir kod eşleşmeleriyle tanımı üretir; build her hash ve üye SKU eşleşmesini doğrular.

| Koleksiyon | PDF sayfaları | Seçilebilir SKU |
|---|---|---|
| Madeira Yatak Odası | 3, 4 | 6 |
| Oriella Yatak Odası | 5, 6 | 21 |
| Bohera Yatak Odası | 7 | 4 |
| Bohera Yaşam Odası | 8 | 3 |
| Cottage Yatak Odası | 9 | 6 |
| Basis Yatak Odası | 10 | 4 |
| Milena Yatak Odası | 11 | 14 |
| Milena Yaşam Odası | 12 | 5 |
| Lunia Yaşam Odası | 13 | 5 |
| Rustica Yaşam Odası | 14 | 3 |
| Sephira Yaşam Odası | 15 | 4 |
| Terria Genç Odası | 17 | 7 |
| Cottage Genç Odası | 18 | 7 |
| Lonera Genç Odası | 19 | 8 |
| Basis Genç Odası | 20 | 10 |
| Alba Genç Odası | 21 | 11 |
| Trendora Genç Odası | 22 | 6 |

## Güncel ürün listesinde bulunmayan katalog kodları

Bu kodlar sepete veya toplu teklife eklenmez; benzer ürünlerden kod/fiyat/görsel türetilmez.

| Kod | PDF sayfaları |
|---|---|
| Ndn-KRY-1616-FF-3 | 4 |
| Ndn-RAF-1700-WW-1 | 5, 6 |
| Ndn-BSH-1902-FV-1 | 8 |
| Ndn-AYN-903-XX-1 | 8 |
| Ndn-KNS-840-FB-1 | 14 |

## Satış kapsamı

Kaynakta tek SKU ile satılan Vitus köşe takımı (4786), masa ve iki tabureden oluşan Step-Up seti (4883) ve Loft Americano köşe takımı (5003) takım biriminde kalır. Ayrı SKU olarak bulunmayan alt parçaları bağımsız ürün gibi satılmaz. Milena gövde ve kapakları ayrı kaynak ürünleridir; kurucuda kapsam açıklaması görünür ve gövde komple kapaklı gardırop diye sunulmaz. Teknik ölçüler ve fiziksel uyum katalog sayfasındaki görselden türetilmez.

Seçim örneği: 1 Bohera gardırop (4907), 2 Bohera komodin (4911), 1 Bohera şifonyer (4915), 0 bazalı karyola (4910). Perakende sepete üç SKU ve toplam dört ürün eklenir. Aynı içerikten 10 toptan takım, sunucuda 10 gardırop/20 komodin/10 şifonyer olarak kaydedilir.
