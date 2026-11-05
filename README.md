# SE Primer v2 · Sizinle Uyumlanan Primer (YZM301 — Yazılım Test ve Gerçekleme)

**Etkileşimli mühendislik karar simülasyonu.** Sağlık randevu sistemi arızasında üç karar (mimari, test, KVKK), iki son ve her karardan sonra teknik açıklama. v1 (geçen hafta) uyumu sabit kurallarla yapıyordu. **v2'de uyumu, oyuncunun davranışından öğrenen küçük bir model yapıyor:** önceki sahnelerdeki karar süresi, sonucu okuma süresi, tutora sorulan soru ve ipucu kullanımından "bu sahnede riskli B'yi seçer mi?" olasılığını tahmin eder; olasılığa göre tutor **destek** verir, **meydan okur** ya da olduğu gibi bırakır.

| Teslim bağlantısı | Durum |
|---|---|
| GitHub | https://github.com/Mervebeyazal/se-primer |
| Hugging Face model (commit'li) | **Yayınlanmadı:** eval kapısı geçilemedi (aşağıdaki not, `RELEASE.md` §8). Yayın aracı hazır: `tools/hf_yayinla.py` |
| Canlı uygulama | https://mervebeyazal.github.io/se-primer/ (model olmadan v1 davranışı; `?veri=1` ile veri toplama) |
| Demo video (83 sn) | https://github.com/Mervebeyazal/se-primer/blob/main/docs/demo.mp4 (model kapıyı geçemediği için olasılık `?p=` test kancasıyla sabitlenir; mod politikası gösterilir. Kaynak: `tools/demo_kayit.py`) |

> ⚠️ **Dürüst durum: model eğitildi ama eval kapısını geçemedi, bu yüzden yayınlanmadı.**
> - Gerçek veri: **18 gerçek oturum** (birinci tur 3 kişi × 5 = 15; ikinci tur 3 oturum), sentetik 150 oturum (yalnız boru hattı denemesi için).
> - `spec.md` eşikleri eğitimden önce yazıldı (AUC ≥ 0.70, Brier < taban, ONNX ≤ 1e-4, ≥ 15 gerçek oturum). **İlk deneme AUC 0.4533, ikinci deneme (18 oturum, gerçek-yalnız GroupKFold) AUC 0.3664**; ikisi de kapıyı geçemedi, eşikler gevşetilmedi. Nedenleri ve ölçüm düzeni değişikliklerinin (spec v2.1, v2.2) kronolojisi `RELEASE.md` §8'de.
> - Bu yüzden `model/` yok; HF'ye model yüklenmedi, `tests/parite.json` üretilmedi (Cypress parite spec'i atlanır). Uygulama modeli bulamayınca **v1 gibi çalışır** (güvenli geri düşüş, `model.cy.js` bunu sınar).
> - Hazır olanlar: eğitim hattı + kapı (`train.py`), ONNX aktarımı ve model kartı üretimi, tarayıcıda çıkarım ve mod politikası (`?p=0.72` ile gösterilebilir), Shadow/Canary mekanizması, testler, `RELEASE.md`.

## Hızlı başlangıç (3 komut)

```bash
pip install -r requirements.txt     # 1) Python bağımlılıkları (scikit-learn 1.9.1 ve skl2onnx 1.20.0 sabit)
python train.py --olcum cv           # 2) eğit + eval kapısı -> geçerse model/{...}. ŞU AN GEÇMEZ (çıkış kodu 1, model/ yazılmaz); bkz. RELEASE.md §8
python3 -m http.server 5173          # 3) http://localhost:5173  (ES modülleri için file:// değil, HTTP gerekir)
```

Uygulama modeli `onnxruntime-web` ile tarayıcıda çalıştırır (CDN'den yüklenir; yüklenemezse oyun v1 gibi sürer).

## v2 nasıl çalışıyor

```
oyuncu davranışı ─► özellikler (7 sayı) ─► model.onnx (tarayıcıda) ─► p ─► mod ─► oyunun davranışı
 (karar/okuma süresi,    src/telemetry.mjs     lojistik regresyon        │    p ≥ 0.60  destek : ipucu otomatik, tutor soru sorar, sayaç kalkar
  tutor soru, ipucu,                                                    │    p ≤ 0.25  meydan : ipucu gizli, sonuçta "Neden?" notu
  önceki B sayısı)                                                      │    arası     normal : v1 davranışı
```

- Model **sahne 2 ve 3'te** çalışır (sahne 1'de geçmiş davranış yok; v1 aynen korunur).
- Model yüklenemezse, hata verirse ya da `yuzde = 0` ise oyun **v1 gibi** sürer; oyun modele bağımlı olarak kilitlenmez.
- **Veri toplama modunda (`?veri=1`) model kapalıdır.** Aksi halde model oyuncuya müdahale eder, seçimler değişir ve etiketler kirlenir.
- Mod, sahnede `DESTEK MODU · p=0.7234` rozetiyle oyuncuya açıkça gösterilir.
- Kontrollü yayın: `src/yayin.json` (`golge`, `yuzde`, `model_taban`); ayrıntı `RELEASE.md`.
- Test kancaları: `?p=0.72` (olasılığı sabitler), `?tani=1` (model tanı paneli: 7 girdiyi elle girip `data-cy="p"` değerini okuma), `?modelBase=…` (model klasörünü değiştirir).

## Veri

`data/oturumlar.csv`: **her karar bir satır**; sütunlar ve birimler `data/SOZLUK.md`'de. `kaynak` sütunu zorunlu: `gercek` | `sentetik`.

**Gerçek oturumlar.** Uygulamayı `…/index.html?veri=1` ile açıp arkadaşlara oynatın (aynı sekmede birden çok oturum birikir). Bitiş ekranında **CSV İNDİR**. Gelen dosyayı doğrulayıp ekleyin:

```bash
python tools/birlestir.py gelen1.csv gelen2.csv                # 1. tur (geliştirme seti): data/oturumlar.csv
python tools/birlestir.py --dogrulama gelen3.csv gelen4.csv    # 2. tur (YENİ kişiler, tutulan set): data/dogrulama.csv
python tools/birlestir.py --kontrol                            # sayıları raporlar; iki set ayrık mı denetler (aynı oturum kimliği iki sette olamaz)
```

**KVKK.** Ad, e-posta, cihaz kimliği, konum, IP ve tutora yazılan serbest metin **hiçbir zaman** kaydedilmez. `oturum_id` tarayıcıda rastgele üretilen 12 hex karakterdir. `birlestir.py` tanımsız sütun içeren (örn. `email`) dosyayı reddeder.

**Sentetik veri.** Gerçek oturumlar toplanırken hattı kurmak (`train.py --deneme`, testler) için kullanılır. **Ne eğitime ne ölçüme girer** (v2.1: üreticinin "uzun düşünen B seçer" varsayımı gerçek veriyle ters çıktı; aşağıda). Üretici: `tools/sentetik_uret.py --oturum 150 --tohum 13`; aynı tohum birebir aynı dosyayı verir. Kural (tam metin dosyanın başında):

- Her oturumun gizli bir becerisi vardır: `s ~ N(0,1)`; `seviye ~ Bernoulli(0.4)`.
- Karar süresi `LogNormal(ln15 − 0.35·s, 0.45)`, okuma süresi `LogNormal(ln8 + 0.25·s, 0.50)`, tutor sorusu `Poisson(exp(−0.6 − 0.4·s))`, ipucu `Bernoulli(σ(−0.4 − 0.6·s))`.
- `P(B) = σ(−0.5 − 0.9·s + 0.35·önceki_B + 0.2·seviye + N(0, 0.6))`; deneyimlide 60 sn aşılırsa B ve `sure_doldu=1`.
- Mevcut dosya: 150 sentetik oturum (tohum 13). Yalnız sentetik veriyle yapılan çalışmada veri puanının yarısı alınır; bu yüzden gerçek oturum toplamak gereklidir.

## Eğitim ve eval kapısı

`python train.py` tek komuttur ve tohum 13 sabittir. Aynı veri ile her ortamda **birebir aynı metrikleri** üretir (CI yeniden eğitip karşılaştırır).

- **Kabul eşiği `spec.md`'de eğitimden önce yazıldı:** ROC-AUC ≥ **0.70**, Brier skoru "hep taban oranı tahmin et"ten düşük, ONNX farkı ≤ **1e-4**, doğrulamada en az **15 gerçek oturum**.
- **Ölçüm düzeni (spec v2.1):** model yalnız birinci turun gerçek oturumlarıyla (`data/oturumlar.csv`) eğitilir; kapı, **farklı kişilerden gelen** tutulan sette (`data/dogrulama.csv`) ölçülür. Doğrulama seti tek kullanımlıktır; sonucu görüp ayar yapılmaz. Kapı geçilirse yayınlanan model iki turun tüm gerçek satırlarıyla yeniden eğitilir.
- **İlk deneme başarısız oldu (dürüst kayıt).** v2.0 düzeni (5 katlı grup çapraz doğrulama + eğitime 300 sentetik satır) 15 gerçek oturumda AUC **0.4533** verdi (eşik 0.70) ve Brier tabandan kötüydü; `model/` yazılmadı. Eşikler gevşetilmedi, ölçüm düzeni v2.1 olarak ikinci tur veriden ve yeniden eğitimden **önce** `spec.md`'ye yazıldı. Ayrıntı: `RELEASE.md` § 8.
- Eşik altındaysa betik **hata koduyla durur ve `model/` altına hiçbir şey yazmaz** (`tests/test_train.py` bunu sınar).
- AUC'si tanımlı olmayan kat (test katında tek sınıf) ortalamaya girmez; en az 3 geçerli kat gerekir. Havuzlanmış AUC ve oturum bazlı bootstrap %95 aralığı da raporlanır.
- `--deneme` bayrağı gerçek veri yokken hattı sınamak içindir: çıktı `_out/deneme/` altına yazılır, "yayınlanamaz" diye işaretlenir.

Çıktılar: `model/model.onnx`, `model/config.json` (özellik adı ve sırası, sınıflar, eşikler, metrikler, veri SHA-256: aynı zamanda tüketici sözleşmesi), `model/README.md` (model kartı: amaç, veri, metrikler, sınırlar, kullanılmaması gerekenler).

## Testler

| Ne | Komut | Kapsam |
|---|---|---|
| Özellik türetme + mod politikası (JS) | `node tests/ozellik.test.mjs` | Ortak örnek dosyası `tests/ozellik_ornekleri.json` |
| Yayın / kova mantığı | `node tests/yayin.test.mjs` | Canary yüzdeleri, iç içe gruplar, yapılandırma |
| Eğitim, eval kapısı, ONNX farkı, tekrarlanabilirlik, özellik türetme (Python) | `python -m unittest tests.test_train -v` | Kapı durdurması ve aynı çıktı |
| Tutor değerlendirmesi (v1) | `node tests/tutor-eval.mjs` | 20 girdi |
| **Oracle** (Python onnxruntime) | `python tests/parite.py --yaz` / `python tests/parite.py` | 5 referans girdi → `tests/parite.json` |
| **Diferansiyel test (parite)** | `npm run test:e2e` → `cypress/e2e/parite.cy.js` | Tarayıcı `data-cy="p"` ile Oracle farkı < 1e-4 |
| **Regresyon (v1)** | `cypress/e2e/primer.cy.js` (**değiştirilmedi**) | 8 karar yolu, sayaç, tutor; model aktifken de geçmeli |
| Model davranışı | `cypress/e2e/model.cy.js` | Destek, meydan, normal, sahne 1, model yok, Canary %0, Shadow, veri modu |
| Çevrimdışı Shadow | `python tools/golge_degerlendir.py yeni.csv` | Eğitimde görülmemiş yeni gerçek oturumlarda kapı |

Cypress için `npm install` ve başka terminalde `python3 -m http.server 5173` gerekir. CI: `.github/workflows/ci.yml`.

## Yapay zekâ kullanım beyanı

Bu çalışmada **Claude (Claude Code ile bir oturum)** kullanıldı. Süreç ben yönettim; model fikri ve eşikler (AUC ≥ 0.70, mod eşikleri 0.60 / 0.25) oturumda konuşularak onaylandı.

1. **Spec v2 bölümü, veri hattı** (`?veri=1` toplama modu, `tools/birlestir.py`, `tools/sentetik_uret.py`, `data/SOZLUK.md`): Claude taslakladı, ben tasarım kararlarını (model KAPALI veri toplama, grup bazlı doğrulama, ölçümün yalnız gerçek veride yapılması) onayladım.
2. **`train.py`, `src/telemetry.mjs`, `src/model.mjs`, `src/main.js` değişiklikleri, mod davranışları, `tools/hf_yayinla.py`, `tools/golge_degerlendir.py`**: Claude yazdı. Claude'un oturumda yakaladığı bir tutarsızlık: eğitimde süreler kırpılırken tarayıcı tarafı kırpmıyordu; JS ve Python için ortak örnek dosyasıyla düzeltildi.
3. **Testler** (Python `unittest`, Node, Cypress `model.cy.js` / `parite.cy.js`) ve **`RELEASE.md` taslağı**: Claude yazdı. Tarayıcı doğrulaması Playwright (Chromium) ile yapıldı; **Cypress bu geliştirme ortamında çalıştırılamadı** (Cypress ikilisi indirilemedi), aynı senaryolar Playwright'ta birebir sınandı. Cypress'in gerçek koşusu GitHub Actions'tadır.
4. **Elle düzelttiklerim / reddettiklerim:** (a) Veriyi arkadaşlarımdan ben topladım ve ilk turda herkesin senaryoyu okumadan tıkladığını fark ettiğimizde veri toplama yönergesini ben yeniden yazdırdım. (b) Başarısız sonuçtan sonra Claude'un gösterdiği kolay çıkışları (sentetik veriyi çıkarıp 0.785 AUC ile yayınlamak, eşiği düşürmek) **reddettim**; kapıyı geçemeyen modeli yayınlamamayı seçtim (seçenek A). (c) Eşikleri ve mod politikasını (0.70 / 0.60 / 0.25) ben onayladım. (d) Sentetik üreticinin varsayımının gerçek veriyle ters çıktığını görüp sentetik veriyi eğitimden çıkarma kararı verildi.
5. **Kaynaklar:** fikirler Andrew Ng'nin dersteki 4 başlığı, Shankar vd. (3V), Mitchell vd. (model kartı), Breck vd. (ML Test Score) çerçevelerinden; ayrıntı `RELEASE.md > Kaynaklar`.

## Sınırlar ve yapılmayanlar

- Gerçek veri **az sayıda tanıdık kişiden** gelir; model genel bir öğrenci kitlesini temsil etmez. Model kartı güven aralığını ve sınırları açıkça yazar.
- Model davranış **korelasyonunu** tahmin eder, kişi hakkında yargı değildir; notlandırma ya da karar için kullanılmaz.
- Tutor hâlâ LLM değil, kural tabanlı Sokratik prototiptir.
- **Yapılmadı:** model yayını (kapı geçilemedi), Rails/FastAPI sunucu tüketicisi (bonus), Expo mobil tüketici, canlı otomatik izleme.
- Google Stitch projesi ve Google AI Studio yayını yapılmadı (v1'den kalan açık not).

## v1 (geçen hafta) belgeleri

v1 belgeleri korunmuştur: `spec.md` (v1 bölümleri ve 5 kabul örneği), `DESIGN.md`, `docs/tutor-eval.md`, `docs/STITCH_BRIEF.md`, `docs/AI_STUDIO_BRIEF.md`, `evidence/`, `design/`. v1 durumu (30.10.2026): 8/8 karar yolu Chromium'da geçti; Cypress 11/11 GitHub Actions'ta geçti ([koşu](https://github.com/Mervebeyazal/se-primer/actions/runs/41011390943)).

**Ürün kararı, kapsam dışı üç özellik (v1 ve v2):** (1) kullanıcı hesabı yok: tek oturumluk akışta gereksiz sürtünme ve kişisel veri; (2) ikinci senaryo yok: sekiz karar yolunun tamamını test etmek önceliklidir; (3) gerçek hasta verisi yok: sentetik vaka eğitim hedefini sağlar.

### Teknik tasarım

- `src/main.js`: vanilla JavaScript, ES modülleri, DOM tabanlı durum makinesi.
- `src/telemetry.mjs`: davranış kaydı, CSV sözleşmesi, model özellik vektörü, mod politikası (saf, Node'da test edilir).
- `src/model.mjs`: `onnxruntime-web` ile çıkarım, yayın yapılandırması, kova hesabı.
- `src/tutor.mjs`: çevrimdışı, deterministik Sokratik sorular; kullanıcı metni sunucuya gönderilmez.
- `src/yayin.json`: `golge`, `yuzde`, `model_taban` (Shadow / Canary / geri alma).

## Kaynaklar

Ders PDF'i *SE Primer — YZM301* (2026); *Modelden Ürüne: Yapay Zekâ* ve *Yazılım Testi Tartışması* (30 Ekim 2026) ders notları. Shankar vd. (2022); Amershi vd. (2019); Mitchell vd. (2019); Breck vd. (2017); Sommerville, *Software Engineering* (10. baskı). ONNX Runtime, skl2onnx, Hugging Face Hub belgeleri; Cypress: https://docs.cypress.io; KVKK: https://www.kvkk.gov.tr. Ayrıntılı atıflar `RELEASE.md`'de.
