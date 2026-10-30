# SE Primer — Mobil Arayüz Tasarım Belgesi

## Tasarım amacı

390 px mobil ekranı öncelik alan bir eğitim uygulaması. Kullanıcı bir mühendislik krizinde yön bulur, karar verir, seçimin nedenini ve sonucunu görür. Tasarım büyük tekil çağrılar, kısa metin blokları ve belirgin ilerleme çubuğu kullanır.

## Üç ekran ve kanıt

| Ekran | Görsel | İşlev |
|---|---|---|
| 1. Giriş | `design/01-intro.jpg` | Senaryo + seviye, rol, hedef + başlat |
| 2. Sahne | `design/02-scene.jpg` | İlerleme, iki seçenek, tutor sorusu, ipucu ve teknik geri bildirim |
| 3. Son | `design/03-ending.jpg` | İyi/kötü son, 3 adımlı karar günlüğü, yeniden oyna |

> Görseller uygulamanın gerçek Chromium ekran görüntüleridir. **Google Stitch tarafından üretildiği iddia edilmez.** Stitch'e yeniden çizim için `docs/STITCH_BRIEF.md` kullanılabilir.

## Görsel sistem

- Arka plan: `#080e1b`; kart: `#131f31`; ikinci yüzey: `#19283a`
- Birincil aksan: `#d5fa91`; ikincil: `#a9f1d6`; gövde metni: `#a9b8cb`
- Tipografi: DM Sans, Space Grotesk (erişilemezse sistem sans)
- Ana kart: `23px` radius, seçenek: `12px` radius; buton yüksekliği dokunmaya uygundur
- Arayüzde ilerleme çubuğu, klavye `focus-visible` ve azaltılmış hareket tercihi desteklenir

## Etkileşim ve kişiselleştirme

- **Yeni başlayan:** ipucunu otomatik gösterir.
- **Deneyimli:** karar başına 60 saniye sayacı; süre dolduğunda B seçimi uygulanır, neden açıklanır.
- **Rol:** anlatı girişinde yazılım geliştirici / test mühendisi / teknik lider kullanılır.
- **Hedef:** karar ekranında test, güvenlik veya mimari odağı gösterilir.
- **Tutor:** serbest kullanıcı metnine önceden tanımlı, Sokratik bir soru üretir; kişisel veriler sunucuya gitmez.

## Stitch teslim sınırı

Stitch bağlantısı oluşturulamadığı için bu belge ve üç tasarım görseli tam bir Stitch proje kanıtının yerine **geçmez**. İlgili yönergeler `docs/STITCH_BRIEF.md` içindedir.
