import assert from 'node:assert/strict';
import {
  calculateWater,
  garbageGroupFor,
  migrationCandidate,
  nextGarbageDates,
  nurseryForAge
} from '../assets/search-tools.mjs';

assert.equal(garbageGroupFor('黒田'), 0);
assert.equal(garbageGroupFor('若宮'), 10);
assert.equal(garbageGroupFor('存在しない地区'), -1);

const garbage = nextGarbageDates('城下上', '2026-08-06');
assert.equal(garbage.resource, '2026-08-07');
assert.equal(garbage.plastic, '2026-08-26');
assert.equal(garbage.burnable, '2026-08-06');

assert.deepEqual(calculateWater(40, 13, true), {water: 5324, sewer: 4400, total: 9724});
assert.deepEqual(calculateWater(16, 13, false), {water: 2420, sewer: 0, total: 2420});

assert.deepEqual(nurseryForAge(3).map(row => row.status), ['×', '○', '△', '—', '—']);

assert.equal(migrationCandidate({
  move: 'yes', tokyo: 'yes', withinYear: 'yes', fiveYears: 'yes', route: 'telework'
}), 'candidate');
assert.equal(migrationCandidate({
  move: 'yes', tokyo: 'unsure', withinYear: 'yes', fiveYears: 'yes', route: 'job'
}), 'confirm');

console.log('検索支援機能の計算テスト: すべて合格');
