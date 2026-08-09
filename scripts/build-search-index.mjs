// data/topics_master.json（title/aliases/needs/department/audience の手動管理データ）から
// 本文冒頭リードと最終確認日を実ページHTMLから抽出し、検索用の search-index.json を生成する。
// 本文全文は含めない（意図的）。実行: node scripts/build-search-index.mjs
//
// 改修指示書 9.1「検索辞書」/ 9.2「検索結果表示」に対応:
//   aliases（日常語・表記ゆれ）, needs（困りごとの文章）, department（担当課）,
//   audience（対象者）, keyword（主検索語）, summary（1行の結論）, kind（種別）,
//   verified（最終確認日）
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..');
const LEAD_MAX_CHARS = 300;

function stripTags(html) {
  return html
    .replace(/<[^>]+>/g, '')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/\s+/g, ' ')
    .trim();
}

function pageFilePath(href) {
  if (href === '/') return path.join(ROOT, 'index.html');
  return path.join(ROOT, href.replace(/^\//, '').replace(/\/$/, ''), 'index.html');
}

function readPage(href) {
  const filePath = pageFilePath(href);
  if (!fs.existsSync(filePath)) return null; // 未公開・統合済みは検索対象外
  return fs.readFileSync(filePath, 'utf8');
}

function extractLead(html, href) {
  const m = html.match(/<p class="lead">([\s\S]*?)<\/p>/);
  if (!m) {
    console.warn(`[warn] leadが見つかりません（空扱い）: ${href}`);
    return '';
  }
  return stripTags(m[1]).slice(0, LEAD_MAX_CHARS);
}

function extractVerified(html) {
  const m = html.match(/最終確認日[：:]\s*(\d{4}-\d{2}-\d{2})/);
  return m ? m[1] : '';
}

function extractMeta(html, pattern) {
  const match = html.match(pattern);
  return match ? stripTags(match[1]) : '';
}

// 検索結果に出す種別ラベル（改修指示書 9.2）
function kindOf(topic) {
  const href = topic.href;
  if (href.startsWith('/shrine/') || href.startsWith('/temple/')) return '地域情報';
  if (href.startsWith('/tools/') || href.startsWith('/checklist/')) return 'ツール';
  if (href.startsWith('/questions/')) return 'よくある質問';
  if (href.startsWith('/blog/')) return '読み物';
  if (href.startsWith('/about/') || href.startsWith('/terms/')) return 'サイト情報';
  if (topic.hub === 'enjoy') return '地域情報';
  if (/相談|悩み|不安|困っ/.test(topic.intent || '')) return '相談';
  return '公式手続き';
}

// 1行の結論（改修指示書 9.2）。intent があればそれを、無ければリード先頭文を使う。
function summaryOf(topic, lead) {
  if (topic.intent) return topic.intent;
  const first = (lead || '').split(/(?<=。)/)[0] || '';
  return first.slice(0, 60);
}

function main() {
  const topicsMaster = JSON.parse(fs.readFileSync(path.join(ROOT, 'data/topics_master.json'), 'utf8'));
  // /tools/ と /checklist/ は固有の出典を持たない集約ページなので topics_master とは別台帳で管理する。
  const auxPages = JSON.parse(fs.readFileSync(path.join(ROOT, 'data/aux-pages.json'), 'utf8'));
  const questionPages = JSON.parse(fs.readFileSync(path.join(ROOT, 'data/questions.json'), 'utf8'));
  const expansionPages = JSON.parse(fs.readFileSync(path.join(ROOT, 'data/search-expansion-pages.json'), 'utf8'));
  const phase1Path = path.join(ROOT, 'data/seo-phase1-publication.json');
  const phase1Pages = fs.existsSync(phase1Path) ? JSON.parse(fs.readFileSync(phase1Path, 'utf8')) : [];

  let mergedSkipped = 0;
  const baseIndex = [...topicsMaster, ...auxPages]
    .map((topic) => {
      // 統合済み（301）のページは検索候補に出さない
      if (topic.action === 'merge') {
        mergedSkipped++;
        return null;
      }
      const html = readPage(topic.href);
      if (html === null) return null;
      const lead = extractLead(html, topic.href);
      const aliases = topic.aliases || topic.synonyms || [];
      return {
        href: topic.href,
        icon: topic.icon,
        title: topic.title,
        category: topic.category,
        hub: topic.hub || '',
        kind: kindOf(topic),
        summary: summaryOf(topic, lead),
        keyword: topic.primary_keyword || '',
        aliases,
        needs: topic.needs || [],
        department: topic.department || [],
        audience: topic.audience || [],
        verified: extractVerified(html),
        lead,
      };
    })
    .filter(Boolean);

  const questionIndex = questionPages.map((question) => {
    const html = readPage(question.href);
    if (html === null) return null;
    return {
      href: question.href,
      icon: question.icon || '💬',
      title: question.question,
      category: question.category || '質問',
      hub: question.hub || '',
      kind: 'よくある質問',
      summary: question.answer.slice(0, 90),
      keyword: question.keyword || '',
      aliases: [question.context, ...(question.needs || [])].filter(Boolean),
      needs: question.needs || [],
      department: [],
      audience: question.audience || [],
      verified: question.verified_date || '',
      lead: extractLead(html, question.href),
    };
  }).filter(Boolean);
  const expansionIndex = expansionPages.map((page) => {
    const html = readPage(page.href);
    if (html === null) return null;
    return {
      href: page.href,
      icon: '🧭',
      title: page.title,
      category: '検索意図別ガイド',
      hub: page.href.includes('/living-soon/') ? 'procedures' :
        page.href.includes('/housing/') ? 'property' : 'trouble',
      kind: page.href.includes('/living-soon/') ? '地域情報' : '公式手続き',
      summary: page.conclusion.slice(0, 90),
      keyword: page.title.split('｜')[0],
      aliases: [page.audience, ...page.faq.map((row) => row.q)],
      needs: page.steps,
      department: [page.window],
      audience: [page.audience],
      verified: extractVerified(html),
      lead: extractLead(html, page.href),
    };
  }).filter(Boolean);
  const existingHrefs = new Set([...baseIndex, ...questionIndex, ...expansionIndex].map((item) => item.href));
  const phase1Index = phase1Pages.map((page) => {
    if (existingHrefs.has(page.url)) return null;
    const html = readPage(page.url);
    if (html === null) return null;
    const lead = extractLead(html, page.url);
    const title = extractMeta(html, /<h1\b[^>]*>([\s\S]*?)<\/h1>/i) || page.proposed_title_h1;
    const description = extractMeta(html, /<meta\s+name="description"\s+content="([^"]*)"/i);
    return {
      href: page.url,
      icon: '🧭',
      title,
      category: '検索意図別ガイド',
      hub: page.url.startsWith('/food/') || page.url.startsWith('/events/') ? 'enjoy' : '',
      kind: page.url.startsWith('/life/') ? '公式手続き' : '地域情報',
      summary: description.slice(0, 90),
      keyword: page.primary_keyword || '',
      aliases: [page.primary_keyword, page.proposed_title_h1].filter(Boolean),
      needs: [],
      department: [],
      audience: [],
      verified: extractVerified(html) || page.fact_checked_at || '',
      lead,
    };
  }).filter(Boolean);
  const searchIndex = [...baseIndex, ...questionIndex, ...expansionIndex, ...phase1Index];

  const outPath = path.join(ROOT, 'search-index.json');
  const json = JSON.stringify(searchIndex);
  fs.writeFileSync(outPath, json);

  const dictFields = searchIndex.reduce(
    (sum, t) => sum + t.aliases.length + t.needs.length + t.department.length + t.audience.length,
    0
  );

  console.log(`生成完了: ${outPath}`);
  console.log(`項目数: ${searchIndex.length}（統合により除外: ${mergedSkipped}）`);
  console.log(`辞書エントリ数（別名・困りごと・担当課・対象者）: ${dictFields}`);
  console.log(`ファイルサイズ: ${(json.length / 1024).toFixed(1)} KB`);

  const thin = searchIndex.filter((t) => t.aliases.length + t.needs.length < 3);
  if (thin.length) {
    console.log(`[warn] 辞書が薄いページ ${thin.length} 件:`);
    thin.slice(0, 15).forEach((t) => console.log(`  ${t.href}`));
  }
}

main();
