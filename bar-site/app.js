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
  document.querySelectorAll('[data-menu-filter]').forEach(button => button.addEventListener('click', () => {
    const id = button.dataset.menuFilter;
    document.querySelectorAll('[data-menu-filter]').forEach(b => b.setAttribute('aria-pressed', String(b === button)));
    document.querySelectorAll('[data-menu-category]').forEach(section => { section.hidden = id !== 'all' && section.dataset.menuCategory !== id; });
    const count = data.items.filter(item => id === 'all' || item.category === id).length;
    document.getElementById('menu-status').textContent = 'В разделе: ' + count;
  }));
  document.getElementById('show-nutrition').addEventListener('change', event => document.body.classList.toggle('nutrition-off', !event.target.checked));
})();
