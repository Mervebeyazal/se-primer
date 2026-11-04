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


def sentetik_csv(yol: Path, n_oturum: int, kaynak: str, sinyal: bool, tohum: int = 5, baslangic: int = 0, ters: bool = False):
    """Test verisi. sinyal=True: etiket önceki karar süresinden gelir (model kolayca öğrenir);
    sinyal=False: etiket yazı-tura (öğrenilecek bir şey yok). ters=True: sinyalin yönü tersine çevrilir."""
    rng = np.random.default_rng(tohum)
    satirlar = []
    for i in range(n_oturum):
        oid = f"{baslangic + i:012x}"
        onceki_karar, b_sayisi = 15.0, 0
        for sahne in (1, 2, 3):
            karar = float(round(rng.uniform(3, 40), 1))
            b = int((onceki_karar > 20) != ters) if sinyal else int(rng.random() < 0.5)
            satirlar.append([oid, kaynak, sahne, 0, karar, 6.0, 0, 0, "B" if b else "A", 0, b])
            onceki_karar = karar
            b_sayisi += b
    yeni = not yol.exists()
    with yol.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        if yeni:
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
    """spec.md v2.1: geliştirme seti (--veri) ile eğitilir, kapı ayrı kişilerin doğrulama setinde (--dogrulama) ölçülür."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.dev, self.dog, self.cikti = self.dir / "dev.csv", self.dir / "dog.csv", self.dir / "cikti"

    def tearDown(self):
        self.tmp.cleanup()

    def kos(self, *ek):
        return calistir("--veri", str(self.dev), "--dogrulama", str(self.dog), "--cikti", str(self.cikti), *ek)

    def test_dogrulama_seti_yoksa_durur(self):
        sentetik_csv(self.dev, 40, "gercek", sinyal=True)
        r = self.kos()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("Doğrulama seti yok", r.stdout + r.stderr)
        self.assertFalse(self.cikti.exists())

    def test_dogrulama_oturumu_az_ise_durur_ve_artefakt_yazmaz(self):
        sentetik_csv(self.dev, 40, "gercek", sinyal=True)
        sentetik_csv(self.dog, 10, "gercek", sinyal=True, tohum=6, baslangic=1000)  # 10 < 15
        r = self.kos()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("en az 15", r.stdout)
        self.assertFalse(self.cikti.exists(), "kapı geçilemedi ama çıktı klasörü oluştu")

    def test_dogrulamada_sinyal_yoksa_durur(self):
        sentetik_csv(self.dev, 40, "gercek", sinyal=True)
        sentetik_csv(self.dog, 40, "gercek", sinyal=False, tohum=6, baslangic=1000)
        r = self.kos()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("EVAL KAPISI GEÇİLEMEDİ", r.stdout)
        self.assertFalse(self.cikti.exists())

    def test_ortak_oturum_kimligi_sizintidir_durur(self):
        sentetik_csv(self.dev, 40, "gercek", sinyal=True)
        sentetik_csv(self.dog, 40, "gercek", sinyal=True, tohum=6, baslangic=20)  # kimlikler 20-39 çakışır
        r = self.kos()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("sızıntı", r.stdout + r.stderr)
        self.assertFalse(self.cikti.exists())

    def test_sentetik_satirlar_egitime_girmez(self):
        # Geliştirme setinde gerçek sinyal bir yönde, sentetik satırlar ters yönde ve 5 kat fazla.
        # Sentetik eğitime girseydi model ters öğrenir ve doğrulamada kalırdı.
        sentetik_csv(self.dev, 40, "gercek", sinyal=True)
        sentetik_csv(self.dev, 200, "sentetik", sinyal=True, tohum=7, baslangic=5000, ters=True)
        sentetik_csv(self.dog, 40, "gercek", sinyal=True, tohum=6, baslangic=1000)
        r = self.kos()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        c = json.loads((self.cikti / "config.json").read_text(encoding="utf-8"))
        self.assertEqual(c["veri"]["sentetik_satir"], 0)

    def test_sinyal_varsa_gecer_artefakt_ve_onnx_farki(self):
        sentetik_csv(self.dev, 40, "gercek", sinyal=True)
        sentetik_csv(self.dog, 40, "gercek", sinyal=True, tohum=6, baslangic=1000)
        r = self.kos()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        for ad in ("model.onnx", "config.json", "README.md"):
            self.assertTrue((self.cikti / ad).exists(), ad)
        c = json.loads((self.cikti / "config.json").read_text(encoding="utf-8"))
        self.assertTrue(c["kapi_gecti"])
        self.assertFalse(c["deneme"])
        self.assertEqual(c["metrics"]["yontem"], "holdout")
        self.assertGreaterEqual(c["metrics"]["auc_ortalama"], train.ESIK_AUC)
        self.assertLess(c["metrics"]["brier_model"], c["metrics"]["brier_taban"])
        self.assertLessEqual(c["onnx_maks_fark"], train.ONNX_TOLERANS)
        self.assertEqual([f["name"] for f in c["features"]], train.OZELLIKLER)
        self.assertEqual((c["esik_destek"], c["esik_meydan"]), (0.60, 0.25))

    def test_tekrarlanabilir_iki_kosu_birebir_ayni(self):
        sentetik_csv(self.dev, 40, "gercek", sinyal=True)
        sentetik_csv(self.dog, 40, "gercek", sinyal=True, tohum=6, baslangic=1000)
        ozetler = []
        for k in ("a", "b"):
            self.cikti = self.dir / k
            r = self.kos()
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            ozetler.append({ad: ozet(self.cikti / ad) for ad in ("model.onnx", "config.json", "README.md")})
        self.assertEqual(ozetler[0], ozetler[1])


if __name__ == "__main__":
    unittest.main()
