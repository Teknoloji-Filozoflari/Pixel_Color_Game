# Linux paketleme ve yayın devir notu — 2026-10-04

## Yapılanlar

v0.16.0 korunarak 0.16.1 hazırlandı. Mevcut AppImage ve DEB üretimi sabit
Linux bağımlılıkları, temiz kurulum ve X11 kontrolleriyle güçlendirildi.
Fedora 43 RPM, core24 strict Snap ve Nix/NixOS flake paketi eklendi.
Paketlerde 900 resim, fontlar, ikonlar ve lisans belgeleri bulunur.
Oyun kuralları, koleksiyon kimlikleri ve kullanıcı ilerlemesi değiştirilmedi.
Beş mevcut Ruff import sırası hatası düzeltildi.

## Değiştirilen önemli dosyalar

- `packaging/build_bundle.py`, `build_rpm.py`, RPM spec ve Linux constraints.
- AppImage/DEB workflow'ları, Dockerfile ve Debian sistem bağımlılıkları.
- `snap/`, `packaging/nix/`, `flake.nix`, `flake.lock`, `default.nix`.
- Linux build ve doğrulanmış artifact yayın workflow'ları.
- README, Linux rehberi, release notları, MANIFEST ve temiz kaynak ZIP betiği.
- Eksik veya yinelenen koleksiyonu reddeden iki paket bütünlüğü testi.

## Test sonucu

Yerelde Ruff, 55 pytest ve offscreen oyun açılışı başarılı.
Workflow YAML ve shell sözdizimi kontrol edildi. Temiz kaynak ZIP üretimi
900 resmin sıfır boyama ilerlemesiyle dağıtıldığını doğruladı.

GitHub başarılı koşuları:

| Paket | Build / kurulum / açılış |
|---|---|
| AppImage | [37215788862](https://github.com/Teknoloji-Filozoflari/Pixel_Color_Game/actions/runs/37215788862) — Ubuntu 22.04/24.04 X11 |
| DEB | [37215790934](https://github.com/Teknoloji-Filozoflari/Pixel_Color_Game/actions/runs/37215790934) — Debian 12/13 offscreen/X11 |
| RPM | [37215987924](https://github.com/Teknoloji-Filozoflari/Pixel_Color_Game/actions/runs/37215987924) — temiz Fedora 43 offscreen/X11 |
| Snap | [37215901631](https://github.com/Teknoloji-Filozoflari/Pixel_Color_Game/actions/runs/37215901631) — strict kurulum, offscreen/X11 |
| Nix | [37215987923](https://github.com/Teknoloji-Filozoflari/Pixel_Color_Game/actions/runs/37215987923) — x86_64 build, 55 test, kurulu wrapper offscreen |

## Manuel kontrol

X11 kontrolleri Xvfb üzerindedir. AppImage/DEB/RPM/Snap açılışlarından sonra
veritabanındaki koleksiyon sayısı 900 olarak kontrol edildi.
DEB/RPM kaldırıldıktan sonra kullanıcı kayıt dosyasının kaldığı doğrulandı.
Yayın workflow'u bütün build koşularının başarılı sonucunu zorunlu tutar;
doğrulanmış artifact'leri, kaynak ZIP, wheel/sdist ve ortak SHA256SUMS'u yükler.

## Bilinen sorunlar

- AUR, Snap Store, resmî Nixpkgs veya dağıtım depolarına yayın yapılmadı.
- Snap devel/strict kullanır; GitHub dosyası yerel `--dangerous` ile kurulur.
- AppImage glibc 2.35+, DEB glibc 2.36+, Fedora 43 RPM glibc 2.42+ hedefler.
- Nixpkgs tam PySide6 dağıtımı sağladığından yalnız Nix build metadata'sında
  Essentials adı PySide6'ya eşleştirilir.
- Fedora Python 3.14 için Qt 6.11; AppImage/DEB/Snap Python 3.13 için Qt 6.8
  kullanılır. Her ortam kendi paket üretiminde test edilir.
- Gerçek NixOS, Pardus masaüstü, ARM64 ve donanım sürücüsü testleri yapılmadı.
- Snap kayıtları sistem kurulumundan ayrı SNAP_USER_COMMON altında kalır.

## Sonraki faz

Kullanıcının sonraki isteği.
