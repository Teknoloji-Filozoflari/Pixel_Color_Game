# Windows sürümü

Windows 10/11 x64 hedeflenir. Python ve Qt, paketle birlikte gelir; oyuncunun Python veya pip kurması gerekmez. ARM64 için yerel paket üretilmez.

## Oyuncu için

[GitHub Releases](https://github.com/Teknoloji-Filozoflari/Pixel_Color_Game/releases/latest) sayfasından:

- `Piksel-Atolyesi-<sürüm>-Setup-x64.exe`: kullanıcı hesabına kurulum, Başlat menüsü kısayolu ve isteğe bağlı masaüstü kısayolu. Yönetici izni istemez.
- `piksel-atolyesi-<sürüm>-windows-x64.zip`: tamamını çıkarıp `Piksel-Atolyesi.exe` dosyasını çalıştır.

Her ikisi de 900 resmi içerir. Kayıtlar `%LOCALAPPDATA%\PixelColoring\PikselAtolyesi` altında tutulur; ZIP'in içine yazılmaz. Kurulum, güncelleme veya kaldırma bu dizini silmez. Klasörü oyun kapalıyken yedekleyebilirsin.

Dosya bütünlüğünü PowerShell'de kontrol etmek için:

```powershell
Get-FileHash .\Piksel-Atolyesi-0.17.0-Setup-x64.exe -Algorithm SHA256
```

Sonucu aynı yayının `SHA256SUMS` dosyasındaki satırla karşılaştır. Üretilen dosyalar kod imzalı değildir; imzalama sertifikası bu projeye eklenmemiştir.

## Windows üzerinde paket üretimi

[PyInstaller](https://pyinstaller.org/en/stable/operating-mode.html) Windows programını Windows üzerinde üretir; Linux üzerinde `.exe` derlenmez. [Inno Setup 6](https://jrsoftware.org/isinfo.php) kurulu olmalıdır.

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -c requirements-tested.txt ".[dev]" PyInstaller==6.22.3
.\.venv\Scripts\python.exe packaging/build_windows.py
.\.venv\Scripts\python.exe packaging/windows/smoke_test.py
```

Farklı Inno Setup yolu için `--iscc 'C:\...\ISCC.exe'` verilebilir. Çıktılar `dist/` içindedir; EXE ve ZIP kaynak Git deposuna eklenmez, Release dosyası olarak yüklenir.

Ortak PyInstaller spec'i `packaging/appimage/piksel-atolyesi.spec` dosyasındadır. Windows'ta ikonlu, konsolsuz `Piksel-Atolyesi.exe` ve `_internal/` dizini üretir. NumPy/Pillow/Qt ve bütün kaynaklar bu dizindedir. Onedir düzeni, her açılışta bütün koleksiyonu geçici klasöre çıkarma gereğini önler. Lisanslar ve kaynak kod bağlantısı pakete eklenir.

Inno Setup kullanıcı hesabına kurulur (`PrivilegesRequired=lowest`). Sabit `AppId` sonraki sürümlerin aynı kurulumu güncellemesini sağlar. Oyuncu verileri için `[UninstallDelete]` tanımlanmaz.

## GitHub Actions doğrulaması

`Windows EXE` iş akışı Windows Server 2022 runner'ında:

1. Ruff ve bütün pytest testlerini çalıştırır.
2. Pakette 900 benzersiz resim ve ikon bulunduğunu doğrular.
3. Paketlenmiş EXE'yi geçici kayıt klasörüyle offscreen açar ve veritabanındaki 900 resmi kontrol eder.
4. EXE yükleyiciyi boş, adında boşluk bulunan bir dizine sessizce kurar.
5. Kurulu oyunu yerel Windows Qt penceresiyle açıp kapatır; koleksiyon sayısını kontrol eder.
6. Kaldırıcıyı çalıştırır ve ayrı kayıt dosyasının kaldığını kontrol eder.
7. EXE, taşınabilir ZIP ve SHA256SUMS'u artifact olarak saklar.

Yerel Linux testlerinin başarılı olması Windows doğrulaması yerine geçmez. İş akışı başarılı olmadan Windows dosyası yayınlanmaz. Yayın adımları: [GITHUB_SETUP.md](GITHUB_SETUP.md).
