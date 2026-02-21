import avatar from "sumo/img/avatar.png";

const FALLBACK_URL = new URL(avatar, window.location.href).href;
const AVATAR_SELECTOR = 'img.avatar, .avatar img';

window.addEventListener(
  'error',
  (event) => {
    const target = event.target;
    if (isAvatar(target) && target.src != FALLBACK_URL) {
      target.src = avatar;
    }
  },
  true
);

// Apply the fallback to the images not caught by the above listener.
const imgs = Array.from(new Set(
  document.querySelectorAll(AVATAR_SELECTOR)
));
if (imgs) {
  imgs.forEach(function(img) {
    if (img.complete && img.currentSrc && img.naturalWidth === 0) {
      img.src = avatar;
    }
  });
}

function isAvatar(target) {
  return target instanceof HTMLImageElement && target.matches(AVATAR_SELECTOR);
}