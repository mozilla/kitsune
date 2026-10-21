function pageLocale() {
  try {
    return Intl.getCanonicalLocales(document.documentElement.lang)[0];
  } catch (e) {
    return undefined;
  }
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
      title: element.dataset.title || "",
      updated: Number.isNaN(updated) ? -Infinity : updated,
    };
  });

  const comparators = {
    server: (a, b) => a.index - b.index,
    updated: (a, b) => b.updated - a.updated || a.index - b.index,
    title: (a, b) => collator.compare(a.title, b.title) || a.index - b.index,
  };

  function applySort() {
    const comparator = comparators[sortSelect.value] || comparators.server;
    list.append(...rows.slice().sort(comparator).map((row) => row.element));
  }

  sortSelect.addEventListener("change", applySort);
  controls.classList.remove("is-hidden");
}
