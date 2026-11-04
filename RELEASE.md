# RELEASE: SE Primer v2.0 ("Akış Modeli")

> Bu belge yayın kararlarını ve gerekçelerini taşır. `⚠️ DOLDURULACAK` ile işaretli alanlar yalnız Hugging Face yayını yapıldıktan sonra bilinebilir; gerçekleşmemiş bir değer yazılmaz.

## 1. v2.0'da ne değişti

| | v1.1 (geçen hafta) | v2.0 (bu hafta) |
|---|---|---|
| Uyum | Sabit kural: seviye "yeni başlayan" → ipucu, "deneyimli" → 60 sn sayaç | Model: önceki sahnelerdeki **davranıştan** `p = P(riskli B seçimi)` tahmin eder; `p`'ye göre mod seçilir |
| Modlar | yok | **destek** (`p ≥ 0.60`: ipucu otomatik, tutor kendiliğinden soru sorar, sayaç kalkar), **normal** (v1), **meydan** (`p ≤ 0.25`: ipucu gizli, sonuçta "Neden?" notu) |
| Kapsam | 3 sahne | Model yalnız sahne 2-3'te; sahne 1 v1 davranışında |
| Artefakt | yok | `model/model.onnx` + `config.json` (sözleşme) + `README.md` (model kartı) |
| Veri | yok | `data/oturumlar.csv` (gerçek + sentetik), `?veri=1` toplama modu |
| Yayın | tek sürüm | `src/yayin.json` ile kontrollü açma: `golge`, `yuzde`, `model_taban` |

Geri uyumluluk: model yüklenemezse, sahne 1'de ya da `yuzde = 0` iken oyun **birebir v1** davranır. Geçen haftanın 8 karar yolu ve 5 kabul örneği bozulmaz (Cypress `primer.cy.js` değiştirilmedi).

## 2. Sürümleme: commit'e sabitlenmiş model

Tüketiciler modeli `main` dalından **indirmez**. `main` hareket eder; birisi repoya yeni bir model iterse yayındaki uygulama haberi olmadan farklı davranır. Bu, üretimdeki ML mühendisliğinin üç derdinden biri olan *Versioning* sorunudur (Shankar vd., 2022).

| Artefakt | Sürüm kimliği | Nerede |
|---|---|---|
| `model.onnx` + `config.json` | HF commit `⚠️ DOLDURULACAK <COMMIT_SHA>` | `https://huggingface.co/⚠️ <HF_KULLANICI>/<HF_REPO>/resolve/<COMMIT_SHA>/model.onnx` |
| Eğitim verisi | `config.json > veri.veri_sha256` | `data/oturumlar.csv` (git) |
| Uygulama | git etiketi `v2.0.0` | GitHub, GitHub Pages |
| Önceki sürüm (v1.1) | git commit `4d43e38` (etiket: `v1.1.0`) | GitHub |

Yayın tek komutla yapılır ve her adımı doğrular (`tools/hf_yayinla.py`): eval kapısı geçmemiş ya da `parite.json` başka bir modele ait ise durur; yükledikten sonra **sabit URL'den indirip SHA-256'yı yerel dosyayla karşılaştırır**; ancak o zaman `src/yayin.json > model_taban` değerini sabit URL'ye çevirir.

```bash
hf auth login                                                       # bir kez, Write token
python train.py                                                     # eval kapısı; geçmezse model/ yazılmaz
python tests/parite.py --yaz                                        # Oracle referanslarını yenile
python tools/hf_yayinla.py --repo <kullanici>/se-primer-akis-v2 --kuru   # önce plan
python tools/hf_yayinla.py --repo <kullanici>/se-primer-akis-v2
```

## 3. Yeni sürümü güvenle devreye alma

Yeni modeli herkese birden açmak yerine dört kapıdan geçiririz. Mekanizma uygulamadadır (`src/yayin.json`); kova numarası oturum kimliğinden türetilir (`kovaNo = ilk 8 hex % 100`), kimlik rastgele olduğundan kişiyle eşleşmez (KVKK) ve aşamalı geçişte gruplar **iç içe** kalır (5 ⊂ 25 ⊂ 50 ⊂ 100; `tests/yayin.test.mjs`).

| Aşama | `yayin.json` | Oyuncu ne görür | Ne ölçülür | Sonrakine geçiş kriteri |
|---|---|---|---|---|
| **0. Çevrimdışı kapı** | (yayın yok) | | `train.py`: AUC ≥ 0.70, Brier < taban, ONNX farkı ≤ 1e-4, ≥ 15 gerçek oturum | Kapı geçer |
| **1. Shadow** (Gölge) | `golge: true, yuzde: 100` | **v1** (model sessiz) | Model her sahne 2-3'te çalışır, `p` ve mod yalnız `console.info` / `data-cy="golge-p"` olarak oluşur. Müdahalesiz toplanan yeni gerçek oturumlarda `p` ile gözlenen seçim karşılaştırılır: `python tools/golge_degerlendir.py yeni.csv` | Eğitimde görülmemiş veride AUC ≥ 0.70, Brier < taban, ≥ 15 oturum; tarayıcıda hata yok |
| **2. Canary** (Kanarya) | `golge: false, yuzde: 5` | Oturumların %5'i modelin müdahalesini görür, %95'i v1 | Çökme / yükleme hatası, mod dağılımı, kanarya ile kontrol grubunun B oranı ve tamamlama farkı | Hata yok; mod dağılımı Shadow'dakiyle tutarlı; B oranı kontrolden **kötü değil** |
| **3. Aşamalı** (Progressive) | `yuzde: 25 → 50 → 100` | Giderek daha çok oturum | Canary ile aynı ölçütler her basamakta | Her basamakta kriterler korunur |

**Neden Shadow önce?** Model oyuncuya müdahale edince seçimler değişir; yalnız müdahalesiz oturumlar modelin tahmin kalitesini temiz ölçer. Canary ise müdahalenin *etkisini* ölçer: iki farklı soru, iki farklı aşama.

**Dürüst sınır.** Sunucumuz yok ve kimlik tutmayız; yayın ölçümleri gönüllülerin `?veri=1` CSV'leri ve `console.info` ile sınırlıdır. Bu ölçekte (onlarca oturum) %5 Canary yalnızca 0-2 oturum demektir. Bu nedenle bu projede Canary **istatistiksel A/B testi değil duman testidir** (çöküyor mu, yükleniyor mu); anlamlı bir A/B karşılaştırması için yüzlerce oturum gerekir. Ayrıca kova oturum başınadır; "Yeniden oyna" yeni kova çeker. Kalıcı kimlik tutmamak için bilinçli bir ödünleşimdir.

## 4. Geri alma planı (Rollback)

| Seviye | Ne zaman | Nasıl | Süre |
|---|---|---|---|
| **1. Anahtarı kapat** | Canary/aşamalı geçişte hata ya da kötü metrik | `src/yayin.json` → `"yuzde": 0`, commit + push (GitHub Pages dağıtır). Oyun v1'e döner; model **hiç indirilmez** | Pages dağıtım süresi (dakikalar) |
| **2. Önceki modele dön** | Yeni model kötü ama eski model iyiydi | `model_taban` → önceki commit'in sabit URL'si. HF'de commit'ler değişmez; eski URL her zaman aynı dosyayı verir | Aynı |
| **3. Kodu geri al** | Uygulama kodunda hata | `git revert <commit>` ya da `git checkout v1.1.0 -- src/`. v1.1 etiketi: `git tag v1.1.0 4d43e38` | Dakikalar |

Geri alma tetikleyicileri (önceden yazıldı): Shadow/Canary'de AUC < 0.70; model yükleme ya da çıkarım hatası; kanarya grubunun B oranının kontrolden belirgin kötü olması; model kartında "kullanılmaması gereken" bir kullanım görülmesi.

## 5. Mimari dağıtım kararı ve ödünleşim matrisi

**Karar: modeli tarayıcıda çalıştır (`onnxruntime-web`), dosyayı HF'den commit'e sabit URL ile indir.**

Üç adayı dersteki üç soruyla değerlendirdik:

| Soru | **Tarayıcı** (`onnxruntime-web`) ← seçilen | **Cihaz içi mobil** (React Native / Expo, gömülü ONNX) | **Kendi sunucu** (Render.com, Rails/FastAPI + `onnxruntime`) |
|---|---|---|---|
| **1. İnternet zorunlu mu, gecikme nasıl?** | İlk açılışta model ve çalışma zamanı (WASM) iner: ilk yükleme gecikmesi. Sonrasında çıkarım yerel ve ağsız. Servis işçisi yok, bu yüzden tamamen çevrimdışı açılış garanti değil | Çevrimdışı çalışır, ağ gecikmesi yok. Model APK ile gelir; güncelleme için yeni sürüm ya da uzaktan indirme gerekir | Her sahne için ağ turu. Ücretsiz katmanda hareketsizlik sonrası uyku ve soğuk başlangıç gecikmesi yaşanabilir. İnternet zorunlu |
| **2. Veri cihazdan çıkar mı?** (KVKK) | **Çıkmaz.** Süreler, seçimler, tutor sayıları yerelde kalır; ağdan yalnız model ve runtime dosyaları iner (CDN/HF bu isteklerden IP görür) | Çıkmaz | **Çıkar.** Davranış verisi sunucuya gider. Ad/e-posta yok ama bu davranışsal veridir: aydınlatma, saklama ve log politikası gerekir (başlangıç Rails örneği `inputs`'u log'dan süzer) |
| **3. Model gizli kalır mı?** | **Hayır.** `model.onnx` herkese açık; 7 katsayılı lojistik regresyon kolayca okunur. Bizim için sorun değil: eğitim amaçlı, hassas veriyle eğitilmedi, HF'de zaten public | Hayır; APK içinden çıkarılabilir | Dosya gizli kalır ama **istek-yanıt üzerinden tersine mühendislik (model extraction)** mümkündür: 7 özellikli doğrusal modelin katsayıları birkaç yüz sorguyla geri kazanılabilir. Kimlik doğrulama ve hız sınırı gerekir |
| Güncelleme / rollback hızı | `yayin.json` + Pages: dakikalar | Mağaza/APK dağıtımı yavaş | En hızlı: sunucuda anında |
| Gözlemlenebilirlik | En zayıf: gizlilik gereği merkezi telemetri yok | Zayıf | En iyi: merkezi log ve metrik |
| Maliyet / işletme | Ücretsiz statik barındırma, işletilecek sunucu yok | Ücretsiz; build/dağıtım yükü | Ücretsiz katman sınırlı; sunucu bakımı ve güvenliği bizde |

**Neden tarayıcı?** (i) Model 7 sayı alan, birkaç yüz baytlık bir lojistik regresyon; sunucu gereksiz karmaşıklık. (ii) Davranış verisi cihazdan çıkmıyor, KVKK riski en düşük seçenek bu. (iii) Gizlenecek bir model sırrı yok. (iv) Uygulama zaten mobil uyumlu bir web uygulaması; ek bir derleme hattı gerekmiyor. (v) Tamamen ücretsiz.

**Kabul ettiğimiz bedeller:** ilk yükleme gecikmesi (model yüklenemezse oyun v1 ile sürer), zayıf gözlemlenebilirlik (bu yüzden Shadow ve Canary çevrimdışı/gönüllü CSV'ye dayanır), model dosyasının herkese açık olması.

**Kararı ne zaman değiştirirdik?** Model hassas ya da kişisel veriyle eğitilirse ya da ticari sır olursa → sunucu (private HF/S3 + kimlik doğrulama + hız sınırı). Tam çevrimdışı kullanım gerekirse → cihaz içi mobil. Çok sayıda kullanıcıda gerçek A/B ölçümü gerekirse → sunucu tarafı telemetri (açık rıza ile).

**Yapılmadı:** Rails/FastAPI sunucu tüketicisi (bonus), Expo mobil tüketici. Tek ortamda uçtan uca çalıştırma koşulu web ile karşılandı.

## 6. ML test puanı ve yayına hazırlık özeti

Breck vd. (2017) ML Test Score rubriğinin dört başlığına göre elimizdekiler:

| Başlık | Yapılan | Eksik / sınır |
|---|---|---|
| Veri ve özellik | `tools/birlestir.py` şema + KVKK sütun denetimi; `data/SOZLUK.md`; JS ve Python özellik türetmenin ortak örnek dosyasıyla sınanması | Az sayıda tanıdık kişiden veri; dağılım kayması izlenmiyor |
| Model geliştirme | Eşik eğitimden önce yazıldı (`spec.md`), grup çapraz doğrulama, tabanla karşılaştırma, bootstrap güven aralığı, tekrarlanabilirlik testi | Küçük örneklem, geniş güven aralığı |
| Altyapı | Tek komutla eğitim, ONNX ↔ sklearn ≤ 1e-4, tarayıcı ↔ Python parite (Cypress), v1 regresyon testleri, rollback anahtarı | Cypress koşusu yalnız GitHub Actions'ta |
| İzleme | Shadow modu, `tools/golge_degerlendir.py` | Canlı otomatik izleme ve uyarı yok |

## 7. Kaynaklar

- Shankar vd. (2022), *Operationalizing Machine Learning: An Interview Study*: Velocity, Validation, Versioning (3V).
- Amershi vd. (2019), *Software Engineering for Machine Learning: A Case Study*: yaşayan ML yaşam döngüsü.
- Mitchell vd. (2019), *Model Cards for Model Reporting*: `model/README.md` biçimi.
- Breck vd. (2017), *The ML Test Score*: bölüm 6.
- Sommerville, *Software Engineering* (10. baskı): Bl. 8 (doğrulama ve geçerleme), Bl. 25 (konfigürasyon yönetimi).
- Hugging Face Hub belgeleri (`resolve/<revision>`), ONNX Runtime (`onnxruntime-web`).

> ⚠️ Bu belge yazılırken bu kaynakların **yalnız kavramsal çerçevesi** (3V, model kartı, test rubriği, V&V) kullanıldı; sayfa/bölüm düzeyinde alıntı yapılmadı. Teslimden önce kaynaklara inip bu bölümdeki atıfları kendi okumanla doğrulayın.

## 8. İlk eğitim denemesi başarısız oldu ve neden ölçüm düzenini değiştirdik

Kronoloji (git geçmişi kanıttır): `spec.md` eşikleri eğitimden önce yazıldı (9c12a51) → ilk gerçek veriyle `python train.py` koşuldu → kapı geçilemedi → ölçüm düzeni v2.1 olarak ikinci tur veriden ve yeniden eğitimden **önce** `spec.md`'ye yazıldı (687b0e0).

**Sonuç (v2.0 düzeni: 15 gerçek oturum, 30 modele girebilen satır, GroupKFold(5), eğitim katlarında 300 sentetik satır):**

| Metrik | Değer | Eşik |
|---|---|---|
| ROC-AUC (kat ortalaması) | **0.4533** | ≥ 0.70 → **kaldı** |
| Brier (model / taban) | 0.2638 / 0.2511 | model < taban → **kaldı** |

`model/` yazılmadı, hiçbir şey yayınlanmadı.

**Gözlemler (neden olduğu kanıtlanmış değil, olası açıklamalar):**
- Oyuncular sahneleri hızlı tıklayarak geçti: karar süresi medyanı 1.2 sn, okuma süresi medyanı 0.7 sn (okuma satırlarının %96'sı 2 sn altında). Tutor sorusu ve ipucu girdileri hiç kullanılmadı, yani 7 girdinin 2'si sabit 0.
- Sentetik üreticinin varsayımı ("uzun düşünen B seçer") gerçek veride ters yönde göründü (tek özellik AUC'si karar süresi için 0.32, okuma süresi için 0.15). 300 sentetik satır 30 gerçek satırı bastırdı.
- Aynı kişilerin art arda 5 oturumu bağımsız olmayabilir (merak için diğer seçeneği deneme). B oranı sahne sırasıyla 0.27 → 0.40 → 0.53 yükseldi.

**Bilerek yapmadığımız şey.** Başarısız sonucu gördükten sonra sentetik veriyi çıkarıp aynı 15 oturumda yeniden ölçmek AUC 0.785 verdi (güven aralığı 0.45–0.88, n = 30). Bu sayıyı **yayın gerekçesi olarak kullanmadık**: sonucu görüp ayar yaptığımız için iyimserdir ve aralık 0.5'i içerir. Eşikler (0.70, Brier < taban, 1e-4, 15 oturum) hiçbir zaman gevşetilmedi.

**Karar (spec v2.1).** (1) Sentetik veri eğitimden çıkarıldı (yönü gerçekle çelişiyor). (2) Birinci tur veri **geliştirme seti** sayıldı. (3) Kapı, birinci turdakilerden farklı kişilerin ikinci tur oturumlarından oluşan **tutulan sette** ölçülür; set tek kullanımlıktır. (4) Veri toplama yönergesi ve dışlama kuralı sonucu görmeden yazıldı. İkinci turun sonucu bu bölümün altına olduğu gibi eklenecektir (geçse de kalsa da).

**İkinci tur sonucu:** ⚠️ DOLDURULACAK (ikinci tur veri toplandıktan ve `python train.py` koşulduktan sonra).
