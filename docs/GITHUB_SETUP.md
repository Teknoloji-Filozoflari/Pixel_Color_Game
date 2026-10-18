# GitHub ve sürüm yayını

Kaynak depo: https://github.com/Teknoloji-Filozoflari/Pixel_Color_Game

## Kaynağı gönderme

`pyproject.toml` ve `.git` bulunan depo kökünde:

```bash
gh auth login --hostname github.com --git-protocol https --web
gh auth setup-git
gh auth status
git remote -v
git status --short
git push origin main
```

Commit henüz oluşturulmamışsa önce değişiklikleri inceleyip `git add` ve `git commit` kullan. Token veya cihaz giriş kodunu depoya, issue'ya veya sohbet mesajına yazma. Başka bir bilgisayardaki kurulu oyunun dosyalarını bu kaynağın üstüne kopyalama.

## Paketleri üretme

`Windows EXE`, main'e push ile otomatik çalışır. Diğer paketleri aynı main commit'inde Actions sayfasından veya CLI ile başlat:

```bash
gh workflow run appimage.yml --ref main
gh workflow run debian-package.yml --ref main
gh workflow run rpm.yml --ref main
gh workflow run snap.yml --ref main
gh workflow run nix.yml --ref main
```

Windows için yeniden üretim gerekirse `gh workflow run windows.yml --ref main` kullan. `Python package` testlerinin de başarılı olduğunu kontrol et.

```bash
gh run list --branch main --limit 15
```

Her iş akışının başarılı koşusundaki **ID**'yi not et. Bu sırada main'e yeni commit gönderme: bütün koşular yayınlanacak kaynakla aynı `head_sha` değerine sahip olmalıdır. Paket üretim dosyalarında veya notlarda bir hata düzeltilirse yeni commit'te kontroller yeniden çalıştırılır.

## Doğrulanmış sürümü yayınlama

`pyproject.toml`, `src/pixel_coloring/__init__.py` ve `snap/snapcraft.yaml` sürümleri aynı olmalıdır. `docs/release-notes/v<sürüm>.md` bulunmalıdır. Yeni bir etiket elle oluşturmak gerekli değildir; yayın iş akışı hedef commit üzerinde oluşturur.

Actions → **Publish verified release** → **Run workflow** bölümünde altı koşu ID'sini gir. CLI karşılığı (yer tutucuları gerçek sayılarla değiştir):

```bash
gh workflow run publish-verified.yml --ref main \
  -f appimage_run=APPIMAGE_ID -f deb_run=DEB_ID \
  -f rpm_run=RPM_ID -f snap_run=SNAP_ID \
  -f nix_run=NIX_ID -f windows_run=WINDOWS_ID
```

Yayın kontrolü her koşunun doğru depodan, doğru iş akışından ve **aynı commit'ten** geldiğini; başarıyla tamamlandığını doğrular. Farklı koşuların `SHA256SUMS` dosyaları birbirinin üstüne yazılmaz; paketler önce ayrı dizinlerde kontrol edilir. Aynı isimli dosyalar reddedilir.

Son adım Windows EXE/ZIP, Linux paketleri, kaynak ZIP, Python wheel/sdist ve ortak `SHA256SUMS` ile `v<sürüm>` yayınını oluşturur. Mevcut sürümler silinmez veya değiştirilmez. Önceden var olan bir sürüm etiketinin üzerine yazılmaz.

Nix flake üzerinden sunulur; ayrı Nix kurulum dosyası yüklenmez. AppImage, DEB, RPM, Snap ve Windows dosyalarının beklenen sürümlü adları zorunlu tutulur. Wheel içinde 900 `.pcolor` bulunduğu da kontrol edilir.

## Yerel kaynak arşivi

```bash
python packaging/build_release.py
```

Temiz kaynak ZIP'ine sanal ortamlar, önbellekler, kişisel veritabanları, günlükler, kimlik bilgileri veya derlenmiş EXE eklenmez. Geçici hazırlık dizini otomatik temizlenir; komut tekrar çalıştırılabilir. Windows paketleri için eski gömülü Python `--runtime` yöntemi kaldırılmıştır; `packaging/build_windows.py` kullanılır.
