const byId = id => document.getElementById(id);
const data = JSON.parse(byId('share-data').textContent);
const shareStatus = byId('share-status');
const posterStatus = byId('poster-status');
const dialog = byId('poster-dialog');
const shareLink = byId('share-link');
const posterShare = byId('poster-share');
const posterImage = byId('poster-image');
const download = byId('poster-download');
const copyButton = byId('copy-link');
const posterButton = byId('poster-open');
const isPair = data.kind === 'duo';
const invitation = isPair ? '喊上朋友，各翻一张县城人物卡。' : '你会翻到哪位县城人物？点开也测一张。';
const shareText = isPair
  ? `我们在县城隐藏属性测试翻到了「${data.roles[0]}」和「${data.roles[1]}」。\n${invitation}`
  : `我在县城隐藏属性测试翻到了「${data.role}」。\n${invitation}`;
const shareCopy = `${shareText}\n\n${data.url}`;
let posterFile;
let posterPending;
let posterUrl;

async function copyShare() {
  try {
    await navigator.clipboard.writeText(shareCopy);
    byId('manual-copy').hidden = true;
    shareStatus.textContent = '分享文案已复制。';
  } catch {
    byId('manual-copy').hidden = false;
    const input = byId('share-copy');
    input.value = shareCopy;
    input.focus();
    input.select();
    shareStatus.textContent = '分享文案已选中，可以直接复制。';
  }
}

async function sendShare(payload, status, help) {
  try {
    await navigator.share(payload);
    status.textContent = '';
  } catch (error) {
    if (error.name !== 'AbortError') status.textContent = help;
  }
}

function canSharePoster(file) {
  try {
    return !!(file && typeof navigator.share === 'function' && navigator.canShare?.({ files: [file] }));
  } catch {
    return false;
  }
}

function writeLines(ctx, text, x, y, width, lineHeight) {
  let line = '';
  for (const character of text) {
    if (line && ctx.measureText(line + character).width > width) {
      ctx.fillText(line, x, y);
      y += lineHeight;
      line = '';
    }
    line += character;
  }
  ctx.fillText(line, x, y);
  return y + lineHeight;
}

function drawQR(ctx, rows, left, top, size) {
  const unit = Math.floor(size / (rows.length + 8));
  const dimension = unit * (rows.length + 8);
  const inset = Math.floor((size - dimension) / 2);
  ctx.fillStyle = '#fff';
  ctx.fillRect(left, top, size, size);
  ctx.fillStyle = '#000';
  for (const [y, row] of rows.entries()) {
    for (const [x, value] of [...row].entries()) {
      if (value === '1') ctx.fillRect(left + inset + (x + 4) * unit, top + inset + (y + 4) * unit, unit, unit);
    }
  }
}

const ink = '#1e352c';
const paper = '#fffaf0';
const yellow = '#f5db79';
const red = '#a8332b';
const sans = '"PingFang SC", "Microsoft YaHei", "Noto Sans CJK SC", sans-serif';
const display = '"STZhongsong", "Songti SC", "Noto Serif CJK SC", "SimSun", serif';

function drawPortrait(ctx, image, x, y, width, height) {
  const scale = Math.min(width / image.naturalWidth, height / image.naturalHeight);
  const imageWidth = image.naturalWidth * scale;
  const imageHeight = image.naturalHeight * scale;
  ctx.fillStyle = '#e2ebdc';
  ctx.fillRect(x, y, width, height);
  ctx.drawImage(image, x + (width - imageWidth) / 2, y + (height - imageHeight) / 2, imageWidth, imageHeight);
  ctx.strokeStyle = ink;
  ctx.strokeRect(x, y, width, height);
}

function createPoster(info, portraits) {
  const canvas = document.createElement('canvas');
  canvas.width = 840;
  canvas.height = 1120;
  const ctx = canvas.getContext('2d');
  if (!ctx) return Promise.reject(new Error('Canvas unavailable'));
  ctx.textBaseline = 'top';
  ctx.fillStyle = ink;
  ctx.fillRect(0, 0, 840, 1120);
  ctx.fillStyle = paper;
  ctx.fillRect(32, 32, 776, 1056);
  ctx.strokeStyle = ink;
  ctx.lineWidth = 2;
  ctx.strokeRect(51, 51, 738, 1018);
  ctx.fillStyle = yellow;
  ctx.fillRect(75, 75, 690, 90);
  ctx.fillStyle = ink;
  ctx.font = '700 39px ' + display;
  ctx.fillText('县城浮世绘', 100, 98);
  ctx.textAlign = 'right';
  ctx.font = '700 27px ' + sans;
  ctx.fillText(isPair ? '双人结果' : '隐藏属性卡', 740, 109);
  ctx.textAlign = 'left';

  if (isPair) {
    portraits.forEach((image, index) => {
      const x = 75 + index * 353;
      drawPortrait(ctx, image, x, 205, 337, 449);
      ctx.fillStyle = ink;
      ctx.font = '700 36px ' + display;
      writeLines(ctx, info.roles[index], x, 679, 337, 44);
    });
  } else {
    drawPortrait(ctx, portraits[0], 75, 205, 417, 556);
    ctx.fillStyle = red;
    ctx.font = '700 27px ' + sans;
    ctx.fillText('我翻到的县城人物', 520, 256);
    ctx.fillStyle = ink;
    ctx.font = '700 46px ' + display;
    const nameEnd = writeLines(ctx, info.role, 520, 310, 245, 60);
    ctx.fillStyle = red;
    ctx.font = '700 29px ' + sans;
    writeLines(ctx, info.detail, 520, nameEnd + 24, 245, 37);
  }

  ctx.setLineDash([8, 8]);
  ctx.strokeStyle = ink;
  ctx.beginPath();
  ctx.moveTo(75, 793);
  ctx.lineTo(765, 793);
  ctx.stroke();
  ctx.setLineDash([]);
  ctx.fillStyle = ink;
  ctx.font = '700 36px ' + display;
  ctx.fillText('扫码翻一张县城人物卡', 75, 838);
  ctx.font = '25px ' + sans;
  ctx.fillText('答一道题就能翻卡', 75, 900);
  ctx.font = '20px ' + sans;
  ctx.fillText('肖像：县城浮世绘人物图鉴 · yuxuan6426', 75, 1002, 450);
  drawQR(ctx, info.qr, 555, 820, 210);

  return new Promise((resolve, reject) => {
    canvas.toBlob(blob => blob ? resolve(blob) : reject(new Error('Poster encoding failed')), 'image/png');
  });
}

async function makePoster() {
  const portraits = [...document.querySelectorAll('.result-portrait img, .duo-role img')];
  await Promise.all(portraits.map(image => image.decode()));
  if (!data.qr) {
    const { default: qrcode } = await import('./qrcode.mjs');
    const code = qrcode(0, 'M');
    code.addData(data.url);
    code.make();
    const size = code.getModuleCount();
    data.qr = Array.from({ length: size }, (_, row) =>
      Array.from({ length: size }, (_, col) => code.isDark(row, col) ? '1' : '0').join(''));
  }
  return createPoster(data, portraits);
}

async function openPoster() {
  if (!dialog.open) {
    if (typeof dialog.showModal === 'function') dialog.showModal();
    else dialog.setAttribute('open', '');
  }
  if (posterUrl || posterPending) return;
  posterStatus.textContent = '正在排版海报…';
  posterPending = makePoster();
  try {
    const blob = await posterPending;
    const fileName = 'county-quiz-' + data.id + '.png';
    posterUrl = URL.createObjectURL(blob);
    if (typeof File === 'function') posterFile = new File([blob], fileName, { type: 'image/png' });
    posterImage.src = posterUrl;
    posterImage.hidden = false;
    download.href = posterUrl;
    download.download = fileName;
    download.hidden = false;
    posterShare.hidden = !canSharePoster(posterFile);
    posterStatus.textContent = '可以下载，手机上也可以长按图片保存。';
  } catch {
    posterStatus.textContent = '这次海报没画出来，可以关掉重试，或复制分享文案。';
  } finally {
    posterPending = null;
  }
}

if (typeof dialog.showModal !== 'function') {
  dialog.querySelector('form').addEventListener('submit', event => {
    event.preventDefault();
    dialog.removeAttribute('open');
    posterButton.focus();
  });
}
copyButton.addEventListener('click', copyShare);
posterButton.addEventListener('click', openPoster);
posterShare.addEventListener('click', () => {
  if (posterFile) sendShare({ files: [posterFile], title: data.title }, posterStatus, '可以下载或长按图片保存。');
});
if (typeof navigator.share === 'function') {
  shareLink.hidden = false;
  shareLink.addEventListener('click', () => {
    sendShare({ title: data.title, text: shareText, url: data.url }, shareStatus, '可以点「复制分享文案」发给朋友。');
  });
}
document.querySelector('.result').classList.add('reveal');
copyButton.disabled = false;
posterButton.disabled = false;
