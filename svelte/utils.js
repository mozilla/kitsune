const staticJinjaTag = "{{ STATIC_URL_WEBPACK }}";

export function srcset(...sources) {
  return sources
    .map(
      (source, index) =>
        encodeURI(source).replace(encodeURI(staticJinjaTag), staticJinjaTag) +
        ` ${index + 1}x`
    )
    .join(", ");
}

export function gettext(...args) {
  return (typeof window === "undefined" ? global : window).gettext(...args);
}
