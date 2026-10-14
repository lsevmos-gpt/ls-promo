'use strict';
(() => {
  const menuButton = document.querySelector('.menu-toggle');
  const menu = document.getElementById('main-nav');
  if (menuButton && menu) {
    const setOpen = (isOpen) => {
      menu.classList.toggle('open', isOpen);
      document.body.classList.toggle('menu-open', isOpen);
      menuButton.setAttribute('aria-expanded', String(isOpen));
      menuButton.setAttribute('aria-label', isOpen ? 'Закрыть меню' : 'Открыть меню');
    };
    menuButton.addEventListener('click', () => setOpen(menuButton.getAttribute('aria-expanded') !== 'true'));
    menu.addEventListener('click', (event) => {
      if (event.target.closest('a')) setOpen(false);
    });
    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape') setOpen(false);
    });
    window.addEventListener('resize', () => {
      if (window.matchMedia('(min-width: 681px)').matches) setOpen(false);
    });
  }

  const tabs = [...document.querySelectorAll('[role="tab"][data-tab]')];
  const selectTab = (newTab, shouldFocus = false) => {
    const wanted = newTab.dataset.tab;
    for (const tab of tabs) {
      const selected = tab === newTab;
      tab.setAttribute('aria-selected', String(selected));
      tab.tabIndex = selected ? 0 : -1;
      const panel = document.getElementById(`price-${tab.dataset.tab}`);
      if (panel) panel.hidden = !selected;
    }
    if (shouldFocus) newTab.focus();
    if (history.replaceState && wanted) {
      // Preserve anchor if the visitor linked directly to a specialist's tab.
      if (location.hash.startsWith('#price-')) history.replaceState(null, '', '#price-' + wanted);
    }
  };
  for (const tab of tabs) {
    tab.addEventListener('click', () => selectTab(tab));
    tab.addEventListener('keydown', (event) => {
      if (!['ArrowRight','ArrowLeft','Home','End'].includes(event.key)) return;
      event.preventDefault();
      const i = tabs.indexOf(tab);
      const next = event.key === 'Home' ? 0 : event.key === 'End' ? tabs.length-1 : event.key === 'ArrowRight' ? (i+1)%tabs.length : (i-1+tabs.length)%tabs.length;
      selectTab(tabs[next], true);
    });
  }
  if (location.hash.startsWith('#price-')) {
    const tab = tabs.find(t => `#price-${t.dataset.tab}` === location.hash);
    if (tab) selectTab(tab);
  }
})();
