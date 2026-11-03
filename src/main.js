import { tutorRespond, stagePrompts, destekPrompts } from './tutor.mjs';
import { yeniOturumId, satirOlustur, csvUret, ozellikVektoru, modSec, OZELLIKLER } from './telemetry.mjs';
import { modelYukle, tabanBelirle, pKancasi, yayinOku, kovadaMi } from './model.mjs';

const scenes = [
  { title:'Geri dönüş mü, canlı yama mı?',tag:'MİMARİ',clock:'08:03',icon:'⌁',
    story:'Gece yayımlanan sürümden sonra hastane randevu sistemi yanıt vermiyor. Bekleyen 300 hasta var. Veritabanı şemasının değişip değişmediği henüz bilinmiyor.',
    question:'İlk teknik kararın ne?',
    options:[
      {id:'A',label:'Önce uyumluluğu kontrol ederek önceki sürüme dön',result:'Geri dönüşten önce veritabanı şemasını ve geri alınabilirliği kontrol ettin. Uyumsuzluk veya veri kaybı riskini azaltan kontrollü bir yol seçtin.'},
      {id:'B',label:'Üretim ortamında doğrudan hızlı yama yap',result:'Kök neden ve etki alanı doğrulanmadan canlı yama yapıldı. Ek arıza ve geri alma güçlüğü riski büyüdü.'}
    ],hint:'Önceki sürüm yeni veritabanı şemasını okuyabilir mi?',
    derin:'Geri dönüş yalnızca eski sürüm yeni şemayı okuyabiliyorsa güvenlidir. Göçleri "önce genişlet, sonra daralt" (expand/contract) biçiminde geriye uyumlu tutmak, baskı altında bile geri dönüş seçeneğini ayakta tutar. Kök neden doğrulanmadan yapılan yama ise iki bilinmeyeni, hatayı ve yamayı, aynı anda üretime taşır.' },
  { title:'Süre daralıyor.',tag:'TEST',clock:'08:12',icon:'⌘',
    story:'Kritik hata için bir düzeltme hazır. Sistem yeniden açılabilir; fakat randevu oluşturma ve iptal etme akışlarının doğrulandığına dair kanıt yok.',
    question:'Yayına çıkmadan önce ne yaparsın?',
    options:[
      {id:'A',label:'Kritik akışlar için kısa smoke test uygula',result:'Giriş, randevu oluşturma ve iptal gibi en önemli işlevler kontrol edildi. Yayın öncesi temel regresyon riski azaltıldı.'},
      {id:'B',label:'Testleri atlayıp hemen yayına al',result:'Sistem açıldı ancak kritik işlevlerin doğrulandığına dair kanıt yok. Görünmeyen hataların hastalara ulaşma riski arttı.'}
    ],hint:'Sistemin açılması, randevu oluşturmanın çalıştığını kanıtlar mı?',
    derin:'Sistemin yanıt vermesi ile doğru çalışması farklı iddialardır. Smoke test ucuz bir doğrulamadır; kritik akışlar için otomatik regresyon testi "tekrar bozulmadı mı?" sorusunun kanıtını verir. Testi atlamak riski yok etmez, hastaya ertelenmiş bir hata olarak yansıtır.' },
  { title:'Loglarda kişisel veri var.',tag:'KVKK',clock:'08:19',icon:'▣',
    story:'Sorunu inceleyen ekip hata loglarını istiyor. Log satırlarında hastaların adları ve randevu bilgileri bulunuyor.',
    question:'Logları nasıl paylaşırsın?',
    options:[
      {id:'A',label:'Kişisel verileri maskeleyip yetkili ekiple paylaş',result:'Gereksiz tanımlayıcı alanlar maskelendi ve erişim sınırlandı. Veri minimizasyonu ilkesi korundu.'},
      {id:'B',label:'Hız kazanmak için ham logları ekibe gönder',result:'Ham loglardaki hasta kimlikleri gereğinden geniş bir gruba ifşa edildi. Gizlilik ve mevzuata uyumsuzluk riski oluştu.'}
    ],hint:'Hata incelemesi için hasta adını gerçekten görmeleri gerekiyor mu?',
    derin:'Veri minimizasyonu: hata ayıklamak için hastanın kim olduğu değil, hatanın hangi kayıtta ve hangi koşulda oluştuğu gerekir. Maskeleme ve erişim sınırı ihlal olasılığını azaltır; ham log paylaşımı ise ifşayı geri alınamaz kılar (KVKK m.12: veri güvenliği yükümlülükleri).' },
];

const root = document.querySelector('#root');
const state = {page:'intro',level:'beginner',role:'developer',goal:'testing',step:0,choices:[],selection:null,tutor:'',tutorCategory:'',hint:false,seconds:60,interval:null,
  // v2: davranış kaydı. Veri toplama modu ?veri=1 ile açılır; kayıt yalnız bu tarayıcıda kalır, hiçbir yere gönderilmez.
  collect:new URLSearchParams(location.search).get('veri')==='1',oturumId:yeniOturumId(),rows:[],sceneStart:0,feedbackStart:0,decisionSec:0,tutorCount:0,hintClicked:false,timedOut:false,
  // v2: model. mod = normal | destek | meydan. ?tani=1 model tanı panelini, ?p=0.72 test kancasını açar.
  tani:new URLSearchParams(location.search).get('tani')==='1',pOverride:pKancasi(location.search),p:null,mod:'normal',jeton:0,modelDurum:'',golgeP:null,golgeMod:null};
const STORE_KEY='primer_v2_veri';
function loadRows(){if(!state.collect)return;try{const raw=localStorage.getItem(STORE_KEY);if(raw)state.rows=JSON.parse(raw);}catch(e){}}
function saveRows(){if(!state.collect)return;try{localStorage.setItem(STORE_KEY,JSON.stringify(state.rows));}catch(e){}}
function beginScene(){state.sceneStart=Date.now();state.tutorCount=0;state.hintClicked=false;state.timedOut=false;state.p=null;state.mod='normal';state.golgeP=null;state.golgeMod=null;state.jeton+=1;modUygula();}
function csvText(){return csvUret(state.rows.map(r=>({...r,kaynak:'gercek'})));}
function collectPanel(){if(!state.collect)return '';const n=new Set(state.rows.map(r=>r.oturum_id)).size;return `<div class="tutor" data-testid="collect"><div class="tutor-heading">● VERİ TOPLAMA MODU</div><p data-testid="collect-count">Bu tarayıcıda ${n} oturum, ${state.rows.length} karar kaydı var. Ad, e-posta, konum veya tutora yazdığın metin kaydedilmez; oturum kimliği rastgele üretilir.</p><button data-action="csv" data-testid="csv-indir">CSV İNDİR</button> <button data-action="csv-kopyala" data-testid="csv-kopyala">PANOYA KOPYALA</button></div>`;}
const escapeHtml = (value) => String(value).replace(/[&<>"']/g, ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
const roles = {developer:'Yazılım geliştirici',tester:'Test mühendisi',lead:'Teknik lider'};
const goals = {testing:'TEST VE DOĞRULAMA',security:'VERİ GÜVENLİĞİ',architecture:'MİMARİ KARARLAR'};

function intro() {return `<section class="panel intro" data-testid="intro"><div class="eyebrow">VAKA DOSYASI / 001</div><div class="hero-art" aria-hidden="true"><span class="pulse">+</span><div class="art-grid"></div><div class="art-center">08:00 <small>SİSTEM KESİNTİSİ</small></div></div><h1>Bir karar.<br><em>Yüzlerce hayat.</em></h1><p class="lead">Hastane randevu sistemi çöktü. Nöbetçi mühendis sensin. Verdiğin her kararın teknik bir sonucu var.</p><div class="section-title">SİMÜLASYONU KİŞİSELLEŞTİR</div>
<label for="level">Deneyim seviyen<select data-testid="level" id="level"><option value="beginner" ${state.level==='beginner'?'selected':''}>Yeni başladım — rehberli</option><option value="expert" ${state.level==='expert'?'selected':''}>Deneyimliyim — 60 sn karar süresi</option></select></label>
<label for="role">Rolün<select data-testid="role" id="role"><option value="developer" ${state.role==='developer'?'selected':''}>Yazılım geliştirici</option><option value="tester" ${state.role==='tester'?'selected':''}>Test mühendisi</option><option value="lead" ${state.role==='lead'?'selected':''}>Teknik lider</option></select></label>
<label for="goal">Öğrenme hedefin<select data-testid="goal" id="goal"><option value="testing" ${state.goal==='testing'?'selected':''}>Test ve doğrulama</option><option value="security" ${state.goal==='security'?'selected':''}>Veri güvenliği</option><option value="architecture" ${state.goal==='architecture'?'selected':''}>Mimari kararlar</option></select></label>
<button data-testid="start" class="primary" data-action="start">SİMÜLASYONU BAŞLAT <span>↗</span></button><p class="micro">3 karar · 2 olası son · Gerçek hasta verisi kullanılmaz</p>${state.collect?'<p class="micro" data-testid="collect-note">VERİ TOPLAMA MODU AÇIK · Karar sürelerin ve seçimlerin kaydedilir; kişisel bilgi toplanmaz. Bu modda model kapalıdır.</p>':''}${state.tani?taniPanel():''}</section>`;}

function scene() {
 const scene = scenes[state.step];
 const progress = Math.round(state.step/3*100);
 const explain = state.selection ? scene.options.find(o=>o.id===state.selection) : null;
 const tutorText = state.tutor || stagePrompts[state.step];
 return `<section class="panel scene" data-testid="scene"><div class="progress"><span>VAKA 001 / KARAR ${state.step+1}–3</span><span>${progress}% TAMAMLANDI</span></div><div class="track" role="progressbar" aria-valuenow="${progress}" aria-valuemin="0" aria-valuemax="100"><div style="width:${progress}%"></div></div><div class="scene-top"><span class="eyebrow">${scene.tag} / ${scene.clock}</span>${state.p!==null?`<span class="mod-rozet ${state.mod}" data-testid="mode-badge">${MOD_ADI[state.mod]} · p=<span data-cy="p">${state.p.toFixed(6)}</span><span data-cy="mode" hidden>${state.mod}</span></span>`:''}${state.level==='expert'&&state.mod!=='destek'?`<span data-testid="timer" class="timer" aria-live="off">⏱ ${state.seconds} SN</span>`:''}</div>${state.golgeP!==null?`<span hidden data-cy="golge-p">${state.golgeP.toFixed(6)}</span><span hidden data-cy="golge-mod">${state.golgeMod}</span>`:''}<div class="scene-icon" aria-hidden="true">${scene.icon}</div><h1>${scene.title}</h1><p class="lead">${roles[state.role]} olarak, ${scene.story}</p><p class="goal">ODAK: ${goals[state.goal]}</p><h2>${scene.question}</h2><div class="options">${scene.options.map(o=>`<button data-testid="option-${o.id}" data-action="choose" data-value="${o.id}" ${state.selection?'disabled':''} class="option ${state.selection===o.id?'selected':''}"><b>${o.id}</b><span>${o.label}</span><span aria-hidden="true">↗</span></button>`).join('')}</div>
 ${explain ? `<div data-testid="feedback" class="feedback" aria-live="polite"><div class="eyebrow">KARARIN TEKNİK SONUCU</div><p>${explain.result}</p><p class="subtle">${state.selection==='A'?'Kontrollü yaklaşım seçtin.':'Seçimin yeni riskler doğurdu. Bir sonraki adımda etkisini düşün.'}</p>${state.mod==='meydan'?`<p class="neden" data-cy="neden" data-testid="neden"><b>NEDEN?</b> ${scene.derin}</p>`:''}<button data-testid="next" data-action="next" class="primary">${state.step===2?'SONUCU GÖR':'SONRAKİ KARAR'} <span>→</span></button></div>` : `<div class="tutor" data-testid="tutor"><div class="tutor-heading">✧ AI TUTOR · SOKRATİK REHBER</div><p id="tutor-response" aria-live="polite">${escapeHtml(tutorText)}</p>${((state.level==='beginner'||state.hint||state.mod==='destek')&&state.mod!=='meydan')?`<p class="hint" data-testid="hint">İpucu: ${scene.hint}</p>`:''}
 <form id="tutor-form"><label for="student-input">Tutor'a düşünceni sor <span class="optional">(isteğe bağlı)</span></label><div class="ask-row"><input id="student-input" name="student-input" maxlength="500" placeholder="Örn. Şema değiştiyse ne olur?" autocomplete="off" aria-label="Tutor'a soru" required><button data-testid="ask-tutor" type="submit">SOR</button></div><p class="tiny-note">Tutor yönlendirici sorular üretir; doğru şıkkı söylemez. Bu sürüm çevrimdışı kural tabanlıdır.</p></form><div class="tutor-actions">${state.mod==='meydan'?'':'<button data-action="hint" data-testid="show-hint">İpucu göster</button>'}<button data-action="more">Bir soru daha sor</button></div></div>`}</section>`;
}
function ending(){
 const good = state.choices.length===3&&state.choices.every(x=>x==='A');
 return `<section class="panel ending" data-testid="ending"><div class="eyebrow">VAKA 001 / TAMAMLANDI</div><div class="end-icon">${good?'✓':'!'}</div><div class="end-tag">${good?'SON A / GÜVENLİ TOPARLANMA':'SON B / RİSKLİ TOPARLANMA'}</div><h1>${good?'Sistem ayakta.\nVeriler güvende.':'Sistem açıldı.\nRiskler sürüyor.'}</h1><p class="lead">${good?'08:25 — Kritik akışlar doğrulandı, loglar maskelendi ve hizmet kontrollü şekilde geri döndü.':'08:25 — Hizmet geri döndü; ancak seçilen yollara bağlı olarak regresyon, uyumluluk veya kişisel veri ifşası riski oluştu.'}</p><div class="summary"><h2>Karar günlüğün</h2>${state.choices.map((c,i)=>`<div class="summary-row"><span>${String(i+1).padStart(2,'0')} · ${scenes[i].tag}</span><b>${c} ${c==='A'?'✓':'⚠'}</b></div>`).join('')}</div><div class="tutor"><div class="tutor-heading">✧ ÖĞRENME NOTU</div><p>Bir sistemi yeniden çalıştırmak ile güvenli ve doğrulanmış biçimde hizmete almak aynı şey değildir. Her karar için kanıt, test ve veri minimizasyonu gerekir.</p></div>${collectPanel()}<button data-testid="restart" data-action="restart" class="primary">YENİDEN OYNA <span>↻</span></button></section>`;
}
function stopTimer(){if(state.interval){clearInterval(state.interval);state.interval=null;}}
function startTimer(){stopTimer();if(state.level!=='expert'||state.page!=='scene'||state.selection||state.mod==='destek')return;state.interval=setInterval(()=>{if(state.page!=='scene'||state.selection){stopTimer();return;}state.seconds=Math.max(0,state.seconds-1);const el=document.querySelector('[data-testid="timer"]');if(el)el.textContent=`⏱ ${state.seconds} SN`;if(state.seconds===0){choose('B',true);}},1000);}
function render(){root.innerHTML=`<main class="app"><header><div class="brand"><span class="logo">✦</span><div><strong>SE PRIMER</strong><small>ETKİLEŞİMLİ MÜHENDİSLİK HİKÂYESİ</small></div></div><span class="status">● SİMÜLASYON</span></header>${state.page==='intro'?intro():state.page==='scene'?scene():ending()}<footer>SE PRIMER © 2026 <span>YZM301 · YAZILIM TEST VE GERÇEKLEME</span></footer></main>`;}
function choose(option,timedOut=false){if(state.page!=='scene'||state.selection||!['A','B'].includes(option))return;state.decisionSec=(Date.now()-state.sceneStart)/1000;state.feedbackStart=Date.now();state.timedOut=timedOut;state.selection=option;state.choices.push(option);stopTimer();render();}
function next(){if(!state.selection)return;
 state.rows.push(satirOlustur({oturumId:state.oturumId,sahneNo:state.step+1,seviye:state.level==='expert'?1:0,kararSn:state.decisionSec,okumaSn:(Date.now()-state.feedbackStart)/1000,tutorSoru:state.tutorCount,ipucu:state.hintClicked?1:0,secim:state.selection,sureDoldu:state.timedOut?1:0}));saveRows();
 state.step+=1;state.selection=null;state.tutor='';state.hint=false;state.seconds=60;beginScene();if(state.step===3){state.page='end';stopTimer();}render();startTimer();}
function restart(){stopTimer();Object.assign(state,{page:'intro',step:0,choices:[],selection:null,tutor:'',hint:false,seconds:60,oturumId:yeniOturumId(),p:null,mod:'normal',jeton:state.jeton+1});render();}
function downloadCsv(){const blob=new Blob([csvText()],{type:'text/csv'});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=`primer_oturum_${state.oturumId}.csv`;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(a.href),1000);}
function copyCsv(){try{navigator.clipboard.writeText(csvText());}catch(e){}}
// ---- v2: model ve mod ----
const MOD_ADI={normal:'NORMAL',destek:'DESTEK MODU',meydan:'MEYDAN OKUMA'};
const TANI_ORNEK=[2,0,15,8,1,0,0];
let modelSoz=null;
function setDurum(t){state.modelDurum=t;const el=document.querySelector('[data-cy="model-durum"]');if(el)el.textContent=t;}
let yayinSoz=null;
function yayinHazir(){if(!yayinSoz)yayinSoz=yayinOku();return yayinSoz;}
function modelHazirla(){if(!modelSoz){modelSoz=yayinHazir().then(y=>modelYukle(tabanBelirle(location.search,y.model_taban))).then(m=>{setDurum('model hazır: '+m.config.title);return m;}).catch(e=>{setDurum('model yok, normal mod ('+e.message+')');return null;});}return modelSoz;}
function renderKoru(){const eski=document.querySelector('#student-input');const v=eski?eski.value:'';const odak=!!eski&&document.activeElement===eski;render();const yeni=document.querySelector('#student-input');if(yeni&&v){yeni.value=v;if(odak)yeni.focus();}}
async function modUygula(){
 const sahneNo=state.step+1;
 // Veri toplama modunda model KAPALI: oyuncuya müdahale etmesi etiketleri (seçimleri) kirletir. Sahne 1'de geçmiş davranış yok.
 if(state.collect||sahneNo<2||sahneNo>3)return;
 const jeton=state.jeton;
 const yayin=await yayinHazir();
 // Canary / aşamalı geçiş: oturum bu yüzdenin dışındaysa v1 davranışı (model hiç çalışmaz).
 if(!kovadaMi(state.oturumId,yayin.yuzde))return;
 let p=state.pOverride;let esik={};
 if(p===null){
  const vektor=ozellikVektoru(state.rows.filter(r=>r.oturum_id===state.oturumId),sahneNo,state.level==='expert'?1:0);
  if(!vektor)return;
  const m=await modelHazirla();if(!m)return;
  try{p=await m.tahmin(vektor);}catch(e){return;}
  esik={destek:m.config.esik_destek,meydan:m.config.esik_meydan};
 }
 // Model dönene kadar oyuncu seçtiyse ya da sahne değiştiyse sonucu uygulama.
 if(jeton!==state.jeton||state.page!=='scene'||state.selection)return;
 const mod=modSec(p,esik.destek,esik.meydan);
 // Shadow Deployment: model gerçek oyuncuda sessizce çalışır, sonucu yalnız kaydedilir; oyun v1 davranışında kalır.
 if(yayin.golge){state.golgeP=p;state.golgeMod=mod;console.info('[golge]',{sahne:sahneNo,p,mod});renderKoru();return;}
 state.p=p;state.mod=mod;
 if(state.mod==='destek'){stopTimer();state.tutor=destekPrompts[state.step];}
 renderKoru();
}
function taniPanel(){return `<div class="tutor" data-testid="tani"><div class="tutor-heading">◈ MODEL TANI</div><p class="tiny-note" data-cy="model-durum">${escapeHtml(state.modelDurum||'model: henüz yüklenmedi')}</p><div class="tani-grid">${OZELLIKLER.map((k,i)=>`<label>${k}<input data-cy="in-${k}" value="${TANI_ORNEK[i]}" inputmode="decimal"></label>`).join('')}</div><button data-action="hesapla" data-cy="hesapla" class="primary">HESAPLA <span>→</span></button><p class="tani-sonuc">p = <b data-cy="p">—</b> · mod: <b data-cy="mode">—</b></p></div>`;}
async function hesapla(){
 const v=OZELLIKLER.map(k=>parseFloat(document.querySelector(`[data-cy="in-${k}"]`).value));
 const pEl=document.querySelector('[data-cy="p"]'),mEl=document.querySelector('[data-cy="mode"]');
 if(v.some(Number.isNaN)){pEl.textContent='hata';return;}
 const m=await modelHazirla();if(!m){pEl.textContent='model yok';mEl.textContent='normal';return;}
 try{const p=await m.tahmin(v);pEl.textContent=p.toFixed(6);mEl.textContent=modSec(p,m.config.esik_destek,m.config.esik_meydan);}catch(e){pEl.textContent='hata';}
}
if(!state.collect||state.tani)yayinHazir().then(y=>{if(y.yuzde>0||state.tani)modelHazirla();}); // yuzde=0 (rollback) iken modeli hiç indirme
loadRows();
root.addEventListener('click',event=>{
 const button=event.target.closest('button[data-action]');if(!button||button.disabled)return;
 switch(button.dataset.action){case'start':state.page='scene';beginScene();render();startTimer();break;case'choose':choose(button.dataset.value);break;case'next':next();break;case'restart':restart();break;case'hint':state.hint=true;state.hintClicked=true;render();break;case'more':state.tutorCount+=1;state.tutor=tutorRespond('Bir soru daha sor',state.step,state).text;render();break;case'csv':downloadCsv();break;case'csv-kopyala':copyCsv();break;case'hesapla':hesapla();break;}
});
root.addEventListener('change',event=>{if(['level','role','goal'].includes(event.target.id))state[event.target.id]=event.target.value;});
root.addEventListener('submit',event=>{
 if(event.target.id!=='tutor-form')return;event.preventDefault();const input=event.target.elements['student-input'];if(!input.value.trim())return;
 state.tutorCount+=1;const response=tutorRespond(input.value,state.step,state);state.tutor=response.text;state.tutorCategory=response.category;document.querySelector('#tutor-response').textContent=response.text;input.value='';
});
render();
