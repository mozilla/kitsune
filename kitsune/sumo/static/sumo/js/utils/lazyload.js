/*
 * Lazy-load images that defer their real source in a data-original-src
 * attribute, swapping it into src as they scroll near the viewport. Vanilla
 * IntersectionObserver replacement for the vendored jquery.lazyload plugin.
 */

const DEFAULT_ROOT_MARGIN = "750px";

// Swap data-original-src into src and drop the lazy marker. Safe to call
// directly (mirrors the old $.fn.lazyload.loadOriginalImage helper).
export function loadImage(img) {
  const src = img.getAttribute("data-original-src");
  if (src) {
    img.setAttribute("src", src);
    img.removeAttribute("data-original-src");
  }
  img.classList.remove("lazy");
}

// Immediately load every lazy image under `root` (replaces $.fn.loadnow).
export function loadAllImages(root = document) {
  const scope = root && root.querySelectorAll ? root : document;
  Array.from(scope.querySelectorAll("img.lazy[data-original-src]")).forEach(
    loadImage
  );
}

// Observe every img.lazy[data-original-src] under `root` (default: document)
// and load each as it approaches the viewport. Returns the IntersectionObserver
// (or undefined when unsupported, in which case images load immediately).
export function lazyload(root = document, options = {}) {
  const scope = root && root.querySelectorAll ? root : document;
  const images = Array.from(
    scope.querySelectorAll("img.lazy[data-original-src]")
  );

  if (!("IntersectionObserver" in window)) {
    images.forEach(loadImage);
    return undefined;
  }

  const observer = new window.IntersectionObserver(
    (entries, obs) => {
      for (const entry of entries) {
        if (entry.isIntersecting) {
          loadImage(entry.target);
          obs.unobserve(entry.target);
        }
      }
    },
    { rootMargin: options.rootMargin || DEFAULT_ROOT_MARGIN }
  );

  images.forEach((img) => observer.observe(img));
  return observer;
}
