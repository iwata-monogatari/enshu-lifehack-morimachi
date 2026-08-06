const RESOURCE_DATES = [
  ['2026-04-01','2026-05-01','2026-06-01','2026-07-01','2026-08-03','2026-09-02','2026-10-02','2026-11-02','2026-12-02','2027-01-06','2027-02-03','2027-03-01'],
  ['2026-04-03','2026-05-08','2026-06-03','2026-07-03','2026-08-05','2026-09-04','2026-10-05','2026-11-04','2026-12-04','2027-01-08','2027-02-05','2027-03-03'],
  ['2026-04-06','2026-05-11','2026-06-05','2026-07-06','2026-08-07','2026-09-07','2026-10-07','2026-11-05','2026-12-07','2027-01-13','2027-02-08','2027-03-05'],
  ['2026-04-08','2026-05-13','2026-06-08','2026-07-08','2026-08-10','2026-09-09','2026-10-14','2026-11-11','2026-12-09','2027-01-15','2027-02-10','2027-03-08'],
  ['2026-04-10','2026-05-15','2026-06-10','2026-07-10','2026-08-17','2026-09-11','2026-10-16','2026-11-13','2026-12-11','2027-01-18','2027-02-12','2027-03-10'],
  ['2026-04-13','2026-05-18','2026-06-12','2026-07-13','2026-08-19','2026-09-14','2026-10-19','2026-11-16','2026-12-14','2027-01-20','2027-02-15','2027-03-12'],
  ['2026-04-15','2026-05-20','2026-06-15','2026-07-15','2026-08-21','2026-09-16','2026-10-21','2026-11-18','2026-12-16','2027-01-22','2027-02-17','2027-03-15'],
  ['2026-04-17','2026-05-22','2026-06-17','2026-07-22','2026-08-24','2026-09-18','2026-10-23','2026-11-20','2026-12-18','2027-01-25','2027-02-19','2027-03-17'],
  ['2026-04-20','2026-05-25','2026-06-19','2026-07-24','2026-08-26','2026-09-25','2026-10-26','2026-11-25','2026-12-21','2027-01-27','2027-02-22','2027-03-19'],
  ['2026-04-22','2026-05-27','2026-06-22','2026-07-27','2026-08-28','2026-09-28','2026-10-28','2026-11-27','2026-12-23','2027-01-29','2027-02-24','2027-03-24'],
  ['2026-04-24','2026-05-29','2026-06-24','2026-07-29','2026-08-31','2026-09-30','2026-10-30','2026-11-30','2026-12-25','2027-02-01','2027-02-26','2027-03-26']
];

const GARBAGE_GROUPS = [
  ['黒田','三倉','中村','上野平','木根','乙丸','大河内','中野','大府川','大久保（三倉）','田能'],
  ['大鳥居','黒石','葛布','西俣','問詰','鍛治島','亀久保','嵯塚'],
  ['城下上','城下下','赤松','川向','本丁','川久保','川原町'],
  ['向天方下','向天方上','戸綿','北戸綿','南戸綿'],
  ['大上','橘','薄場','開運町','明治町','新町','仲横町'],
  ['本町','下宿','栄町上','栄町中','南町','促進住宅森'],
  ['大門','西幸町','草ヶ谷','円田'],
  ['米倉','大久保（一宮）','片瀬','赤根','谷崎','宮代西','宮代東'],
  ['谷中','中川上','中川下','牛飼'],
  ['城北','梶ヶ谷','鴨谷','福田地','上飯田','西組','円田（上川原）'],
  ['市場','下飯田','中飯田','東組','若宮']
];

const PLASTIC_DATE_GROUP = [6,7,8,9,10,0,1,2,3,4,5];
const BURN_MON_THU = new Set([
  ...GARBAGE_GROUPS[0], ...GARBAGE_GROUPS[1],
  '城下上','城下下','赤松','川向','本丁','川久保',
  '大上','橘','薄場','開運町','明治町','新町',
  '梶ヶ谷','鴨谷','福田地','戸綿','北戸綿','南戸綿'
]);
const BURN_TUE_FRI = new Set([
  '川原町','仲横町','本町','下宿','栄町上','栄町中','南町',
  '大門','西幸町','促進住宅森','向天方上','向天方下'
]);

const NURSERY = [
  {name:'ときわ保育園', status:['○','△','○','×','×','×']},
  {name:'摩耶保育園', status:['○','○','○','○','×','×']},
  {name:'プティ森町園', status:['○','×','×','△','△','△']},
  {name:'もりの保育所', status:['△','△','○','—','—','—']},
  {name:'ゆうな保育園', status:['△','△','×','—','—','—']}
];

const WATER = {
  '13': {included: 8, basic: 1100}, '20': {included: 10, basic: 2250},
  '25': {included: 10, basic: 2850}, '30': {included: 15, basic: 4250},
  '40': {included: 15, basic: 7750}, '50': {included: 20, basic: 11500},
  '75': {included: 50, basic: 26750}, '100': {included: 50, basic: 42100}
};

const esc = (value) => String(value ?? '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
const localDate = (value) => new Date(`${value}T00:00:00`);
const formatDate = (value) => {
  if (!value) return '年度内の予定なし';
  const d = localDate(value);
  return `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日（${'日月火水木金土'[d.getDay()]}）`;
};

export function garbageGroupFor(area) {
  return GARBAGE_GROUPS.findIndex(group => group.includes(area));
}

function nextListed(dates, from) {
  const start = typeof from === 'string' ? localDate(from) : from;
  return dates.find(value => localDate(value) >= start) || null;
}

function nextWeekday(days, from) {
  const d = new Date(from.getFullYear(), from.getMonth(), from.getDate());
  for (let offset = 0; offset < 8; offset += 1) {
    if (days.includes(d.getDay())) {
      const year = d.getFullYear();
      const month = String(d.getMonth() + 1).padStart(2, '0');
      const day = String(d.getDate()).padStart(2, '0');
      return `${year}-${month}-${day}`;
    }
    d.setDate(d.getDate() + 1);
  }
  return null;
}

export function nextGarbageDates(area, from = new Date()) {
  const group = garbageGroupFor(area);
  if (group < 0) return null;
  const start = typeof from === 'string' ? localDate(from) : from;
  const burnDays = BURN_MON_THU.has(area) ? [1,4] : BURN_TUE_FRI.has(area) ? [2,5] : [3,6];
  return {
    group,
    resource: nextListed(RESOURCE_DATES[group], start),
    plastic: nextListed(RESOURCE_DATES[PLASTIC_DATE_GROUP[group]], start),
    burnable: nextWeekday(burnDays, start),
    burnableLabel: burnDays.map(day => `${'日月火水木金土'[day]}曜日`).join('・')
  };
}

export function nurseryForAge(age) {
  const index = Number(age);
  return NURSERY.map(row => ({name: row.name, status: row.status[index]}));
}

export function calculateWater(usage, diameter, sewer = true) {
  const amount = Math.max(0, Number(usage));
  const rate = WATER[String(diameter)];
  if (!Number.isFinite(amount) || !rate) return null;
  const waterPreTax = rate.basic * 2 + Math.max(0, amount - rate.included * 2) * 110;
  const water = Math.floor(waterPreTax * 1.1);
  let sewerPreTax = 0;
  if (sewer) {
    sewerPreTax = 2000;
    let remaining = Math.max(0, amount - 20);
    for (const [capacity, price] of [[60,100],[120,110],[200,120],[600,130],[Infinity,140]]) {
      const used = Math.min(remaining, capacity);
      sewerPreTax += used * price;
      remaining -= used;
      if (remaining <= 0) break;
    }
  }
  const sewerFee = sewer ? Math.floor(sewerPreTax * 1.1) : 0;
  return {water, sewer: sewerFee, total: water + sewerFee};
}

export function migrationCandidate(values) {
  const allBase = values.move === 'yes' && values.tokyo === 'yes'
    && values.withinYear === 'yes' && values.fiveYears === 'yes';
  const validRoute = ['job','telework','professional','relationship','startup'].includes(values.route);
  return allBase && validRoute ? 'candidate' : 'confirm';
}

function initGarbage(form) {
  const select = form.querySelector('[name="area"]');
  GARBAGE_GROUPS.flat().forEach(area => select.insertAdjacentHTML('beforeend', `<option>${esc(area)}</option>`));
  form.addEventListener('submit', event => {
    event.preventDefault();
    const result = nextGarbageDates(select.value, new Date());
    const output = form.parentElement.querySelector('[data-tool-result]');
    if (!result) {
      output.innerHTML = '<p>町内会名を選んでください。</p>';
      return;
    }
    output.innerHTML = `<h3>${esc(select.value)}の次の収集日</h3><ul>`
      + `<li><strong>燃やせるごみ：</strong>${formatDate(result.burnable)}（通常は${result.burnableLabel}）</li>`
      + `<li><strong>資源ごみ・埋立ごみ：</strong>${formatDate(result.resource)}</li>`
      + `<li><strong>容器包装プラスチック：</strong>${formatDate(result.plastic)}</li></ul>`
      + '<p class="search-tool-note">令和8年度カレンダーによる目安です。臨時変更や年度外の日程は森町公式で確認してください。</p>';
  });
}

function initNursery(form) {
  form.addEventListener('submit', event => {
    event.preventDefault();
    const age = Number(new FormData(form).get('age'));
    const rows = nurseryForAge(age).map(row => `<tr><th scope="row">${esc(row.name)}</th><td>${row.status}</td></tr>`).join('');
    form.parentElement.querySelector('[data-tool-result]').innerHTML = `<h3>${age}歳児の受入れ見込み</h3>`
      + `<table class="nursery-table"><thead><tr><th>施設</th><th>見込み</th></tr></thead><tbody>${rows}</tbody></table>`
      + '<p>○＝4人以上、△＝1〜3人、×＝空きなし、—＝対象年齢外。入所を約束する表示ではありません。</p>';
  });
}

function initWater(form) {
  form.addEventListener('submit', event => {
    event.preventDefault();
    const data = new FormData(form);
    const result = calculateWater(data.get('usage'), data.get('diameter'), data.get('sewer') === 'yes');
    const output = form.parentElement.querySelector('[data-tool-result]');
    if (!result) {
      output.innerHTML = '<p>使用量と口径を確認してください。</p>';
      return;
    }
    output.innerHTML = '<h3>2か月分の概算</h3><ul>'
      + `<li>水道料金：<strong>${result.water.toLocaleString('ja-JP')}円</strong></li>`
      + `<li>下水道使用料：<strong>${result.sewer.toLocaleString('ja-JP')}円</strong></li>`
      + `<li>合計：<strong>${result.total.toLocaleString('ja-JP')}円</strong></li></ul>`
      + '<p>消費税込みの概算です。使用日数、認定水量、減免などにより実際の請求額と異なる場合があります。</p>';
  });
}

function initSchool(form) {
  form.addEventListener('submit', event => {
    event.preventDefault();
    const address = String(new FormData(form).get('address') || '').trim();
    const output = form.parentElement.querySelector('[data-tool-result]');
    if (!address) {
      output.innerHTML = '<p>住所または地区名を入力してください。</p>';
      return;
    }
    output.innerHTML = `<h3>学校教育課へ確認する内容</h3><p>「森町${esc(address)}の住所で、指定される小学校と中学校を確認したいです」</p>`
      + '<p><a class="btn" href="tel:0538851112">学校教育課へ電話する（0538-85-1112）</a></p>'
      + '<p>住所別通学区域の公式公開一覧を確認できないため、この機能は学校名を推測しません。</p>';
  });
}

function initMigration(form) {
  form.addEventListener('submit', event => {
    event.preventDefault();
    const data = Object.fromEntries(new FormData(form));
    const status = migrationCandidate(data);
    form.parentElement.querySelector('[data-tool-result]').innerHTML = status === 'candidate'
      ? '<h3>対象候補です</h3><p>入力した範囲では、移住就業支援金の主な条件に当てはまる可能性があります。転入・就業の前後で条件が変わるため、申請前に定住推進課へ確認してください。</p><p><a class="btn" href="tel:0538856321">定住推進課へ電話する（0538-85-6321）</a></p>'
      : '<h3>個別確認が必要です</h3><p>この回答だけで対象外とは決まりません。時期、東京圏での在住・通勤歴、就業等の経路を定住推進課へ確認してください。</p><p><a class="btn" href="tel:0538856321">定住推進課へ電話する（0538-85-6321）</a></p>';
  });
}

if (typeof document !== 'undefined') {
  document.querySelectorAll('[data-garbage-tool]').forEach(initGarbage);
  document.querySelectorAll('[data-nursery-tool]').forEach(initNursery);
  document.querySelectorAll('[data-water-tool]').forEach(initWater);
  document.querySelectorAll('[data-school-tool]').forEach(initSchool);
  document.querySelectorAll('[data-migration-tool]').forEach(initMigration);
}
