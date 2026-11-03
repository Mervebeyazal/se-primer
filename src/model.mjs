/**
 * SE Primer v2: tarayıcıda ONNX çıkarımı (onnxruntime-web).
 * `ort` global olarak index.html'deki <script> ile gelir; yüklenemezse (çevrimdışı) hata fırlatılır ve
 * oyun v1 davranışıyla (normal mod) sürer. Oyun asla modele bağımlı olarak kilitlenmez.
 */
export const ORT_SURUM = '1.22.0';
export const ORT_WASM_YOLU = `https://cdn.jsdelivr.net/npm/onnxruntime-web@${ORT_SURUM}/dist/`;

/**
 * Yayın yapılandırması (src/yayin.json). Kodu değiştirmeden sürümü açıp kapatmayı sağlar:
 *   model_taban : modelin indirildiği klasör. Yayında HF'deki COMMIT'e SABİTLENMİŞ URL (…/resolve/<commit>/).
 *   yuzde       : 0-100. Oturumların bu yüzdesi modeli kullanır (Canary %5, Aşamalı %25 → %50 → %100). 0 = kapalı (rollback).
 *   golge       : true ise model çalışır ama oyunun davranışını DEĞİŞTİRMEZ (Shadow Deployment); p yalnız karşılaştırma içindir.
 */
export const YAYIN_VARSAYILAN = { model_taban: './model/', yuzde: 100, golge: false };

export async function yayinOku(getir = globalThis.fetch) {
  try {
    const r = await getir('./src/yayin.json', { cache: 'no-store' });
    if (!r.ok) throw new Error('yayin.json yok');
    return { ...YAYIN_VARSAYILAN, ...(await r.json()) };
  } catch (e) {
    return { ...YAYIN_VARSAYILAN };
  }
}

/**
 * Oturum kimliğinden 0-99 arası sabit kova. Kimlik rastgele olduğundan kovalar eşit dağılır ve kişiyle eşleşmez (KVKK).
 * Aşamalı geçişte kova < yuzde olanlar modeli alır; yuzde arttıkça önceki gruplar içeride KALIR (5 ⊂ 25 ⊂ 50 ⊂ 100).
 * Not: kova oturum başınadır; "Yeniden oyna" yeni kova çeker (kalıcı kimlik tutmamak için bilinçli ödünleşim).
 */
export const kovaNo = (oturumId) => parseInt(oturumId.slice(0, 8), 16) % 100;
export const kovadaMi = (oturumId, yuzde) => kovaNo(oturumId) < yuzde;

/** Model klasörü. Varsayılan yayin.json > model_taban. Test için ?modelBase=... ile değiştirilebilir. */
export function tabanBelirle(arama, varsayilan = './model/') {
  const v = new URLSearchParams(arama).get('modelBase');
  if (!v) return varsayilan;
  return v.endsWith('/') ? v : v + '/';
}

/** ?p=0.72 test kancası: modeli atlayıp olasılığı sabitler (kabul örnekleri 6-7). */
export function pKancasi(arama) {
  const v = new URLSearchParams(arama).get('p');
  if (v === null) return null;
  const p = parseFloat(v);
  return Number.isNaN(p) ? null : Math.min(1, Math.max(0, p));
}

export async function modelYukle(taban, ortam = globalThis) {
  const ort = ortam.ort;
  if (!ort) throw new Error('onnxruntime-web yüklenemedi');
  ort.env.wasm.wasmPaths = ORT_WASM_YOLU;
  ort.env.wasm.numThreads = 1; // SharedArrayBuffer / çapraz kaynak yalıtımı gerektirmesin
  const config = await (await fetch(taban + 'config.json', { cache: 'no-store' })).json();
  const oturum = await ort.InferenceSession.create(taban + 'model.onnx');
  return {
    config,
    taban,
    /** vektor: config.features sırasında 7 sayı -> P(B) */
    async tahmin(vektor) {
      if (vektor.length !== config.features.length) throw new Error('özellik sayısı uyuşmuyor');
      const x = new ort.Tensor('float32', Float32Array.from(vektor), [1, vektor.length]);
      const cikti = await oturum.run({ input: x });
      const i = config.classes.indexOf(config.positive_class || '1');
      return Number(cikti.probabilities.data[i]);
    },
  };
}
