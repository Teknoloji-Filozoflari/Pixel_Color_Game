# Koleksiyon özeti

Piksel Atölyesi toplam **900** hazır resim içerir. Uygulamanın kullandığı eksiksiz ve makine tarafından okunabilir liste `src/pixel_coloring/resources/paintings/catalog.json` dosyasındadır.

## Kategoriler

| Kategori | Resim sayısı |
|---|---:|
| Doğa | 91 |
| Fantastik | 91 |
| Hayvanlar | 91 |
| Manzaralar | 91 |
| Şehirler | 91 |
| TÜRKİYE | 81 |
| TÜRK MOTİFLERİ | 91 |
| Harikalar | 91 |
| Teknoloji | 91 |
| Arabalar | 91 |
| **Toplam** | **900** |

## Zorluk dağılımı

| Zorluk | Resim sayısı |
|---|---:|
| Çok Kolay | 69 |
| Kolay | 74 |
| Kolay-Orta | 119 |
| Orta | 119 |
| Orta-Zor | 119 |
| Zor | 119 |
| Uzman | 281 |
| **Toplam** | **900** |

Görseller 48×48 ile 1920×1080 arasında, 2.880 ile 2.073.600 hücre ve 10–60 renk aralığındadır. Katalogdaki kimlikler kayıt ilerlemesini eşleştirdiği için mevcut bir resmin kimliği yayınlar arasında değiştirilmemelidir.

Türk Motifleri koleksiyonundaki 91 görsel 512×512 boyutunda ve en fazla 12 renkli paletle paketlenmiştir. Özgün ad ve anlamlar seviye dosyalarında ve katalogda korunur; koleksiyon ve boyama ekranında beş dilde gösterilir. Tasarımlar geleneksel motiflerden esinlenen çağdaş yorumlardır. Anlamlar kaynak tablodan aktarılmıştır; bağımsız tarihsel doğrulama veya belirli bir boyun belgelenmiş damgası iddiası içermez.

Harikalar koleksiyonu kaynak klasörlerinin yedi zorluk basamağını ve her basamakta 13 resmi korur. Her basamağın içinde görseller renk sınırları ve küçük renk parçalarının yoğunluğuna göre sıralanır. Izgaralar, Doğa koleksiyonunun aynı basamaktaki gerçek ölçü ve palet basamaklarından seçilir; Hayvanlar ve Fantastik koleksiyonlarının piksel sayılarıyla da doğrulanır. Dikey ölçüler yatay çevrilir, toplam piksel sayısı korunur. Kaynak resmin tamamı oranı korunarak ızgaraya sığdırılır; kalan kenarlar dış manzaranın yansıtılmasıyla doldurulur. İlk üç basamakta komşuların çoğunluğuyla uyuşmayan tek piksellik renk parçaları azaltılır. Sabit kimlikler korunur; sürüm 3 güncellemesi mevcut ilerlemeyi yedekleyerek yeni ızgaraya taşır.

| Harikalar zorluğu | Piksel sayısı aralığı | Renk üst sınırları |
|---|---:|---:|
| Çok Kolay | 2.880–5.120 | 10–15 |
| Kolay | 8.000–13.068 | 16–20 |
| Kolay-Orta | 15.680–27.380 | 22–25 |
| Orta | 28.880–44.180 | 26–30 |
| Orta-Zor | 46.080–68.440 | 31–35 |
| Zor | 72.000–118.560 | 36–40 |
| Uzman | 200.000–2.073.600 | 44–60 |

Kaynak pakette eksik olan 018 — Özgürlük Heykeli görseli, kullanıcının isteğiyle aynı stile uygun yeniden üretilmiştir. Kaynak PNG ve üretim istemi `packaging/sources/harikalar/` içindedir. Görseller dünyanın tanınmış yapıları ve doğal harikalarının sanatsal yorumlarıdır.

Teknoloji koleksiyonu envanterdeki yedi seviyede 13'er görseli korur ve Harikalar ile aynı dönüştürme/sıralama yöntemini kullanır. Izgaralar ve palet sınırları yukarıdaki oyun basamaklarından seçilir; özgün kaynak kimlikleri, başlıklar ve kaynak üretim revizyonları korunur. Kaynak PNG'ler değiştirilmez. İlk üç seviyede küçük renk parçaları azaltılır; resimlerin tamamı oranı korunarak hedef ızgaraya sığdırılır. Kategori ve başlıklar beş dilde gösterilir.

Arabalar koleksiyonundaki 91 görsel de aynı oyun basamaklarına uyarlanır; yedi seviyede 13'er görsel korunur ve her seviyede görsel karmaşıklığına göre sıralanır. Otomobil, motosiklet, tren, uçak ve tekne görsellerinin kaynak PNG dosyaları değiştirilmez. Başlıklar beş dilde gösterilir.
