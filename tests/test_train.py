"""train.py testleri (standart kütüphane unittest; ek bağımlılık yok).
Çalıştırma: python -m unittest tests.test_train -v     (depo kökünden)

Sınananlar: özellik türetme (JS ile ortak örnekler), eval kapısının DURDURMASI, kapı geçince artefakt,
ONNX farkı, tekrarlanabilirlik (birebir aynı çıktı).
"""
import csv
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK))
import train  # noqa: E402

KOLONLAR = ["oturum_id", "kaynak", "sahne_no", "seviye", "karar_suresi_sn", "okuma_suresi_sn",
            "tutor_soru_sayisi", "ipucu_acildi", "secim", "sure_doldu", "secim_b"]


def sentetik_csv(yol: Path, n_oturum: int, kaynak: str, sinyal: bool, tohum: int = 5, baslangic: int = 0):
    """Test verisi. sinyal=True: etiket önceki karar süresinden gelir (model kolayca öğrenir);
    sinyal=False: etiket yazı-tura (öğrenilecek bir şey yok)."""
    rng = np.random.default_rng(tohum)
    satirlar = []
    for i in range(n_oturum):
        oid = f"{baslangic + i:012x}"
        onceki_karar, b_sayisi = 15.0, 0
        for sahne in (1, 2, 3):
            karar = float(round(rng.uniform(3, 40), 1))
            b = int(onceki_karar > 20) if sinyal else int(rng.random() < 0.5)
            satirlar.append([oid, kaynak, sahne, 0, karar, 6.0, 0, 0, "B" if b else "A", 0, b])
            onceki_karar = karar
            b_sayisi += b
    with yol.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(KOLONLAR)
        w.writerows(satirlar)


def calistir(*args):
    return subprocess.run([sys.executable, str(KOK / "train.py"), *args], capture_output=True, text=True, cwd=KOK)


def ozet(yol: Path) -> str:
    return hashlib.sha256(yol.read_bytes()).hexdigest()


class OzellikTurevi(unittest.TestCase):
    def test_ortak_ornekler(self):
        ornek = json.loads((KOK / "tests" / "ozellik_ornekleri.json").read_text(encoding="utf-8"))
        for o in ornek["oturumlar"]:
            sonuc = train.ozellik_uret(pd.DataFrame(o["satirlar"]))
            for sahne, beklenen in o["beklenen"].items():
                satir = sonuc[sonuc["sahne_no"] == float(sahne)]
                if beklenen is None:
                    self.assertEqual(len(satir), 0, f"{o['ad']} / sahne {sahne}: girdi üretilmemeli")
                else:
                    self.assertEqual(satir[train.OZELLIKLER].iloc[0].tolist(), [float(x) for x in beklenen],
                                     f"{o['ad']} / sahne {sahne}")


class EvalKapisi(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_gercek_oturum_az_ise_durur_ve_artefakt_yazmaz(self):
        veri, cikti = self.dir / "v.csv", self.dir / "cikti"
        sentetik_csv(veri, 10, "gercek", sinyal=True)  # 10 < 15
        r = calistir("--veri", str(veri), "--cikti", str(cikti))
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("en az 15", r.stdout)
        self.assertFalse(cikti.exists(), "kapı geçilemedi ama çıktı klasörü oluştu")

    def test_ogrenilecek_sinyal_yoksa_durur(self):
        veri, cikti = self.dir / "v.csv", self.dir / "cikti"
        sentetik_csv(veri, 40, "gercek", sinyal=False)
        r = calistir("--veri", str(veri), "--cikti", str(cikti))
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("EVAL KAPISI GEÇİLEMEDİ", r.stdout)
        self.assertFalse(cikti.exists())

    def test_gercek_veri_hic_yoksa_durur(self):
        veri, cikti = self.dir / "v.csv", self.dir / "cikti"
        sentetik_csv(veri, 40, "sentetik", sinyal=True)
        r = calistir("--veri", str(veri), "--cikti", str(cikti))
        self.assertEqual(r.returncode, 1)
        self.assertFalse(cikti.exists())

    def test_sinyal_varsa_gecer_artefakt_ve_onnx_farki(self):
        veri, cikti = self.dir / "v.csv", self.dir / "cikti"
        sentetik_csv(veri, 60, "gercek", sinyal=True)
        r = calistir("--veri", str(veri), "--cikti", str(cikti))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        for ad in ("model.onnx", "config.json", "README.md"):
            self.assertTrue((cikti / ad).exists(), ad)
        c = json.loads((cikti / "config.json").read_text(encoding="utf-8"))
        self.assertTrue(c["kapi_gecti"])
        self.assertFalse(c["deneme"])
        self.assertGreaterEqual(c["metrics"]["auc_ortalama"], train.ESIK_AUC)
        self.assertLess(c["metrics"]["brier_model"], c["metrics"]["brier_taban"])
        self.assertLessEqual(c["onnx_maks_fark"], train.ONNX_TOLERANS)
        self.assertEqual([f["name"] for f in c["features"]], train.OZELLIKLER)
        self.assertEqual((c["esik_destek"], c["esik_meydan"]), (0.60, 0.25))

    def test_tekrarlanabilir_iki_kosu_birebir_ayni(self):
        veri = self.dir / "v.csv"
        sentetik_csv(veri, 60, "gercek", sinyal=True)
        ozetler = []
        for k in ("a", "b"):
            cikti = self.dir / k
            r = calistir("--veri", str(veri), "--cikti", str(cikti))
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            ozetler.append({ad: ozet(cikti / ad) for ad in ("model.onnx", "config.json", "README.md")})
        self.assertEqual(ozetler[0], ozetler[1])


if __name__ == "__main__":
    unittest.main()
