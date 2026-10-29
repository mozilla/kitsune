function pageLocale() {
  try {
    return Intl.getCanonicalLocales(document.documentElement.lang)[0];
  } catch (e) {
    return undefined;
  }
}

// Skip leading punctuation when filing a title, and list titles that start with a digit after Z.
function titleSortKey(title) {
  const key = title.replace(/^[^\p{L}\p{N}]+/u, "");
  return { key, group: /^\p{L}/u.test(key) ? 0 : 1 };
}

export function initTopicList(root = document) {
  const toolbar = root.querySelector("[data-list-toolbar]");
  const list = root.querySelector("[data-topic-list]");
  if (!toolbar || !list) {
    return;
  }

  const controls = toolbar.querySelector("[data-list-controls]");
  const sortSelect = toolbar.querySelector("[data-list-sort]");
  if (!controls || !sortSelect) {
    return;
  }

  const collator = new Intl.Collator(pageLocale());

  const rows = Array.from(list.querySelectorAll(".topic-doc-list--item")).map((element, index) => {
    const updated = Date.parse(element.dataset.updated);
    return {
      element,
      index,
      title: titleSortKey(element.dataset.title || ""),
      updated: Number.isNaN(updated) ? -Infinity : updated,
    };
  });

  const comparators = {
    server: (a, b) => a.index - b.index,
    updated: (a, b) => b.updated - a.updated || a.index - b.index,
    title: (a, b) =>
      a.title.group - b.title.group || collator.compare(a.title.key, b.title.key) || a.index - b.index,
  };

  function applySort() {
    const comparator = comparators[sortSelect.value] || comparators.server;
    list.append(...rows.slice().sort(comparator).map((row) => row.element));
  }

  sortSelect.addEventListener("change", applySort);
  controls.classList.remove("is-hidden");
}
