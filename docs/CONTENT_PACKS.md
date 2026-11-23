# İçerik paketleri (downloadable category packs)

Piksel Atölyesi çekirdek koleksiyonu uygulamayla birlikte gelir. Ek kategoriler
GitHub Releases üzerinden isteğe bağlı ZIP paketleri olarak indirilir.

## Çekirdek (bundled, çevrimdışı)

- Doğa
- Hayvanlar
- Fantastik
- Manzaralar
- Şehirler

İnternet olmadan bu beş kategori tam oynanır.

## İsteğe bağlı (downloadable)

- TÜRKİYE
- TÜRK MOTİFLERİ
- Harikalar
- Araçlar
- Teknoloji

Uygulama içi **Mağaza** ekranından bir dokunuşla indirilir; tarayıcı açılmaz.
İndirme bitince SHA-256 doğrulanır, seviyeler kurulur ve koleksiyon yenilenir.

## Manifest

`src/pixel_coloring/resources/packs/manifest.json`

- `base_url` — GitHub Release asset kökü  
  örn. `https://github.com/Teknoloji-Filozoflari/Pixel_Color_Game/releases/download/content-v1/`
- `release_tag` — asset’lerin yayınlandığı tag (`content-v1`)
- Her pack: `id`, `category`, `bundled`, `version`, `bytes`, `sha256`, `file`, `painting_ids`

## Pack ZIP üretimi

Kaynak ağaçta tüm `.pcolor` dosyaları durur (içerik testleri ve pack üretimi için).
Dağıtım paketlerinden (AppImage/Snap/Windows/macOS) yalnızca çekirdek kategorilerin
`.pcolor` dosyaları bırakılır.

```bash
python3 packaging/build_content_packs.py --out-dir dist/content-packs
```

Bu komut ZIP’leri üretir ve manifest’teki `bytes` / `sha256` alanlarını günceller.

## Yayınlama

1. `python3 packaging/build_content_packs.py`
2. GitHub’da `content-v1` (veya manifest’teki `release_tag`) release’ini oluştur
3. `dist/content-packs/pack-*.zip` dosyalarını release asset olarak yükle  
   İsimler manifest `file` alanlarıyla birebir aynı olmalı
4. Uygulama `base_url + file` adresinden indirir

İçerik değişince pack `version` artır, yeni ZIP üret, yeni release tag kullan veya
aynı tag’de asset’i değiştirip manifest SHA’sını güncelleyip uygulama sürümüyle yayınla.

## Snap

Snap paketinde `network` plug’u vardır; mağaza indirmeleri için gerekir.
Network yokken çekirdek beş kategori çalışmaya devam eder.
