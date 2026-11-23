export function addPortraitFallback(image) {
  if (!image.dataset.backup) return;
  const useBackup = () => { image.src = image.dataset.backup; };
  if (image.complete && !image.naturalWidth) useBackup();
  else image.addEventListener('error', useBackup, { once: true });
}
