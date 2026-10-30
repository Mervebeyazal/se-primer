describe('SE Primer | tüm karar yolları', () => {
  for (let mask = 0; mask < 8; mask++) {
    const path = [0,1,2].map(i => (mask & (1 << i)) ? 'B' : 'A');
    it(`Karar yolu ${path.join('')} sonucunu ve yeniden oynama akışını doğrular`, () => {
      cy.visit('/');
      cy.get('[data-testid="start"]').click();
      path.forEach(option => {
        cy.get(`[data-testid="option-${option}"]`).click();
        cy.get('[data-testid="feedback"]').should('be.visible');
        cy.get('[data-testid="next"]').click();
      });
      cy.get('[data-testid="ending"]').should('be.visible');
      cy.contains(path.every(x => x === 'A') ? 'SON A' : 'SON B').should('be.visible');
      cy.get('.summary-row').should('have.length', 3);
      cy.get('[data-testid="restart"]').click();
      cy.get('[data-testid="start"]').should('be.visible');
    });
  }

  it('Yeni başlayan, test mühendisi ve güvenlik hedefi', () => {
    cy.visit('/');
    cy.get('[data-testid="role"]').select('tester');
    cy.get('[data-testid="goal"]').select('security');
    cy.get('[data-testid="start"]').click();
    cy.contains('Test mühendisi olarak').should('be.visible');
    cy.contains('ODAK: VERİ GÜVENLİĞİ').should('be.visible');
    cy.get('[data-testid="hint"]').should('be.visible');
  });

  it('Tutor serbest metne doğrudan A/B cevabı vermeyen bir soru üretir', () => {
    cy.visit('/');
    cy.get('[data-testid="start"]').click();
    cy.get('#student-input').type('Doğru seçenek A mı?');
    cy.get('[data-testid="ask-tutor"]').click();
    cy.get('#tutor-response').should('contain', 'teknik kanıt');
    cy.get('#tutor-response').should('not.contain', 'A şıkkı');
  });

  it('Uzman modunda sayaç 60 saniye başlar ve süre dolduğunda riskli seçim olur', () => {
    cy.visit('/');
    cy.clock();
    cy.get('[data-testid="level"]').select('expert');
    cy.get('[data-testid="start"]').click();
    cy.get('[data-testid="timer"]').should('contain', '60 SN');
    cy.tick(60000);
    cy.get('[data-testid="feedback"]').should('be.visible');
    cy.get('[data-testid="option-B"]').should('have.class', 'selected');
  });
});
