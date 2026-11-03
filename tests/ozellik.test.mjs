// Node ile çalışır: node tests/ozellik.test.mjs
// JS tarafı (src/telemetry.mjs) özellik türetmenin ve mod seçiminin beklenen değerleri verdiğini sınar.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { ozellikVektoru, modSec, csvUret, satirOlustur, KOLONLAR, OZELLIKLER } from '../src/telemetry.mjs';

const ornek = JSON.parse(readFileSync(new URL('./ozellik_ornekleri.json', import.meta.url)));
let sayi = 0;
const gecti = (ad) => { sayi += 1; console.log('PASS', ad); };

for (const o of ornek.oturumlar) {
  for (const [sahne, beklenen] of Object.entries(o.beklenen)) {
    const s = Number(sahne);
    const hedef = o.satirlar.find((r) => r.sahne_no === s);
    const onceki = o.satirlar.filter((r) => r.sahne_no < s);
    const vektor = ozellikVektoru(onceki, s, hedef ? hedef.seviye : 0);
    assert.deepEqual(vektor, beklenen, `${o.ad} / sahne ${s}`);
    gecti(`ozellikVektoru: ${o.ad} / sahne ${s}`);
  }
}

assert.equal(OZELLIKLER.length, 7);
gecti('OZELLIKLER 7 girdi');

// mod politikası (spec.md: destek >= 0.60, meydan <= 0.25)
assert.equal(modSec(0.72), 'destek');
assert.equal(modSec(0.60), 'destek');
assert.equal(modSec(0.10), 'meydan');
assert.equal(modSec(0.25), 'meydan');
assert.equal(modSec(0.4), 'normal');
assert.equal(modSec(null), 'normal');
assert.equal(modSec(undefined), 'normal');
assert.equal(modSec(NaN), 'normal');
gecti('modSec eşikleri ve güvenli geri düşüş (null/NaN -> normal)');

// CSV sözleşmesi
const satir = satirOlustur({ oturumId: 'aabbccddeeff', sahneNo: 2, seviye: 1, kararSn: 12.34, okumaSn: 5.06, tutorSoru: 1, ipucu: 0, secim: 'B', sureDoldu: 0 });
assert.equal(satir.secim_b, 1);
assert.equal(satir.karar_suresi_sn, 12.3);
assert.equal(satir.okuma_suresi_sn, 5.1);
const csv = csvUret([satir]).trim().split('\n');
assert.equal(csv[0], KOLONLAR.join(','));
assert.equal(csv[1], 'aabbccddeeff,gercek,2,1,12.3,5.1,1,0,B,0,1');
gecti('CSV başlığı ve satır biçimi');

console.log(`\n${sayi} kontrol geçti`);
