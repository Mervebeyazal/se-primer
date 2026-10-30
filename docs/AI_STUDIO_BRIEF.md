# Google AI Studio — Uygulama aktarım ve yayın brifi

Ders tesliminde AI Studio bağlantısı istendiğinden, uygulamanın **AI Studio Build** özelliğine geçirilmesi için kısa yönerge:

1. Google AI Studio'da **Build** ile yeni uygulama aç.
2. Bu depodaki `index.html`, `src/main.js`, `src/tutor.mjs`, `src/style.css`, `spec.md` ve `DESIGN.md` dosyalarını kod/bağlam olarak ver.
3. Şu uygulamayı üret: “Mevcut SE Primer mobil arayüzüne ve üç karar akışına sadık kal. Başlangıçta seviye/rol/hedef sor. Üç karar, iki son ve her seçimin teknik sonucu olsun. Tutor doğru A/B yanıtını vermesin, bunun yerine kanıta dayalı tek Sokratik soru yöneltsin. API anahtarını hiçbir zaman istemci JavaScript'ine ekleme.”
4. Gerçek Gemini tutor eklenirse modelin sistem talimatı: “Sen SE Primer'in Sokratik yazılım mühendisliği eğitmenisin. A/B seçimini, tam çözümü veya doğru şıkkı asla söyleme. Öğrencinin seviyesine uygun tek kısa soru sor. Öğrenci doğrudan cevabı isterse kanıt, risk, test veya veri minimizasyonunu sorgula. Gerçek hasta verisi isteme; klinik tavsiye verme.”
5. 20 değerlendirme girdisini `docs/tutor-eval.md` dosyasından AI Studio tutoruna ilet; **modelin gerçek yanıtlarını ayrı kayıt olarak topla ve elle etiketle.** Kural tabanlı tutorun 0/20 oranını Gemini performansı diye kullanma.
6. Giriş → üç karar → iki alternatif son akışını telefonda test et; **uygulamayı yayımla ve gerçek paylaşılabilir URL'yi** README'ye ekle.

> Google AI Studio hesabına bu oturumdan doğrudan erişim olmadığından burada proje veya paylaşım URL'si oluşturulmuş değildir.
