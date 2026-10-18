# Sabit renk bütçesinde daha iyi dönüşüm

Önceki `MEDIANCUT` dönüşümü, geniş alanları kaplayan tonlara çok sayıda palet
girdisi ayırırken küçük ama farklı renkteki alanları komşu tonlarla
birleştirebiliyordu. Renk sayısını 250'ye çıkarmak bu sorunu hafifletse de
oyundaki boyama yükünü artırıyordu.

Yeni `importer/quantization.py` aynı renk bütçesinde paleti algısal uzaklıkla
seçer. Tüm pikseller palet öğrenimine katkı verir. Sıklığı yumuşatılmış
başlangıç seçimi ve ağırlıklı kümeleme, seyrek vurgu renklerine de yer açar.
Son piksel eşlemesi, küçültülmüş bir örnek yerine seçilen boyuttaki her
piksel üzerinde yapılır. Dithering uygulanmaz; aynı RGB rengi her konumda aynı
palet girdisine gider. Kullanılan renk sayısı talep edilen sınırı aşmaz.

Kaynak zaten seçilen renk sayısına sığıyorsa renkler değişmeden aktarılır.
İnce gri tonları da kaba histogramın kutu sayısına indirgenmez. Yeni paket
bağımlılığı eklenmedi. Tekli önizleme ve toplu içe aktarma aynı kodu kullanır;
`.pcolor` ve önceden kaydedilmiş boyamalar yeniden dönüştürülmez.

## Doğrulama

`tests/test_quantization.py` içinde 16 senaryo doğrulanır:

- Küçük pembe vurgu alanını eski yöntemin kaybettiği örnekte 60 renkle koruma.
- Bütçeye sığan 1, 2, 15, 60 ve 256 renkli görsellerde tam RGB eşitliği.
- 2, 16, 60, 250 ve 256 renk sınırları; tutarlı çıktı ve geçerli indeksler.
- Gri geçişlerde ince tonlar, nötr renkler ve noktalama olmaması.
- sRGB–Oklab referans değerleri ve 8192 rastgele rengin gidiş-dönüş eşitliği.
- Gerçek kaynak görselde aynı 60 renk bütçesinde daha düşük algısal hata.
- 1920 × 1080 aktarımda boyut ve küçük vurgu renginin korunması.

Tam test paketi: **154 test geçti**. Ruff kontrolü başarılı.

## Gerçek örnekte ölçüm

Depodaki `packaging/sources/harikalar/018-statue-of-liberty.png` dosyası,
en boy oranı korunarak 1440 × 1080'e getirildi. Her iki yöntem de 60 renk
üzerinden değerlendirildi. Aşağıdakiler bu tek örneğe ait ölçümlerdir;
başka resimler için aynı iyileşme oranı iddia edilmez.

| Ölçüm | Önceki yöntem | Yeni yöntem |
| --- | ---: | ---: |
| Ortalama karesel Oklab uzaklığı | 0,0013782 | 0,0002253 |
| Karesel uzaklığın yüzde 99 değeri | 0,0288143 | 0,0024833 |
| Dönüşüm süresi, bu makinede | 0,136 sn | 0,321 sn |

Bu örnekte ortalama karesel algısal uzaklık **%83,6** azaldı. Ölçüm, insan
değerlendirmesi veya bütün görsellerde aynı kalite artışı garantisi değildir.
1920 × 1080 rastgele renk gürültüsünde süre 60 renkte yaklaşık 0,57 saniye,
256 renkte 1,32 saniyeydi. Donanıma ve resme göre süre değişir; dönüşüm mevcut
arka plan işçisinde yürür.

Çalışma klasöründeki karşılaştırma çıktıları:

- `.gelistirme/inceleme/renk-kalitesi-60.png`: özgün, önceki ve yeni sonuç.
- `.gelistirme/inceleme/renk-kalitesi-60.json`: ham ölçüm değerleri.

Çok renkli bir görselin tüm renklerini 60 girdili paletle birebir korumak
mümkün değildir. Bu değişiklik aynı bütçede daha uygun renkleri seçer.
Yeni sonucu görmek için özgün görseli yeniden önizlemeden içe aktarmak gerekir.

Renk uzayı formülleri ve tanımı:
[Björn Ottosson — Oklab](https://bottosson.github.io/posts/oklab/).
