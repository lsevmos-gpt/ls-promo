(() => {
  'use strict';
  const data = JSON.parse(document.getElementById('menu-data').textContent);
  const items = new Map(data.items.map(item => [item.id, item]));
  const dialog = document.getElementById('item-dialog');
  const methodDialog = document.getElementById('method-dialog');
  const categoryDialog = document.getElementById('category-dialog');
  const categoryLauncher = document.querySelector('[data-open-categories]');
  const nf = new Intl.NumberFormat('ru-RU');
  const price = value => (Array.isArray(value) ? value.map(v => nf.format(v)).join('–') : nf.format(value)) + ' ₽';
  const variantBox = dialog.querySelector('[data-dialog-variants]');
  const servingLine = dialog.querySelector('[data-dialog-serving]');
  const displayDetails = (item, selected) => {
    const current = selected || item;
    const nutrition = current.nutrition || item.nutrition || {};
    dialog.querySelector('[data-dialog-name]').textContent = current.name || item.name;
    dialog.querySelector('[data-dialog-category]').textContent = data.categories.find(c => c.id === item.category).name;
    dialog.querySelector('[data-dialog-price]').textContent = price(current.price_rub);
    dialog.querySelector('[data-dialog-composition]').textContent = current.composition || item.composition || (item.volume_ml ? 'Объём: ' + item.volume_ml + ' мл.' : 'Состав уточните на баре.');
    servingLine.textContent = current.serving || '';
    servingLine.hidden = !current.serving;
    const nutrients = dialog.querySelector('[data-dialog-nutrition]');
    const label = dialog.querySelector('[data-dialog-nutrition-label]');
    const values = nutrition.values;
    nutrients.hidden = !values;
    label.hidden = !values;
    if (values) {
      for (const key of ['kcal', 'protein', 'fat', 'carbs']) nutrients.querySelector('[data-value="' + key + '"]').textContent = '≈' + values[key];
    }
    dialog.querySelector('[data-dialog-assumption]').textContent = nutrition.assumption || nutrition.reason || '';
    dialog.querySelector('[data-dialog-estimate-note]').hidden = !values || !nutrition.approximate;
  };
  const showItem = id => {
    const item = items.get(id);
    if (!item) return;
    variantBox.replaceChildren();
    const variants = Array.isArray(item.variants) ? item.variants : [];
    variantBox.hidden = variants.length === 0;
    variants.forEach((variant, index) => {
      const choice = document.createElement('button');
      choice.type = 'button';
      choice.className = 'dialog-variant-choice';
      choice.setAttribute('aria-pressed', String(index === 0));
      const name = document.createElement('span');
      name.textContent = variant.name;
      const amount = document.createElement('strong');
      amount.textContent = price(variant.price_rub);
      choice.append(name, amount);
      choice.addEventListener('click', () => {
        variantBox.querySelectorAll('button').forEach(button => button.setAttribute('aria-pressed', String(button === choice)));
        displayDetails(item, variant);
      });
      variantBox.append(choice);
    });
    displayDetails(item, variants[0] || item);
    dialog.showModal();
  };
  document.querySelectorAll('[data-details]').forEach(button => button.addEventListener('click', () => showItem(button.dataset.details)));
  document.querySelectorAll('[data-close-dialog]').forEach(button => button.addEventListener('click', () => button.closest('dialog').close()));
  [dialog, methodDialog, categoryDialog].forEach(modal => modal.addEventListener('click', event => { if (event.target === modal) modal.close(); }));
  document.querySelectorAll('[data-show-method]').forEach(button => button.addEventListener('click', () => methodDialog.showModal()));
  categoryLauncher.addEventListener('click', () => {
    categoryDialog.showModal();
    categoryLauncher.setAttribute('aria-expanded', 'true');
  });
  categoryDialog.addEventListener('close', () => categoryLauncher.setAttribute('aria-expanded', 'false'));
  window.matchMedia('(max-width: 760px)').addEventListener('change', event => {
    if (!event.matches && categoryDialog.open) categoryDialog.close();
  });
  const categoryIds = new Set(['all', ...data.categories.map(category => category.id)]);
  const selectCategory = (id, scroll = true, updateHash = true) => {
    if (!categoryIds.has(id)) return;
    if (categoryDialog.open) categoryDialog.close();
    document.querySelectorAll('[data-menu-filter]').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.menuFilter === id)));
    document.querySelector('.menu-section').dataset.activeCategory = id;
    document.querySelectorAll('[data-menu-category]').forEach(section => { section.hidden = id !== 'all' && section.dataset.menuCategory !== id; });
    const count = data.items.filter(item => id === 'all' || item.category === id).length;
    document.getElementById('menu-status').textContent = 'В разделе: ' + count;
    if (updateHash) history.replaceState(null, '', id === 'all' ? '#menu' : '#menu-' + id);
    if (scroll) document.querySelector('.menu-toolbar').scrollIntoView({ block: 'start', behavior: 'instant' });
    const rail = document.querySelector('.menu-filters');
    const selected = rail.querySelector('[data-menu-filter="' + id + '"]');
    rail.scrollTo({ left: selected.offsetLeft - rail.offsetLeft - (rail.clientWidth - selected.offsetWidth) / 2, behavior: 'instant' });
  };
  document.querySelectorAll('[data-menu-filter]').forEach(button => button.addEventListener('click', () => selectCategory(button.dataset.menuFilter)));
  const readCategoryHash = () => {
    const hash = location.hash;
    if (hash === '#menu') selectCategory('all', false, false);
    else if (hash.startsWith('#menu-')) selectCategory(hash.slice(6), false, false);
  };
  readCategoryHash();
  window.addEventListener('hashchange', readCategoryHash);
  document.getElementById('show-nutrition').addEventListener('change', event => document.body.classList.toggle('nutrition-off', !event.target.checked));

  const videos = [...document.querySelectorAll('.story-video')];
  const visibleVideos = new Map();
  const pausedByUser = new Set();
  let activeVideo = null;
  let manuallySelectedVideo = null;
  let userPausedAutoplay = false;
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const saveData = navigator.connection && navigator.connection.saveData;
  const loadVideo = video => {
    if (!video.getAttribute('src')) {
      video.src = video.dataset.videoSrc;
      video.load();
    }
  };
  const pauseOthers = current => videos.forEach(video => { if (video !== current) video.pause(); });
  const playVideo = (video, manual = false) => {
    activeVideo = video;
    manuallySelectedVideo = manual ? video : null;
    pauseOthers(video);
    loadVideo(video);
    video.play().then(() => {
      if (activeVideo !== video) video.pause();
    }).catch(() => {
      if (activeVideo === video) activeVideo = null;
    });
  };
  videos.forEach(video => {
    const button = document.querySelector('[aria-controls="' + video.id + '"]');
    const label = button.querySelector('[data-play-label]');
    const icon = button.querySelector('[aria-hidden]');
    const update = () => {
      const playing = !video.paused;
      button.setAttribute('aria-pressed', String(playing));
      button.setAttribute('aria-label', (playing ? 'Приостановить ' : 'Смотреть ') + video.getAttribute('aria-label').toLowerCase());
      label.textContent = playing ? 'Пауза' : 'Смотреть';
      icon.textContent = playing ? 'Ⅱ' : '▶';
    };
    const toggle = () => {
      if (video.paused) {
        pausedByUser.delete(video);
        userPausedAutoplay = false;
        playVideo(video, true);
      } else {
        pausedByUser.add(video);
        userPausedAutoplay = true;
        if (activeVideo === video) activeVideo = null;
        manuallySelectedVideo = null;
        video.pause();
      }
    };
    button.addEventListener('click', toggle);
    video.addEventListener('click', toggle);
    video.addEventListener('play', update);
    video.addEventListener('pause', update);
  });
  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        const video = entry.target;
        if (entry.isIntersecting) visibleVideos.set(video, entry.intersectionRatio);
        else visibleVideos.delete(video);
        const shouldPause = !entry.isIntersecting || (entry.intersectionRatio < .65 && manuallySelectedVideo !== video);
        if (shouldPause) {
          video.pause();
          if (activeVideo === video) activeVideo = null;
          if (manuallySelectedVideo === video) manuallySelectedVideo = null;
        }
      });
      if (document.hidden || reducedMotion.matches || saveData || userPausedAutoplay) return;
      if (activeVideo) return;
      const candidate = [...visibleVideos.entries()].filter(([video, ratio]) => ratio >= .65 && !pausedByUser.has(video)).sort((a, b) => b[1] - a[1])[0];
      if (candidate) playVideo(candidate[0]);
    }, { threshold: [0, .65, .9] });
    videos.forEach(video => observer.observe(video));
  }
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
      activeVideo = null;
      manuallySelectedVideo = null;
      videos.forEach(video => video.pause());
    }
  });
})();
