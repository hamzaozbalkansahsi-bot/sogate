# Rapor tanımları

Raporlar PostgreSQL kayıtlarından hesaplanır; yerel ortamda bu kayıtlar test siparişleridir. Gerçek satış veya işletme başarısı gibi sunulmaz. Para birimleri ayrı gruplarda gösterilir; TRY ile EUR toplamı tek para birimi altında birleştirilmez.

- Ödenen sipariş: doğrulanmış ödemesi başarılı, kısmen iade veya iade edilmiş; ödeme istisnasındaki siparişler satış toplamına dahil edilmez.
- Tahsilat toplamı: uygun siparişlerin orijinal toplamı. Banka hesabına geçen net ödeme veya muhasebe hasılatı değildir; başarılı iadeler ayrı raporlanır.
- Ortalama sepet: aynı para birimindeki tahsilat toplamı / uygun ödenen sipariş sayısı. Veri yoksa0 ve boş durum gösterilir.
- Başarılı iade: yalnız sağlayıcıdan doğrulanmış veya açıkça yerel test adaptörüyle kesinleşmiş iade tutarı. Bekleyen/başarısız iade tahsilatı azaltmış sayılmaz.
- Hesaplanan sipariş katkısı: kayıtlı satış, vergi, maliyet, ödeme/kanal ücreti, reklam/risk karşılığı, gerçek kaydedilen sevkiyat gideri ve iade değerlerine dayanır. Net işletme kârı değildir. Henüz girilmemiş veya doğrulanmamış giderler gerçek sıfır gider varsayımıyla muhasebe kararı için kullanılamaz; kapsam ve kaynak doğrulaması gerekir.
- Azalan stok: yapılandırılmış minimum + güvenlik stoğuna yaklaşan varyant. Satılabilir miktar aktif rezervasyonlardan sonra hesaplanır; tedarikçi stoğu dahil değildir.
- Ödeme başarısızlığı: başarısız olarak doğrulanmış girişim. Webhook bekleyen işlem başarısız sayılmaz; mutabakat ayrı yürür.

Stok yaşlanması, lot/FEFO, kanal gerçek komisyon mutabakatı, teslimat süresi ve tam pazarlama maliyeti raporları için gereken gerçek olay/gider verileri henüz sağlanmadı; ilgili ileri raporlar tamamlanmış kabul edilmez. Dış sistem raporlarıyla mali mutabakat ayrıca yapılmalıdır.
