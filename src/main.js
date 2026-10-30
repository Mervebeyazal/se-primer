import { tutorRespond, stagePrompts } from './tutor.mjs';

const scenes = [
  { title:'Geri dönüş mü, canlı yama mı?',tag:'MİMARİ',clock:'08:03',icon:'⌁',
    story:'Gece yayımlanan sürümden sonra hastane randevu sistemi yanıt vermiyor. Bekleyen 300 hasta var. Veritabanı şemasının değişip değişmediği henüz bilinmiyor.',
    question:'İlk teknik kararın ne?',
    options:[
      {id:'A',label:'Önce uyumluluğu kontrol ederek önceki sürüme dön',result:'Geri dönüşten önce veritabanı şemasını ve geri alınabilirliği kontrol ettin. Uyumsuzluk veya veri kaybı riskini azaltan kontrollü bir yol seçtin.'},
      {id:'B',label:'Üretim ortamında doğrudan hızlı yama yap',result:'Kök neden ve etki alanı doğrulanmadan canlı yama yapıldı. Ek arıza ve geri alma güçlüğü riski büyüdü.'}
    ],hint:'Önceki sürüm yeni veritabanı şemasını okuyabilir mi?' },
  { title:'Süre daralıyor.',tag:'TEST',clock:'08:12',icon:'⌘',
    story:'Kritik hata için bir düzeltme hazır. Sistem yeniden açılabilir; fakat randevu oluşturma ve iptal etme akışlarının doğrulandığına dair kanıt yok.',
    question:'Yayına çıkmadan önce ne yaparsın?',
    options:[
      {id:'A',label:'Kritik akışlar için kısa smoke test uygula',result:'Giriş, randevu oluşturma ve iptal gibi en önemli işlevler kontrol edildi. Yayın öncesi temel regresyon riski azaltıldı.'},
      {id:'B',label:'Testleri atlayıp hemen yayına al',result:'Sistem açıldı ancak kritik işlevlerin doğrulandığına dair kanıt yok. Görünmeyen hataların hastalara ulaşma riski arttı.'}
    ],hint:'Sistemin açılması, randevu oluşturmanın çalıştığını kanıtlar mı?' },
  { title:'Loglarda kişisel veri var.',tag:'KVKK',clock:'08:19',icon:'▣',
    story:'Sorunu inceleyen ekip hata loglarını istiyor. Log satırlarında hastaların adları ve randevu bilgileri bulunuyor.',
    question:'Logları nasıl paylaşırsın?',
    options:[
      {id:'A',label:'Kişisel verileri maskeleyip yetkili ekiple paylaş',result:'Gereksiz tanımlayıcı alanlar maskelendi ve erişim sınırlandı. Veri minimizasyonu ilkesi korundu.'},
      {id:'B',label:'Hız kazanmak için ham logları ekibe gönder',result:'Ham loglardaki hasta kimlikleri gereğinden geniş bir gruba ifşa edildi. Gizlilik ve mevzuata uyumsuzluk riski oluştu.'}
    ],hint:'Hata incelemesi için hasta adını gerçekten görmeleri gerekiyor mu?' },
];

const root = document.querySelector('#root');
const state = {page:'intro',level:'beginner',role:'developer',goal:'testing',step:0,choices:[],selection:null,tutor:'',tutorCategory:'',hint:false,seconds:60,interval:null};
const escapeHtml = (value) => String(value).replace(/[&<>"']/g, ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
const roles = {developer:'Yazılım geliştirici',tester:'Test mühendisi',lead:'Teknik lider'};
const goals = {testing:'TEST VE DOĞRULAMA',security:'VERİ GÜVENLİĞİ',architecture:'MİMARİ KARARLAR'};

function intro() {return `<section class="panel intro" data-testid="intro"><div class="eyebrow">VAKA DOSYASI / 001</div><div class="hero-art" aria-hidden="true"><span class="pulse">+</span><div class="art-grid"></div><div class="art-center">08:00 <small>SİSTEM KESİNTİSİ</small></div></div><h1>Bir karar.<br><em>Yüzlerce hayat.</em></h1><p class="lead">Hastane randevu sistemi çöktü. Nöbetçi mühendis sensin. Verdiğin her kararın teknik bir sonucu var.</p><div class="section-title">SİMÜLASYONU KİŞİSELLEŞTİR</div>
<label for="level">Deneyim seviyen<select data-testid="level" id="level"><option value="beginner" ${state.level==='beginner'?'selected':''}>Yeni başladım — rehberli</option><option value="expert" ${state.level==='expert'?'selected':''}>Deneyimliyim — 60 sn karar süresi</option></select></label>
<label for="role">Rolün<select data-testid="role" id="role"><option value="developer" ${state.role==='developer'?'selected':''}>Yazılım geliştirici</option><option value="tester" ${state.role==='tester'?'selected':''}>Test mühendisi</option><option value="lead" ${state.role==='lead'?'selected':''}>Teknik lider</option></select></label>
<label for="goal">Öğrenme hedefin<select data-testid="goal" id="goal"><option value="testing" ${state.goal==='testing'?'selected':''}>Test ve doğrulama</option><option value="security" ${state.goal==='security'?'selected':''}>Veri güvenliği</option><option value="architecture" ${state.goal==='architecture'?'selected':''}>Mimari kararlar</option></select></label>
<button data-testid="start" class="primary" data-action="start">SİMÜLASYONU BAŞLAT <span>↗</span></button><p class="micro">3 karar · 2 olası son · Gerçek hasta verisi kullanılmaz</p></section>`;}

function scene() {
 const scene = scenes[state.step];
 const progress = Math.round(state.step/3*100);
 const explain = state.selection ? scene.options.find(o=>o.id===state.selection) : null;
 const tutorText = state.tutor || stagePrompts[state.step];
 return `<section class="panel scene" data-testid="scene"><div class="progress"><span>VAKA 001 / KARAR ${state.step+1}–3</span><span>${progress}% TAMAMLANDI</span></div><div class="track" role="progressbar" aria-valuenow="${progress}" aria-valuemin="0" aria-valuemax="100"><div style="width:${progress}%"></div></div><div class="scene-top"><span class="eyebrow">${scene.tag} / ${scene.clock}</span>${state.level==='expert'?`<span data-testid="timer" class="timer" aria-live="off">⏱ ${state.seconds} SN</span>`:''}</div><div class="scene-icon" aria-hidden="true">${scene.icon}</div><h1>${scene.title}</h1><p class="lead">${roles[state.role]} olarak, ${scene.story}</p><p class="goal">ODAK: ${goals[state.goal]}</p><h2>${scene.question}</h2><div class="options">${scene.options.map(o=>`<button data-testid="option-${o.id}" data-action="choose" data-value="${o.id}" ${state.selection?'disabled':''} class="option ${state.selection===o.id?'selected':''}"><b>${o.id}</b><span>${o.label}</span><span aria-hidden="true">↗</span></button>`).join('')}</div>
 ${explain ? `<div data-testid="feedback" class="feedback" aria-live="polite"><div class="eyebrow">KARARIN TEKNİK SONUCU</div><p>${explain.result}</p><p class="subtle">${state.selection==='A'?'Kontrollü yaklaşım seçtin.':'Seçimin yeni riskler doğurdu. Bir sonraki adımda etkisini düşün.'}</p><button data-testid="next" data-action="next" class="primary">${state.step===2?'SONUCU GÖR':'SONRAKİ KARAR'} <span>→</span></button></div>` : `<div class="tutor" data-testid="tutor"><div class="tutor-heading">✧ AI TUTOR · SOKRATİK REHBER</div><p id="tutor-response" aria-live="polite">${escapeHtml(tutorText)}</p>${(state.level==='beginner'||state.hint)?`<p class="hint" data-testid="hint">İpucu: ${scene.hint}</p>`:''}
 <form id="tutor-form"><label for="student-input">Tutor'a düşünceni sor <span class="optional">(isteğe bağlı)</span></label><div class="ask-row"><input id="student-input" name="student-input" maxlength="500" placeholder="Örn. Şema değiştiyse ne olur?" autocomplete="off" aria-label="Tutor'a soru" required><button data-testid="ask-tutor" type="submit">SOR</button></div><p class="tiny-note">Tutor yönlendirici sorular üretir; doğru şıkkı söylemez. Bu sürüm çevrimdışı kural tabanlıdır.</p></form><div class="tutor-actions"><button data-action="hint" data-testid="show-hint">İpucu göster</button><button data-action="more">Bir soru daha sor</button></div></div>`}</section>`;
}
function ending(){
 const good = state.choices.length===3&&state.choices.every(x=>x==='A');
 return `<section class="panel ending" data-testid="ending"><div class="eyebrow">VAKA 001 / TAMAMLANDI</div><div class="end-icon">${good?'✓':'!'}</div><div class="end-tag">${good?'SON A / GÜVENLİ TOPARLANMA':'SON B / RİSKLİ TOPARLANMA'}</div><h1>${good?'Sistem ayakta.\nVeriler güvende.':'Sistem açıldı.\nRiskler sürüyor.'}</h1><p class="lead">${good?'08:25 — Kritik akışlar doğrulandı, loglar maskelendi ve hizmet kontrollü şekilde geri döndü.':'08:25 — Hizmet geri döndü; ancak seçilen yollara bağlı olarak regresyon, uyumluluk veya kişisel veri ifşası riski oluştu.'}</p><div class="summary"><h2>Karar günlüğün</h2>${state.choices.map((c,i)=>`<div class="summary-row"><span>${String(i+1).padStart(2,'0')} · ${scenes[i].tag}</span><b>${c} ${c==='A'?'✓':'⚠'}</b></div>`).join('')}</div><div class="tutor"><div class="tutor-heading">✧ ÖĞRENME NOTU</div><p>Bir sistemi yeniden çalıştırmak ile güvenli ve doğrulanmış biçimde hizmete almak aynı şey değildir. Her karar için kanıt, test ve veri minimizasyonu gerekir.</p></div><button data-testid="restart" data-action="restart" class="primary">YENİDEN OYNA <span>↻</span></button></section>`;
}
function stopTimer(){if(state.interval){clearInterval(state.interval);state.interval=null;}}
function startTimer(){stopTimer();if(state.level!=='expert'||state.page!=='scene'||state.selection)return;state.interval=setInterval(()=>{if(state.page!=='scene'||state.selection){stopTimer();return;}state.seconds=Math.max(0,state.seconds-1);const el=document.querySelector('[data-testid="timer"]');if(el)el.textContent=`⏱ ${state.seconds} SN`;if(state.seconds===0){choose('B');}},1000);}
function render(){root.innerHTML=`<main class="app"><header><div class="brand"><span class="logo">✦</span><div><strong>SE PRIMER</strong><small>ETKİLEŞİMLİ MÜHENDİSLİK HİKÂYESİ</small></div></div><span class="status">● SİMÜLASYON</span></header>${state.page==='intro'?intro():state.page==='scene'?scene():ending()}<footer>SE PRIMER © 2026 <span>YZM301 · YAZILIM TEST VE GERÇEKLEME</span></footer></main>`;}
function choose(option){if(state.page!=='scene'||state.selection||!['A','B'].includes(option))return;state.selection=option;state.choices.push(option);stopTimer();render();}
function next(){if(!state.selection)return;state.step+=1;state.selection=null;state.tutor='';state.hint=false;state.seconds=60;if(state.step===3){state.page='end';stopTimer();}render();startTimer();}
function restart(){stopTimer();Object.assign(state,{page:'intro',step:0,choices:[],selection:null,tutor:'',hint:false,seconds:60});render();}
root.addEventListener('click',event=>{
 const button=event.target.closest('button[data-action]');if(!button||button.disabled)return;
 switch(button.dataset.action){case'start':state.page='scene';render();startTimer();break;case'choose':choose(button.dataset.value);break;case'next':next();break;case'restart':restart();break;case'hint':state.hint=true;render();break;case'more':state.tutor=tutorRespond('Bir soru daha sor',state.step,state).text;render();break;}
});
root.addEventListener('change',event=>{if(['level','role','goal'].includes(event.target.id))state[event.target.id]=event.target.value;});
root.addEventListener('submit',event=>{
 if(event.target.id!=='tutor-form')return;event.preventDefault();const input=event.target.elements['student-input'];if(!input.value.trim())return;
 const response=tutorRespond(input.value,state.step,state);state.tutor=response.text;state.tutorCategory=response.category;document.querySelector('#tutor-response').textContent=response.text;input.value='';
});
render();
