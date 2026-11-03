---
library_name: sklearn
tags:
- onnx
- tabular-classification
- sklearn
- education
pipeline_tag: tabular-classification
---

# SE Primer v2: Akış Modeli

> ⚠️ **DENEME ÇIKTISI.** Değerlendirme sentetik veride yapıldı, eval kapısı GEÇİLEMEDİ; bu model yayınlanamaz.

Bir sahne başlamadan önce oyuncunun riskli (B) seçeneği seçme olasılığını önceki sahnelerdeki davranışından tahmin eder. Olasılık, tutorun müdahale modunu (destek / normal / meydan) belirler.

## Amaç
SE Primer (yazılım mühendisliği kriz simülasyonu) her sahneden önce bu modeli tarayıcıda çalıştırır.
Olasılık `p` yüksekse oyuncuya **destek** (ipucu otomatik açılır, tutor soru sorar, süre baskısı kalkar),
düşükse **meydan okuma** (ipucu gizlenir, "Neden?" notu eklenir), arada **normal** akış uygulanır.
Eşikler: destek `p ≥ 0.6`, meydan `p ≤ 0.25` (`config.json`).

## Model
`Pipeline(StandardScaler → LogisticRegression)`, tohum 13. Girdi 7 sayı (sıra ve birimler `config.json` → `features`):
`sahne_no`, `seviye`, `onceki_karar_suresi_sn`, `onceki_okuma_suresi_sn`, `onceki_tutor_soru_sayisi`, `onceki_ipucu_acildi`, `onceki_b_sayisi`.
Çıktı: `probabilities` `[n, 2]`; sınıf 1 = riskli B seçimi. Eğitim: Python 3.13, scikit-learn 1.9.1, skl2onnx 1.20.0.

## Veri
- Kaynak: SE Primer veri toplama modu. Gerçek oturumlar tanıdık kişilerden, rastgele oturum kimliğiyle toplandı; ad, e-posta, cihaz kimliği, konum ve serbest metin **yoktur**.
- Değerlendirmede kullanılan **sentetik** oturum: **150** (300 karar satırı). Eğitim katlarına ek olarak 0 sentetik satır girdi (üretici kural `tools/sentetik_uret.py` başında). Son model, eğitime uygun tüm satırlarla (0 gerçek + 300 sentetik) yeniden eğitilir.
- `data/oturumlar.csv` SHA-256: `f2e97133b8b61c2b…` (tam değer `config.json`'da).

## Metrikler (kabul eşiği eğitimden önce `spec.md`'de yazıldı)
Doğrulama: `GroupKFold(5)`, grup = oturum (bir oturumun satırları hem eğitimde hem testte olmaz). **Yalnız gerçek satırlarda ölçülür**; sentetik satırlar yalnız eğitim katlarındadır.

| Metrik | Değer | Eşik |
|---|---|---|
| ROC-AUC (geçerli katların ortalaması, 5/5 kat) | **0.646** | ≥ 0.7 |
| ROC-AUC (tüm test tahminleri havuzlanmış) | 0.641 (oturum bootstrap %95 aralığı: 0.5809 – 0.7013) | bilgi |
| Brier skoru (model) | 0.2375 | taban (0.2513) altında |
| B seçim oranı (taban) | 0.4967 | bilgi |
| ONNX ↔ sklearn en büyük olasılık farkı | 7.549e-08 | ≤ 0.0001 |

Mod dağılımı (test tahminlerinde): her modda kaç karar var ve gerçekte B seçilme oranı. Modlar ayrışıyorsa `destek` oranı `meydan` oranından yüksek olmalıdır.

| Mod | Karar sayısı | Gerçek B oranı |
|---|---|---|
| destek | 73 | 0.6438 |
| normal | 224 | 0.4464 |
| meydan | 3 | 0.6667 |

## Sınırlar
- **Az veri.** Birkaç tanıdık kişiden az sayıda oturum. Güven aralığı geniştir; AUC'yi kesin bir değer gibi okumayın.
- **Dar popülasyon.** Arkadaş grubu, tek bir senaryo (sağlık randevu sistemi arızası), yalnız 3 karar. Başka senaryo ya da kitleye genellenmez.
- Model davranış korelasyonu öğrenir; neden-sonuç iddia etmez. "Tereddüt eden oyuncu yanlış yapar" bir tahmindir, kişi hakkında bir yargı değildir.
- Sahne 1'de model çalışmaz (geçmiş davranış yok). Model yüklenemezse oyun normal akışla sürer.

## Kullanılmaması gereken durumlar
- Öğrenci notlandırma, sınav, işe alım ya da herhangi bir **kişi hakkında karar** için kullanılmaz.
- Gerçek kişisel veriyle yeniden eğitilmez. Bu model yalnız öğretici bir simülasyonun akışını uyarlar.
- Güvenlik ya da sağlık kararlarında kullanılmaz.

## Kullanım
Sözleşme: girdi `input` float32 `[n, 7]` (sıra: `config.json` → `features`), çıktı `probabilities` float32 `[n, 2]` (sıra: `config.json` → `classes`).
Tüketiciler modeli `main` dalından değil, **commit'e sabitlenmiş** URL'den indirir:
```
https://huggingface.co/<kullanici>/<repo>/resolve/<commit>/model.onnx
```
