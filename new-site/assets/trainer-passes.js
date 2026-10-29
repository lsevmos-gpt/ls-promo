(() => {
  'use strict';
  const number = new Intl.NumberFormat('ru-RU');
  document.querySelectorAll('[data-trainer-passes]').forEach(block => {
    const buttons = [...block.querySelectorAll('[data-trainer-sessions]')];
    const cards = [...block.querySelectorAll('[data-trainer-pass]')];
    const setSessions = sessions => {
      // Resolve both prices before updating the view, so an incomplete package
      // cannot leave the two format cards showing different session counts.
      const prices = cards.map(card => Number(card.dataset['price' + sessions]));
      if (prices.some(price => !Number.isFinite(price) || price <= 0)) return;
      buttons.forEach(button => {
        const active = Number(button.dataset.trainerSessions) === sessions;
        button.classList.toggle('active', active);
        button.setAttribute('aria-pressed', String(active));
      });
      cards.forEach((card, i) => {
        card.querySelector('[data-trainer-price]').textContent = number.format(prices[i]);
        card.querySelector('[data-trainer-quantity]').textContent = 'За ' + sessions + ' тренировок с тренером';
      });
    };
    buttons.forEach(button => {
      button.disabled = false;
      button.addEventListener('click', () => setSessions(Number(button.dataset.trainerSessions)));
    });
  });
})();
