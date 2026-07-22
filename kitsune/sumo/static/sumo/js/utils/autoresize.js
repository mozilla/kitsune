/*
 * Native textarea auto-grow - vanilla replacement for the vendored
 * jquery.autoresize plugin (which only had a single textarea consumer).
 *
 * Grows the textarea's height to fit its content between minHeight and
 * maxHeight, switching to a scrollbar once maxHeight is reached. Uses the
 * scrollHeight measurement rather than the old clone-based approach.
 */

export function autoResize(el, options = {}) {
  if (!el) {
    return el;
  }
  const minHeight = options.minHeight || 0;
  const maxHeight = options.maxHeight || 500;

  el.style.resize = "none";
  el.style.overflowY = "hidden";

  function resize() {
    // Reset so scrollHeight reflects the content, not the current box.
    el.style.height = "auto";
    let height = el.scrollHeight;
    if (height < minHeight) {
      height = minHeight;
    }
    if (height >= maxHeight) {
      height = maxHeight;
      el.style.overflowY = "auto";
    } else {
      el.style.overflowY = "hidden";
    }
    el.style.height = height + "px";
  }

  el.addEventListener("input", resize);
  el.addEventListener("change", resize);
  resize();

  return el;
}
