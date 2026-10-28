/* Browser-local interactions. No forms, analytics, or visitor data collection. */
(() => {
  'use strict';
  const data = window.LS_DATA;
  const $ = (s, root = document) => root.querySelector(s);
  const $$ = (s, root = document) => [...root.querySelectorAll(s)];
  const menuToggle = $('.menu-toggle');
  const mobileMenu = $('#mobile-menu');
  const closeMenu = () => {
    menuToggle?.setAttribute('aria-expanded', 'false');
    menuToggle?.setAttribute('aria-label', 'Открыть меню');
    if (mobileMenu) mobileMenu.hidden = true;
    document.body.classList.remove('menu-open');
  };
  menuToggle?.addEventListener('click', () => {
    const open = menuToggle.getAttribute('aria-expanded') !== 'true';
    menuToggle.setAttribute('aria-expanded', String(open));
    menuToggle.setAttribute('aria-label', open ? 'Закрыть меню' : 'Открыть меню');
    mobileMenu.hidden = !open;
    document.body.classList.toggle('menu-open', open);
  });
  $$('#mobile-menu a').forEach(a => a.addEventListener('click', closeMenu));
  document.addEventListener('keydown', ev => { if (ev.key === 'Escape') closeMenu(); });

  const setClub = id => {
    const c = data.clubs.find(c => c.id === id);
    if (!c || !$('#club-panel')) return;
    $$('[data-club]').forEach(t => {
      const selected = t.dataset.club === id;
      t.classList.toggle('active', selected);
      t.setAttribute('aria-selected', String(selected));
      t.tabIndex = selected ? 0 : -1;
    });
    $('#club-panel').setAttribute('aria-labelledby', 'club-tab-' + id);
    $('#club-image-link').href = '/clubs/' + id + '/';
    $('.club-image').src = c.image;
    $('.club-image').alt = c.caption;
    $('#club-photo-caption').textContent = c.caption;
    $('#club-title').textContent = c.street;
    $('#club-card').textContent = c.card;
    $('#club-area').textContent = c.area;
    $('#club-lead').textContent = c.lead;
    $('#club-features').replaceChildren(...c.features.map(f => {
      const li = document.createElement('li'); li.textContent = f; return li;
    }));
    $('#club-details').href = '/clubs/' + id + '/';
    const massageLink = $('#club-massage');
    if (massageLink) {
      massageLink.hidden = !c.massage;
      if (c.massage) massageLink.href = c.massage.url;
      else massageLink.removeAttribute('href');
    }
    $('#club-phone').href = 'tel:' + c.tel;
    $('#club-phone').textContent = c.phone;
  };
  $$('[data-club]').forEach((t, i, tabs) => {
    t.addEventListener('click', () => setClub(t.dataset.club));
    t.addEventListener('keydown', ev => {
      let index;
      if (ev.key === 'ArrowDown' || ev.key === 'ArrowRight') index = (i + 1) % tabs.length;
      if (ev.key === 'ArrowUp' || ev.key === 'ArrowLeft') index = (i - 1 + tabs.length) % tabs.length;
      if (ev.key === 'Home') index = 0;
      if (ev.key === 'End') index = tabs.length - 1;
      if (index !== undefined) { ev.preventDefault(); tabs[index].focus(); setClub(tabs[index].dataset.club); }
    });
  });

  let mode = 'full', period = 0;
  const updatePrice = () => {
    $$('[data-price]').forEach(el => el.textContent = new Intl.NumberFormat('ru-RU').format(data.prices[el.dataset.price][mode][period]));
    $$('[data-period-label]').forEach(el => el.textContent = ['за 1 месяц', 'за 6 месяцев', 'за 12 месяцев'][period]);
    $$('[data-card-time]').forEach(el => el.textContent = mode === 'day' ? 'С 07:00 до 16:00, в часы работы клуба' : mode === 'impulse22' ? 'Полный день · Импульс 22' : 'Посещение в часы работы клуба');
    $$('[data-card-format]').forEach(el => el.textContent = {full: 'Полный день', day: 'Дневной формат', impulse22: 'Импульс 22'}[mode]);
    $$('[data-card-freeze]').forEach(el => el.textContent = 'Заморозка: ' + data.pricing_rules.freeze[period]);
    $$('[data-plan-mode]').forEach(b => { const a = b.dataset.planMode === mode; b.classList.toggle('active', a); b.setAttribute('aria-pressed', String(a)); });
    $$('[data-plan-period]').forEach(b => { const a = Number(b.dataset.planPeriod) === period; b.classList.toggle('active', a); b.setAttribute('aria-pressed', String(a)); });
  };
  $$('[data-plan-mode]').forEach(b => b.addEventListener('click', () => { mode = b.dataset.planMode; updatePrice(); }));
  $$('[data-plan-period]').forEach(b => b.addEventListener('click', () => { period = Number(b.dataset.planPeriod); updatePrice(); }));

  const openDialog = id => { const d = $(id); if (d && !d.open) d.showModal(); };
  $$('[data-open-app]').forEach(b => b.addEventListener('click', () => openDialog('#app-dialog')));
  $$('[data-open-video]').forEach(b => b.addEventListener('click', () => openDialog('#video-dialog')));
  $$('[data-close-dialog]').forEach(b => b.addEventListener('click', () => b.closest('dialog').close()));
  $$('dialog').forEach(d => {
    d.addEventListener('click', ev => { if (ev.target === d) { const r = d.getBoundingClientRect(); if (ev.clientX < r.left || ev.clientX > r.right || ev.clientY < r.top || ev.clientY > r.bottom) d.close(); } });
    d.addEventListener('close', () => { $$('video', d).forEach(v => v.pause()); });
  });

  let galleryClub, galleryIndex = 0;
  const showGalleryImage = () => {
    $('#gallery-image').src = galleryClub.gallery[galleryIndex];
    $('#gallery-image').alt = galleryClub.caption + ', фото ' + (galleryIndex + 1);
    $('#gallery-caption').textContent = galleryClub.caption;
    $('#gallery-count').textContent = `${galleryIndex + 1} / ${galleryClub.gallery.length}`;
  };
  $$('[data-gallery]').forEach(b => b.addEventListener('click', () => {
    galleryClub = data.clubs.find(c => c.id === b.dataset.gallery);
    galleryIndex = Number(b.dataset.imageIndex) || 0;
    showGalleryImage(); openDialog('#gallery-dialog');
  }));
  const moveGallery = direction => { if (!galleryClub) return; galleryIndex = (galleryIndex + direction + galleryClub.gallery.length) % galleryClub.gallery.length; showGalleryImage(); };
  $('#gallery-prev')?.addEventListener('click', () => moveGallery(-1));
  $('#gallery-next')?.addEventListener('click', () => moveGallery(1));
  $('#gallery-dialog')?.addEventListener('keydown', ev => { if (ev.key === 'ArrowLeft') moveGallery(-1); if (ev.key === 'ArrowRight') moveGallery(1); });

  $('#trainer-search')?.addEventListener('input', ev => {
    const needle = ev.target.value.trim().toLocaleLowerCase('ru');
    const cards = $$('.all-trainers .trainer-card'); let count = 0;
    cards.forEach(c => { const show = c.textContent.toLocaleLowerCase('ru').includes(needle); c.hidden = !show; if (show) count++; });
    $('#trainer-search-count').textContent = 'Найдено: ' + count;
    $('.empty-search').hidden = count > 0;
  });
})();
