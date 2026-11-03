#!/usr/bin/env python3
"""Çevrimdışı Shadow değerlendirmesi: model oyuncuya HİÇBİR ŞEY göstermeden gerçek oturumlarda sınanır.

Yeni toplanan (modelin KAPALI olduğu, ?veri=1 ile alınan) gerçek oturumlarda model.onnx'in tahmin ettiği p ile
oyuncunun gerçekte yaptığı seçimi karşılaştırır. Eğitimde hiç görülmemiş veridir; bu yüzden yayın öncesi
bağımsız bir kontroldür (RELEASE.md > Shadow).

  python tools/golge_degerlendir.py yeni1.csv yeni2.csv [--model-dir model]

Kapı: AUC >= train.ESIK_AUC ve Brier < taban (eğitimdeki B oranı) ve en az MIN_GERCEK_OTURUM oturum.
Geçerse çıkış kodu 0 (Canary'ye geçilebilir), aksi halde 1.
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import onnxruntime as ort
import pandas as pd
from sklearn.metrics import brier_score_loss, roc_auc_score

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK))
import train  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dosyalar", nargs="+")
    ap.add_argument("--model-dir", default=str(KOK / "model"))
    a = ap.parse_args()
    md = Path(a.model_dir)
    config = json.loads((md / "config.json").read_text(encoding="utf-8"))
    oturum = ort.InferenceSession(str(md / "model.onnx"), providers=["CPUExecutionProvider"])

    ham = pd.concat([pd.read_csv(d) for d in a.dosyalar], ignore_index=True)
    if list(ham.columns) != list(pd.read_csv(KOK / "data" / "oturumlar.csv", nrows=0).columns):
        sys.exit("✗ sütunlar data/oturumlar.csv sözleşmesine uymuyor.")
    if set(ham["kaynak"]) != {"gercek"}:
        sys.exit("✗ Shadow değerlendirmesi yalnız kaynak=gercek satırlarla yapılır.")
    z = train.ozellik_uret(ham)
    if z.empty:
        sys.exit("✗ Modele girecek satır yok (sahne 2-3 ve önceki sahne kaydı gerekir).")

    X = z[[f["name"] for f in config["features"]]].to_numpy(np.float32)
    sutun = config["classes"].index(config.get("positive_class", "1"))
    p = oturum.run(["probabilities"], {"input": X})[0][:, sutun]
    y = z["secim_b"].to_numpy()
    n_oturum = z["oturum_id"].nunique()
    taban = config["metrics"]["taban_orani_b"]  # eğitimdeki B oranı: "hep bunu tahmin et" tabanı

    iki_sinif = len(set(y)) == 2
    auc = float(roc_auc_score(y, p)) if iki_sinif else float("nan")
    brier, brier_taban = float(brier_score_loss(y, p)), float(brier_score_loss(y, np.full(len(y), taban)))
    ga = train.bootstrap_ga95(y, p, z["oturum_id"].to_numpy()) if iki_sinif else None

    print(f"Yeni veri: {n_oturum} oturum, {len(z)} karar | B oranı {y.mean():.3f} (eğitimde {taban})")
    print(f"AUC {auc:.4f}  GA95 {ga}  (eşik {train.ESIK_AUC})")
    print(f"Brier {brier:.4f}  taban {brier_taban:.4f}")
    for ad, maske in (("destek", p >= config["esik_destek"]), ("normal", (p > config["esik_meydan"]) & (p < config["esik_destek"])),
                      ("meydan", p <= config["esik_meydan"])):
        oran = f"{y[maske].mean():.3f}" if maske.any() else "-"
        print(f"  mod {ad:7s}: {int(maske.sum()):4d} karar, gerçek B oranı {oran}")

    hatalar = []
    if n_oturum < train.MIN_GERCEK_OTURUM:
        hatalar.append(f"yalnız {n_oturum} oturum var; en az {train.MIN_GERCEK_OTURUM} gerekli (kanıt yetersiz)")
    if not iki_sinif:
        hatalar.append("yeni veride tek sınıf var, AUC tanımsız")
    elif auc < train.ESIK_AUC:
        hatalar.append(f"AUC {auc:.4f} < eşik {train.ESIK_AUC}")
    if not brier < brier_taban:
        hatalar.append(f"Brier {brier:.4f} tabandan ({brier_taban:.4f}) iyi değil")
    if hatalar:
        print("✗ SHADOW KAPISI GEÇİLEMEDİ, Canary'ye geçilmez:")
        for h in hatalar:
            print("   -", h)
        sys.exit(1)
    print("✓ Shadow kapısı geçti: Canary'ye (%5) geçilebilir.")


if __name__ == "__main__":
    main()
