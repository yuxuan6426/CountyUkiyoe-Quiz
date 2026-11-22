import catalog from './cards.mjs';
import { readPair } from './quiz-core.mjs';

const { cards, gallery, site, version } = catalog;
const ids = readPair(new URLSearchParams(location.search), cards);

function element(tag, className, value = '') {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (value) node.textContent = value;
  return node;
}

function link(text, href, className) {
  const node = element('a', className, text);
  node.href = href;
  return node;
}

function makeCard(id, index) {
  const card = cards[id];
  const folder = new URL(`gallery/characters/${card.slug}/`, gallery);
  const section = element('section', 'duo-role');
  const figure = element('figure');
  const image = element('img');
  image.src = new URL('portrait.jpg', folder);
  image.alt = `${card.name}的图鉴肖像`;
  image.width = 864;
  image.height = 1152;
  image.decoding = 'async';
  figure.append(image, element('figcaption', '', index === 0 ? '发起方' : '应邀方'));

  const copy = element('div', 'duo-role-copy');
  const links = element('p', 'duo-links');
  links.append(
    link('看个人卡', new URL(`r/${version}/${id}/`, site)),
    ' ',
    link('读图鉴档案 ↗', new URL('dossier.md', folder), 'archive'),
  );
  copy.append(element('h2', '', card.name), element('p', '', card.style), links);
  section.append(figure, copy);
  return section;
}

async function showPair() {
  document.getElementById('pair-cards').replaceChildren(...ids.map(makeCard));
  document.getElementById('pair-view').hidden = false;

  const shareUrl = new URL(`duo/${version}/`, site);
  shareUrl.search = new URLSearchParams({ a: ids[0], b: ids[1] });
  const shareData = element('script');
  shareData.type = 'application/json';
  shareData.id = 'share-data';
  shareData.textContent = JSON.stringify({
    kind: 'duo', title: '我们的县城人物卡', line: '各翻一张，一起看看',
    edition: version, url: shareUrl.href, id: ids.join('-'),
    roles: ids.map(id => ({ title: cards[id].name, part: cards[id].style })),
  });
  document.body.append(shareData);
  await import('./share.mjs');
}

if (ids) await showPair();
else document.getElementById('pair-missing').hidden = false;
