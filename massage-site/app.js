'use strict';
(() => {
  const menuButton = document.querySelector('.menu-button');
  const menu = document.getElementById('mobile-nav');
  if (menu && menuButton) {
    function setMenu(open) {
      const newState = !!open;
      menu.classList.toggle('open', newState);
      menuButton.setAttribute('aria-expanded', String(newState));
      menuButton.setAttribute('aria-label', newState ? 'Закрыть меню' : 'Открыть меню');
      document.body.classList.toggle('lock-scroll', newState);
    }
    menuButton.addEventListener('click', () => setMenu(menuButton.getAttribute('aria-expanded') !== 'true'));
    menu.addEventListener('click', e => { if (e.target.closest('a')) setMenu(false); });
    document.addEventListener('keydown', e => { if (e.key === 'Escape') setMenu(false); });
    window.addEventListener('resize', () => { if (window.innerWidth > 920) setMenu(false); });
  }
  const tabs = Array.from(document.querySelectorAll('[role="tab"][data-tab]'));
  function activate(tab, focus=false) {
    if (!tab) return;
    for (const item of tabs) {
      const selected = item === tab;
      item.setAttribute('aria-selected', String(selected));
      item.tabIndex = selected ? 0 : -1;
      const panel = document.getElementById('panel-'+item.dataset.tab);
      if(panel) panel.hidden = !selected;
    }
    if (focus) tab.focus();
  }
  tabs.forEach((tab,i) => {
    tab.addEventListener('click', () => activate(tab));
    tab.addEventListener('keydown', e => {
      if (!['ArrowRight','ArrowLeft','Home','End'].includes(e.key)) return;
      e.preventDefault();
      const j = e.key === 'Home' ? 0 : e.key === 'End' ? tabs.length-1 : e.key === 'ArrowRight' ? (i+1)%tabs.length : (i-1+tabs.length)%tabs.length;
      activate(tabs[j], true);
    });
  });
  if (location.hash.startsWith('#price-')) {
    const target=location.hash.replace('#price-','');
    activate(tabs.find(t=>t.dataset.tab===target));
  }
})();
