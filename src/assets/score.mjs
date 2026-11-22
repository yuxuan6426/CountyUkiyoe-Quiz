export function resultPath(version, ids) {
  const kind = ids.length === 1 ? 'r' : 'duo';
  return [kind, version, [...ids].sort().join('-'), ''].join('/');
}

export function scoreQuiz(questions, answers) {
  if (answers.length !== questions.length) throw new Error('请答完所有题目。');
  const votes = answers.map((answer, index) => questions[index].options[answer]?.[0]);
  if (votes.includes(undefined)) throw new Error('答案无效，请重新选择。');
  const counts = new Map();
  for (const role of votes) counts.set(role, (counts.get(role) ?? 0) + 1);
  const highest = Math.max(...counts.values());
  return votes.findLast(role => counts.get(role) === highest);
}
