# 0.17.0 yayın hazırlığı — 18 Ekim 2026

## Kapsam

Uygulama başlangıcı/kapanışı, boyama ve kamera akışı, kayıt uyumluluğu, içe aktarma,
yeni oyun araçları, koleksiyon kaynakları, Python dağıtımı ve masaüstü paketleme
incelendi. Bu sürümde önceki geliştirme çalışmaları da bir araya getirildi.

## Temizlik ve düzeltmeler

- Hiçbir yerden çağrılmayan eski altı örnek resim üreticisi ve ona ait kullanılmayan
  büyütme metodu kaldırıldı. Aktif koleksiyon güncellemesi `bundle_update.py` üzerinden devam eder.
- Görünmeyen eski gezinme paneli, boş gezinme düğmesi sözlüğü ve gereksiz ana sayfa
  sarmalayıcısı kaldırıldı. Odak modu gerçek durum çubuğunu gizlemeyi sürdürür.
- Kaldırılan kırmızı hücre çerçevesinin kullanılmayan varsayılan ayarı temizlendi.
- Eski gömülü Python taşınabilir arşiv yöntemi yerine Windows EXE/ZIP üretimi eklendi.
- Kaynak ZIP hazırlığı geçici dizin kullanır; tekrar çalıştırma eski çalışma
  klasörleriyle çakışmaz. Önbellek, ortam, EXE ve kişisel kayıtlar dışarıda tutulur.
- Eski devir notu ve yeni README'de kullanılmayan eski ekran görüntüsü kaldırıldı.
- RPM, Snap ve Nix metadata'sındaki eski MIT ifadesi mevcut GPL-3.0-or-later
  proje lisansına düzeltildi. Görsel sayısı ve kaynak dağıtımı açıklamaları güncellendi.
- Konsolsuz Windows EXE'de bulunmayan `sys.stderr` için StreamHandler oluşturulmaz.
- Yayın kontrolü artık bütün paket koşularının aynı commit'ten, doğru depodan ve
  beklenen iş akışından geldiğini zorunlu tutar. Her paket grubunun checksum'u
  ayrı kontrol edilir; aynı isimli dosyaların üstüne yazılmaz.

900 koleksiyon dosyası ve katalog değiştirilmedi. Lisans metinleri, kaynak görsel
ve üretim açıklamaları, anlamlı testler ve kayıt uyumluluğu kodu korundu.

## Yerel doğrulama

- Python 3.14 / Linux / Qt offscreen: **180 test geçti**.
- Uygulama, testler ve değişen paketleme yardımcılarında Ruff başarılı.
- Bütün workflow YAML'ları, Python sözdizimi, kaynak JSON'ları ve yeni belge bağlantıları kontrol edildi.
- Temiz kaynak ZIP'i, wheel ve sdist başarıyla üretildi. Üçü de 900 resmi içerir.
- Kaynak ZIP'i ve wheel içinde bilgi kitapçığı ve ikon bulunur; kişisel veritabanı,
  günlük, Python önbelleği veya sanal ortam bulunmaz.
- Ayrı geçici veri dizininde açılış/kapanış başarılı; açılış kaydı yaklaşık 0,45 saniye.
- Güncel arayüzden koleksiyon, boyama, içe aktarma, kitapçık ve tamamlanma ekranları alındı.

## Dış ortamda kalan doğrulama

Windows EXE Linux üzerinde derlenmedi. `Windows EXE` iş akışı gerçek Windows
runner'ında test, EXE üretimi, yükleyici kurulumu, yerel Qt açılışı ve kaldırmayı
kontrol eder. Linux paketlerinin temiz kurulumları da kendi iş akışlarında yeniden
çalıştırılmalıdır. Bu kontroller geçmeden 0.17.0 ikili paketleri yayınlanmış sayılmaz.

Bu hazırlık ortamından `github.com` DNS çözümlemesi başarısız olduğu için push ve
GitHub Actions koşuları burada doğrulanamadı. Gönderme ve yayın adımları
[GITHUB_SETUP.md](GITHUB_SETUP.md) içindedir.
