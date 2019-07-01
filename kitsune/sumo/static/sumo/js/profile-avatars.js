var imgs = document.querySelectorAll('img.avatar');

if (imgs) {
  imgs.forEach(function(e) {
    e.addEventListener('error', defaultAvatar);
  });
}

function defaultAvatar() {
  this.onerror = null;
  this.src = k.STATIC_URL + 'sumo/img/avatar.png';
}
