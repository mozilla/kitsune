/*
 * Small DOM helpers - vanilla replacements for the handful of jQuery niceties
 * we relied on.
 *
 * Effects use the Web Animations API for the visible transition and CSSOM
 * property setters (el.style.*) for the final state. Neither is governed by
 * the CSP style-src directive (which only covers markup <style> blocks and
 * style="" attributes), so this is safe under the production policy - and it
 * matches how jQuery's .css()/.animate() behaved. Environments without the Web
 * Animations API (e.g. jsdom) fall back to an immediate state change, so unit
 * tests can assert the final DOM state while browsers get the animation.
 */

// Normalize a selector string, DOM node, NodeList, array, or jQuery object
// into an array of elements. This lets migrated modules keep accepting the
// jQuery objects that not-yet-migrated callers still pass in during the
// transition, alongside plain selectors/elements.
export function toElements(input) {
  if (!input) {
    return [];
  }
  if (typeof input === "string") {
    return Array.from(document.querySelectorAll(input));
  }
  if (input.nodeType) {
    return [input];
  }
  if (typeof input.length === "number") {
    return Array.from(input);
  }
  return [input];
}

// Like toElements, but returns the first matched element (or null).
export function toElement(input) {
  return toElements(input)[0] || null;
}

function animate(el, keyframes, duration) {
  if (typeof el.animate === "function") {
    // Animation.finished rejects if the animation is cancelled; swallow that.
    return el
      .animate(keyframes, { duration, fill: "forwards" })
      .finished.catch(() => {});
  }
  return new Promise((resolve) => setTimeout(resolve, 0));
}

// Fade an element out and set display:none. Resolves when done.
export function fadeOut(el, duration = 400) {
  return animate(el, [{ opacity: 1 }, { opacity: 0 }], duration).then(() => {
    el.style.display = "none";
  });
}

// Make an element visible and fade it in. Resolves when done.
export function fadeIn(el, duration = 400) {
  if (window.getComputedStyle(el).display === "none") {
    el.style.display = "";
  }
  return animate(el, [{ opacity: 0 }, { opacity: 1 }], duration).then(() => {
    el.style.opacity = "";
  });
}

// Slide an element up (collapse its height) and set display:none. Resolves
// when done. jsdom lacks layout/WAAPI, so it falls back to the final state.
export function slideUp(el, duration = 400) {
  const height = el.offsetHeight;
  const prevOverflow = el.style.overflow;
  el.style.overflow = "hidden";
  return animate(el, [{ height: height + "px" }, { height: "0px" }], duration).then(
    () => {
      el.style.display = "none";
      el.style.height = "";
      el.style.overflow = prevOverflow;
    }
  );
}

// Serialize a form's successful controls into a plain object (name -> value),
// mirroring jQuery's $.fn.serializeArray semantics: skips disabled controls,
// buttons/submits/resets, file/image inputs, and unchecked checkboxes/radios.
// Repeated names (e.g. multi-selects, checkbox groups) collapse into an array.
export function serialize(form) {
  const data = {};
  const skipTypes = ["submit", "button", "reset", "file", "image"];

  for (const el of form.elements) {
    if (!el.name || el.disabled || skipTypes.includes(el.type)) {
      continue;
    }
    if ((el.type === "checkbox" || el.type === "radio") && !el.checked) {
      continue;
    }

    let values;
    if (el.type === "select-multiple") {
      values = Array.from(el.selectedOptions, (opt) => opt.value);
    } else {
      values = [el.value];
    }

    for (const value of values) {
      if (el.name in data) {
        data[el.name] = [].concat(data[el.name], value);
      } else {
        data[el.name] = value;
      }
    }
  }

  return data;
}
