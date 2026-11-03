"""Sentetik oturum üretici (data/oturumlar.csv içindeki kaynak=sentetik satırları).

Amaç: gerçek oturumlar toplanırken eğitim hattını kurmak ve eğitim kümesini büyütmek.
UYARI: Sentetik satırlar ölçümde KULLANILMAZ (spec.md: başarı yalnız kaynak=gercek satırlarında ölçülür).
Üretici kural aşağıda açıkça yazılıdır; model bu kuralı öğrenirse bu bir başarı sayılmaz.

Kullanım:  python tools/sentetik_uret.py --oturum 150 --tohum 13 --cikti data/sentetik.csv
Aynı tohum + aynı parametre = birebir aynı dosya.

Üretici kural (her oturum için):
  1. Gizli beceri  s ~ N(0, 1). Oyuncu bunu bilmez, modelin de girdisi değildir.
  2. seviye ~ Bernoulli(0.4)  (1 = deneyimli).
  3. Her sahne için, s'ye bağlı davranış:
       karar_suresi_sn   ~ LogNormal(ln 15 - 0.35·s, 0.45)        (düşük beceri → daha uzun tereddüt)
       okuma_suresi_sn   ~ LogNormal(ln 8  + 0.25·s, 0.50)        (yüksek beceri → sonucu daha dikkatli okur)
       tutor_soru_sayisi ~ Poisson(exp(-0.6 - 0.4·s))             (düşük beceri → daha çok soru)
       ipucu_acildi      ~ Bernoulli(σ(-0.4 - 0.6·s))
  4. Seçim: P(B) = σ(-0.5 - 0.9·s + 0.35·önceki_B_sayısı + 0.2·seviye + gürültü N(0, 0.6)).
  5. Deneyimli oyuncuda karar_suresi_sn > 60 ise süre dolar: secim = B, sure_doldu = 1, karar_suresi_sn = 60.
Gürültü bilerek yüksek tutuldu; sentetik veride bile mükemmel ayrım beklenmez.
"""
import argparse
import csv
from pathlib import Path

import numpy as np

KOLONLAR = ["oturum_id", "kaynak", "sahne_no", "seviye", "karar_suresi_sn", "okuma_suresi_sn",
            "tutor_soru_sayisi", "ipucu_acildi", "secim", "sure_doldu", "secim_b"]


def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


def uret(oturum_sayisi: int, tohum: int):
    rng = np.random.default_rng(tohum)
    satirlar = []
    for _ in range(oturum_sayisi):
        oturum_id = "".join(f"{b:02x}" for b in rng.integers(0, 256, size=6))
        s = rng.normal(0, 1)
        seviye = int(rng.random() < 0.4)
        onceki_b = 0
        for sahne_no in (1, 2, 3):
            karar = float(np.exp(rng.normal(np.log(15) - 0.35 * s, 0.45)))
            okuma = float(np.exp(rng.normal(np.log(8) + 0.25 * s, 0.50)))
            tutor = int(rng.poisson(np.exp(-0.6 - 0.4 * s)))
            ipucu = int(rng.random() < sigmoid(-0.4 - 0.6 * s))
            p_b = sigmoid(-0.5 - 0.9 * s + 0.35 * onceki_b + 0.2 * seviye + rng.normal(0, 0.6))
            secim_b = int(rng.random() < p_b)
            sure_doldu = 0
            if seviye == 1 and karar > 60:
                karar, secim_b, sure_doldu = 60.0, 1, 1
            satirlar.append({
                "oturum_id": oturum_id, "kaynak": "sentetik", "sahne_no": sahne_no, "seviye": seviye,
                "karar_suresi_sn": round(min(max(karar, 0.8), 90.0), 1),
                "okuma_suresi_sn": round(min(max(okuma, 0.8), 120.0), 1),
                "tutor_soru_sayisi": min(tutor, 6), "ipucu_acildi": ipucu,
                "secim": "B" if secim_b else "A", "sure_doldu": sure_doldu, "secim_b": secim_b,
            })
            onceki_b += secim_b
    return satirlar


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--oturum", type=int, default=150)
    ap.add_argument("--tohum", type=int, default=13)
    ap.add_argument("--cikti", default="data/sentetik.csv")
    a = ap.parse_args()
    satirlar = uret(a.oturum, a.tohum)
    yol = Path(a.cikti)
    yol.parent.mkdir(parents=True, exist_ok=True)
    with yol.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=KOLONLAR, lineterminator="\n")
        w.writeheader()
        w.writerows(satirlar)
    print(f"{len(satirlar)} satır ({a.oturum} oturum, tohum {a.tohum}) -> {yol}")


if __name__ == "__main__":
    main()
