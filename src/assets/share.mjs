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
const shareText = data.kind === 'role' ? '来和「' + data.title + '」搭伙。' : '我们在县城搭伙的结果';
let posterFile;
let posterPending;
let posterUrl;

async function copyLink() {
  try {
    await navigator.clipboard.writeText(data.url);
    byId('manual-copy').hidden = true;
    shareStatus.textContent = '已复制，可以发给朋友。';
  } catch {
    byId('manual-copy').hidden = false;
    const input = byId('share-url');
    input.value = data.url;
    input.focus();
    input.select();
    shareStatus.textContent = '链接已选中，可以手动复制。';
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

function drawDetails(ctx, info, y) {
  if (info.kind === 'role') {
    ctx.fillStyle = info.accent;
    ctx.fillRect(75, y, 690, 148);
    ctx.fillStyle = paper;
    ctx.font = '700 26px ' + sans;
    ctx.fillText('随身道具', 105, y + 40);
    ctx.font = '700 53px ' + display;
    ctx.fillText(info.prop, 105, y + 79);
    ctx.font = '700 24px ' + sans;
    ctx.fillText('图鉴原型', 357, y + 42);
    ctx.font = '700 31px ' + sans;
    ctx.fillText(info.role, 357, y + 88);
    return;
  }
  info.roles.forEach((role, index) => {
    const x = 75 + index * 353;
    ctx.fillStyle = index ? '#e2ebdc' : '#f8e8a9';
    ctx.fillRect(x, y, 337, 187);
    ctx.strokeStyle = ink;
    ctx.lineWidth = 2;
    ctx.strokeRect(x, y, 337, 187);
    ctx.fillStyle = ink;
    ctx.font = '700 30px ' + sans;
    writeLines(ctx, role.title, x + 17, y + 28, 303, 34);
    ctx.font = '25px ' + sans;
    writeLines(ctx, role.part, x + 17, y + 88, 303, 35);
  });
}

function createPoster(info) {
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
  ctx.fillText(info.kind === 'duo' ? '双人搭档卡' : '隐藏属性卡', 740, 109);
  ctx.textAlign = 'left';

  ctx.font = '700 77px ' + display;
  const bodyY = writeLines(ctx, info.title, 75, 209, 690, 92);
  ctx.fillStyle = red;
  ctx.font = '700 34px ' + sans;
  const detailY = writeLines(ctx, info.line, 75, bodyY + 18, 690, 49) + 33;
  drawDetails(ctx, info, Math.max(detailY, 466));

  ctx.setLineDash([8, 8]);
  ctx.strokeStyle = ink;
  ctx.beginPath();
  ctx.moveTo(75, 793);
  ctx.lineTo(765, 793);
  ctx.stroke();
  ctx.setLineDash([]);
  ctx.fillStyle = ink;
  ctx.font = '700 36px ' + display;
  ctx.fillText('扫码领你的县城属性', 75, 838);
  ctx.font = '25px ' + sans;
  ctx.fillText(info.kind === 'duo' ? '打开搭档卡，选一位接着测' : '打开这张卡，测测你俩怎么搭伙', 75, 900);
  ctx.font = '20px ' + sans;
  ctx.fillText('县城隐藏属性测试 · 朋友局娱乐', 75, 1002);
  drawQR(ctx, info.qr, 555, 820, 210);

  return new Promise((resolve, reject) => {
    canvas.toBlob(blob => blob ? resolve(blob) : reject(new Error('Poster encoding failed')), 'image/png');
  });
}

async function openPoster() {
  if (!dialog.open) {
    if (typeof dialog.showModal === 'function') dialog.showModal();
    else dialog.setAttribute('open', '');
  }
  if (posterUrl || posterPending) return;
  posterStatus.textContent = '正在排版海报…';
  posterPending = createPoster(data);
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
    posterStatus.textContent = '这次海报没画出来，可以关掉重试，或复制结果链接。';
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
copyButton.addEventListener('click', copyLink);
posterButton.addEventListener('click', openPoster);
posterShare.addEventListener('click', () => {
  if (posterFile) sendShare({ files: [posterFile], title: data.title }, posterStatus, '可以下载或长按图片保存。');
});
if (typeof navigator.share === 'function') {
  shareLink.hidden = false;
  shareLink.addEventListener('click', () => {
    sendShare({ title: data.title, text: shareText, url: data.url }, shareStatus, '可以点「复制链接」发给朋友。');
  });
}
document.querySelector('.result').classList.add('reveal');
copyButton.disabled = false;
posterButton.disabled = false;
