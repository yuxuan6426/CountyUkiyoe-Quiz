import catalog from './cards-share.mjs';
import { readPair } from './quiz-core.mjs';

const { cards, galleryEntry, site, version } = catalog;
const siteBase = new URL('../', import.meta.url);
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
  const cardUrl = new URL(galleryEntry);
  cardUrl.searchParams.set('card', card.slug);
  const section = element('section', 'duo-role');
  const figure = element('figure');
  const image = element('img');
  image.src = new URL(`portraits/${version}/${id}.jpg`, siteBase);
  image.alt = `${card.name}的图鉴肖像`;
  image.width = 864;
  image.height = 1152;
  image.decoding = 'async';
  const portraitLink = link('', cardUrl, 'portrait-link');
  portraitLink.setAttribute('aria-label', `查看${card.name}的图鉴卡`);
  portraitLink.append(image);
  figure.append(portraitLink, element('figcaption', '', index === 0 ? '发起方' : '应邀方'));

  const copy = element('div', 'duo-role-copy');
  const links = element('p', 'duo-links');
  links.append(
    link('看个人卡', new URL(`r/${version}/${id}/`, site)),
    ' ',
    link('查看图鉴卡 ↗', cardUrl, 'archive'),
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
    kind: 'duo', title: '我们的县城人物卡', url: shareUrl.href, id: ids.join('-'),
    roles: ids.map(id => cards[id].name),
  });
  document.body.append(shareData);
  await import('./share-cards.mjs');
}

if (ids) await showPair();
else document.getElementById('pair-missing').hidden = false;
