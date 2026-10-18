# Yeni oyun araçları — 18 Ekim 2026

Bu tur son öneri listesindeki **1, 5, 6, 7 ve 9** numaralı özellikleri kapsar.
Önceki listedeki yalnızca 2 ve 7 seçimi ayrı bir turdu. Çift görünüm önerisi
(son listedeki 10) uygulanmadı. Kurulu oyun değiştirilmedi.

## Kullanım

- Üstteki sürgü simgesi: numaralar, numara boyutu, ızgara görünürlüğü,
  kalınlığı, yoğunluğu ve tamamlanma animasyonu. Varsayılana döndürme vardır.
- Kamera simgesi: kaydı başlat, duraklat/sürdür ve GIF olarak kaydet.
  Kayıt başlatılan andan itibaren tutulur; önceki hareketler üretilmez.
  Resimden ayrılmadan GIF kaydedilmelidir.
- ⓘ simgesi: resmin boyutu, kullanılan renk sayısı, ilerleme ve açıklama.
  Türkiye’de 81 ve Harikalar’da 91 görselin tamamında mekân adı ve üç cümlelik
  Türkçe tanıtım bulunur. İlgili kurumun kaynak bağlantısı her kartta gösterilir.
  Türk motifleri mevcut anlam açıklamalarını kullanır. Diğer resimlerde teknik
  bilgiler gösterilir. Kartı okumak için internet gerekmez.
- Ana sayfa resim ekleme menüsü: tek resim, birden fazla dosya veya klasör.
  Klasör seçimi alt klasörlere inmez. Ortak boyut sınırı ve renk seçimi vardır.
  İptal mevcut dosyayı tamamladıktan sonra durur; eklenmiş resimler korunur.

Yeni arayüz metinleri Türkçe, İngilizce, Azerbaycanca, İspanyolca ve Rusça
olarak bulunur. Tarihî bilgiler başlıklardan tahmin edilmez; açık kimlik
eşleşmesi kullanılır. Kaynaklar UNESCO, resmî turizm kurumları, millî park
idareleri ve ilgili yapıların resmî kurumlarıdır. Genişletilen yeni mekân
tanıtımları Türkçe sunulur; daha önce mevcut olan yabancı dil açıklamaları korunur.

## Düzeltmeler ve kontroller

- Yanlış renkli hücre için kırmızı çerçeve eklenmedi. Eski kırmızı geri bildirim
  ayarı arayüzden kaldırıldı; işlevsiz seçenek artık gösterilmiyor.
- Tekli veya toplu eklemede veritabanı kaydı başarısız olursa yeni seviye
  dosyası temizlenir. Kaynak görsellere dokunulmaz.
- Bozuk bir dosya toplu işlemin geri kalanını durdurmaz; hatalar ayrıntılarıyla
  listelenir. İşlem sırasında iptal ve kapanış desteklenir.
- GIF kaydı en fazla 180 küçük kare tutar; uzun kayıtta aralar seyreltilir.
  İlk ve son kare korunur. Başarısız dışa aktarma eski hedef dosyayı bozmaz.
- Tamamlanma animasyonu giriş olaylarını engellemez. Kutlama sonunda aynı
  kartta koleksiyona dönüş veya resimde kalma seçilir. İkinci tebrik/uyarı
  penceresi kaldırıldı. Animasyon kapalıysa seçenekler doğrudan gösterilir.
  Sayfadan ayrılmak kartı ve animasyonu iptal eder.
- 960 × 640 pencere boyutunda yeni araç düğmeleri çakışmıyor.
- Kişisel dosya başlıkları ve açıklamalar düz metin gösterilir.
- Qt offscreen ortamında arayüz görüntüleri incelendi; etkileşim testleri,
  statik kontrol ve uygulama açılış kontrolü çalıştırıldı.

Kaynaklar, `resources/artwork_facts.json` içinde resim kimliği ve kontrol
tarihiyle listelenir. Çalışma kopyasını üst klasörden başlatma komutu:

```bash
bash gelistir.sh
```
