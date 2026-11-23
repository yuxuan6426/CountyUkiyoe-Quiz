import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { drawQuestions, pickRole, quizResultUrl, readPair, restoreRound } from '../src/assets/quiz-core.mjs';

const load = path => JSON.parse(readFileSync(new URL(path, import.meta.url), 'utf8'));
const questions = load('../src/questions.json');
const pools = load('../src/pools.json');
const byId = new Map(questions.map(question => [question.id, question]));

test('draw six distinct questions from either end of the bank', () => {
  assert.deepEqual(drawQuestions(questions, () => 0), questions.slice(0, 6).map(question => question.id));
  const last = drawQuestions(questions, () => .9999);
  assert.equal(last[0], questions.at(-1).id);
  assert.equal(new Set(last).size, 6);
  assert.ok(last.every(id => byId.has(id)));
});

test('score selected answers only and use the last voting question to break a tie', () => {
  const selected = ['q01', 'q02', 'q03', 'q04', 'q05', 'q06'].map(id => byId.get(id));
  assert.equal(pickRole(selected, [null, null, null, null, null, null], pools), null);
  assert.equal(pickRole(selected, [null, null, null, null, null, 0], pools, () => 0), pools.fix[0]);
  assert.equal(pickRole(selected, [0, null, 2, 0, 1, null], pools, () => 0), pools.connect[0]);
  assert.equal(pickRole(selected, [0, 0, 2, 2, null, null], pools, () => 0), pools.fix[0]);
});

test('every style can produce roles throughout its pool from one answer', () => {
  for (const [style, ids] of Object.entries(pools)) {
    const question = questions.find(item => item.options.some(option => option[0] === style));
    const answer = question.options.findIndex(option => option[0] === style);
    assert.equal(pickRole([question], [answer], pools, () => 0), ids[0]);
    assert.equal(pickRole([question], [answer], pools, () => .9999), ids.at(-1));
  }
});

test('restore the exact round, including skipped questions and editable answers', () => {
  const ids = drawQuestions(questions, () => .5);
  const draft = { ids, answers: [null, 2, 0, null, null, 1], index: 5 };
  assert.deepEqual(restoreRound(draft, byId), draft);
  assert.equal(restoreRound({ ...draft, ids: Array(6).fill(ids[0]) }, byId), null);
  assert.equal(restoreRound({ ...draft, answers: [9, 2, 0, null, null, 1] }, byId).answers[0], null);
  assert.equal(restoreRound({ ...draft, ids: ['unknown', ...ids.slice(1)] }, byId), null);
  assert.equal(restoreRound({ ...draft, answers: 'damaged' }, byId), null);
});

test('pair URLs preserve inviter order and allow repeated IDs', () => {
  const base = new URL('https://example.com/quiz/');
  const roles = { '0055': 'first', '1190': 'second' };
  assert.equal(quizResultUrl(base, 'v2', '0055', null).pathname, '/quiz/r/v2/0055/');
  const url = quizResultUrl(base, 'v2', '0055', '1190');
  assert.equal(url.pathname, '/quiz/duo/v2/');
  assert.deepEqual(readPair(url.searchParams, roles), ['1190', '0055']);
  assert.deepEqual(readPair(new URLSearchParams('a=0055&b=0055'), roles), ['0055', '0055']);
  assert.equal(readPair(new URLSearchParams('a=0055&b=constructor'), roles), null);
  assert.equal(readPair(new URLSearchParams('a=0055'), roles), null);
});
