(() => {
  const dataNode = document.querySelector('#discover-data');
  const search = document.querySelector('#discover-search');
  const clear = document.querySelector('#discover-clear');
  const reset = document.querySelector('#discover-reset');
  const list = document.querySelector('#discover-list');
  const more = document.querySelector('#discover-more');
  const result = document.querySelector('#discover-result');
  const currentTab = document.querySelector('#discover-current-tab');
  const empty = document.querySelector('#discover-empty');
  const suggestions = document.querySelector('#discover-suggestions');
  const tabs = [...document.querySelectorAll('.guide-tab')];
  const keywords = [...document.querySelectorAll('.keyword-chip')];
  if (!dataNode || !search || !list || !result || !more || !empty) return;

  let guides;
  try {
    guides = JSON.parse(dataNode.textContent || '[]');
  } catch (error) {
    result.textContent = '一覧を読み込めませんでした。ページを再読み込みしてください。';
    return;
  }

  const normalise = (value) => String(value || '')
    .normalize('NFKC')
    .toLocaleLowerCase('ja')
    .replace(/[\s　]+/g, ' ')
    .trim();

  const params = new URLSearchParams(location.search);
  const validTabs = new Set(['all', ...tabs.map((tab) => tab.dataset.tab)]);
  let activeTab = validTabs.has(params.get('category')) ? params.get('category') : 'all';
  let visibleLimit = 10;
  search.value = params.get('q') || '';

  const make = (tag, className, text) => {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  };

  const matchingGuides = () => {
    const terms = normalise(search.value).split(' ').filter(Boolean);
    return guides.filter((guide) => {
      const tabMatches = activeTab === 'all' || guide.tab === activeTab;
      const haystack = normalise(guide.search);
      return tabMatches && terms.every((term) => haystack.includes(term));
    });
  };

  const guideItem = (guide) => {
    const item = make('li', 'guide-list-item');
    const link = make('a');
    link.href = `/discover/${encodeURIComponent(guide.slug)}/`;
    const thumb = make('span', 'guide-thumb');
    const image = document.createElement('img');
    image.src = guide.image;
    image.alt = guide.imageAlt;
    image.width = 168;
    image.height = 88;
    image.loading = 'lazy';
    image.decoding = 'async';
    thumb.append(image, make('small', '', guide.mediaType));
    const copy = make('span', 'guide-copy');
    const meta = make('span', 'guide-meta');
    meta.append(make('small', '', guide.tabLabel), make('small', '', guide.category));
    const heading = make('strong', '', guide.shortTitle);
    heading.title = guide.title;
    copy.append(meta, heading, make('span', 'guide-summary', guide.description));
    link.append(thumb, copy, make('span', 'guide-arrow', '読む'));
    item.append(link);
    return item;
  };

  const syncUrl = () => {
    const next = new URL(location.href);
    const query = search.value.trim();
    if (query) next.searchParams.set('q', query); else next.searchParams.delete('q');
    if (activeTab !== 'all') next.searchParams.set('category', activeTab); else next.searchParams.delete('category');
    history.replaceState(null, '', next.pathname + next.search + next.hash);
  };

  const renderSuggestions = () => {
    if (!suggestions) return;
    suggestions.replaceChildren();
    guides.filter((guide) => ['tourism', 'parenting', 'disaster'].includes(guide.tab)).slice(0, 3).forEach((guide) => {
      const item = make('li');
      const link = make('a', '', guide.shortTitle);
      link.href = `/discover/${encodeURIComponent(guide.slug)}/`;
      item.append(link);
      suggestions.append(item);
    });
  };

  const render = () => {
    const matches = matchingGuides();
    const shown = matches.slice(0, visibleLimit);
    list.replaceChildren(...shown.map(guideItem));
    tabs.forEach((tab) => {
      const selected = tab.dataset.tab === activeTab;
      tab.classList.toggle('is-active', selected);
      tab.setAttribute('aria-selected', String(selected));
      tab.tabIndex = selected ? 0 : -1;
    });
    const label = tabs.find((tab) => tab.dataset.tab === activeTab)?.childNodes[0]?.textContent || 'すべての分類';
    if (currentTab) currentTab.textContent = activeTab === 'all' ? 'すべての分類' : label;
    result.textContent = matches.length ? `${matches.length}件中${shown.length}件を表示` : '0件';
    empty.hidden = matches.length !== 0;
    list.hidden = matches.length === 0;
    more.hidden = matches.length === 0 || shown.length >= matches.length;
    if (!more.hidden) more.querySelector('span').textContent = `残り${matches.length - shown.length}件`;
    syncUrl();
  };

  const resetAll = () => {
    search.value = '';
    activeTab = 'all';
    visibleLimit = 10;
    render();
    search.focus();
  };

  let timer;
  search.addEventListener('input', () => {
    clearTimeout(timer);
    timer = setTimeout(() => { visibleLimit = 10; render(); }, 80);
  });
  clear?.addEventListener('click', resetAll);
  reset?.addEventListener('click', resetAll);
  more.addEventListener('click', () => { visibleLimit += 20; render(); });
  tabs.forEach((tab) => tab.addEventListener('click', () => {
    activeTab = tab.dataset.tab || 'all';
    visibleLimit = 10;
    render();
    document.querySelector('.list-heading')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }));
  keywords.forEach((button) => button.addEventListener('click', () => {
    search.value = button.dataset.keyword || button.textContent;
    activeTab = 'all';
    visibleLimit = 10;
    render();
    search.focus();
  }));

  renderSuggestions();
  render();
})();
