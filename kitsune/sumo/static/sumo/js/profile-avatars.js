import avatar from "sumo/img/avatar.png";

var imgs = document.querySelectorAll('img.avatar');

if (imgs) {
  imgs.forEach(function(e) {
    e.addEventListener('error', defaultAvatar);
  });
}

function defaultAvatar() {
  this.onerror = null;
  this.src = avatar;
}
