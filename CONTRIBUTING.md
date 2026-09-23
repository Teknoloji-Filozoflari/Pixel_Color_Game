# Katkı rehberi

Katkılar hata düzeltmesi, performans iyileştirmesi, erişilebilirlik, çeviri ve belge güncellemesi olarak yapılabilir.

## Geliştirme ortamı

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
```

Değişiklik göndermeden önce:

```bash
python -m pytest -q
python -m ruff check src tests run.py
QT_QPA_PLATFORM=offscreen python run.py --smoke-test --data-dir /tmp/piksel-atolyesi-smoke
```

Yeni koleksiyon dosyalarında `catalog.json` kaydı ile `.pcolor` metadata bilgileri aynı olmalıdır. Mevcut resim kimlikleri kullanıcı ilerlemesiyle eşleştiği için değiştirilmemelidir.

Katkı göndererek değişikliklerinin projenin MIT lisansı altında yayımlanmasını kabul etmiş olursun. Üçüncü taraf içerikleri yalnızca dağıtım hakkı açıkça doğrulanmışsa ekle.
