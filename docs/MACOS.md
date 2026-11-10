# macOS sürümü

macOS 14+ / Apple Silicon (arm64) hedeflenir. Python ve Qt paketle birlikte gelir; oyuncunun ayrıca Python kurması gerekmez. Dosyalar kod imzalı veya notarize edilmiş değildir.

## Oyuncu için

[GitHub Releases](https://github.com/Teknoloji-Filozoflari/Pixel_Color_Game/releases/latest) sayfasından:

- `piksel-atolyesi-<sürüm>-macos-arm64.zip` — Apple Silicon (M1/M2/M3/M4)

ZIP'i çıkar, `Piksel Atölyesi.app` dosyasını Uygulamalar'a taşıyabilir veya bulunduğu klasörden açabilirsin. İlk açılışta Gatekeeper uyarısı çıkarsa: sağ tık → Aç. 900 resim pakete dahildir. Kayıtlar `~/Library/Application Support/PixelColoring/PikselAtolyesi` altında tutulur.

Intel Mac için resmi paket üretilmez; kaynak koddan çalıştırma seçeneği README'dedir.

## macOS üzerinde paket üretimi

Apple Silicon Mac gerekir:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -c requirements-tested.txt ".[dev]" PyInstaller==6.22.3
python packaging/build_macos.py
python packaging/macos/smoke_test.py
```

Çıktı `dist/piksel-atolyesi-<sürüm>-macos-arm64.zip` ve `SHA256SUMS` dosyasıdır. İkon `.icns` dosyası PNG'den `sips` / `iconutil` ile üretilir.

## GitHub Actions

`macOS app` iş akışı `macos-14` (arm64) runner'ında testleri çalıştırır, uygulamayı paketler ve offscreen açılışta 900 resmi doğrular. PR'larda otomatik çalışmaz; `main` push veya Actions → **macOS app** → **Run workflow** ile tetiklenir. Yayın süreci: [GITHUB_SETUP.md](GITHUB_SETUP.md).
