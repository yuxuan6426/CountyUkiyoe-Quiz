export const ROUND_SIZE = 6;

export function drawQuestions(questions, random = Math.random) {
  const pool = questions.map(question => question.id);
  for (let index = 0; index < ROUND_SIZE; index += 1) {
    const next = index + Math.floor(random() * (pool.length - index));
    [pool[index], pool[next]] = [pool[next], pool[index]];
  }
  return pool.slice(0, ROUND_SIZE);
}

export function pickRole(questions, answers, pools, random = Math.random) {
  const votes = questions.flatMap((question, index) => {
    const option = question.options[answers[index]];
    return option ? [option[0]] : [];
  });
  if (!votes.length) return null;

  const counts = new Map();
  for (const vote of votes) counts.set(vote, (counts.get(vote) ?? 0) + 1);
  const highest = Math.max(...counts.values());
  const style = votes.findLast(vote => counts.get(vote) === highest);
  const pool = pools[style];
  return pool[Math.floor(random() * pool.length)];
}

export function restoreRound(draft, questionsById) {
  if (!Array.isArray(draft?.ids) || draft.ids.length !== ROUND_SIZE ||
      new Set(draft.ids).size !== ROUND_SIZE || !draft.ids.every(id => questionsById.has(id)) ||
      !Array.isArray(draft.answers) || draft.answers.length !== ROUND_SIZE) return null;

  const answers = draft.answers.map((answer, index) => (
    Number.isInteger(answer) && questionsById.get(draft.ids[index]).options[answer] ? answer : null
  ));
  const index = Number.isInteger(draft.index) ? Math.max(0, Math.min(draft.index, ROUND_SIZE - 1)) : 0;
  return { ids: draft.ids, answers, index };
}

export function quizResultUrl(base, version, role, inviter) {
  if (!inviter) return new URL(`r/${version}/${role}/`, base);
  const url = new URL(`duo/${version}/`, base);
  url.search = new URLSearchParams({ a: inviter, b: role });
  return url;
}

export function readPair(params, roles) {
  const ids = ['a', 'b'].map(key => params.get(key));
  return ids.every(id => Object.hasOwn(roles, id)) ? ids : null;
}
