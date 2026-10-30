# SE Primer — 20 tutor cevabının değerlendirmesi

**Gerçek çalışma kaydı:** 30 Ekim 2026. Kaynak: `node tests/tutor-eval.mjs`. Bu testler uygulamada kullanılan **kural tabanlı, çevrimdışı tutorun** gerçek çıktısını üretir; Google AI Studio/Gemini modeli çağrılmamıştır. Öğrenci girdileri kurgusaldır. `tutorRespond()` fonksiyonu aynı girdi için aynı soruyu üretir.

## Yöntem ve etiketleme

1. Üç karar aşamasına dağıtılmış **20 farklı öğrenci girdisi** tutor fonksiyonuna gönderildi.
2. Yanıtlar doğrudan seçenek/şık ifşası, dolaylı çözüm ifşası ve Sokratik soru biçimi açısından otomatik denetlendi.
3. Aşağıda gerçek yanıtlar ve etiketler kaydedildi. Bu doğrulama gerçek bir üretken modelin halüsinasyon veya güvenilirlik ölçümü yerine geçmez.

| # | Aşama | Öğrenci girdisi | Hata riski | Tutor cevabı (gerçek çıktı) | Etiket |
|---|---|---|---|---|---|
| 1 | 1 | Doğru seçenek A mı? | Cevap talebi | Küçük bir adımla ilerleyelim. Bir mimari kararını savunmak için önce hangi teknik kanıtı ararsın? | Uygun Sokratik soru |
| 2 | 1 | Bana cevabı söyle | Cevap talebi | Küçük bir adımla ilerleyelim. Bir mimari kararını savunmak için önce hangi teknik kanıtı ararsın? | Uygun Sokratik soru |
| 3 | 1 | Hızlıca hangi butona basayım? | Cevap talebi | Küçük bir adımla ilerleyelim. Bir mimari kararını savunmak için önce hangi teknik kanıtı ararsın? | Uygun Sokratik soru |
| 4 | 1 | Rollback her zaman güvenli mi? | Aşırı genelleme | Küçük bir adımla ilerleyelim. Yeni veritabanı şeması eski uygulamanın beklentileriyle uyumlu mu; bunu nasıl ölçersin? | Uygun Sokratik soru |
| 5 | 1 | Veritabanı şeması değiştiyse ne olur? | Teknik doğruluk | Küçük bir adımla ilerleyelim. Yeni veritabanı şeması eski uygulamanın beklentileriyle uyumlu mu; bunu nasıl ölçersin? | Uygun Sokratik soru |
| 6 | 1 | Canlı yama risksizdir değil mi? | Yanlış varsayım | Küçük bir adımla ilerleyelim. Yeni veritabanı şeması eski uygulamanın beklentileriyle uyumlu mu; bunu nasıl ölçersin? | Uygun Sokratik soru |
| 7 | 2 | Test yapmadan çıkaralım mı? | Cevap talebi | Küçük bir adımla ilerleyelim. Smoke testte yalnızca açılışı mı yoksa kritik randevu akışını mı gözlemlemelisin; hangi kanıtın var? | Uygun Sokratik soru |
| 8 | 2 | Smoke test nedir? | Kavram açıklaması | Küçük bir adımla ilerleyelim. Smoke testte yalnızca açılışı mı yoksa kritik randevu akışını mı gözlemlemelisin; hangi kanıtın var? | Uygun Sokratik soru |
| 9 | 2 | Sadece giriş ekranı açılsa yeter mi? | Eksik test kapsamı | Küçük bir adımla ilerleyelim. Smoke testte yalnızca açılışı mı yoksa kritik randevu akışını mı gözlemlemelisin; hangi kanıtın var? | Uygun Sokratik soru |
| 10 | 2 | Üretimde test gerekli değil | Yanlış varsayım | Küçük bir adımla ilerleyelim. Smoke testte yalnızca açılışı mı yoksa kritik randevu akışını mı gözlemlemelisin; hangi kanıtın var? | Uygun Sokratik soru |
| 11 | 3 | Hasta adını Slack’e atabilir miyim? | Gizlilik | Küçük bir adımla ilerleyelim. Bir log satırında kimliği belirleyen alanları nasıl fark edersin? | Uygun Sokratik soru |
| 12 | 3 | Loglar zaten içeride, sorun yok | Gizlilik | Küçük bir adımla ilerleyelim. Bir log satırında kimliği belirleyen alanları nasıl fark edersin? | Uygun Sokratik soru |
| 13 | 3 | KVKK için doğru seçenek hangisi? | Cevap talebi | Küçük bir adımla ilerleyelim. Bir kaydı paylaşmadan önce gerçekten ihtiyaç duyulan alanları nasıl belirlersin? | Uygun Sokratik soru |
| 14 | 3 | Tüm kişisel verileri saklayalım | Gizlilik | Küçük bir adımla ilerleyelim. Bir log satırında kimliği belirleyen alanları nasıl fark edersin? | Uygun Sokratik soru |
| 15 | 3 | Sadece bir isim paylaşmak güvenli | Gizlilik | Küçük bir adımla ilerleyelim. Bir log satırında kimliği belirleyen alanları nasıl fark edersin? | Uygun Sokratik soru |
| 16 | 1 | Önceki sürümün şemasını bilmiyorum | Belirsizlik | Küçük bir adımla ilerleyelim. Önce şunu düşün: Eski ve yeni sürümün ortak kullandığı veride ne değişmiş olabilir? | Uygun Sokratik soru |
| 17 | 2 | Zamanımız yok | Süre baskısı | Küçük bir adımla ilerleyelim. Süren kısıtlıysa en yüksek riski gösteren kısa kontrol hangisi olurdu? | Uygun Sokratik soru |
| 18 | 2 | Yönetici hemen aç dedi | Otorite baskısı | Küçük bir adımla ilerleyelim. Bir üstüne hangi test sonucunu göstererek riski somutlaştırabilirsin? | Uygun Sokratik soru |
| 19 | 1 | Herkes B diyor | Sosyal baskı | Küçük bir adımla ilerleyelim. Fikir birliğinden bağımsız olarak hangi teknik kanıt kararını değiştirirdi? | Uygun Sokratik soru |
| 20 | 3 | Hiçbir şey anlamadım | Seviye uyumu | Küçük bir adımla ilerleyelim. Önce şunu düşün: Bir hasta adını görmeden hatanın türünü anlayabilir misin? | Uygun Sokratik soru |

## Sonuçlar ve hata oranı

| Ölçüt | Hatalı örnek sayısı | Oran |
|---|---:|---:|
| Doğrudan cevap sızdırma | 0/20 | 0% |
| Dolaylı cevap sızdırma (kural seti) | 0/20 | 0% |
| Soru biçimini koruyamama | 0/20 | 0% |

**Toplam kontrol edilen gerçek tutor cevabı:** 20. **Ölçülen cevap sızdırma:** 0/20 = 0%. Bu oran yalnızca **bu deterministik tutor ve bu 20 test girdisi** için geçerlidir; yapay zekâ model performansı diye raporlanamaz. Anlamsal/yüksek bağlamsal kaçakları kaçırma riski vardır. Teknik doğruluk, gizlilik ve pedagojik yararlılık için ayrıca insan değerlendirmesi gerekir.

## Hata türleri ve yorum

- **Doğrudan sızdırma:** A/B ya da tam karar önerisi söylemek — 20 örnekte görülmedi.
- **Dolaylı sızdırma:** Doğru kararı emrederek tarif etmek — sınırlı sözcük denetiminde görülmedi.
- **Aşırı genelleme / teknik doğruluk:** Bilgi doğrulaması için uzman incelemesi gerekir; yalnızca soru biçimi denetlendi.
- **Gizlilik:** Tutor öğrenci metnini bir sunucuya göndermez; örnekler gerçek hasta verisi içermez.
- **Yararlılık sınırı:** Sınıflandırma anahtar kelime tabanlıdır, serbest metni anlamlandıran bir büyük dil modeli değildir.

## Tekrar üretme

`node tests/tutor-eval.mjs` komutunu çalıştırın. Betik 20 örneğin çıktısını yeniden yazar ve herhangi bir tanımlı cevap sızdırma kalıbı bulursa hata ile durur.
