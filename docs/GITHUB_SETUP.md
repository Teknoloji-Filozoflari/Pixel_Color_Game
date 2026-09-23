# GitHub'a hazırlama

Bu paket bir GitHub deposuna yüklenebilecek kaynak ağacıdır. README, LICENSE, pyproject.toml ve src aynı depo kökünde olmalıdır. Ekran görüntüleri `docs/images/` altında olduğundan README bağlantıları GitHub'da da çalışır.

1. Kaynak paketini çıkar ve bu klasörü depo kökü olarak kullan.
2. `README.md`, `LICENSE`, `ASSETS_LICENSE.md`, `THIRD_PARTY.md`, `LICENSES/`, `docs/`, `src/`, `tests/`, başlatıcı kaynakları ve proje ayarlarını ekle.
3. `.gitignore` dosyasını koru. `runtime/`, `.venv/`, `work/`, kullanıcı veri tabanları, günlükler, erişim anahtarları ve derlenmiş EXE dosyalarını depoya koyma.
4. GitHub'da kendi hesabında boş bir depo oluştur. Bu pakette README ve lisans bulunduğundan GitHub'da ikinci bir başlangıç README/lisansı oluşturmana gerek yoktur.
5. Depoyu GitHub Desktop veya Git ile yükle. Yüklemeden önce hazırlanmış dosyaları gözden geçir.

Git kullanıyorsan yerel ilk adımlar:

```bash
git init
git add .
git status
git commit -m "Add Piksel Atolyesi source and documentation"
```

Uzak depo adresi, kullanıcı adın ve depo adın belli olduğunda eklenir; belgelerde uydurma bir hesap veya yayın bağlantısı kullanılmamıştır. Bu hazırlık işlemi GitHub'a otomatik yükleme yapmaz.

## Yayın paketleri

Kaynak depo ile taşınabilir oyun ZIP'i farklıdır. Windows çalışma ortamını ve EXE'yi Git geçmişine koymak yerine ayrı bir GitHub Release eki olarak dağıtabilirsin. README'ye gerçek Release bağlantısını yayın oluşturulduktan sonra ekle.

İkili dağıtımlarda üçüncü taraf lisanslarını ve kullanılan sürümlere ait kaynak erişimi yükümlülüklerini ayrıca ele al. LICENSES dizininin varlığı tek başına her dağıtım biçimi için tam uygunluk onayı değildir. Qt ile ilgili kaynak ve lisans bağlantıları THIRD_PARTY.md içindedir.

## Rozetler ve kimlik

README rozetleri statik lisans/teknoloji bilgisi verir; test başarısı veya resmî sertifikasyon iddiası taşımaz. LICENSE içindeki mevcut “Pixel Coloring contributors” telif bildirimi korunmuştur. Gelecekte kendi adını eklerken mevcut katkı sahiplerinin bildirimlerini silme.
