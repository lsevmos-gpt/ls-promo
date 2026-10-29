(() => {
  'use strict';
  const search = document.querySelector('#team-search');
  const filters = [...document.querySelectorAll('[data-team-club]')];
  if (search) {
    const cards = [...document.querySelectorAll('#team-results .trainer-card')];
    const status = document.querySelector('#team-result-count');
    const empty = document.querySelector('.team-empty');
    const normalize = value => value.trim().toLocaleLowerCase('ru').replace(/ё/g, 'е');
    const params = new URLSearchParams(location.search);
    let club = filters.some(button => button.dataset.teamClub === params.get('club')) ? params.get('club') : 'all';
    search.value = params.get('q') || '';
    const apply = (writeUrl = true) => {
      const needle = normalize(search.value);
      let count = 0;
      cards.forEach(card => {
        const inClub = club === 'all' || card.dataset.trainerClubs.split(' ').includes(club);
        card.hidden = !(inClub && normalize(card.textContent).includes(needle));
        if (!card.hidden) count++;
      });
      filters.forEach(button => {
        const active = button.dataset.teamClub === club;
        button.classList.toggle('active', active);
        button.setAttribute('aria-pressed', String(active));
      });
      status.textContent = 'Найдено: ' + count;
      empty.hidden = count !== 0;
      if (writeUrl) {
        const url = new URL(location.href);
        club === 'all' ? url.searchParams.delete('club') : url.searchParams.set('club', club);
        search.value.trim() ? url.searchParams.set('q', search.value.trim()) : url.searchParams.delete('q');
        history.replaceState(null, '', url);
      }
    };
    filters.forEach(button => button.addEventListener('click', () => { club = button.dataset.teamClub; apply(); }));
    search.addEventListener('input', () => apply());
    document.querySelector('[data-reset-team]')?.addEventListener('click', () => { club = 'all'; search.value = ''; apply(); search.focus(); });
    window.addEventListener('popstate', () => {
      const next = new URLSearchParams(location.search);
      club = filters.some(button => button.dataset.teamClub === next.get('club')) ? next.get('club') : 'all';
      search.value = next.get('q') || '';
      apply(false);
    });
    apply(false);
  }

  const dialog = document.querySelector('#trainer-photo-dialog');
  const photos = [...document.querySelectorAll('[data-trainer-photo]')];
  if (!dialog || !photos.length) return;
  const full = dialog.querySelector('#trainer-photo-full');
  const caption = dialog.querySelector('#trainer-photo-caption');
  const counter = dialog.querySelector('#trainer-photo-count');
  let index = 0;
  let opener;
  const show = () => {
    const thumb = photos[index].querySelector('img');
    full.src = photos[index].getAttribute('href');
    full.alt = thumb.alt;
    caption.textContent = thumb.alt;
    counter.textContent = `${index + 1} / ${photos.length}`;
  };
  photos.forEach((photo, i) => photo.addEventListener('click', event => {
    if (event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    index = i;
    opener = photo;
    show();
    dialog.showModal();
  }));
  const move = direction => { index = (index + direction + photos.length) % photos.length; show(); };
  dialog.querySelector('[data-trainer-photo-prev]').addEventListener('click', () => move(-1));
  dialog.querySelector('[data-trainer-photo-next]').addEventListener('click', () => move(1));
  dialog.querySelector('[data-close-trainer-photo]').addEventListener('click', () => dialog.close());
  dialog.addEventListener('keydown', event => {
    if (event.key === 'ArrowLeft') { event.preventDefault(); move(-1); }
    if (event.key === 'ArrowRight') { event.preventDefault(); move(1); }
  });
  dialog.addEventListener('click', event => {
    if (event.target !== dialog) return;
    const rect = dialog.getBoundingClientRect();
    if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) dialog.close();
  });
  dialog.addEventListener('close', () => opener?.focus());
})();
