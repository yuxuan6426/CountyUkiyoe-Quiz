import deck from './questions-v2.mjs';
import { drawQuestions, pickRole, quizResultUrl, restoreRound, ROUND_SIZE } from './quiz-core.mjs';

const byId = id => document.getElementById(id);
const siteBase = new URL('../', import.meta.url);
const requestedInviter = new URLSearchParams(location.search).get('with');
const inviter = Object.hasOwn(deck.roles, requestedInviter) ? requestedInviter : null;
const draftKey = ['county-quiz', deck.version, inviter ?? 'solo'].join(':');
const questionsById = new Map(deck.questions.map(question => [question.id, question]));
const landing = byId('landing');
const quiz = byId('quiz');
const title = byId('question-title');
const next = byId('next');
const previous = byId('previous');
const finish = byId('finish');
const options = byId('options');
let round;

function loadDraft() {
  try {
    return restoreRound(JSON.parse(sessionStorage.getItem(draftKey)), questionsById);
  } catch {
    return null;
  }
}

function saveDraft() {
  try {
    sessionStorage.setItem(draftKey, JSON.stringify(round));
  } catch {
    // The current page still works when the browser restricts session storage.
  }
}

function optionLabel(text, choice, selected) {
  const label = document.createElement('label');
  label.className = 'option';
  const input = document.createElement('input');
  input.type = 'radio';
  input.name = 'answer';
  input.value = choice;
  input.checked = selected === choice;
  const caption = document.createElement('span');
  caption.textContent = text;
  label.append(input, caption);
  return label;
}

function updateControls() {
  const { answers, index } = round;
  const hasAnswer = answers.some(answer => answer !== null);
  next.hidden = index === ROUND_SIZE - 1;
  next.textContent = answers[index] === null ? '跳过本题' : '下一题';
  finish.disabled = !hasAnswer;
  byId('finish-hint').hidden = hasAnswer;
}

function renderQuestion() {
  const { answers, index, ids } = round;
  const question = questionsById.get(ids[index]);
  byId('scene').textContent = question.scene;
  byId('progress').textContent = '第 ' + (index + 1) + ' / ' + ROUND_SIZE + ' 题';
  byId('progress-track').replaceChildren(...ids.map((_, number) => {
    const segment = document.createElement('span');
    segment.classList.toggle('done', answers[number] !== null);
    segment.classList.toggle('active', number === index);
    return segment;
  }));
  title.textContent = question.title;
  options.replaceChildren(...question.options.map(([, label], choice) => optionLabel(label, choice, answers[index])));
  updateControls();
  previous.textContent = index === 0 ? '回首页' : '上一题';
  title.focus({ preventScroll: true });
  window.scrollTo(0, 0);
}

function renderRoute() {
  const answering = location.hash === '#quiz';
  landing.hidden = answering;
  quiz.hidden = !answering;
  if (answering) {
    if (!round) {
      round = { ids: drawQuestions(deck.questions), answers: Array(ROUND_SIZE).fill(null), index: 0 };
      saveDraft();
    }
    renderQuestion();
    return;
  }
  const start = byId('start');
  start.firstChild.textContent = round ? '继续答题 ' : '开始测评 ';
  if (inviter) {
    const invite = byId('invite');
    invite.textContent = '「' + deck.roles[inviter] + '」邀请你一起翻卡';
    invite.hidden = false;
  }
}

byId('question-form').addEventListener('change', event => {
  if (event.target.name !== 'answer') return;
  round.answers[round.index] = Number(event.target.value);
  saveDraft();
  updateControls();
});

previous.addEventListener('click', () => {
  if (round.index === 0) {
    history.replaceState(null, '', location.pathname + location.search);
    renderRoute();
    byId('start').focus();
    return;
  }
  round.index -= 1;
  saveDraft();
  renderQuestion();
});

next.addEventListener('click', () => {
  if (round.index === ROUND_SIZE - 1) return;
  round.index += 1;
  saveDraft();
  renderQuestion();
});

let finishing = false;
byId('question-form').addEventListener('submit', event => {
  event.preventDefault();
  if (!round || finishing) return;
  const questions = round.ids.map(id => questionsById.get(id));
  const role = pickRole(questions, round.answers, deck.pools);
  if (!role) return;
  finishing = true;
  finish.disabled = true;
  try {
    sessionStorage.removeItem(draftKey);
  } catch {
    // Download and sharing remain available when storage is unavailable.
  }
  location.assign(quizResultUrl(siteBase, deck.version, role, inviter));
});

function loadPage() {
  const url = new URL(location.href);
  if (url.searchParams.has('new')) {
    try {
      sessionStorage.removeItem(draftKey);
    } catch {
      // A new round still works without storage.
    }
    url.searchParams.delete('new');
    history.replaceState(null, '', url);
    round = null;
  } else {
    round = loadDraft();
  }
  finishing = false;
  renderRoute();
}

window.addEventListener('pageshow', event => {
  if (event.persisted) loadPage();
});
window.addEventListener('hashchange', renderRoute);
loadPage();
