/**
 * SE Primer v2: davranış kaydı ve model özellik vektörü.
 * Saf fonksiyonlar. DOM'a dokunmaz; Node'da test edilebilir.
 * Tek doğruluk kaynağı: hem veri toplama (CSV) hem model girdisi buradan çıkar.
 * Python tarafındaki karşılığı: train.py > ozellik_uret() (tests/ozellik_ornekleri.json ile doğrulanır).
 */

// CSV sütunları (data/SOZLUK.md ile aynı sıra). Her karar = bir satır.
export const KOLONLAR = [
  'oturum_id', 'kaynak', 'sahne_no', 'seviye',
  'karar_suresi_sn', 'okuma_suresi_sn', 'tutor_soru_sayisi', 'ipucu_acildi',
  'secim', 'sure_doldu', 'secim_b',
];

// Modelin girdileri. Sıra = model/config.json "features" sırası (sözleşme).
export const OZELLIKLER = [
  'sahne_no', 'seviye',
  'onceki_karar_suresi_sn', 'onceki_okuma_suresi_sn',
  'onceki_tutor_soru_sayisi', 'onceki_ipucu_acildi', 'onceki_b_sayisi',
];

export const yuvarla = (x) => Math.round(x * 10) / 10;

// Üst sınırlar. train.py > KIRPMA ile AYNI olmalı (eğitim ve çıkarım aynı girdiyi görsün).
export const KIRPMA = {
  onceki_karar_suresi_sn: 120,
  onceki_okuma_suresi_sn: 120,
  onceki_tutor_soru_sayisi: 10,
};

/** Rastgele 12 hex karakterlik oturum kimliği. Cihaz/kişi bilgisi içermez. */
export function yeniOturumId() {
  const b = new Uint8Array(6);
  const c = globalThis.crypto;
  if (c && c.getRandomValues) c.getRandomValues(b);
  else for (let i = 0; i < b.length; i++) b[i] = Math.floor(Math.random() * 256);
  return Array.from(b, (x) => x.toString(16).padStart(2, '0')).join('');
}

/** Tamamlanmış bir kararın satırı. Süreler 0.1 sn'ye yuvarlanır. */
export function satirOlustur({ oturumId, kaynak = 'gercek', sahneNo, seviye, kararSn, okumaSn, tutorSoru, ipucu, secim, sureDoldu }) {
  return {
    oturum_id: oturumId,
    kaynak,
    sahne_no: sahneNo,
    seviye,
    karar_suresi_sn: yuvarla(kararSn),
    okuma_suresi_sn: yuvarla(okumaSn),
    tutor_soru_sayisi: tutorSoru,
    ipucu_acildi: ipucu,
    secim,
    sure_doldu: sureDoldu,
    secim_b: secim === 'B' ? 1 : 0,
  };
}

export function csvUret(satirlar) {
  const govde = satirlar.map((s) => KOLONLAR.map((k) => s[k]).join(','));
  return [KOLONLAR.join(','), ...govde].join('\n') + '\n';
}

/**
 * Bir sahne başlamadan önce model girdisini üretir.
 * @param {object[]} oturumSatirlari  bu oturumun tamamlanmış satırları
 * @param {number} sahneNo            şimdi başlayacak sahne (1-3)
 * @param {number} seviye             0 yeni başlayan, 1 deneyimli
 * @returns {number[]|null} OZELLIKLER sırasında vektör; sahne 1'de null (model çalışmaz)
 */
export function ozellikVektoru(oturumSatirlari, sahneNo, seviye) {
  if (sahneNo < 2) return null;
  const onceki = oturumSatirlari.find((s) => s.sahne_no === sahneNo - 1);
  if (!onceki) return null;
  const bSayisi = oturumSatirlari.filter((s) => s.sahne_no < sahneNo && s.secim === 'B').length;
  return [
    sahneNo, seviye,
    Math.min(onceki.karar_suresi_sn, KIRPMA.onceki_karar_suresi_sn),
    Math.min(onceki.okuma_suresi_sn, KIRPMA.onceki_okuma_suresi_sn),
    Math.min(onceki.tutor_soru_sayisi, KIRPMA.onceki_tutor_soru_sayisi),
    onceki.ipucu_acildi,
    bSayisi,
  ];
}

/** Olasılığı oyun moduna çevirir. Eşikler config.json'dan gelir (spec.md). */
export function modSec(p, esikDestek = 0.60, esikMeydan = 0.25) {
  if (p === null || p === undefined || Number.isNaN(p)) return 'normal';
  if (p >= esikDestek) return 'destek';
  if (p <= esikMeydan) return 'meydan';
  return 'normal';
}
