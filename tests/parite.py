#!/usr/bin/env python3
"""Test Kahini (Oracle) — diferansiyel testin ikinci tüketicisi.

Aynı model.onnx'i Python onnxruntime ile çalıştırır. Uygulamadaki (tarayıcı, onnxruntime-web) sonuç bu
referansla `tolerans` (1e-4) içinde aynı olmak zorundadır; bunu Cypress (cypress/e2e/parite.cy.js) sınar.

  python tests/parite.py --yaz      # 5 referans girdi için tests/parite.json üretir (model değişince yeniden)
  python tests/parite.py            # parite.json'u yeniden hesaplayıp doğrular; model.onnx değiştiyse HATA verir

Seçenekler: --model-dir model  --cikti tests/parite.json
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import onnxruntime as ort

KOK = Path(__file__).resolve().parent.parent
TOLERANS = 1e-4

# Beş referans girdi: sıra = config.json "features" sırası.
# sahne_no, seviye, onceki_karar_suresi_sn, onceki_okuma_suresi_sn, onceki_tutor_soru_sayisi, onceki_ipucu_acildi, onceki_b_sayisi
REFERANS = [
    ("ortalama oyuncu", [2, 0, 15.0, 8.0, 1, 0, 0]),
    ("hızlı ve kendinden emin", [3, 1, 4.0, 12.0, 0, 0, 0]),
    ("tereddütlü, tutora ve ipucuna başvurdu, bir B", [2, 0, 55.0, 5.0, 4, 1, 1]),
    ("süre doldu, iki B birikti", [3, 1, 60.0, 2.0, 0, 0, 2]),
    ("sonucu uzun okuyan, dikkatli", [3, 0, 20.0, 60.0, 2, 1, 0]),
]


def oracle(model_dir: Path):
    config = json.loads((model_dir / "config.json").read_text(encoding="utf-8"))
    oturum = ort.InferenceSession(str(model_dir / "model.onnx"), providers=["CPUExecutionProvider"])
    sutun = config["classes"].index(config.get("positive_class", "1"))
    isimler = [f["name"] for f in config["features"]]

    def p_hesapla(vektor):
        x = np.array([vektor], dtype=np.float32)
        return float(oturum.run(["probabilities"], {"input": x})[0][0][sutun])

    return config, isimler, p_hesapla


def mod_sec(p, config):
    if p >= config["esik_destek"]:
        return "destek"
    if p <= config["esik_meydan"]:
        return "meydan"
    return "normal"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--yaz", action="store_true", help="parite.json üret")
    ap.add_argument("--model-dir", default=str(KOK / "model"))
    ap.add_argument("--cikti", default=str(KOK / "tests" / "parite.json"))
    a = ap.parse_args()
    model_dir, cikti = Path(a.model_dir), Path(a.cikti)
    if not (model_dir / "model.onnx").exists():
        sys.exit(f"✗ {model_dir}/model.onnx yok. Önce `python train.py` çalıştırın.")

    config, isimler, p_hesapla = oracle(model_dir)
    sha = hashlib.sha256((model_dir / "model.onnx").read_bytes()).hexdigest()

    if a.yaz:
        ornekler = []
        for ad, v in REFERANS:
            p = p_hesapla(v)
            ornekler.append({"ad": ad, "girdi": dict(zip(isimler, v)), "vektor": v, "p": p, "mod": mod_sec(p, config)})
        cikti.parent.mkdir(parents=True, exist_ok=True)
        cikti.write_text(json.dumps({
            "aciklama": "Test Kahini (Python onnxruntime) referans olasılıkları. Uygulamadaki sonuç tolerans içinde aynı olmalı.",
            "tolerans": TOLERANS, "model_sha256": sha, "ozellik_sirasi": isimler, "ornekler": ornekler,
        }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        for o in ornekler:
            print(f"  p={o['p']:.6f}  {o['mod']:7s}  {o['ad']}")
        print(f"✓ {cikti} yazıldı ({len(ornekler)} örnek, model sha256 {sha[:12]}…)")
        return

    kayit = json.loads(cikti.read_text(encoding="utf-8"))
    if kayit["model_sha256"] != sha:
        sys.exit("✗ parite.json başka bir model.onnx için üretilmiş (sha256 uyuşmuyor). `python tests/parite.py --yaz` ile yenileyin.")
    if kayit["ozellik_sirasi"] != isimler:
        sys.exit("✗ özellik sırası config.json ile uyuşmuyor.")
    en_buyuk = 0.0
    for o in kayit["ornekler"]:
        fark = abs(p_hesapla(o["vektor"]) - o["p"])
        en_buyuk = max(en_buyuk, fark)
        if fark >= TOLERANS:
            sys.exit(f"✗ '{o['ad']}': fark {fark:.2e} >= {TOLERANS}")
    print(f"✓ parite.json doğrulandı: {len(kayit['ornekler'])} örnek, en büyük fark {en_buyuk:.1e} (< {TOLERANS})")


if __name__ == "__main__":
    main()
