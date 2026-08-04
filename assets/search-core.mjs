// 森町ライフハック サイト内検索のスコアリング（構造化キーワード方式）
// 対象は title / aliases（同義語・表記ゆれ）/ needs（困りごとの文章）/ department（担当課）/
// audience（対象者）/ category / lead のみ。本文全文は評価しない。
// ブラウザ（search-app.js）と Node（scripts/test-search.mjs）の双方から同一ロジックを import する。

const WEIGHTS = {
  title: 3.0,
  aliases: 2.5,
  needs: 2.2,
  keyword: 2.0,
  department: 1.6,
  category: 1.5,
  audience: 1.0,
  lead: 0.5,
};
const SHORT_QUERY_MAX = 4;

export function normalizeQuery(text) {
  return (text || '')
    .toLowerCase()
    .replace(/\s+/g, '')
    .replace(/[・、，,／/。．!！?？]/g, '');
}

function fieldMatchScore(fieldText, compactQuery, weight, allowNgram) {
  const norm = normalizeQuery(fieldText);
  if (!norm || !compactQuery) return 0;
  if (norm === compactQuery) return weight * 4;
  if (norm.includes(compactQuery)) return weight * 2;
  // 「親が認知症かもしれない」のような文章クエリでは、辞書側が部分文字列になる
  if (compactQuery.length >= 4 && norm.length >= 3 && compactQuery.includes(norm)) {
    return weight * 1.5;
  }
  if (!allowNgram) return 0;

  // 部分一致（N-gram）は誤爆を避けるため大幅に減衰させたフォールバック。
  // 日本語では2文字一致がほぼ偶然に成立する（「ヨット」と「ペット」など）ため、
  // 3文字以上でしか拾わない。拾えないときは0件として代替導線を出す方がよい。
  const maxSize = Math.min(4, compactQuery.length);
  let best = 0;
  for (let size = maxSize; size >= 3; size--) {
    for (let i = 0; i <= compactQuery.length - size; i++) {
      const part = compactQuery.slice(i, i + size);
      if (norm.includes(part)) {
        best = Math.max(best, size);
      }
    }
    if (best) break;
  }
  return best ? weight * 0.3 * best : 0;
}

function bestOf(list, compact, weight, allowNgram) {
  let best = 0;
  for (const value of list || []) {
    best = Math.max(best, fieldMatchScore(value, compact, weight, allowNgram));
  }
  return best;
}

/**
 * @param {{title:string, category:string, aliases:string[], needs:string[],
 *          department:string[], audience:string[], keyword:string, lead:string}} item
 * @param {string} rawQuery
 */
/**
 * @param {{title:string, category:string, aliases:string[], needs:string[],
 *          department:string[], audience:string[], keyword:string, lead:string}} item
 * @param {string} rawQuery
 * @param {boolean} allowNgram false にすると部分一致を一切使わない（確信度の判定用）
 */
function scoreWith(item, rawQuery, allowNgram) {
  const compact = normalizeQuery(rawQuery);
  if (!compact) return 0;
  const isShort = compact.length <= SHORT_QUERY_MAX;
  const ng = (flag) => allowNgram && flag;

  // synonyms は旧フィールド名。既存データとの互換のため両方見る。
  const aliases = item.aliases || item.synonyms || [];

  return (
    bestOf(aliases, compact, WEIGHTS.aliases, ng(true)) +
    bestOf(item.needs, compact, WEIGHTS.needs, ng(!isShort)) +
    bestOf(item.department, compact, WEIGHTS.department, false) +
    bestOf(item.audience, compact, WEIGHTS.audience, false) +
    fieldMatchScore(item.title, compact, WEIGHTS.title, ng(true)) +
    fieldMatchScore(item.keyword, compact, WEIGHTS.keyword, ng(!isShort)) +
    fieldMatchScore(item.category, compact, WEIGHTS.category, ng(!isShort)) +
    // 短語入力時は aliases/title の完全一致・前方一致を最優先し、lead 由来の弱いN-gram一致は使わない
    fieldMatchScore(item.lead, compact, WEIGHTS.lead, ng(!isShort))
  );
}

export function scoreItem(item, rawQuery) {
  return scoreWith(item, rawQuery, true);
}

/**
 * 部分一致（N-gram）を使わずに得られる点数。
 * これが 0 より大きいということは、どこかのフィールドに検索語そのものが入っていたということ。
 * 「パスポート」が「スポーツ施設」に部分一致してしまうような偶然を、結果から締め出すために使う。
 */
export function strongScore(item, rawQuery) {
  return scoreWith(item, rawQuery, false);
}

export function isConfident(results) {
  return results.length > 0 && results[0].strong > 0;
}

/**
 * @param {Array} items search-index.json の配列
 * @param {string} rawQuery
 * @param {{limit?: number, threshold?: number}} opts
 */
export function searchTopics(items, rawQuery, opts = {}) {
  const limit = opts.limit ?? 8;
  const threshold = opts.threshold ?? 1.0;
  return items
    .map((item) => ({ item, score: scoreItem(item, rawQuery) }))
    .filter((r) => r.score >= threshold)
    .sort((a, b) => b.score - a.score)
    .slice(0, limit)
    .map((r) => ({ ...r.item, score: r.score, strong: strongScore(r.item, rawQuery) }));
}

/**
 * 0件だったときに出す近いページ（改修指示書 9.2）。
 * 入力文字を1文字ずつ含むページを弱いスコアで拾い、「見つかりません」だけで終わらせない。
 */
export function fallbackTopics(items, rawQuery, opts = {}) {
  const limit = opts.limit ?? 4;
  const compact = normalizeQuery(rawQuery);
  if (!compact) return [];
  return items
    .map((item) => {
      const aliases = item.aliases || item.synonyms || [];
      const haystack = [item.title, item.category, item.keyword, ...aliases]
        .map(normalizeQuery)
        .join('');
      let score = 0;
      for (const ch of compact) {
        if (haystack.includes(ch)) score += 1;
      }
      return { item, score };
    })
    .filter((r) => r.score >= Math.max(1, Math.ceil(compact.length / 2)))
    .sort((a, b) => b.score - a.score)
    .slice(0, limit)
    .map((r) => r.item);
}
