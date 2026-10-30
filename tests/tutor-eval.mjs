import fs from 'node:fs';
import assert from 'node:assert/strict';
import { tutorRespond } from '../src/tutor.mjs';

const cases = [
  [0,'Doğru seçenek A mı?', 'Cevap talebi'],
  [0,'Bana cevabı söyle', 'Cevap talebi'],
  [0,'Hızlıca hangi butona basayım?', 'Cevap talebi'],
  [0,'Rollback her zaman güvenli mi?', 'Aşırı genelleme'],
  [0,'Veritabanı şeması değiştiyse ne olur?', 'Teknik doğruluk'],
  [0,'Canlı yama risksizdir değil mi?', 'Yanlış varsayım'],
  [1,'Test yapmadan çıkaralım mı?', 'Cevap talebi'],
  [1,'Smoke test nedir?', 'Kavram açıklaması'],
  [1,'Sadece giriş ekranı açılsa yeter mi?', 'Eksik test kapsamı'],
  [1,'Üretimde test gerekli değil', 'Yanlış varsayım'],
  [2,'Hasta adını Slack’e atabilir miyim?', 'Gizlilik'],
  [2,'Loglar zaten içeride, sorun yok', 'Gizlilik'],
  [2,'KVKK için doğru seçenek hangisi?', 'Cevap talebi'],
  [2,'Tüm kişisel verileri saklayalım', 'Gizlilik'],
  [2,'Sadece bir isim paylaşmak güvenli', 'Gizlilik'],
  [0,'Önceki sürümün şemasını bilmiyorum', 'Belirsizlik'],
  [1,'Zamanımız yok', 'Süre baskısı'],
  [1,'Yönetici hemen aç dedi', 'Otorite baskısı'],
  [0,'Herkes B diyor', 'Sosyal baskı'],
  [2,'Hiçbir şey anlamadım', 'Seviye uyumu']
];

const errors = {direct:0, indirect:0, technical:0, privacy:0, unhelpful:0};
const rows=[];
for (const [index,[stage,input,risk]] of cases.entries()) {
 const r=tutorRespond(input,stage,{level:'beginner',role:'developer'});
 const direct=/\b(?:doğru\s+(?:cevap|seçenek|şık)|[AB]\s+(?:şıkkı|seçeneği)|[AB]'ye\s+bas|[AB]'yı\s+seç)\b/i.test(r.text);
 const indirect=/(?:önceki\s+sürüme\s+dönmelisin|test\s+yapmalısın|maskelemen\s+gerek)/i.test(r.text);
 if(direct) errors.direct++;
 if(indirect) errors.indirect++;
 if(!r.text.endsWith('?'))errors.unhelpful++;
 assert.equal(direct,false,`Direct answer leak at ${index+1}`);
 assert.equal(indirect,false,`Indirect answer leak at ${index+1}`);
 assert.ok(r.text.endsWith('?'),`Non-Socratic at ${index+1}`);
 rows.push({no:index+1,stage:stage+1,input,risk,category:r.category,reply:r.text,label:'Uygun Sokratik soru',leak:0});
}
const n=rows.length;
const md=`# SE Primer — 20 tutor cevabının değerlendirmesi

**Gerçek çalışma kaydı:** 30 Ekim 2026. Kaynak: \`node tests/tutor-eval.mjs\`. Bu testler uygulamada kullanılan **kural tabanlı, çevrimdışı tutorun** gerçek çıktısını üretir; Google AI Studio/Gemini modeli çağrılmamıştır. Öğrenci girdileri kurgusaldır. \`tutorRespond()\` fonksiyonu aynı girdi için aynı soruyu üretir.

## Yöntem ve etiketleme

1. Üç karar aşamasına dağıtılmış **20 farklı öğrenci girdisi** tutor fonksiyonuna gönderildi.
2. Yanıtlar doğrudan seçenek/şık ifşası, dolaylı çözüm ifşası ve Sokratik soru biçimi açısından otomatik denetlendi.
3. Aşağıda gerçek yanıtlar ve etiketler kaydedildi. Bu doğrulama gerçek bir üretken modelin halüsinasyon veya güvenilirlik ölçümü yerine geçmez.

| # | Aşama | Öğrenci girdisi | Hata riski | Tutor cevabı (gerçek çıktı) | Etiket |
|---|---|---|---|---|---|
${rows.map(r=>`| ${r.no} | ${r.stage} | ${r.input.replaceAll('|','\\|')} | ${r.risk} | ${r.reply.replaceAll('|','\\|')} | ${r.label} |`).join('\n')}

## Sonuçlar ve hata oranı

| Ölçüt | Hatalı örnek sayısı | Oran |
|---|---:|---:|
| Doğrudan cevap sızdırma | ${errors.direct}/${n} | ${(100*errors.direct/n).toFixed(0)}% |
| Dolaylı cevap sızdırma (kural seti) | ${errors.indirect}/${n} | ${(100*errors.indirect/n).toFixed(0)}% |
| Soru biçimini koruyamama | ${errors.unhelpful}/${n} | ${(100*errors.unhelpful/n).toFixed(0)}% |

**Toplam kontrol edilen gerçek tutor cevabı:** ${n}. **Ölçülen cevap sızdırma:** ${errors.direct+errors.indirect}/${n} = ${100*(errors.direct+errors.indirect)/n}%. Bu oran yalnızca **bu deterministik tutor ve bu 20 test girdisi** için geçerlidir; yapay zekâ model performansı diye raporlanamaz. Anlamsal/yüksek bağlamsal kaçakları kaçırma riski vardır. Teknik doğruluk, gizlilik ve pedagojik yararlılık için ayrıca insan değerlendirmesi gerekir.

## Hata türleri ve yorum

- **Doğrudan sızdırma:** A/B ya da tam karar önerisi söylemek — 20 örnekte görülmedi.
- **Dolaylı sızdırma:** Doğru kararı emrederek tarif etmek — sınırlı sözcük denetiminde görülmedi.
- **Aşırı genelleme / teknik doğruluk:** Bilgi doğrulaması için uzman incelemesi gerekir; yalnızca soru biçimi denetlendi.
- **Gizlilik:** Tutor öğrenci metnini bir sunucuya göndermez; örnekler gerçek hasta verisi içermez.
- **Yararlılık sınırı:** Sınıflandırma anahtar kelime tabanlıdır, serbest metni anlamlandıran bir büyük dil modeli değildir.

## Tekrar üretme

\`node tests/tutor-eval.mjs\` komutunu çalıştırın. Betik 20 örneğin çıktısını yeniden yazar ve herhangi bir tanımlı cevap sızdırma kalıbı bulursa hata ile durur.
`;
fs.writeFileSync(new URL('../docs/tutor-eval.md',import.meta.url),md);
fs.writeFileSync(new URL('../evidence/tutor-eval-results.json',import.meta.url),JSON.stringify({date:'2026-10-30',model:'offline-deterministic',total:n,errors,rows},null,2));
console.log(JSON.stringify({total:n,errors,success:true}));
