// サイト内検索の画面側。改修指示書 9.2「検索結果表示」/ 16.1「計測イベント」に対応。
// 検索結果には ページ名・1行の結論・対象者・種別・最終確認日 を表示する。
// 0件のときは「見つかりません」で終わらせず、近いページ・よく使う入口・送信ボタンを出す。
import { searchTopics, fallbackTopics, isConfident } from '/assets/search-core.mjs';

let indexPromise = null;
function loadIndex() {
  if (!indexPromise) {
    indexPromise = fetch('/search-index.json').then((res) => res.json());
  }
  return indexPromise;
}

function escapeHtml(text) {
  return String(text == null ? '' : text).replace(/[&<>"']/g, (char) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  }[char]));
}

// 計測（改修指示書 16.1）。トラッカー未読込でも検索を止めない。
function track(name, detail) {
  try {
    if (typeof window.fujigaokaTrack === 'function') {
      window.fujigaokaTrack(name, detail || {});
    }
    document.dispatchEvent(new CustomEvent('lifehack:' + name, { detail: detail || {} }));
  } catch (e) {
    /* 計測の失敗で検索を止めない */
  }
}

// 検索語そのものは送らない。0件語の傾向を見るための形だけを渡す（16.2 個人情報の除去）。
function queryShape(value) {
  return {
    length: value.length,
    hasDigits: /\d/.test(value),
    hasSpace: /\s/.test(value),
  };
}

function resultItem(page) {
  const meta = [];
  if (page.kind) meta.push(`<span class="hit-kind">${escapeHtml(page.kind)}</span>`);
  if (page.audience && page.audience.length) {
    meta.push(`<span class="hit-audience">対象：${escapeHtml(page.audience.join('・'))}</span>`);
  }
  if (page.verified) {
    meta.push(`<span class="hit-verified">最終確認日 ${escapeHtml(page.verified)}</span>`);
  }
  return `<li><a class="search-hit" href="${escapeHtml(page.href)}" data-search-hit="result">` +
    `<span class="result-ic" aria-hidden="true">${escapeHtml(page.icon)}</span>` +
    '<span class="hit-body">' +
    `<strong>${escapeHtml(page.title)}</strong>` +
    `<span class="hit-summary">${escapeHtml(page.summary || '')}</span>` +
    `<span class="hit-meta">${meta.join('')}</span>` +
    '</span>' +
    '<span class="hit-arrow" aria-hidden="true">›</span>' +
    '</a></li>';
}

// 0件時に必ず出す、よく使う入口（改修指示書 9.2）
const ALWAYS_OFFERED = [
  { href: '/hub/trouble/', icon: '🆘', label: '困った・緊急', note: '夜間診療・避難・詐欺・お金の相談' },
  { href: '/hub/procedures/', icon: '📄', label: '手続きしたい', note: '住民票・戸籍・税・ごみ・水道' },
  { href: '/hub/care/', icon: '👵', label: '親・介護', note: '介護の相談・要介護認定・施設探し' },
  { href: '/hub/property/', icon: '🏠', label: '家・土地', note: '空き家・相続・固定資産税' },
];

function nearItem(page, kind) {
  return `<li><a class="search-hit" href="${escapeHtml(page.href)}" data-search-hit="${kind}">` +
    `<span class="result-ic" aria-hidden="true">${escapeHtml(page.icon)}</span>` +
    `<span class="hit-body"><strong>${escapeHtml(page.title)}</strong>` +
    `<span class="hit-summary">${escapeHtml(page.summary || '')}</span></span></a></li>`;
}

function zeroResultHtml(query, near) {
  const nearHtml = near.length
    ? '<p class="mini">言葉が近いページです。</p><ul class="search-near">' +
      near.map((p) => nearItem(p, 'near')).join('') + '</ul>'
    : '';
  const offered = ALWAYS_OFFERED.map((o) =>
    `<li><a class="search-hit" href="${o.href}" data-search-hit="offered">` +
    `<span class="result-ic" aria-hidden="true">${o.icon}</span>` +
    `<span class="hit-body"><strong>${o.label}</strong>` +
    `<span class="hit-summary">${o.note}</span></span></a></li>`).join('');
  return `<h2>「${escapeHtml(query)}」に一致するページは見つかりませんでした</h2>` +
    nearHtml +
    '<p class="mini">こちらの入口から探すこともできます。</p>' +
    `<ul class="search-near">${offered}</ul>` +
    '<p class="search-request"><button type="button" class="btn" data-search-request>' +
    'この言葉のページが必要だと伝える</button></p>' +
    '<p class="search-request-thanks" hidden>ありがとうございました。今後のページ追加の参考にします。</p>';
}

let lastQuery = '';

async function runSearch(query, opts) {
  const resultsEl = document.getElementById('search-results');
  if (!resultsEl) return;
  const value = (query || '').trim();
  if (!value) {
    resultsEl.innerHTML = '';
    return;
  }
  const items = await loadIndex();
  const scored = searchTopics(items, value);
  // 弱い部分一致しか無いときは「候補」として出さない。
  // 無関係なページを並べるより、0件画面から別の入口へ案内するほうが早く解決できる。
  const matched = isConfident(scored) ? scored : [];

  if (opts && opts.submitted) {
    track(matched.length ? 'site_search' : 'search_zero_result', queryShape(value));
  }
  lastQuery = value;

  if (!matched.length) {
    const near = scored.length ? scored.slice(0, 4) : fallbackTopics(items, value);
    resultsEl.innerHTML = zeroResultHtml(value, near);
    return;
  }
  resultsEl.innerHTML =
    `<h2>「${escapeHtml(value)}」の候補（${matched.length}件）</h2>` +
    `<ul class="search-hits">${matched.map(resultItem).join('')}</ul>`;
}

// 汎用名。他地域版と共有するため地域名を含めない（改修指示書 9.3）。
window.siteSearch = function siteSearch(event) {
  event.preventDefault();
  const input = document.getElementById('site-search-input');
  runSearch(input ? input.value : '', { submitted: true });
  return false;
};

document.addEventListener('DOMContentLoaded', () => {
  const input = document.getElementById('site-search-input');
  const initial = new URLSearchParams(window.location.search).get('q') || '';
  loadIndex();
  if (input && initial) {
    input.value = initial;
    runSearch(initial, { submitted: true });
  }
  input?.addEventListener('input', () => runSearch(input.value));

  const resultsEl = document.getElementById('search-results');
  resultsEl?.addEventListener('click', (event) => {
    const hit = event.target.closest('[data-search-hit]');
    if (hit) {
      track('search_result_click', {
        href: hit.getAttribute('href'),
        kind: hit.getAttribute('data-search-hit'),
      });
      return;
    }
    const request = event.target.closest('[data-search-request]');
    if (request) {
      track('search_request_page', queryShape(lastQuery));
      request.disabled = true;
      const thanks = resultsEl.querySelector('.search-request-thanks');
      if (thanks) thanks.hidden = false;
    }
  });
});
