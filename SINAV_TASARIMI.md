# Sizinle uyumlanan sınav: tasarım notu

**İlke.** The Primer oyuncunun davranışından öğrenip akışı değiştirir. Kapalı kitap, kâğıt bir sınav model çalıştıramaz ama aynı fikri **dallanma** ile taşıyabilir: soru, öğrencinin ilk cevabındaki *hata örüntüsüne* göre farklı bir devam sorusuna götürür. Amaç ezberi değil, bir kavramın **gerekçesini** ölçmektir; bu yüzden her alt soru "neden?" ister ve tanım yazdırmaz.

## Soru (25 puan, 30 dk)

Bir kargo firması, belgesi olmayan eski ücret hesaplama fonksiyonunu (`eski`) yeni bir servise (`yeni`) taşıyor. Ekip, `eski`'yi referans alıp **300 girdilik bir diferansiyel test** çalıştırıyor: 297 girdide sonuç aynı, 2 girdide fark 0,004 TL, 1 girdide fark 12 TL.

1. **(6p)** Bu testte `eski` neden "test kahini (Oracle)" olarak kullanılabiliyor? Kahinin *doğru* olduğunu varsayıyor muyuz? Kararınızı gerekçelendirin.
2. **(6p)** 0,004 TL'lik farklar için bir hata toleransı seçin: mutlak mı göreli mi, hangi değer, neden? Parayı `float` ile tutmanın bir riskini yazın.
3. **(7p)** 12 TL'lik fark çıktı. Bir **doğrulama** sorusu ve bir **geçerleme** sorusu yazın; hangisini kim, hangi kanıtla yanıtlar?
4. **(6p)** Üç ay sonra yeni bir kampanya kuralı ekleniyor. Bu 300 girdi artık hangi testin parçası olur? Fark edilen 12 TL "kasıtlı değişiklik" ise kayıtlı beklenen sonuç ne olmalı ve kim onaylamalı?

## Dallanma (uyumlanma)

- **1. soruda "eski doğru olduğu için her fark hatadır" diyen** öğrenci → **Soru 2'ye değil, 1b'ye** gider: *"`eski` 1998'de yazıldı ve iki müşteri şikâyeti var. Farkın hata olduğunu hangi kanıt gösterir?"* (ölçülen kavram: Oracle problemi, karakterizasyon testinin "doğruyu değil mevcut davranışı sabitlediği").
- **Kahini doğru yorumlayan** öğrenci → **1c'ye** gider ve kavramı yeni bağlamda kullanır: *"ONNX modelinin tarayıcıdaki ve Python'daki çıktısını karşılaştırıyorsunuz. Kahin kim? Tolerans neden 0 değil de 1e-4?"* (ölçülen kavram: aktarım, `float32`, tolerans gerekçesi).

## Beklenen kavramlar

Diferansiyel test, Oracle, **karakterizasyon testi** (mevcut davranışı sabitler), regresyon testi, mutlak/göreli hata toleransı, **doğrulama** ("ürünü doğru mu yapıyoruz?", spesifikasyona uygunluk) ile **geçerleme** ("doğru ürünü mü yapıyoruz?", kullanıcı ihtiyacı).

## Çeldiriciler

- "300 girdi kapsamı kanıtlar": girdi uzayı sınırsızdır; kapsam doğruluk değildir.
- "Tolerans her zaman 0 olmalı": kayan nokta ve yuvarlama; ama para için asıl çözüm tamsayı kuruş.
- "Oracle her zaman doğrudur": o yalnızca *karşılaştırma referansıdır*.
- "Regresyon testi yeni özelliği sınar": hayır, eski davranışın bozulmadığını sınar.
- "Doğrulama ile geçerleme aynı şeydir."

## Puanlama ölçeği

Tanım doğruluğu en fazla puanın %30'u; kalan %70 **gerekçe** ve **yeni durumda kullanma** içindir. Aynı kavramı yanlış gerekçeyle kullanan cevap, doğru sonuca ulaşsa bile tam puan almaz.
