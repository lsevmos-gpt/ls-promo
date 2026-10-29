(() => {
  'use strict';
  const data = JSON.parse(document.getElementById('menu-data').textContent);
  const items = new Map(data.items.map(item => [item.id, item]));
  const dialog = document.getElementById('item-dialog');
  const methodDialog = document.getElementById('method-dialog');
  const nf = new Intl.NumberFormat('ru-RU');
  const price = value => (Array.isArray(value) ? value.map(v => nf.format(v)).join('–') : nf.format(value)) + ' ₽';
  const showItem = id => {
    const item = items.get(id);
    if (!item) return;
    dialog.querySelector('[data-dialog-name]').textContent = item.name;
    dialog.querySelector('[data-dialog-category]').textContent = data.categories.find(c => c.id === item.category).name;
    dialog.querySelector('[data-dialog-price]').textContent = price(item.price_rub);
    dialog.querySelector('[data-dialog-composition]').textContent = item.composition || (item.volume_ml ? 'Объём: ' + item.volume_ml + ' мл.' : 'Выберите вкус и уточните состав у администратора бара.');
    const nutrients = dialog.querySelector('[data-dialog-nutrition]');
    const label = dialog.querySelector('[data-dialog-nutrition-label]');
    const values = item.nutrition.values;
    nutrients.hidden = !values;
    label.hidden = !values;
    if (values) {
      for (const key of ['kcal', 'protein', 'fat', 'carbs']) nutrients.querySelector('[data-value="' + key + '"]').textContent = '≈' + values[key];
    }
    dialog.querySelector('[data-dialog-assumption]').textContent = item.nutrition.assumption || item.nutrition.reason;
    dialog.querySelector('[data-dialog-estimate-note]').hidden = !values;
    dialog.showModal();
  };
  document.querySelectorAll('[data-details]').forEach(button => button.addEventListener('click', () => showItem(button.dataset.details)));
  document.querySelectorAll('[data-close-dialog]').forEach(button => button.addEventListener('click', () => button.closest('dialog').close()));
  [dialog, methodDialog].forEach(modal => modal.addEventListener('click', event => { if (event.target === modal) modal.close(); }));
  document.querySelectorAll('[data-show-method]').forEach(button => button.addEventListener('click', () => methodDialog.showModal()));
  const mobileCategory = document.getElementById('mobile-menu-category');
  const selectCategory = id => {
    document.querySelectorAll('[data-menu-filter]').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.menuFilter === id)));
    mobileCategory.value = id;
    document.querySelectorAll('[data-menu-category]').forEach(section => { section.hidden = id !== 'all' && section.dataset.menuCategory !== id; });
    const count = data.items.filter(item => id === 'all' || item.category === id).length;
    document.getElementById('menu-status').textContent = 'В разделе: ' + count;
    document.querySelector('.menu-toolbar').scrollIntoView({ block: 'start', behavior: 'instant' });
  };
  document.querySelectorAll('[data-menu-filter]').forEach(button => button.addEventListener('click', () => selectCategory(button.dataset.menuFilter)));
  mobileCategory.addEventListener('change', () => selectCategory(mobileCategory.value));
  document.getElementById('show-nutrition').addEventListener('change', event => document.body.classList.toggle('nutrition-off', !event.target.checked));

  const videos = [...document.querySelectorAll('.story-video')];
  const visibleVideos = new Map();
  const pausedByUser = new Set();
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const saveData = navigator.connection && navigator.connection.saveData;
  const loadVideo = video => {
    if (!video.getAttribute('src')) {
      video.src = video.dataset.videoSrc;
      video.load();
    }
  };
  const pauseOthers = current => videos.forEach(video => { if (video !== current) video.pause(); });
  const playVideo = video => {
    pauseOthers(video);
    loadVideo(video);
    video.play().catch(() => {});
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
        playVideo(video);
      } else {
        pausedByUser.add(video);
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
        if (entry.intersectionRatio >= .65) visibleVideos.set(entry.target, entry.intersectionRatio);
        else {
          visibleVideos.delete(entry.target);
          entry.target.pause();
        }
      });
      if (document.hidden || reducedMotion.matches || saveData) return;
      if (videos.some(video => !video.paused)) return;
      const candidate = [...visibleVideos.entries()].filter(([video]) => !pausedByUser.has(video)).sort((a, b) => b[1] - a[1])[0];
      if (candidate) playVideo(candidate[0]);
    }, { threshold: [0, .65, .9] });
    videos.forEach(video => observer.observe(video));
  }
  document.addEventListener('visibilitychange', () => { if (document.hidden) videos.forEach(video => video.pause()); });
})();
