(() => {
  'use strict';

  const section = document.getElementById('fitness-passes');
  if (!section || section.dataset.fitnessPassesReady === 'true') return;

  const switcher = section.querySelector('[data-fitness-passes-switcher]');
  const buttons = switcher ? [...switcher.querySelectorAll('[data-fitness-passes-target]')] : [];
  const panels = [...section.querySelectorAll('[data-fitness-passes-panel]')];
  if (buttons.length !== 2 || panels.length !== 2) return;
  if (buttons.some(button => !panels.some(panel => panel.id === button.dataset.fitnessPassesTarget))) return;

  const activate = panelId => {
    panels.forEach(panel => { panel.hidden = panel.id !== panelId; });
    buttons.forEach(button => {
      const selected = button.dataset.fitnessPassesTarget === panelId;
      button.classList.toggle('active', selected);
      button.setAttribute('aria-pressed', String(selected));
    });
  };

  const revealHashTarget = () => {
    let targetId;
    try { targetId = decodeURIComponent(window.location.hash.slice(1)); }
    catch { return; }

    if (!targetId || targetId === section.id) {
      activate(buttons[0].dataset.fitnessPassesTarget);
      return;
    }

    const target = document.getElementById(targetId);
    if (!target) return;
    const panel = panels.find(candidate => candidate === target || candidate.contains(target));
    if (!panel) return;

    const wasHidden = panel.hidden;
    activate(panel.id);
    if (wasHidden) {
      const scrollTarget = target.matches('.fitness-personal-title, .fitness-personal-panel-title') ? panel : target;
      window.requestAnimationFrame(() => { scrollTarget.scrollIntoView({ block: 'start' }); });
    }
  };

  buttons.forEach(button => button.addEventListener('click', () => {
    activate(button.dataset.fitnessPassesTarget);
  }));

  activate(buttons[0].dataset.fitnessPassesTarget);
  section.dataset.fitnessPassesReady = 'true';
  switcher.hidden = false;
  revealHashTarget();
  window.addEventListener('hashchange', revealHashTarget);
})();
