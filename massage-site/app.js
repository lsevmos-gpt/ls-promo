'use strict';
(() => {
  const menu = document.querySelector('.mobile-nav');
  const menuToggle = document.querySelector('.menu-toggle');
  if (menu && menuToggle) {
    const setMenu = open => {
      menu.hidden = !open;
      menuToggle.setAttribute('aria-expanded', String(open));
      menuToggle.setAttribute('aria-label', open ? 'Закрыть меню' : 'Открыть меню');
      document.body.classList.toggle('menu-open', open);
    };
    menuToggle.addEventListener('click', () => setMenu(menu.hidden));
    menu.querySelectorAll('a').forEach(a => a.addEventListener('click', () => setMenu(false)));
    document.addEventListener('keydown', event => { if (event.key === 'Escape') setMenu(false); });
    window.addEventListener('resize', () => { if (window.innerWidth > 960) setMenu(false); });
  }
  const tabs = [...document.querySelectorAll('[role="tab"][data-panel-id]')];
  const activate = (tab, focus = false) => {
    if (!tab) return;
    for (const t of tabs) {
      const active = (t === tab);
      t.setAttribute('aria-selected', String(active));
      t.tabIndex = active ? 0 : -1;
      const panel = document.getElementById('panel-' + t.dataset.panelId);
      if (panel) panel.hidden = !active;
    }
    if (focus) tab.focus();
  };
  tabs.forEach((tab, i) => {
    tab.addEventListener('click', () => activate(tab));
    tab.addEventListener('keydown', ev => {
      if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(ev.key)) return;
      ev.preventDefault();
      const index = ev.key === 'Home' ? 0 : ev.key === 'End' ? tabs.length-1 : ev.key === 'ArrowRight' ? (i+1)%tabs.length : (i+tabs.length-1)%tabs.length;
      activate(tabs[index], true);
    });
  });
  const ref = location.hash.replace(/^#price-/, '');
  const selected = tabs.find(t => t.dataset.panelId === ref);
  if (location.hash.startsWith('#price-') && selected) activate(selected);
})();
