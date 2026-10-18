# Kaldığın görünüm ve görsel önizlemesi

Son kullanıcı düzeltmesine göre bu turda yalnızca önceki önerilerin **2 ve 7**
numaralı maddeleri uygulanmıştır. Geri al/ileri al, seçili renk için mini harita
değişikliği, renk değiştirme kısayolları ve palet filtresi bu turun kapsamında değildir.
Tuvalde kırmızı çerçeve çizilmez.

## Kaldığın görünümden devam et

- Her resmin yakınlaştırması ve mantıksal bakış merkezi ayrı kaydedilir.
- Boyama ilerlemesiyle görünüm aynı veritabanı işlemi içinde yazılır.
- Oyun veya resim yeniden açılınca görünüm geri gelir. Pencere boyutu farklıysa
  merkez korunur; kenarlarda resim sınırları uygulanır.
- Önceki kayıtlar okunabilir; eksik `view_states` tablosu otomatik oluşturulur.
- Geçersiz kamera verisi veya resim boyutunun değişmesi ilerleme kaybına yol
  açmaz; görünüm için ekrana sığdırma kullanılır.
- “Baştan başla” hem ilerlemeyi hem kayıtlı görünümü sıfırlar.

## Kendi resmini eklerken önizleme

PNG, JPEG veya WEBP seçilince özgün resim ve boyama önizlemesi yan yana gösterilir.
Genişlik ve yükseklik ayarlanabilir; en boy oranı varsayılan olarak korunur.
Renk sayısı otomatik seçilebilir veya 2–256 arasında elle ayarlanabilir.
Boyama boyutu en fazla 1920 × 1080'dir; daha büyük raster kaynaklar bu ekranda
küçültülebilir. Görselin EXIF yönü uygulanır, şeffaf alanlar beyaza birleştirilir.

Önizleme arka planda hesaplanır. Ayar değiştirildiğinde eski sonuç onaylanamaz;
yalnızca güncel önizlemedeki piksel haritası koleksiyona eklenir. İptal kaynak
görseli değiştirmez ve seviye dosyası yazmaz. `.pcolor` dosyaları hazır paletleriyle
doğrudan eklenmeye devam eder.

## Yeniden incelemede kontrol edilen sorunlar

- Önizleme hesapları yarıştığında eski sonucun yeni ayarlar yerine eklenmesi:
  istek revizyonu kontrolü ve onay düğmesinin devre dışı bırakılmasıyla önlenir.
- Önizleme iptal/kapanışında işçi ve zamanlayıcıların açık kalması:
  kapanış bir kez çalışır, bekleyen işler iptal edilir ve zamanlayıcılar durdurulur.
- Değişen pencere boyutunda kameranın yanlış yere kayması:
  ekran pikseli yerine mantıksal merkez kaydedilir.
- Eski veya geçersiz görünüm kaydı: güvenli sığdırmaya dönülür; boyama maskesi korunur.
- Qt testlerinin kapanışında görülen çökme: bütün arayüz testlerinde tek
  `QApplication` kullanılır ve kalan pencereler uygulamadan önce temizlenir.

Testler kayıt uyumluluğunu, bozuk görünüm verisini, yeniden açma ve yeniden
başlatmayı, ayarlı önizlemeyi, onaylanan sonucun aynen yazılmasını, iptali,
EXIF yönünü ve şeffaflığı kapsar. Önceki kırmızı çerçevenin yokluğunu denetleyen
tekli/toplu boyama testleri de korunmuştur.

Son doğrulama: **124 test geçti**, Ruff kontrolü hatasız tamamlandı ve ayrı
geliştirme kayıtlarıyla açılış/kapanış kontrolü başarılı oldu. Önizleme ekranı
ayrıca 96 × 96 piksel ve 16 renkli örnekle görsel olarak kontrol edildi.
