// Diferansiyel test (parite testi) ve hata toleransı.
// İki farklı sistem aynı 5 referans girdiye aynı cevabı vermelidir:
//   (1) Test Kahini (Oracle): Python onnxruntime  -> tests/parite.json  (python tests/parite.py --yaz)
//   (2) Uygulama:             tarayıcıda onnxruntime-web, model tanı paneli (?tani=1), data-cy="p"
// Kabul: |p_uygulama - p_oracle| < tolerans (1e-4).
import parite from '../../tests/parite.json';

const MODEL_BASE = Cypress.env('MODEL_BASE'); // boşsa uygulamanın varsayılan modeli (./model/) kullanılır

describe('Diferansiyel test: tarayıcı çıkarımı = Python Oracle', () => {
  it('parite.json geçerli: 5 örnek ve 1e-4 tolerans', () => {
    expect(parite.ornekler).to.have.length(5);
    expect(parite.tolerans).to.equal(1e-4);
  });

  parite.ornekler.forEach((o) => {
    it(`${o.ad}: fark < ${parite.tolerans}`, () => {
      cy.visit('/?tani=1' + (MODEL_BASE ? `&modelBase=${MODEL_BASE}` : ''));
      cy.get('[data-cy="model-durum"]', { timeout: 30000 }).should('contain', 'model hazır');
      Object.entries(o.girdi).forEach(([ad, deger]) => {
        cy.get(`[data-cy="in-${ad}"]`).clear().type(String(deger));
      });
      cy.get('[data-cy="hesapla"]').click();
      cy.get('[data-cy="p"]', { timeout: 10000 }).invoke('text').should('match', /^\d\.\d+$/);
      cy.get('[data-cy="p"]').invoke('text').then((metin) => {
        const fark = Math.abs(parseFloat(metin) - o.p);
        expect(fark, `uygulama ${metin} vs oracle ${o.p}`).to.be.lessThan(parite.tolerans);
      });
      cy.get('[data-cy="mode"]').should('have.text', o.mod);
    });
  });
});
