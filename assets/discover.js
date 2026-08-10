(() => {
  const search = document.querySelector('#discover-search');
  const clear = document.querySelector('#discover-clear');
  const cards = [...document.querySelectorAll('.discover-card')];
  const sections = [...document.querySelectorAll('.discover-section')];
  const chips = [...document.querySelectorAll('.filter-chip')];
  const result = document.querySelector('#discover-result');
  const empty = document.querySelector('#discover-empty');
  if (!search || !cards.length) return;

  const normalise = (value) => value
    .normalize('NFKC')
    .toLocaleLowerCase('ja')
    .replace(/[\s　]+/g, ' ')
    .trim();

  let category = 'all';
  const params = new URLSearchParams(location.search);
  const initialQuery = params.get('q') || '';
  const initialCategory = params.get('category') || 'all';
  if (initialQuery) search.value = initialQuery;
  if (chips.some((chip) => chip.dataset.category === initialCategory)) category = initialCategory;

  const syncUrl = () => {
    const next = new URL(location.href);
    const query = normalise(search.value);
    if (query) next.searchParams.set('q', search.value.trim()); else next.searchParams.delete('q');
    if (category !== 'all') next.searchParams.set('category', category); else next.searchParams.delete('category');
    history.replaceState(null, '', next.pathname + next.search + next.hash);
  };

  const apply = () => {
    const query = normalise(search.value);
    const terms = query.split(' ').filter(Boolean);
    let visible = 0;
    cards.forEach((card) => {
      const text = normalise(card.dataset.search || card.textContent || '');
      const categoryMatch = category === 'all' || card.dataset.category === category;
      const queryMatch = terms.every((term) => text.includes(term));
      card.hidden = !(categoryMatch && queryMatch);
      if (!card.hidden) visible += 1;
    });
    sections.forEach((section) => {
      section.hidden = !section.querySelector('.discover-card:not([hidden])');
    });
    chips.forEach((chip) => {
      const active = chip.dataset.category === category;
      chip.classList.toggle('is-active', active);
      chip.setAttribute('aria-pressed', String(active));
    });
    result.textContent = `${visible}件を表示中`;
    empty.hidden = visible !== 0;
    syncUrl();
  };

  let timer;
  search.addEventListener('input', () => {
    clearTimeout(timer);
    timer = setTimeout(apply, 80);
  });
  clear.addEventListener('click', () => {
    search.value = '';
    category = 'all';
    apply();
    search.focus();
  });
  chips.forEach((chip) => chip.addEventListener('click', () => {
    category = chip.dataset.category || 'all';
    apply();
    document.querySelector('#discover-results')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }));
  apply();
})();
