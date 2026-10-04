# Linux paketleri

[v0.16.1 sürümünü indir](https://github.com/Teknoloji-Filozoflari/Pixel_Color_Game/releases/tag/v0.16.1).
900 resim, fontlar, ikonlar ve lisans belgeleri paketlere dahil edilir.
Paketler kişisel boyama ilerlemesi içermez; kayıtlar kullanıcı veri dizinine yazılır.

## AppImage

Ubuntu 22.04 tabanında Python 3.13 ve Qt 6.8 ile üretilir; x86_64 ve
glibc 2.35 veya üzeri gerekir. Python, NumPy, Pillow ve Qt paketin içindedir.
Sistemin EGL/OpenGL sürücü kitaplıkları kullanılır.

```bash
chmod +x Piksel-Atolyesi-0.16.1-x86_64.AppImage
./Piksel-Atolyesi-0.16.1-x86_64.AppImage
```

FUSE bulunmuyorsa:

```bash
APPIMAGE_EXTRACT_AND_RUN=1 ./Piksel-Atolyesi-0.16.1-x86_64.AppImage
```

Ubuntu'da Qt sürücü kitaplıkları gerektiğinde `sudo apt install libegl1 libgl1
libfontconfig1 libxkbcommon-x11-0` kullanılabilir. Üretim ve temiz Ubuntu
22.04/24.04 üzerinde gerçek Qt/X11 pencere açılışı workflow'da kontrol edilir.

## DEB

Debian 12 tabanındaki Python 3.13 container'da üretilir. Debian 12 ve 13
amd64 üzerinde temiz kurulum, offscreen ve X11 açılışı kontrol edilir.
glibc 2.36+ gerekir. Pardus masaüstü ayrıca doğrulanmalıdır.

```bash
sudo apt install ./piksel-atolyesi_0.16.1-1_amd64.deb
```

`apt` sistem bağımlılıklarını kurar. Paket kaldırıldığında oyun kayıtları korunur.
Yerel üretim için `packaging/deb/Dockerfile` veya `packaging/deb/build-deb.sh`
kullanılır. Dağıtımın resmî deposuna gönderilmemiştir.

## RPM

Fedora 43 x86_64 üzerinde sistem Python'u ve Qt 6.11 ile üretilir;
glibc 2.42+ gerekir. Eski Fedora veya openSUSE üzerinde aynı dosyanın
uyumlu olduğu varsayılmaz.

```bash
sudo dnf install ./piksel-atolyesi-0.16.1-1.fc43.x86_64.rpm
```

Python/Qt özel `/usr/lib/piksel-atolyesi` bundle'ında bulunur; bu kütüphaneler
sistem paketleri için Provides/Requires olarak dışa aktarılmaz. Başlatıcı
`/usr/bin/piksel-atolyesi` yolundadır. Kaldırma kullanıcı kayıtlarını silmez.

Fedora build ortamında, gerekli Qt/XCB kitaplıkları ve rpmbuild kurulduktan sonra:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -c requirements-tested.txt '.[dev]' 'PyInstaller==6.22.3'
.venv/bin/python packaging/build_bundle.py
.venv/bin/python packaging/build_rpm.py
```

Tam bağımlılık listesi `.github/workflows/rpm.yml` içindedir.

## Snap

core24 tabanlı amd64 paket strict confinement kullanır. GitHub dosyası
Snap Store imzası taşımadığı için yerel kurulum komutu şöyledir:

```bash
sudo snap install --dangerous ./piksel-atolyesi_0.16.1_amd64.snap
piksel-atolyesi
```

Snap verileri `~/snap/piksel-atolyesi/common/data/PixelColoring/PikselAtolyesi`
altındadır. Sistem paketiyle aynı kayıt klasörünü kullanmaz. Mevcut kayıtları
taşımak için oyun kapalıyken veri klasörünü yedekleyip kopyalayın.
`home` interface'i kendi görsellerini ekleme ve PNG dışa aktarma içindir;
ev dizininin gizli klasörlerine genel erişim vermez.

Snap üretimi önce Ubuntu 22.04/Python 3.13 üzerinde doğrulanmış bundle'ı
`build/bundle/piksel-atolyesi` altında hazırlar, ardından Snapcraft bunu
core24 paketine alır. Temel sistem Python 3.12'sine kurulum yapılmaz.
Yerel üretimde de bundle hazırlandıktan sonra `snapcraft` çalıştırılmalıdır.
İnternet interface'i gerekmez; oyun çevrim dışıdır.
`grade: devel` kullanılır; Store adı kaydı, imzalı yayın ve kanal işlemi yapılmadı.

## Nix / NixOS

Flake desteği etkin Nix ile:

```bash
nix run github:Teknoloji-Filozoflari/Pixel_Color_Game/v0.16.1
nix profile install github:Teknoloji-Filozoflari/Pixel_Color_Game/v0.16.1
```

Flake komutları kapalıysa NixOS yapılandırmasında
`nix.settings.experimental-features = [ "nix-command" "flakes" ];` etkinleştirilir.
Sistem flake'ine `inputs.piksel.url = "github:Teknoloji-Filozoflari/Pixel_Color_Game/v0.16.1";`
eklenip `piksel.packages.x86_64-linux.default` sistem paketlerine veya Home Manager
`home.packages` listesine dahil edilebilir.

```bash
nix build
nix flake check --print-build-logs
./result/bin/piksel-atolyesi
```

`default.nix` ile `nix-build` de kullanılabilir; o yol mevcut Nixpkgs kanalını
kullanır. Flake Nixpkgs 25.11 revizyonunu `flake.lock` ile sabitler.
Nix, tam PySide6 dağıtımı sağladığından yalnız Nix build'inde Essentials bağımlılık
adı PySide6 olarak eşleştirilir. Oyunun modül veya çalışma davranışı değişmez.
Qt yolları Python başlatıcısına sarılır. Nix store salt okunurdur; oyun kayıtları
normal XDG kullanıcı dizinine yazılır.

CI x86_64 build, testler ve kurulu paketin offscreen açılışını kontrol eder;
gerçek NixOS masaüstü testi değildir. aarch64 flake çıktısı tanımlıdır ama bu
mimaride build doğrulanmamıştır. Resmî Nixpkgs yayını yapılmadı.

## Üretim ve yayın

AppImage, DEB, RPM ve Snap workflow'ları Actions üzerinden elle başlatılır.
Her paket üretiminde Ruff, pytest ve açılış kontrolleri çalışır.
Build ve bütün temiz kurulum job'ları başarıyla tamamlanmadan paket yayımlanmaz.
Yayın workflow'u başarılı koşuların artifact'lerini, temiz kaynak ZIP'ini,
Python wheel/sdist dosyalarını ve tüm dosyalar için SHA256SUMS'u aynı sürüme ekler.
Mevcut v0.16.0 sürümü korunur; AUR işlemi yapılmaz.
