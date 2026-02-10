import avatar from "sumo/img/avatar.png";

const imgs = Array.from(new Set(
  document.querySelectorAll('img.avatar, .avatar img')
));

if (imgs) {
  imgs.forEach(function(e) {
    e.addEventListener('error', defaultAvatar);
  });
}

function defaultAvatar() {
  this.onerror = null;
  this.src = avatar;
}
