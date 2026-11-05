import subprocess, time, shutil, glob, os
from playwright.sync_api import sync_playwright
KOK="/home/claude/se-primer"
srv=subprocess.Popen(["python3","-m","http.server","5199","--bind","127.0.0.1"],cwd=KOK,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
time.sleep(1.5)
CAP="""(t)=>{let d=document.getElementById('demo-cap');if(!d){d=document.createElement('div');d.id='demo-cap';
d.style.cssText='position:fixed;left:0;right:0;bottom:0;z-index:99999;background:rgba(10,20,40,.92);color:#fff;font:600 20px/1.35 system-ui,sans-serif;padding:14px 24px;text-align:center';document.body.appendChild(d);}d.textContent=t;}"""
out="/home/claude/demo/v"
shutil.rmtree(out,ignore_errors=True)
with sync_playwright() as p:
    b=p.chromium.launch()
    c=b.new_context(viewport={"width":1280,"height":720},record_video_dir=out,record_video_size={"width":1280,"height":720})
    pg=c.new_page()
    def cap(t,w=0):
        pg.evaluate(CAP,t)
        if w: pg.wait_for_timeout(int(w*1000))
    def tikla(sel,w=1.2):
        pg.click(sel); pg.wait_for_timeout(int(w*1000))
    # Açılış
    pg.goto("http://127.0.0.1:5199/?p=0.72"); pg.wait_for_timeout(800)
    cap("SE Primer v2 demo: aynı sahne, iki farklı model olasılığı → iki farklı oyun davranışı",5)
    cap("Not: model kabul eşiğini geçemedi (AUC 0.37), bu yüzden olasılık test kancası ?p= ile sabitlenir; mod politikası gösterilir",6)
    # Oyuncu 1: deneyimli, p=0.72 -> destek
    cap("Oyuncu 1 · deneyimli · p = 0.72 (yüksek: B seçme ihtimali)",3)
    pg.select_option('[data-testid="level"]','expert'); pg.wait_for_timeout(800)
    tikla('[data-testid="start"]',2)
    cap("Sahne 1: model yok, v1 davranışı",3)
    tikla('[data-testid="option-A"]',2); tikla('[data-testid="next"]',2.5)
    cap("Sahne 2 → DESTEK modu: ipucu otomatik açık, tutor kendiliğinden Sokratik soru soruyor",9)
    pg.wait_for_timeout(1500)
    # Oyuncu 2: yeni başlayan, p=0.10 -> meydan
    pg.goto("http://127.0.0.1:5199/?p=0.10"); pg.wait_for_timeout(1000)
    cap("Oyuncu 2 · yeni başlayan · p = 0.10 (düşük: kontrollü oyuncu)",4)
    tikla('[data-testid="start"]',2)
    tikla('[data-testid="option-A"]',1.5); tikla('[data-testid="next"]',2)
    cap("Sahne 2 → MEYDAN modu: yeni başlayan olsa da ipucu gizli",6)
    tikla('[data-testid="option-A"]',1.5); tikla('[data-testid="next"]',2.5)
    cap("Sahne 3 → MEYDAN: ipucu yok; karardan sonra 'Neden?' derinlik notu gelecek",6)
    tikla('[data-testid="option-A"]',2.5)
    cap("Sonuç ekranında 'Neden?' notu: seçimin gerekçesi sorgulanıyor",8)
    cap("Aynı sahne, iki olasılık, iki davranış. Model yüklenemezse oyun v1 gibi sürer. Kod: github.com/Mervebeyazal/se-primer",4.5)
    pg.wait_for_timeout(500)
    c.close(); b.close()
srv.terminate()
f=glob.glob(out+"/*.webm")[0]
subprocess.run(["ffmpeg","-y","-loglevel","error","-i",f,"-c:v","libx264","-pix_fmt","yuv420p","-crf","28","-preset","veryfast","/home/claude/demo/demo.mp4"],check=True)
print(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration:stream=width,height","-of","default=nw=1","/home/claude/demo/demo.mp4"],capture_output=True,text=True).stdout)
