# Pardus Yazılım Merkezi başvuru taslağı

Başvuru formu: https://apps.pardus.org.tr/suggestapp

- **Uygulama adı:** Piksel Atölyesi
- **Web sitesi:** https://github.com/Teknoloji-Filozoflari/Pixel_Color_Game
- **Ad ve e-posta:** Başvuruyu gönderen kişi veya ekibin iletişim bilgileri

## Gerekçe alanı için metin

Piksel Atölyesi, Türkçe ve çevrim dışı çalışan, numaraya göre piksel boyama oyunudur.
900 hazır resim, yedi zorluk seviyesi, kendi görselini içe aktarma ve otomatik ilerleme
kaydı sunar. Hesap, reklam veya telemetri gerektirmez. Kaynak kodu açıktır; kod MIT
lisanslıdır. Görsellerin ve üçüncü taraf bileşenlerin lisans bilgileri kaynak depodadır.

Debian 12 ve 13 üzerinde amd64 `.deb` paketinin kurulumu ve çevrim dışı açılışı doğrulandı.
Paket şu sürüm sayfasındadır:
https://github.com/Teknoloji-Filozoflari/Pixel_Color_Game/releases/tag/v0.16.0
Başvurudan önce Pardus 25 masaüstünde uygulama açılışı ve boyama ilerlemesinin yeniden
açılışta korunması ayrıca doğrulanmalıdır.

Pardus Yazılım Merkezi'nde değerlendirilmesini rica ediyoruz. Depoya alınması için farklı
bir Debian kaynak paketlemesi gerekiyorsa sağlayabiliriz.

## Paketleme durumu

`packaging/deb/build-deb.sh`, PyInstaller ile Python ve Qt kitaplıklarını içeren bir `.deb`
üretir. Paketin Pardus kurulumu ve `lintian` denetimi bu sürüm için yapılmalıdır.
Depo ekibinin istediği kaynak paketleme biçimi ayrıca netleştirilmelidir.
