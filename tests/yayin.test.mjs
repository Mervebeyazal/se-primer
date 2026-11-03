// node tests/yayin.test.mjs: Canary / aşamalı geçiş kovalama ve yayın yapılandırması.
import assert from 'node:assert/strict';
import { kovaNo, kovadaMi, yayinOku, YAYIN_VARSAYILAN, tabanBelirle } from '../src/model.mjs';
import { yeniOturumId } from '../src/telemetry.mjs';

let sayi = 0;
const gecti = (ad) => { sayi += 1; console.log('PASS', ad); };

assert.equal(kovaNo('000000000000'), 0);
assert.equal(kovaNo('ffffffffffff'), 95); // 0xffffffff % 100
assert.equal(kovaNo('0000000a0000'), 10);
gecti('kovaNo sabit ve deterministik');

assert.equal(kovadaMi('0000000a0000', 0), false); // yüzde 0: kapalı (rollback)
assert.equal(kovadaMi('ffffffffffff', 100), true); // yüzde 100: herkes
gecti('yüzde 0 = kapalı, yüzde 100 = herkes');

// Aşamalı geçiş tek yönlüdür: 5 ⊂ 25 ⊂ 50 ⊂ 100 (içeri giren oturum genişlerken dışarı çıkmaz)
const ids = Array.from({ length: 5000 }, () => yeniOturumId());
const grup = (y) => new Set(ids.filter((i) => kovadaMi(i, y)));
const [g5, g25, g50, g100] = [5, 25, 50, 100].map(grup);
for (const [kucuk, buyuk] of [[g5, g25], [g25, g50], [g50, g100]]) {
  for (const i of kucuk) assert.ok(buyuk.has(i));
}
assert.equal(g100.size, ids.length);
gecti('aşamalı geçişte gruplar iç içe (5 ⊂ 25 ⊂ 50 ⊂ 100)');

// Dağılım: 5000 rastgele oturumda %5 / %25 / %50 hedefe yakın (±%2 mutlak)
for (const [y, g] of [[5, g5], [25, g25], [50, g50]]) {
  const oran = (g.size / ids.length) * 100;
  assert.ok(Math.abs(oran - y) < 2, `%${y} hedefi, gerçekleşen %${oran.toFixed(1)}`);
}
gecti('rastgele kimliklerde kovalar eşit dağılır');

// yapılandırma okuma
const sahte = (govde, ok = true) => async () => ({ ok, json: async () => govde });
assert.deepEqual(await yayinOku(sahte({ yuzde: 5, golge: true })), { model_taban: './model/', yuzde: 5, golge: true });
assert.deepEqual(await yayinOku(sahte({}, false)), YAYIN_VARSAYILAN); // dosya yok -> varsayılan
assert.deepEqual(await yayinOku(async () => { throw new Error('ağ'); }), YAYIN_VARSAYILAN);
gecti('yayinOku: kısmi dosya birleşir, dosya yoksa/ağ hatasında varsayılan');

assert.equal(tabanBelirle('', './model/'), './model/');
assert.equal(tabanBelirle('?modelBase=./x', './model/'), './x/');
assert.equal(tabanBelirle('', 'https://huggingface.co/u/r/resolve/abc/'), 'https://huggingface.co/u/r/resolve/abc/');
gecti('tabanBelirle: yayin.json değeri varsayılan, ?modelBase= test için geçersiz kılar');

console.log(`\n${sayi} kontrol geçti`);
