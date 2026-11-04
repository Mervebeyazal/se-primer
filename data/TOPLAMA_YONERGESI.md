# Veri toplama yönergesi (2. tur: tutulan doğrulama seti)

Bu metni arkadaşlarına olduğu gibi gönderebilirsin. Kurallar `spec.md` > v2.1'de sonucu görmeden yazılmıştır.

## Kimden?
- Birinci turda oynamamış **yeni kişiler** (en az 8 kişi). Birinci turdaki 3 kişi bu sete giremez.
- Kişi başı **en fazla 2 oturum** (toplam en az 15 oturum).

## Linki gönder
`https://mervebeyazal.github.io/se-primer/?veri=1`

## Arkadaşına söyleyeceklerin
> Bu bir ders ödevi için küçük bir simülasyon. Hasta randevu sistemi bozulmuş, 3 karar vereceksin. Doğru ya da yanlış cevap yok, **gerçekte ne yapacaksan onu seç**.
> - Senaryoyu ve seçeneklerin açıklamasını **oku**, sonra normal hızında karar ver (bir karar için 10-30 saniye normaldir).
> - Merak için diğer seçeneği deneme. Tekrar oynarsan yine gerçekten yapacağını seç.
> - İpucu ve tutor isteğe bağlı: merak edersen kullan, etmezsen kullanma.
> - Bitince ekrandaki **CSV İNDİR** düğmesine bas ve dosyayı bana gönder. Dosyada ad, e-posta, konum gibi kişisel bilgi yok; yalnız süreler ve A/B seçimleri var.

## Gelen dosyaları ekleme
```bash
python tools/birlestir.py --dogrulama gelen3.csv gelen4.csv
python tools/birlestir.py --kontrol      # ≥15 oturum, iki set ayrık mı
```

## Yapılmaması gerekenler (kapıyı geçmek için veriyi "düzeltmek" olur)
- Sonucu (AUC) görüp oturum çıkarma/ekleme. Tek dışlama: 3 sahnesi de kaydedilmemiş eksik oturum.
- Aynı kişiye birden çok CSV yeniden oynatma. Kişi başı en fazla 2 oturum.
- Doğrulama setiyle `train.py` koştuktan sonra özellik/model/eşik değiştirip yeniden denemek (set tek kullanımlıktır).
