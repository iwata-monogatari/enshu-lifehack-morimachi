/* Fixed event names only; search text and personal values are never sent. */
(function () {
  'use strict';
  var root = document.querySelector('[data-mori-topic]');
  var topic = root && root.getAttribute('data-mori-topic');
  if (['outings','living','family'].indexOf(topic) !== -1 && typeof window.fgaTrack === 'function') {
    window.fgaTrack('mori_growth_view_' + topic);
  }
  var controls = document.getElementById('mg-controls');
  if (!controls) return;
  var items = Array.from(document.querySelectorAll('.post-item[data-topic]'));
  var input = document.getElementById('mg-search'), count = document.getElementById('mg-count');
  var more = document.getElementById('mg-more'), empty = document.getElementById('mg-empty');
  var buttons = Array.from(controls.querySelectorAll('[data-filter]'));
  var selected = 'all', limit = 24;
  function normalize(value) { return value.normalize('NFKC').toLocaleLowerCase('ja'); }
  var texts = items.map(function (item) { return normalize(item.textContent); });
  function render() {
    var words = normalize(input.value.trim()).split(/\s+/).filter(Boolean), matched = 0;
    items.forEach(function (item, index) {
      var match = (selected === 'all' || item.dataset.topic === selected) && words.every(function (word) { return texts[index].includes(word); });
      if (match) matched++;
      item.hidden = !match || matched > limit;
    });
    buttons.forEach(function (button) { button.setAttribute('aria-pressed', String(button.dataset.filter === selected)); });
    count.textContent = matched + '件中 ' + Math.min(limit, matched) + '件を表示';
    more.hidden = matched <= limit; empty.hidden = matched !== 0;
  }
  function fromHash(scroll) {
    var value = location.hash.slice(1);
    if (['outings','living','family','all'].indexOf(value) === -1) return;
    selected = value; limit = 24; render();
    if (scroll) controls.scrollIntoView({block:'start'});
  }
  buttons.forEach(function (button) { button.addEventListener('click', function () {
    selected = button.dataset.filter; limit = 24; render();
    history.replaceState(null, '', location.pathname + location.search + '#' + selected);
  }); });
  input.addEventListener('input', function () { limit = 24; render(); });
  more.addEventListener('click', function () { limit += 24; render(); });
  window.addEventListener('hashchange', function () { fromHash(true); });
  controls.hidden = false; fromHash(false); render();
})();
