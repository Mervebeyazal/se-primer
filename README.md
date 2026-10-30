# SE Primer · YZM301 — Yazılım Test ve Gerçekleme

**Etkileşimli mühendislik karar simülasyonu.** Sağlık randevu sistemi arızasında üç karar (mimari, test, KVKK), iki son, rol/seviye/hedef uyarlaması, her karardan sonra teknik açıklama ve cevap vermeyen Sokratik tutor.

> **Durum (30.10.2026):** Bağımlılıksız çalışan uygulama hazır. Gerçek Chromium davranış testi: 8/8 karar yolu ve 2 ek kontrol **geçti**. Kural tabanlı tutor: 20/20 girdide tanımlı cevap sızdırma kalıbı görülmedi. **Yeni `se-primer` deposunun `main` dalında Cypress 11/11 geçti ve video kanıtı üretildi.** Google Stitch projesi ve Google AI Studio yayını henüz yapılmadı. Bu ayrım teslim kanıtları için önemlidir.

## Hızlı çalıştırma

Node veya npm **gerekmez**. `index.html` ES modules kullandığı için yerel HTTP sunucu üzerinden açın:

```bash
python3 -m http.server 5173
```

Tarayıcı: http://localhost:5173 (telefon ile aynı ağda makinenin IP'si üzerinden açılabilir; ağ kuralları geçerli). `index.html` dosyasını doğrudan `file://` ile açmak ES module kısıtlarına takılabilir.

## Değerlendirme / test komutları

```bash
node tests/tutor-eval.mjs  # 20 gerçek kural tabanlı tutor yanıtını ve oranı üretir
npm install                # yalnızca Cypress testleri için, ağ bağlantısı gerekir
npm run test:e2e           # başka terminalde sunucu açıkken
```

Cypress testleri `cypress/e2e/primer.cy.js` dosyasında 8 karar yolunu ve kritik davranışları kapsar. `cypress.config.js` test videosunu açar. CI iş akışı `.github/workflows/ci.yml` içindedir. **Yeni depoda doğrulanmış Cypress koşusu: 11/11 başarılı.** [GitHub Actions kanıtı](https://github.com/Mervebeyazal/se-primer/actions/runs/41011390943). Video ve varsa ekran görüntüleri bu koşunun `se-primer-cypress-evidence` adlı artefaktında yer alır.

## Kanıtlar

- Spesifikasyon, kapsam, 5 kabul örneği ve akış: [`spec.md`](spec.md)
- Üç mobil ekran, tasarım ilkeleri ve Stitch aktarım promptu: [`DESIGN.md`](DESIGN.md), [`docs/STITCH_BRIEF.md`](docs/STITCH_BRIEF.md)
- Tutor 20 gerçek çıktı, hata sınıfları, oran: [`docs/tutor-eval.md`](docs/tutor-eval.md)
- Gerçek tarayıcı kontrol senaryoları: [`tests_browser.py`](tests_browser.py), [`evidence/browser-checks.json`](evidence/browser-checks.json)
- Üç mobil ekran tasarım önizlemesi (Stitch üzerinde üretilmedi): [`design/01-intro.svg`](design/01-intro.jpg), [`design/02-scene.svg`](design/02-scene.jpg), [`design/03-end.svg`](design/03-ending.jpg)
- Google AI Studio'ya aktarım açıklaması: [`docs/AI_STUDIO_BRIEF.md`](docs/AI_STUDIO_BRIEF.md)
- 60 saniyelik oynanış videosu: teslim ZIP’inde `SE_Primer_60s_Oynanis_Demosu.mp4` (gerçek etkileşim kaydı) bulunur. Ayrıca `SE_Primer_60s_Demo.mp4` (ekran görüntüsü sunumu) içerir. **Cypress koşusu kaydı** ise GitHub Actions kanıt artefaktındadır.

## Ürün kararı: kapsam dışı üç özellik

1. **Kullanıcı hesabı eklemedik**, çünkü tek oturumluk öğrenme akışında gereksiz kayıt zorunluluğu sürtünme yaratır.
2. **İkinci senaryo eklemedik**, çünkü mevcut sağlık vakasının sekiz karar yolunun tamamını test etmek önceliklidir.
3. **Gerçek hasta verisi kullanmadık**, çünkü sentetik vaka eğitim hedefini sağlar ve kişisel veri riskini doğurmaz.

## Teknik tasarım

- `src/main.js`: vanilla JavaScript, ES modules, DOM tabanlı durum makinesi ve sayaç.
- `src/tutor.mjs`: çevrimdışı deterministik sorular, kullanıcı metni sunucuya gönderilmez.
- `src/style.css`: 390px mobil öncelikli CSS, rol ve hedefe duyarlı sahne.
- `tests/tutor-eval.mjs`: 20 senaryonun yeniden üretilebilir kontrolü.

### Yapılmadı (dürüst teslim sınırı)

- **Üretken AI tutor:** Mevcut tutor bir LLM değil. Google AI Studio/Gemini entegrasyonu ve orada yayımlama yapılmadı.
- **Google Stitch:** Üç mobil ekran için SVG önizleme oluşturuldu; Stitch üzerinde bağımsız proje oluşturulmadı.
- **Cypress yürütme kanıtı:** Yerel ortamda Cypress binary yüklenemese de GitHub Actions koşusu doğrulandı: **11/11 test başarılı**. Ayrıca Chromium + Playwright ile 10 davranış kontrolü geçildi.

## Teslim bağlantıları

- GitHub kaynak: `https://github.com/Mervebeyazal/se-primer`.
- Google AI Studio: **Henüz yayımlanmadı**.
- Demo video: ZIP içinde, oynanış kaydı ve ekran görüntüsü sunumu mevcuttur. GitHub Actions içinde Cypress videosu ayrıca oluşturuldu; harici paylaşım bağlantısı **henüz hazırlanmadı**.

### Referanslar

Ders PDF'i: *SE Primer — YZM301*, 2026. Cypress docs: https://docs.cypress.io. Kişisel Verilerin Korunması Kanunu: https://www.kvkk.gov.tr.

## Teslim doğrulama tablosu (30 Ekim 2026)

| Kriter | Durum | Kanıt |
|---|---|---|
| Spec, 5 kabul örneği, akış | Hazır | `spec.md` |
| Tasarım, 3 mobil ekran | Hazır (Stitch bağlantısı eksik) | `DESIGN.md`, `design/` |
| Çalışan uygulama | Yerel doğrulandı (AI Studio bağlantısı eksik) | `index.html`, `src/` ve Chromium doğrulamaları |
| Tutor eval 20 çıktı, hata oranı | Hazır (kural tabanlı tutor) | `docs/tutor-eval.md` |
| Cypress tüm yollar | Başarılı, 11/11 | [CI kanıtı](https://github.com/Mervebeyazal/se-primer/actions/runs/41011390943) |
| 60 sn demo | Hazır | ZIP içindeki `SE_Primer_60s_Oynanis_Demosu.mp4` |
| Ürün kararı 3 özellik | Hazır | Bu README |