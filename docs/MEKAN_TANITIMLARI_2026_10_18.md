# Türkiye ve Harikalar mekân tanıtımları

Türkiye kategorisindeki **81** ve Harikalar kategorisindeki **91** görselin
tamamına ayrı bir bilgi kartı bağlandı. Her kartta mekân adı, üç cümlelik Türkçe
tanıtım, kaynak kurumun adı, doğrudan bağlantısı ve kontrol tarihi bulunur.
Kaynak dosya: `src/pixel_coloring/resources/artwork_facts.json`.

## Eşleştirme

Türkiye görsellerinin tamamı küçük resim paftaları üzerinden incelendi.
Harikalar görselleri de görsel ve katalog başlığı birlikte ele alınarak
eşleştirildi. Başlıca düzeltilen eski eşleşmeler:

| Görsel | Kartın anlattığı yer |
| --- | --- |
| İzmir | Konak Saat Kulesi; önceki Efes açıklaması kaldırıldı |
| Şanlıurfa | Balıklıgöl; önceki Göbeklitepe açıklaması kaldırıldı |
| İstanbul | Ortaköy Camii ve Boğaziçi; önceki Ayasofya açıklaması kaldırıldı |
| Tokat | Ballıca Mağarası |
| Rajasthan Sarayı | Görseldeki Hawa Mahal, Jaipur |

Tek bir yapı adıyla kesinleştirilemeyen yayla, kıyı veya orman kompozisyonlarında
metin ilgili yerin peyzajını tanıtır; kompozisyonu gerçek bir fotoğrafın tam
coğrafi kaydı gibi sunmaz. Örneğin Artvin kartı Karagöl çevresindeki orman
göllerini, Düzce kartı bölgenin orman ve şelalelerini açıklar. Görsellerin mevcut
sanatsal yorum notu korunur.

## Kaynaklar ve arayüz

Kaynaklar UNESCO Dünya Mirası Merkezi, GoTürkiye, Türkiye Kültür Portalı,
resmî turizm kurulları, millî park idareleri ve ilgili anıtların resmî
kurumlarıdır. Yayıncı etiketi her bağlantıya göre gösterilir; bütün kaynaklar
UNESCO olarak etiketlenmez. Eski GoTürkiye adreslerinde erişim sorunu görülen
Balıkesir, Diyarbakır, Konya, Rize ve Tekirdağ bağlantıları güncel adreslere
çevrildi. Kore sarayları için güncel resmî kurum alan adı kullanıldı.

Kartın başındaki “Mekânı tanı” bölümü yer adını ve açıklamasını gösterir.
Boyut, renk ve ilerleme bilgileri bunun altında yer alır. Metinler uygulamayla
birlikte gelir; kartı okumak için ağ bağlantısı gerekmez. Kaynağa tıklamak,
sayfayı kullanıcının tarayıcısında açar.

Genişletilen tanıtımlar Türkçedir. Daha önce mevcut olan yabancı dildeki mekân
açıklamaları korunmuştur. Eski İzmir, Şanlıurfa ve İstanbul metinleri İngilizce,
Azerbaycanca, İspanyolca ve Rusçada da doğru mekânla değiştirilmiştir. Yeni
arayüz başlığı ve kaynak etiketi mevcut beş dilde desteklenir.

`.pcolor` dosyaları, katalog kimlikleri ve boyama ilerlemesi değiştirilmedi.
Kişisel görsellere otomatik tarihî açıklama eklenmez.

## Doğrulama

- Tam test paketi: **174 test geçti**.
- Ruff ve satır sonu kurallarına uygun Git fark kontrolü başarılı.
- Bütün 172 kimliğin birer karta bağlanması, üç cümlelik metinlerin varlığı,
  kaynak adları ve HTTPS bağlantıları doğrulandı.
- İzmir, Şanlıurfa, İstanbul, Tokat ve Hawa Mahal için mekân eşleşmesi testleri
  eklendi; kişisel görsellerde bu kartların kullanılmadığı kontrol edildi.
- Kartlarda tanıtımın teknik bilgilerden önce gelmesi ve doğru yayıncı
  bağlantısının gösterilmesi Qt offscreen ortamında doğrulandı.
- İzmir, Şanlıurfa, Hawa Mahal ve Özgürlük Heykeli kartları görsel olarak
  incelendi. Çalışma klasöründeki örnekler `.gelistirme/inceleme/bilgi-*.png`.
