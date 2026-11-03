#!/usr/bin/env python3
"""SE Primer v2: "Akış Modeli" için tekrarlanabilir eğitim + eval kapısı.

Tek komut:   python train.py
Ne yapar:    data/oturumlar.csv  ->  doğrulama (kapı)  ->  model/model.onnx + model/config.json + model/README.md

KAPI: spec.md'deki kabul eşikleri sağlanmazsa betik hata koduyla durur ve model/ altına HİÇBİR ŞEY yazmaz.
Aynı veri + aynı tohum (13) = birebir aynı metrikler, aynı config.json, aynı model.onnx (başka makinede de).

--deneme: Gerçek oturum yokken hattı denemek içindir. Değerlendirmeyi sentetik veride yapar, çıktıyı
          _out/deneme/ altına yazar. Bu çıktı YAYINLANAMAZ; model/ klasörüne dokunulmaz.
"""
import argparse
import hashlib
import json
import platform
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, roc_auc_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

# ============================================================================================
# KABUL EŞİKLERİ: spec.md > "Eval metriği ve kabul eşiği" ile AYNI. Eğitimden önce yazıldı;
# eğitimden sonra değiştirilemez (değişirse gerekçesi RELEASE.md'de belgelenir).
# ============================================================================================
SEED = 13                 # proje kuralı: her yerde 13
ESIK_AUC = 0.70           # 5 katlı grup çapraz doğrulama, ROC-AUC ortalaması >=
MIN_GERCEK_OTURUM = 15    # değerlendirmede en az bu kadar gerçek oturum
ONNX_TOLERANS = 1e-4      # ONNX ile sklearn arası en büyük olasılık farkı <=
ESIK_DESTEK = 0.60        # p >= bu  -> destek modu
ESIK_MEYDAN = 0.25        # p <= bu  -> meydan modu
N_KAT = 5
MIN_GECERLI_KAT = 3       # AUC'si tanımlı (iki sınıf da var) en az kaç kat gerekir

BURASI = Path(__file__).resolve().parent
VERI = BURASI / "data" / "oturumlar.csv"
MODEL_DIR = BURASI / "model"
DENEME_DIR = BURASI / "_out" / "deneme"

# Model girdileri. Sıra = config.json "features" sırası = src/telemetry.mjs > OZELLIKLER.
OZELLIKLER = ["sahne_no", "seviye", "onceki_karar_suresi_sn", "onceki_okuma_suresi_sn",
              "onceki_tutor_soru_sayisi", "onceki_ipucu_acildi", "onceki_b_sayisi"]
ETIKETLER = {
    "sahne_no": ("Sahne no", "1-3 (model 2 ve 3'te çalışır)"),
    "seviye": ("Seviye", "0 yeni başlayan, 1 deneyimli"),
    "onceki_karar_suresi_sn": ("Önceki karar süresi", "sn"),
    "onceki_okuma_suresi_sn": ("Önceki sonucu okuma süresi", "sn"),
    "onceki_tutor_soru_sayisi": ("Önceki sahnede tutora sorulan soru", "adet"),
    "onceki_ipucu_acildi": ("Önceki sahnede ipucu açıldı mı", "0/1"),
    "onceki_b_sayisi": ("Şimdiye kadarki riskli (B) seçim", "adet"),
}
# src/telemetry.mjs > KIRPMA ile AYNI olmalı.
KIRPMA = {"onceki_karar_suresi_sn": 120.0, "onceki_okuma_suresi_sn": 120.0, "onceki_tutor_soru_sayisi": 10.0}
REFERANS_ORNEK = {"sahne_no": 2, "seviye": 0, "onceki_karar_suresi_sn": 15.0, "onceki_okuma_suresi_sn": 8.0,
                  "onceki_tutor_soru_sayisi": 1, "onceki_ipucu_acildi": 0, "onceki_b_sayisi": 0}


# --------------------------------------------------------------------------- veri
def ozellik_uret(veri: pd.DataFrame) -> pd.DataFrame:
    """Satır başına karar -> model girdisi. Tanım: data/SOZLUK.md. JS karşılığı: telemetry.mjs > ozellikVektoru."""
    d = veri.sort_values(["kaynak", "oturum_id", "sahne_no"]).reset_index(drop=True)
    g = d.groupby(["kaynak", "oturum_id"], sort=False)
    onceki_sahne = g["sahne_no"].shift(1)
    d["onceki_karar_suresi_sn"] = g["karar_suresi_sn"].shift(1)
    d["onceki_okuma_suresi_sn"] = g["okuma_suresi_sn"].shift(1)
    d["onceki_tutor_soru_sayisi"] = g["tutor_soru_sayisi"].shift(1)
    d["onceki_ipucu_acildi"] = g["ipucu_acildi"].shift(1)
    d["onceki_b_sayisi"] = g["secim_b"].cumsum() - d["secim_b"]
    # Yalnız hemen önceki sahnesi kaydı olan satırlar (eksik oturumlarda kayma olmasın). Sahne 1 modele girmez.
    d = d[(d["sahne_no"] >= 2) & (onceki_sahne == d["sahne_no"] - 1)].copy()
    for kolon, ust in KIRPMA.items():
        d[kolon] = d[kolon].clip(upper=ust)
    d[OZELLIKLER] = d[OZELLIKLER].astype("float64")
    return d[["oturum_id", "kaynak"] + OZELLIKLER + ["secim_b"]].reset_index(drop=True)


def veri_yukle(yol: Path):
    if not yol.exists():
        sys.exit(f"✗ {yol} yok. Önce veri üretin (README.md > Veri).")
    ham = pd.read_csv(yol)
    return ham, ozellik_uret(ham), hashlib.sha256(yol.read_bytes()).hexdigest()


# --------------------------------------------------------------------------- model
def model_kur():
    return Pipeline([("olcek", StandardScaler()), ("lr", LogisticRegression(random_state=SEED, max_iter=1000))])


def bootstrap_ga95(y, p, gruplar, n=1000):
    """Oturum bazlı bootstrap ile havuzlanmış AUC'nin %95 güven aralığı (az veriyle belirsizliği göstermek için)."""
    rng = np.random.RandomState(SEED)
    idler = np.unique(gruplar)
    satirlar = {g: np.where(gruplar == g)[0] for g in idler}
    aucler = []
    for _ in range(n):
        secilen = rng.choice(idler, size=len(idler), replace=True)
        ix = np.concatenate([satirlar[g] for g in secilen])
        if len(set(y[ix])) == 2:
            aucler.append(roc_auc_score(y[ix], p[ix]))
    return [round(float(np.percentile(aucler, 2.5)), 4), round(float(np.percentile(aucler, 97.5)), 4)]


def degerlendir(olcum: pd.DataFrame, ek_egitim: pd.DataFrame) -> dict:
    """GroupKFold(5), grup = oturum. `olcum` satırları yalnız test katında; `ek_egitim` yalnız eğitim katlarında."""
    oof = np.full(len(olcum), np.nan)
    taban = np.full(len(olcum), np.nan)
    kat_auc = []
    for tr, te in GroupKFold(n_splits=N_KAT).split(olcum, groups=olcum["oturum_id"]):
        egitim = pd.concat([olcum.iloc[tr], ek_egitim], ignore_index=True)
        m = model_kur().fit(egitim[OZELLIKLER], egitim["secim_b"])
        p = m.predict_proba(olcum.iloc[te][OZELLIKLER])[:, 1]
        oof[te] = p
        taban[te] = egitim["secim_b"].mean()
        y_te = olcum.iloc[te]["secim_b"].to_numpy()
        kat_auc.append(float(roc_auc_score(y_te, p)) if len(set(y_te)) == 2 else None)

    y = olcum["secim_b"].to_numpy()
    gecerli = [a for a in kat_auc if a is not None]
    mod_dagilimi = {}
    for ad, maske in (("destek", oof >= ESIK_DESTEK), ("normal", (oof > ESIK_MEYDAN) & (oof < ESIK_DESTEK)),
                      ("meydan", oof <= ESIK_MEYDAN)):
        mod_dagilimi[ad] = {"n": int(maske.sum()), "b_orani": round(float(y[maske].mean()), 4) if maske.any() else None}
    return {
        "auc_ortalama": round(float(np.mean(gecerli)), 4) if gecerli else None,
        "auc_kat": [None if a is None else round(a, 4) for a in kat_auc],
        "gecerli_kat": len(gecerli),
        "auc_havuz": round(float(roc_auc_score(y, oof)), 4),
        "auc_havuz_ga95": bootstrap_ga95(y, oof, olcum["oturum_id"].to_numpy()),
        "brier_model": round(float(brier_score_loss(y, oof)), 4),
        "brier_taban": round(float(brier_score_loss(y, taban)), 4),
        "taban_orani_b": round(float(y.mean()), 4),
        "mod_dagilimi": mod_dagilimi,
    }


def kapi(metrik: dict, olcum: pd.DataFrame) -> list:
    """Kabul eşikleri. Boş liste = geçti."""
    hatalar = []
    n_oturum = olcum["oturum_id"].nunique()
    if n_oturum < MIN_GERCEK_OTURUM:
        hatalar.append(f"değerlendirmede {n_oturum} oturum var; en az {MIN_GERCEK_OTURUM} gerekli")
    if metrik["gecerli_kat"] < MIN_GECERLI_KAT:
        hatalar.append(f"AUC'si tanımlı kat sayısı {metrik['gecerli_kat']} < {MIN_GECERLI_KAT} (kat başına iki sınıf da gerekir)")
    elif metrik["auc_ortalama"] < ESIK_AUC:
        hatalar.append(f"AUC {metrik['auc_ortalama']:.4f} < eşik {ESIK_AUC}")
    if not metrik["brier_model"] < metrik["brier_taban"]:
        hatalar.append(f"Brier {metrik['brier_model']:.4f} tabandan ({metrik['brier_taban']:.4f}) iyi değil")
    return hatalar


# --------------------------------------------------------------------------- artefakt
def onnx_aktar(model, X: pd.DataFrame, hedef: Path) -> float:
    """sklearn -> ONNX. Girdi 'input' float32 [n, 7]; çıktı 'probabilities' [n, 2] (zipmap kapalı)."""
    import onnxruntime as ort
    from skl2onnx import to_onnx
    from skl2onnx.common.data_types import FloatTensorType

    onx = to_onnx(model, initial_types=[("input", FloatTensorType([None, X.shape[1]]))],
                  options={id(model): {"zipmap": False}}, target_opset=17)
    yol = hedef / "model.onnx"
    yol.write_bytes(onx.SerializeToString())
    oturum = ort.InferenceSession(str(yol), providers=["CPUExecutionProvider"])
    p_onnx = oturum.run(["probabilities"], {"input": X.to_numpy(np.float32)})[0]
    fark = float(np.abs(p_onnx - model.predict_proba(X.astype(np.float32).astype(np.float64))).max())
    return fark


def config_yaz(hedef: Path, metrik: dict, onnx_fark: float, veri_ozet: dict, deneme: bool, kapi_gecti: bool):
    import onnxruntime
    import skl2onnx
    config = {
        "title": "SE Primer v2: Akış Modeli",
        "description": "Bir sahne başlamadan önce oyuncunun riskli (B) seçeneği seçme olasılığını önceki sahnelerdeki "
                       "davranışından tahmin eder. Olasılık, tutorun müdahale modunu (destek / normal / meydan) belirler.",
        "target": "secim_b",
        "positive_class": "1",
        "classes": ["0", "1"],
        "class_labels": {"0": "A (kontrollü seçim)", "1": "B (riskli seçim)"},
        "features": [{"name": k, "label": ETIKETLER[k][0], "unit": ETIKETLER[k][1], "example": REFERANS_ORNEK[k]}
                     for k in OZELLIKLER],
        "esik_destek": ESIK_DESTEK,
        "esik_meydan": ESIK_MEYDAN,
        "kabul_esigi": {"auc_min": ESIK_AUC, "brier": "model < taban", "min_gercek_oturum": MIN_GERCEK_OTURUM,
                        "onnx_tolerans": ONNX_TOLERANS, "dogrulama": f"GroupKFold({N_KAT}), grup=oturum_id"},
        "metrics": metrik,
        "onnx_maks_fark": float(f"{onnx_fark:.3e}"),
        "veri": veri_ozet,
        "deneme": deneme,
        "kapi_gecti": kapi_gecti,
        "seed": SEED,
        "sklearn_version": sklearn.__version__,
        "skl2onnx_version": skl2onnx.__version__,
        "onnxruntime_version": onnxruntime.__version__,
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}",
    }
    (hedef / "config.json").write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return config


def model_karti(c: dict) -> str:
    m, v = c["metrics"], c["veri"]
    ga = m["auc_havuz_ga95"]
    dagilim = "\n".join(f"| {ad} | {d['n']} | {'-' if d['b_orani'] is None else d['b_orani']} |"
                        for ad, d in m["mod_dagilimi"].items())
    uyari = (f"\n> ⚠️ **DENEME ÇIKTISI.** Değerlendirme sentetik veride yapıldı, eval kapısı {'geçti' if c['kapi_gecti'] else 'GEÇİLEMEDİ'}; bu model yayınlanamaz.\n"
             if c["deneme"] else "")
    return f"""---
library_name: sklearn
tags:
- onnx
- tabular-classification
- sklearn
- education
pipeline_tag: tabular-classification
---

# {c["title"]}
{uyari}
{c["description"]}

## Amaç
SE Primer (yazılım mühendisliği kriz simülasyonu) her sahneden önce bu modeli tarayıcıda çalıştırır.
Olasılık `p` yüksekse oyuncuya **destek** (ipucu otomatik açılır, tutor soru sorar, süre baskısı kalkar),
düşükse **meydan okuma** (ipucu gizlenir, "Neden?" notu eklenir), arada **normal** akış uygulanır.
Eşikler: destek `p ≥ {c["esik_destek"]}`, meydan `p ≤ {c["esik_meydan"]}` (`config.json`).

## Model
`Pipeline(StandardScaler → LogisticRegression)`, tohum {c["seed"]}. Girdi 7 sayı (sıra ve birimler `config.json` → `features`):
{", ".join(f"`{f['name']}`" for f in c["features"])}.
Çıktı: `probabilities` `[n, 2]`; sınıf 1 = riskli B seçimi. Eğitim: Python {c["python_version"]}, scikit-learn {c["sklearn_version"]}, skl2onnx {c["skl2onnx_version"]}.

## Veri
- Kaynak: SE Primer veri toplama modu. Gerçek oturumlar tanıdık kişilerden, rastgele oturum kimliğiyle toplandı; ad, e-posta, cihaz kimliği, konum ve serbest metin **yoktur**.
- Değerlendirmede kullanılan **{v["olcum_kaynak"]}** oturum: **{v["olcum_oturum"]}** ({v["olcum_satir"]} karar satırı). Eğitim katlarına ek olarak {v["ek_egitim_satir"]} sentetik satır girdi (üretici kural `tools/sentetik_uret.py` başında). Son model, eğitime uygun tüm satırlarla ({v["gercek_satir"]} gerçek + {v["sentetik_satir"]} sentetik) yeniden eğitilir.
- `data/oturumlar.csv` SHA-256: `{v["veri_sha256"][:16]}…` (tam değer `config.json`'da).

## Metrikler (kabul eşiği eğitimden önce `spec.md`'de yazıldı)
Doğrulama: `GroupKFold({N_KAT})`, grup = oturum (bir oturumun satırları hem eğitimde hem testte olmaz). **Yalnız gerçek satırlarda ölçülür**; sentetik satırlar yalnız eğitim katlarındadır.

| Metrik | Değer | Eşik |
|---|---|---|
| ROC-AUC (geçerli katların ortalaması, {m["gecerli_kat"]}/{N_KAT} kat) | **{m["auc_ortalama"]}** | ≥ {c["kabul_esigi"]["auc_min"]} |
| ROC-AUC (tüm test tahminleri havuzlanmış) | {m["auc_havuz"]} (oturum bootstrap %95 aralığı: {ga[0]} – {ga[1]}) | bilgi |
| Brier skoru (model) | {m["brier_model"]} | taban ({m["brier_taban"]}) altında |
| B seçim oranı (taban) | {m["taban_orani_b"]} | bilgi |
| ONNX ↔ sklearn en büyük olasılık farkı | {c["onnx_maks_fark"]} | ≤ {c["kabul_esigi"]["onnx_tolerans"]} |

Mod dağılımı (test tahminlerinde): her modda kaç karar var ve gerçekte B seçilme oranı. Modlar ayrışıyorsa `destek` oranı `meydan` oranından yüksek olmalıdır.

| Mod | Karar sayısı | Gerçek B oranı |
|---|---|---|
{dagilim}

## Sınırlar
- **Az veri.** Birkaç tanıdık kişiden az sayıda oturum. Güven aralığı geniştir; AUC'yi kesin bir değer gibi okumayın.
- **Dar popülasyon.** Arkadaş grubu, tek bir senaryo (sağlık randevu sistemi arızası), yalnız 3 karar. Başka senaryo ya da kitleye genellenmez.
- Model davranış korelasyonu öğrenir; neden-sonuç iddia etmez. "Tereddüt eden oyuncu yanlış yapar" bir tahmindir, kişi hakkında bir yargı değildir.
- **Geri besleme döngüsü.** Eğitim verisi modelin KAPALI olduğu (v1) oyundan toplanır. Model yayında oyuncuya müdahale ettiğinde (ipucu, "Neden?") seçimler değişir ve veri dağılımı kayar; bu yüzden yeni veriyle yeniden eğitmeden önce müdahalesiz (Shadow ya da `?veri=1`) oturumlar kullanılmalıdır.
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
"""


# --------------------------------------------------------------------------- ana akış
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--deneme", action="store_true",
                    help="değerlendirmeyi sentetik veride yap; kapı geçilemese de paketlemeyi dene; çıktıyı _out/deneme/ altına yaz")
    ap.add_argument("--veri", default=str(VERI), help="girdi CSV (varsayılan data/oturumlar.csv); testler için")
    ap.add_argument("--cikti", default=None, help="çıktı klasörü (varsayılan model/, --deneme ile _out/deneme/); testler için")
    a = ap.parse_args()

    ham, ozellikler, veri_sha = veri_yukle(Path(a.veri))
    gercek = ozellikler[ozellikler["kaynak"] == "gercek"].reset_index(drop=True)
    sentetik = ozellikler[ozellikler["kaynak"] == "sentetik"].reset_index(drop=True)

    if a.deneme:
        olcum, ek_egitim, hedef = sentetik, sentetik.iloc[0:0], DENEME_DIR
        print("⚠ DENEME: değerlendirme sentetik veride; çıktı yayınlanamaz.")
    else:
        olcum, ek_egitim, hedef = gercek, sentetik, MODEL_DIR
    if a.cikti:
        hedef = Path(a.cikti)

    print(f"Veri: {ham['oturum_id'].nunique()} oturum; modele giren satır: gerçek {len(gercek)}, sentetik {len(sentetik)}")
    if len(olcum) == 0:
        sys.exit("✗ Değerlendirilecek gerçek satır yok. Gerçek oturum ekleyin (python tools/birlestir.py gelen.csv).")

    metrik = degerlendir(olcum, ek_egitim)
    if degerlendir(olcum, ek_egitim) != metrik:  # tekrarlanabilirlik: aynı tohum, aynı sonuç
        sys.exit("✗ Tekrarlanabilirlik bozuk: iki koşu farklı metrik verdi.")

    print(f"AUC (kat ort.) {metrik['auc_ortalama']}  katlar {metrik['auc_kat']}  | havuz {metrik['auc_havuz']} "
          f"GA95 {metrik['auc_havuz_ga95']}  | Brier {metrik['brier_model']} (taban {metrik['brier_taban']})")
    hatalar = kapi(metrik, olcum)
    if hatalar and not a.deneme:
        print("✗ EVAL KAPISI GEÇİLEMEDİ, artefakt yazılmadı:")
        for h in hatalar:
            print(f"   - {h}")
        sys.exit(1)
    if hatalar:  # yalnız --deneme: paketleme hattı sınansın diye devam eder; çıktı "kapı geçmedi" diye işaretlenir
        print("⚠ (deneme) eval kapısı geçilemedi; gerçek modda burada DURULUR:")
        for h in hatalar:
            print(f"   - {h}")

    # Kapı geçildi: son model tüm uygun satırlarla eğitilir.
    egitim = pd.concat([gercek, sentetik], ignore_index=True)
    model = model_kur().fit(egitim[OZELLIKLER], egitim["secim_b"])
    hedef.mkdir(parents=True, exist_ok=True)
    fark = onnx_aktar(model, egitim[OZELLIKLER], hedef)
    if fark > ONNX_TOLERANS:
        (hedef / "model.onnx").unlink(missing_ok=True)
        sys.exit(f"✗ ONNX çıktısı sklearn'den sapıyor (maks fark {fark:.2e} > {ONNX_TOLERANS}); artefakt yazılmadı.")
    veri_ozet = {"olcum_kaynak": "sentetik" if a.deneme else "gercek",
                 "olcum_oturum": int(olcum["oturum_id"].nunique()), "olcum_satir": int(len(olcum)),
                 "ek_egitim_satir": int(len(ek_egitim)),
                 "gercek_satir": int(len(gercek)), "sentetik_satir": int(len(sentetik)), "veri_sha256": veri_sha}
    config = config_yaz(hedef, metrik, fark, veri_ozet, a.deneme, kapi_gecti=not hatalar)
    (hedef / "README.md").write_text(model_karti(config), encoding="utf-8")
    durum = "Eval kapısı geçti." if not hatalar else "DENEME çıktısı (kapı geçmedi, yayınlanamaz)."
    print(f"✓ {durum} Artefakt: {hedef}/ (model.onnx, config.json, README.md); ONNX farkı {fark:.1e}")


if __name__ == "__main__":
    main()
