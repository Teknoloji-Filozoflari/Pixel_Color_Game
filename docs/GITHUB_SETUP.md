# GitHub'a yükleme — 0.16.0

Bu kaynak paketinde 900 görsel korunur. Kişisel boyama ilerlemesi, kullanıcı ayarları,
veri tabanları, test çıktıları ve yerel Python ortamı bulunmaz. Yeni kullanıcıda bütün
resimler sıfır boyama ilerlemesiyle açılır. Güncelleme mevcut oyuncunun ilerlemesini korur.

1. RAR dosyasını başka bilgisayarda tamamen çıkar.
2. GitHub Desktop ile hedef depoyu klonla. Paketin içindeki dosyaları depo köküne kopyala;
   src, pyproject.toml ve .github doğrudan kökte bulunmalı. RAR dosyasını depoya ekleme.
3. Değişiklikleri commit edip push yap. Actions bölümündeki testlerin sonucunu kontrol et.
4. v0.16.0 etiketiyle bir GitHub Release oluştur. AppImage iş akışı Linux paketini derleyip
   Release'e ekler. Başarıyla tamamlandığını Actions üzerinden doğrula.

Kaynak kodu çalıştırmak için Python 3.13 veya üstünü kurup paket klasöründe:

```bash
python -m pip install .
python run.py
```

Windows'ta kaynak klasöründeki start.bat da oyunu açar; Python ve bağımlılıklar kurulu olmalı.
RAR bir kaynak paketidir; içinde hazır Windows EXE'si bulunmaz. Oyunculara Python kurulumu
gerektirmeyen Windows sürümü dağıtmak için ayrıca taşınabilir Windows paketi hazırlanmalıdır.

Yerel paket oluşturma: python packaging/build_release.py
Yerel Python çalışma ortamıyla taşınabilir ZIP: python packaging/build_release.py --runtime .tools/python

Kod MIT lisanslıdır; görseller için ASSETS_LICENSE.md ve üçüncü taraf bileşenler için
THIRD_PARTY.md ile LICENSES dizinini koru.
