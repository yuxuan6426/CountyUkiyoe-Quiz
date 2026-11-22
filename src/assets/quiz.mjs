import deck from './deck.mjs';
import { resultPath, scoreQuiz } from './score.mjs';

const byId = id => document.getElementById(id);
const siteBase = new URL('../', import.meta.url);
const requestedInviter = new URLSearchParams(location.search).get('with');
const inviter = Object.hasOwn(deck.roles, requestedInviter) ? requestedInviter : null;
const draftKey = ['county-quiz', deck.version, inviter ?? 'solo'].join(':');
const { questions } = deck;
const landing = byId('landing');
const quiz = byId('quiz');
const title = byId('question-title');
const next = byId('next');
const previous = byId('previous');
const options = byId('options');
let { answers, index } = loadDraft();

function loadDraft() {
  const empty = { answers: Array(questions.length).fill(null), index: 0 };
  try {
    const draft = JSON.parse(sessionStorage.getItem(draftKey));
    if (!Array.isArray(draft?.answers) || draft.answers.length !== questions.length) return empty;
    const valid = draft.answers.map((answer, i) => (
      Number.isInteger(answer) && questions[i].options[answer] ? answer : null
    ));
    const firstUnanswered = valid.indexOf(null);
    const limit = firstUnanswered < 0 ? valid.length - 1 : firstUnanswered;
    return { answers: valid, index: Number.isInteger(draft.index) ? Math.max(0, Math.min(draft.index, limit)) : 0 };
  } catch {
    return empty;
  }
}

function saveDraft() {
  try {
    sessionStorage.setItem(draftKey, JSON.stringify({ answers, index }));
  } catch {
    // The current page still works when the browser restricts session storage.
  }
}

function optionLabel(text, choice) {
  const label = document.createElement('label');
  label.className = 'option';
  const input = document.createElement('input');
  input.type = 'radio';
  input.name = 'answer';
  input.value = choice;
  input.checked = answers[index] === choice;
  const caption = document.createElement('span');
  caption.textContent = text;
  label.append(input, caption);
  return label;
}

function renderQuestion() {
  const question = questions[index];
  byId('scene').textContent = question.scene;
  byId('progress').textContent = '第 ' + (index + 1) + ' / ' + questions.length + ' 题';
  byId('progress-track').replaceChildren(...questions.map((_, number) => {
    const segment = document.createElement('span');
    segment.classList.toggle('done', number < index);
    segment.classList.toggle('active', number === index);
    return segment;
  }));
  title.textContent = question.title;
  options.replaceChildren(...question.options.map(([, label], choice) => optionLabel(label, choice)));
  next.disabled = answers[index] === null;
  next.textContent = index === questions.length - 1 ? (inviter ? '揭晓搭档卡' : '翻开我的卡') : '下一题';
  previous.textContent = index === 0 ? '回首页' : '上一题';
  title.focus({ preventScroll: true });
  window.scrollTo(0, 0);
}

function renderRoute() {
  const answering = location.hash === '#quiz';
  landing.hidden = answering;
  quiz.hidden = !answering;
  if (answering) {
    renderQuestion();
    return;
  }
  const start = byId('start');
  if (answers.some(answer => answer !== null)) start.firstChild.textContent = '继续答题 ';
  if (inviter) {
    const invite = byId('invite');
    invite.textContent = '「' + deck.roles[inviter] + '」喊你来搭伙';
    invite.hidden = false;
  }
}

byId('question-form').addEventListener('change', event => {
  if (event.target.name !== 'answer') return;
  answers[index] = Number(event.target.value);
  next.disabled = false;
  saveDraft();
});

previous.addEventListener('click', () => {
  if (index === 0) {
    history.replaceState(null, '', location.pathname + location.search);
    renderRoute();
    byId('start').focus();
    return;
  }
  index -= 1;
  saveDraft();
  renderQuestion();
});

byId('question-form').addEventListener('submit', event => {
  event.preventDefault();
  if (answers[index] === null) return;
  if (index < questions.length - 1) {
    index += 1;
    saveDraft();
    renderQuestion();
    return;
  }
  const role = scoreQuiz(questions, answers);
  try {
    sessionStorage.removeItem(draftKey);
  } catch {
    // Download and sharing remain available when storage is unavailable.
  }
  const ids = inviter ? [inviter, role] : [role];
  location.assign(new URL(resultPath(deck.version, ids), siteBase));
});

window.addEventListener('hashchange', renderRoute);
renderRoute();
