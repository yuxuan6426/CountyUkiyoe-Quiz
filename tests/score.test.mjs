import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resultPath, scoreQuiz } from '../src/assets/score.mjs';

const deck = JSON.parse(readFileSync(new URL('../src/deck.json', import.meta.url), 'utf8'));
const { questions, roles, pairs, version } = deck;

test('every answer combination resolves to one reachable role', () => {
  const distribution = new Map(Object.keys(roles).map(id => [id, 0]));
  const answers = Array(questions.length).fill(0);

  function visit(depth) {
    if (depth === questions.length) {
      const result = scoreQuiz(questions, answers);
      assert.ok(distribution.has(result));
      distribution.set(result, distribution.get(result) + 1);
      return;
    }
    for (let choice = 0; choice < questions[depth].options.length; choice += 1) {
      answers[depth] = choice;
      visit(depth + 1);
    }
  }

  visit(0);
  assert.equal([...distribution.values()].reduce((total, count) => total + count, 0), 65_536);
  for (const [role, count] of distribution) assert.ok(count > 0, role);
});

test('the latest selected role breaks ties', () => {
  const sample = [
    { options: [['0055']] },
    { options: [['1105']] },
    { options: [['0055']] },
    { options: [['1105']] },
    { options: [['1190']] },
  ];
  assert.equal(scoreQuiz(sample, [0, 0, 0, 0, 0]), '1105');
  assert.throws(() => scoreQuiz(sample, [0, 0]), /答完/);
  assert.throws(() => scoreQuiz(sample, [0, 0, null, 0, 0]), /答案无效/);
  assert.throws(() => scoreQuiz(sample, [0, 0, 9, 0, 0]), /答案无效/);
});

test('all 36 public pairs, including repeats, are reachable in both orders', () => {
  const urls = new Set();
  for (const first of Object.keys(roles)) {
    assert.equal(resultPath(version, [first]), 'r/v1/' + first + '/');
    for (const second of Object.keys(roles)) {
      const key = [first, second].sort().join('-');
      assert.ok(pairs[key]);
      const url = resultPath(version, [first, second]);
      assert.equal(url, resultPath(version, [second, first]));
      assert.equal(url, 'duo/v1/' + key + '/');
      urls.add(url);
    }
  }
  assert.equal(urls.size, 36);
});
