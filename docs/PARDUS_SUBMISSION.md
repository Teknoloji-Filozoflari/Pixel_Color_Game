# Pardus Yazılım Merkezi başvuru taslağı

Başvuru formu: https://apps.pardus.org.tr/suggestapp

- **Uygulama adı:** Piksel Atölyesi
- **Web sitesi:** https://github.com/Teknoloji-Filozoflari/Pixel_Color_Game
- **Ad ve e-posta:** Başvuruyu gönderen kişi veya ekibin iletişim bilgileri

## Gerekçe alanı için metin

Piksel Atölyesi, Türkçe ve çevrim dışı çalışan, numaraya göre piksel boyama oyunudur.
536 hazır resim, yedi zorluk seviyesi, kendi görselini içe aktarma ve otomatik ilerleme
kaydı sunar. Hesap, reklam veya telemetri gerektirmez. Kaynak kodu açıktır; kod MIT
lisanslıdır. Görsellerin ve üçüncü taraf bileşenlerin lisans bilgileri kaynak depodadır.

Pardus 25 üzerinde amd64 `.deb` paketi kuruldu; uygulama açılışı ve boyama ilerlemesinin
yeniden açılışta korunması test edildi. Pakete ve SHA-256 özetine şu sürüm sayfasından
ulaşılabilir: https://github.com/Teknoloji-Filozoflari/Pixel_Color_Game/releases/tag/v0.15.0

Pardus Yazılım Merkezi'nde değerlendirilmesini rica ediyoruz. Depoya alınması için farklı
bir Debian kaynak paketlemesi gerekiyorsa sağlayabiliriz.

## Paketleme durumu

Mevcut `.deb`, PyInstaller ile Python ve Qt kitaplıklarını içinde taşır. Kullanıcı kurulumu
ve ilk Pardus denemesi için uygundur. Debian `lintian` denetimi gömülü kitaplıklar ve
geleneksel Debian paket metadata dosyaları nedeniyle hatalar bildirdi. Pardus deposuna
doğrudan kabul edileceği varsayılmamalıdır; depo ekibinin istediği kaynak paketleme biçimi
ayrıca netleştirilmelidir.
