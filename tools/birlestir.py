"""Arkadaşlarından gelen CSV dosyalarını doğrulayıp data/oturumlar.csv'ye ekler.

Kullanım:
  python tools/birlestir.py gelen1.csv gelen2.csv ...            # gerçek oturumları ekler
  python tools/birlestir.py --sentetik data/sentetik.csv          # sentetik satırları ekler
  python tools/birlestir.py --dogrulama gelen3.csv ...            # ikinci tur: data/dogrulama.csv (yeni kişiler)
  python tools/birlestir.py --kontrol                             # iki dosyayı doğrular, oturum kimlikleri ayrık mı bakar

Doğrulama (KVKK koruması dahil): tanımsız sütun varsa reddeder (ad, e-posta, konum vb. sızmasın),
oturum_id yalnız 12 hex olabilir, değer aralıklarını ve secim/secim_b tutarlılığını denetler.
Aynı (oturum_id, sahne_no) ikinci kez eklenmez.
"""
import argparse
import csv
import re
import sys
from pathlib import Path

KOLONLAR = ["oturum_id", "kaynak", "sahne_no", "seviye", "karar_suresi_sn", "okuma_suresi_sn",
            "tutor_soru_sayisi", "ipucu_acildi", "secim", "sure_doldu", "secim_b"]
HEDEF = Path("data/oturumlar.csv")        # geliştirme seti (1. tur) + sentetik
DOGRULAMA = Path("data/dogrulama.csv")    # tutulan doğrulama seti (2. tur, yeni kişiler); spec.md > v2.1


def satir_hatasi(s):
    if not re.fullmatch(r"[0-9a-f]{12}", s["oturum_id"]):
        return "oturum_id 12 haneli hex olmalı"
    if s["kaynak"] not in ("gercek", "sentetik"):
        return "kaynak gercek|sentetik olmalı"
    try:
        sahne, seviye = int(s["sahne_no"]), int(s["seviye"])
        karar, okuma = float(s["karar_suresi_sn"]), float(s["okuma_suresi_sn"])
        tutor, ipucu = int(s["tutor_soru_sayisi"]), int(s["ipucu_acildi"])
        doldu, b = int(s["sure_doldu"]), int(s["secim_b"])
    except ValueError:
        return "sayısal alanlar okunamadı"
    if sahne not in (1, 2, 3) or seviye not in (0, 1) or ipucu not in (0, 1) or doldu not in (0, 1) or b not in (0, 1):
        return "aralık dışı (sahne 1-3, seviye/ipucu/sure_doldu/secim_b 0-1)"
    if not (0 <= karar <= 3600 and 0 <= okuma <= 3600 and 0 <= tutor <= 100):
        return "süre/sayaç aralık dışı"
    if s["secim"] not in ("A", "B") or (s["secim"] == "B") != (b == 1):
        return "secim ile secim_b tutarsız"
    if doldu == 1 and (s["secim"] != "B" or seviye != 1):
        return "sure_doldu=1 yalnız deneyimli + B için olabilir"
    return None


def oku(yol):
    with open(yol, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        if r.fieldnames != KOLONLAR:
            sys.exit(f"HATA {yol}: sütunlar sözleşmeye uymuyor.\n  beklenen: {KOLONLAR}\n  gelen:    {r.fieldnames}")
        return list(r)


def rapor(satirlar):
    oturumlar = {}
    for s in satirlar:
        oturumlar.setdefault((s["kaynak"], s["oturum_id"]), set()).add(int(s["sahne_no"]))
    for kaynak in ("gercek", "sentetik"):
        o = [k for k in oturumlar if k[0] == kaynak]
        tam = sum(1 for k in o if oturumlar[k] == {1, 2, 3})
        print(f"  {kaynak:9s}: {len(o):4d} oturum ({tam} tam, {len(o) - tam} eksik), "
              f"{sum(1 for s in satirlar if s['kaynak'] == kaynak)} satır")


def yaz(yol, satirlar):
    satirlar = sorted(satirlar, key=lambda s: (s["kaynak"], s["oturum_id"], int(s["sahne_no"])))
    yol.parent.mkdir(parents=True, exist_ok=True)
    with yol.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=KOLONLAR, lineterminator="\n")
        w.writeheader()
        w.writerows(satirlar)


def dogrula(yol, satirlar):
    for s in satirlar:
        hata = satir_hatasi(s)
        if hata:
            sys.exit(f"HATA {yol}: oturum {s['oturum_id']} sahne {s['sahne_no']}: {hata}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dosyalar", nargs="*")
    ap.add_argument("--sentetik", action="store_true", help="gelen dosya sentetik; kaynak sütunu sentetik olmalı")
    ap.add_argument("--dogrulama", action="store_true", help="gelen dosyalar 2. tur (yeni kişiler): data/dogrulama.csv'ye yazılır")
    ap.add_argument("--kontrol", action="store_true", help="yalnız mevcut dosyaları doğrula")
    a = ap.parse_args()
    if a.sentetik and a.dogrulama:
        ap.error("--sentetik ile --dogrulama birlikte kullanılamaz")

    gelistirme = oku(HEDEF) if HEDEF.exists() else []
    dogrulama = oku(DOGRULAMA) if DOGRULAMA.exists() else []
    hedef, mevcut, diger = (DOGRULAMA, dogrulama, gelistirme) if a.dogrulama else (HEDEF, gelistirme, dogrulama)
    # Sızıntı koruması: aynı oturum kimliği iki sette birden olamaz.
    ortak = {s["oturum_id"] for s in gelistirme} & {s["oturum_id"] for s in dogrulama}
    if ortak:
        sys.exit(f"HATA: {len(ortak)} oturum kimliği hem {HEDEF} hem {DOGRULAMA} içinde (veri sızıntısı): {sorted(ortak)[:3]}")
    if any(s["kaynak"] != "gercek" for s in dogrulama):
        sys.exit(f"HATA {DOGRULAMA}: yalnız kaynak=gercek satırları olabilir")

    anahtar = {(s["oturum_id"], s["sahne_no"]) for s in mevcut}
    diger_idler = {s["oturum_id"] for s in diger}
    yeni, atlanan = [], 0
    if not a.kontrol:
        if not a.dosyalar:
            ap.error("en az bir CSV verin ya da --kontrol kullanın")
        beklenen = "sentetik" if a.sentetik else "gercek"
        for d in a.dosyalar:
            for s in oku(d):
                hata = satir_hatasi(s)
                if hata:
                    sys.exit(f"HATA {d}: oturum {s['oturum_id']} sahne {s['sahne_no']}: {hata}")
                if s["kaynak"] != beklenen:
                    sys.exit(f"HATA {d}: kaynak={s['kaynak']} ama {beklenen} bekleniyordu")
                if s["oturum_id"] in diger_idler:
                    sys.exit(f"HATA {d}: oturum {s['oturum_id']} diğer sette zaten var (geliştirme/doğrulama ayrık olmalı)")
                if (s["oturum_id"], s["sahne_no"]) in anahtar:
                    atlanan += 1
                    continue
                anahtar.add((s["oturum_id"], s["sahne_no"]))
                yeni.append(s)
        yaz(hedef, mevcut + yeni)
        print(f"{len(yeni)} yeni satır eklendi, {atlanan} yinelenen atlandı -> {hedef}")
        mevcut = mevcut + yeni
    else:
        dogrula(HEDEF, gelistirme)
        dogrula(DOGRULAMA, dogrulama)
        print(f"{HEDEF} doğrulandı; {DOGRULAMA} " + ("doğrulandı; iki set ayrık." if dogrulama else "henüz yok."))
    print(f"{HEDEF}:")
    rapor(gelistirme if hedef != HEDEF else mevcut)
    if dogrulama or hedef == DOGRULAMA:
        print(f"{DOGRULAMA}:")
        rapor(mevcut if hedef == DOGRULAMA else dogrulama)


if __name__ == "__main__":
    main()
