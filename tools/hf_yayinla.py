#!/usr/bin/env python3
"""Modeli Hugging Face'e yayınlar ve uygulamayı COMMIT'e SABİTLENMİŞ URL'ye bağlar.

  python tools/hf_yayinla.py --repo <kullanici>/se-primer-akis-v2 --kuru    # ne yapacağını yazar, hiçbir şey göndermez
  python tools/hf_yayinla.py --repo <kullanici>/se-primer-akis-v2           # yayınlar

Ön koşul: `hf auth login` (Write token). Token'ı kimseyle paylaşmayın, repoya koymayın.

Adımlar:
  1. Kapı: model/config.json'da kapi_gecti=true ve deneme=false olmalı; tests/parite.json bu model.onnx ile üretilmiş olmalı.
  2. Public model reposu açar (yoksa) ve model/ klasörünü yükler -> yeni COMMIT kimliği (oid).
  3. https://huggingface.co/<repo>/resolve/<commit>/model.onnx adresinden indirip yerel dosyayla SHA-256 karşılaştırır.
  4. src/yayin.json > model_taban değerini bu sabit URL'ye çevirir (yuzde ve golge değerlerine dokunmaz).
"""
import argparse
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
MODEL = KOK / "model"
YAYIN = KOK / "src" / "yayin.json"
PARITE = KOK / "tests" / "parite.json"


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def kapi_kontrol():
    for ad in ("model.onnx", "config.json", "README.md"):
        if not (MODEL / ad).exists():
            sys.exit(f"✗ model/{ad} yok. Önce `python train.py` (eval kapısını geçmeli).")
    c = json.loads((MODEL / "config.json").read_text(encoding="utf-8"))
    if c.get("deneme") or not c.get("kapi_gecti"):
        sys.exit("✗ model/ bir DENEME çıktısı ya da eval kapısını geçmemiş. Yayınlanamaz.")
    if not PARITE.exists():
        sys.exit("✗ tests/parite.json yok. `python tests/parite.py --yaz` çalıştırın.")
    p = json.loads(PARITE.read_text(encoding="utf-8"))
    if p["model_sha256"] != sha((MODEL / "model.onnx").read_bytes()):
        sys.exit("✗ tests/parite.json başka bir model.onnx için üretilmiş. `python tests/parite.py --yaz` ile yenileyin.")
    return c


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", required=True, help="<kullanici>/<repo adi>")
    ap.add_argument("--kuru", action="store_true", help="hiçbir şey göndermeden planı yaz")
    ap.add_argument("--mesaj", default="v2.0: Akış Modeli (SE Primer)")
    a = ap.parse_args()

    c = kapi_kontrol()
    yerel_sha = sha((MODEL / "model.onnx").read_bytes())
    print(f"✓ Kapı: kapi_gecti=true, AUC {c['metrics']['auc_ortalama']}, parite.json bu modelle tutarlı (sha256 {yerel_sha[:12]}…)")
    if a.kuru:
        print(f"[kuru] {a.repo} public repo açılacak, model/ yüklenecek, resolve/<commit>/model.onnx doğrulanacak, src/yayin.json güncellenecek.")
        return

    from huggingface_hub import HfApi
    api = HfApi()
    api.create_repo(a.repo, repo_type="model", private=False, exist_ok=True)
    bilgi = api.upload_folder(repo_id=a.repo, folder_path=str(MODEL), repo_type="model", commit_message=a.mesaj)
    oid = bilgi.oid
    taban = f"https://huggingface.co/{a.repo}/resolve/{oid}/"

    # Commit'e sabit URL gerçekten aynı dosyayı veriyor mu?
    with urllib.request.urlopen(taban + "model.onnx") as r:
        uzak_sha = sha(r.read())
    if uzak_sha != yerel_sha:
        sys.exit(f"✗ {taban}model.onnx yerel dosyayla aynı değil (sha256 {uzak_sha[:12]}… ≠ {yerel_sha[:12]}…). src/yayin.json DEĞİŞTİRİLMEDİ.")
    print(f"✓ Commit {oid[:12]}… yüklendi; sabit URL doğrulandı (sha256 eşit)")

    yayin = json.loads(YAYIN.read_text(encoding="utf-8")) if YAYIN.exists() else {"yuzde": 100, "golge": False}
    yayin["model_taban"] = taban
    YAYIN.write_text(json.dumps(yayin, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"✓ src/yayin.json > model_taban = {taban}")
    print("\nSıradaki adımlar:")
    print(f"  1. RELEASE.md'deki <HF_KULLANICI>/<HF_REPO> ve <COMMIT_SHA> alanlarını doldurun:  {a.repo}  {oid}")
    print("  2. İlk dağıtımı Shadow ile başlatın: src/yayin.json > \"golge\": true (RELEASE.md bölüm 3)")
    print("  3. git add -A && git commit && git tag v2.0.0 && git push --tags")


if __name__ == "__main__":
    main()
