var imgs = document.querySelectorAll('img.avatar');

if (imgs) {
  imgs.forEach(function(e) {
    e.addEventListener('error', defaultAvatar(e));
  });
}

function defaultAvatar(e) {
  e.onerror = null;
  e.src = k.STATIC_URL + 'sumo/img/avatar.png';
}
