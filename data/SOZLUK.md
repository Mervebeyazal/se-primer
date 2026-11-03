# Veri sözlüğü: `data/oturumlar.csv`

**Bir satır = bir karar.** Bir oturum 3 karar (sahne) içerir, yani 3 satır. Ad, e-posta, cihaz kimliği, konum, IP ve tutora yazılan serbest metin **hiçbir zaman** kaydedilmez (KVKK: kişisel veri toplanmaz). `oturum_id` tarayıcıda rastgele üretilir ve kişiyle eşleştirilemez.

| Sütun | Tür | Birim / değerler | Anlamı | Nasıl ölçülür |
|---|---|---|---|---|
| `oturum_id` | metin | 12 hex karakter | Oturumu tanımlayan rastgele kimlik | `crypto.getRandomValues` ile 6 bayt; "Yeniden oyna" her seferinde yeni kimlik üretir |
| `kaynak` | metin | `gercek` \| `sentetik` | Satırın nereden geldiği. **Zorunlu.** Başarı yalnız `gercek` satırlarında ölçülür | Veri toplama modundan gelen satırlar `gercek`; `tools/sentetik_uret.py` çıktısı `sentetik` |
| `sahne_no` | tam sayı | 1, 2, 3 | Karar sırası: 1 mimari, 2 test, 3 KVKK | Uygulamadaki sahne sırası |
| `seviye` | 0/1 | 0 = yeni başlayan, 1 = deneyimli | Girişte seçilen deneyim seviyesi. 1 ise 60 sn sayaç vardır | Açılır menü değeri |
| `karar_suresi_sn` | ondalık | saniye (0.1 hassasiyet) | Sahne ekrana geldiğinden seçim yapılana kadar geçen süre. Süre dolarak seçilen kararda 60.0 | `Date.now()` farkı |
| `okuma_suresi_sn` | ondalık | saniye (0.1 hassasiyet) | Kararın teknik sonucu ekrana geldiğinden "Sonraki karar / Sonucu gör"e basılana kadar geçen süre | `Date.now()` farkı |
| `tutor_soru_sayisi` | tam sayı | adet, ≥ 0 | Bu sahnede tutora sorulan soru sayısı ("SOR" ve "Bir soru daha sor"). Soru metni kaydedilmez, yalnız sayısı | Sayaç |
| `ipucu_acildi` | 0/1 | 1 = oyuncu "İpucu göster"e kendisi bastı | Yeni başlayanda ipucu zaten otomatik görünür; bu sütun **bilinçli tıklamayı** ölçer | Düğme tıklaması |
| `secim` | metin | `A` \| `B` | Seçilen karar. B = riskli seçenek | Tıklama ya da süre dolumu |
| `sure_doldu` | 0/1 | 1 = 60 sn doldu, B otomatik uygulandı | Yalnız deneyimli oyuncuda 1 olabilir | Sayaç sıfırlanması |
| `secim_b` | 0/1 | 1 = `secim` B | **Modelin etiketi** (hedef değişken). `secim` ile birebir tutarlıdır | `secim == 'B'` |

## Modelin girdilerine dönüşüm

Model, bir sahne başlamadan **önce** çalışır; yalnız önceki sahnelerin davranışını görür. Bu yüzden satırlardan şu girdiler türetilir (aynı oturumda, `sahne_no` sırasına göre). Hem `train.py` hem de uygulama (`src/telemetry.mjs`) aynı tanımı kullanır; `tests/ozellik_ornekleri.json` bu eşdeğerliği sınar.

| Model girdisi | Tanım |
|---|---|
| `sahne_no` | Tahmin edilen sahnenin numarası (2 veya 3) |
| `seviye` | O sahnenin satırındaki `seviye` |
| `onceki_karar_suresi_sn` | Bir önceki sahnenin `karar_suresi_sn` değeri |
| `onceki_okuma_suresi_sn` | Bir önceki sahnenin `okuma_suresi_sn` değeri |
| `onceki_tutor_soru_sayisi` | Bir önceki sahnenin `tutor_soru_sayisi` değeri |
| `onceki_ipucu_acildi` | Bir önceki sahnenin `ipucu_acildi` değeri |
| `onceki_b_sayisi` | Tahmin edilen sahneden önceki sahnelerdeki toplam `secim_b` |
| **etiket** `secim_b` | Tahmin edilen sahnenin kendi seçimi |

Sahne 1 satırları dosyada durur (oyunun tam kaydı), ama geçmiş davranış olmadığı için **eğitim ve ölçümde kullanılmaz**; model sahne 1'de çalışmaz.

## Nasıl toplanır

1. Uygulamayı `…/index.html?veri=1` adresiyle aç (veri toplama modu; girişte uyarı notu çıkar).
2. Kişiye normal oynat. Aynı sekmede birden çok oturum oynanabilir; kayıtlar tarayıcıda birikir.
3. Bittiğinde bitiş ekranındaki **CSV İNDİR** düğmesine bas ve dosyayı sana göndermesini iste (içinde kişisel bilgi yoktur).
4. `python tools/birlestir.py gelen.csv` ile doğrulayıp `data/oturumlar.csv`'ye ekle.

## Sentetik veri

`kaynak = sentetik` satırlarını `tools/sentetik_uret.py --oturum 150 --tohum 13` üretir; kural dosyanın başında yazılıdır ve `README.md`'de özetlenir. Sentetik satırlar yalnız eğitim katlarında kullanılır, başarı ölçümüne girmez.

## Bilinen sınırlar

- Gerçek veri az sayıda tanıdık kişiden gelir (arkadaş grubu); genel bir öğrenci popülasyonunu temsil etmez.
- `okuma_suresi_sn` sekme arka plandayken de akar; çok uzun değerler "ekrandan ayrılma" olabilir. 3600 sn üstü `tools/birlestir.py` tarafından reddedilir; `train.py` eğitimde süreleri ayrıca üst sınıra kırpar.
- Süreler tarayıcı saatine bağlıdır; cihaz hızına duyarlı değildir ama 0.1 sn'den ince ölçülmez.
