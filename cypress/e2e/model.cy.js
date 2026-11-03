// v2 kabul örnekleri 6-8: model oyunun davranışını gerçekten değiştirir.
// `?p=...` test kancası olasılığı sabitler (modeli atlar); böylece mod politikası deterministik sınanır.
// Modelin kendisinin doğruluğu parite.cy.js ve train.py eval kapısıyla sınanır.
const oyna = (secimler) => {
  cy.get('[data-testid="start"]').click();
  secimler.forEach((o) => {
    cy.get(`[data-testid="option-${o}"]`).click();
    cy.get('[data-testid="next"]').click();
  });
};

describe('v2: modelin kararı oyunun davranışını değiştirir', () => {
  it('Kabul 6 — Destek: p=0.72 -> ipucu otomatik, tutor soru sorar, sayaç yok (deneyimli olsa da)', () => {
    cy.visit('/?p=0.72');
    cy.get('[data-testid="level"]').select('expert');
    oyna(['A']); // sahne 2
    cy.get('[data-cy="mode"]').should('have.text', 'destek');
    cy.get('[data-cy="p"]').should('have.text', '0.720000');
    cy.get('[data-testid="hint"]').should('be.visible');
    cy.get('[data-testid="timer"]').should('not.exist');
    cy.get('#tutor-response').should('contain', 'Birlikte küçük adımlarla');
  });

  it('Kabul 7 — Meydan: p=0.10 -> ipucu gizli (yeni başlayan olsa da), sonuçta "Neden?" notu', () => {
    cy.visit('/?p=0.10');
    cy.get('[data-testid="start"]').click();
    cy.get('[data-testid="hint"]').should('be.visible'); // sahne 1: model yok, v1 davranışı
    cy.get('[data-testid="option-A"]').click();
    cy.get('[data-testid="next"]').click();
    cy.get('[data-testid="option-A"]').click();
    cy.get('[data-testid="next"]').click(); // sahne 3
    cy.get('[data-cy="mode"]').should('have.text', 'meydan');
    cy.get('[data-testid="hint"]').should('not.exist');
    cy.get('[data-testid="show-hint"]').should('not.exist');
    cy.get('[data-testid="option-A"]').click();
    cy.get('[data-cy="neden"]').should('be.visible').and('contain', 'KVKK');
  });

  it('Normal: p=0.40 -> v1 davranışı (yeni başlayan ipucu görür, "Neden?" yok)', () => {
    cy.visit('/?p=0.40');
    oyna(['A']);
    cy.get('[data-cy="mode"]').should('have.text', 'normal');
    cy.get('[data-testid="hint"]').should('be.visible');
    cy.get('[data-testid="option-A"]').click();
    cy.get('[data-cy="neden"]').should('not.exist');
  });

  it('Kabul 8 — Sahne 1 modelsiz: v1 davranışı aynen korunur', () => {
    cy.visit('/?p=0.9');
    cy.get('[data-testid="start"]').click();
    cy.get('[data-testid="mode-badge"]').should('not.exist');
    cy.get('[data-testid="hint"]').should('be.visible');
  });

  it('Model indirilemezse oyun kilitlenmez, normal akışla sona varır', () => {
    cy.intercept('**/model/model.onnx', { statusCode: 404, body: '' });
    cy.visit('/');
    oyna(['A', 'A']);
    cy.wait(1500);
    cy.get('[data-testid="mode-badge"]').should('not.exist');
    cy.get('[data-testid="option-A"]').click();
    cy.get('[data-testid="next"]').click();
    cy.get('[data-testid="ending"]').should('be.visible');
  });

  it('Canary %0 (rollback): yayin.json yuzde=0 ise model uygulanmaz, v1 davranışı sürer', () => {
    cy.intercept('**/src/yayin.json', { body: { yuzde: 0 } });
    cy.visit('/?p=0.9');
    cy.get('[data-testid="level"]').select('expert');
    oyna(['A']);
    cy.wait(1500);
    cy.get('[data-testid="mode-badge"]').should('not.exist');
    cy.get('[data-testid="timer"]').should('be.visible');
  });

  it('Shadow: model çalışır (p hesaplanır) ama oyunun davranışı değişmez', () => {
    cy.intercept('**/src/yayin.json', { body: { golge: true } });
    cy.visit('/?p=0.9');
    cy.get('[data-testid="level"]').select('expert');
    oyna(['A']);
    cy.get('[data-cy="golge-mod"]').should('have.text', 'destek');
    cy.get('[data-testid="mode-badge"]').should('not.exist');
    cy.get('[data-testid="timer"]').should('be.visible');
    cy.get('#tutor-response').should('not.contain', 'Birlikte küçük adımlarla');
  });

  it('Veri toplama modunda model kapalıdır ve kayıt 3 satır tutar', () => {
    cy.visit('/?veri=1&p=0.9');
    oyna(['A', 'B']);
    cy.wait(1500);
    cy.get('[data-testid="mode-badge"]').should('not.exist');
    cy.get('[data-testid="option-A"]').click();
    cy.get('[data-testid="next"]').click();
    cy.get('[data-testid="collect-count"]').should('contain', '1 oturum, 3 karar');
    cy.window().then((w) => {
      const satirlar = JSON.parse(w.localStorage.getItem('primer_v2_veri'));
      expect(satirlar).to.have.length(3);
      expect(satirlar.map((s) => s.secim)).to.deep.equal(['A', 'B', 'A']);
    });
  });
});
