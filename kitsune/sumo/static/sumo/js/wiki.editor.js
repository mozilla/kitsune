import TomSelect from "tom-select";
import "sumo/scss/components/_tom-select.scss";
import "sumo/scss/components/_kb-audiences.scss";

function intersection(setA, setB) {
  // Use this function instead of the Set.intersection method,
  // which has been available only since June 2024, so that we
  // support older browser versions. We can switch to the
  // Set.intersection method at some time in the future.
  // Ensure the smaller set is iterated to improve efficiency
  if (setA.size > setB.size) {
    [setA, setB] = [setB, setA];
  }
  return new Set([...setA].filter(item => setB.has(item)));
}

function handleTopicRelationships(topic) {
  // If we've checked a subtopic, automatically check its topic.
  if (topic.classList.contains("level-2-topic") && topic.checked) {
    document.getElementById(`id_topic_${topic.dataset.parentTopicId}`).checked = true;
    // If we've unchecked a topic, automatically uncheck its subtopics.
  } else if (topic.classList.contains("level-1-topic") && !topic.checked) {
    document.querySelectorAll(
      '#relevant-topics input[type="checkbox"][name="topics"]' +
      `[data-parent-topic-id="${topic.dataset.topicId}"]`
    ).forEach(function (subtopic) {
      subtopic.checked = false;
    });
  }
}

function getAllowedTopicIdsFromSelectedProducts() {
  // Gather the intersection of topic ids associated with all selected products.
  let allowedTopicIds = "all";
  document.querySelectorAll(
    '#relevant-products input[type="checkbox"][name="products"]:checked'
  ).forEach(function (product) {
    let topicIds = new Set(JSON.parse(product.dataset.topicIds));
    if (allowedTopicIds === "all") {
      allowedTopicIds = topicIds;
    } else {
      allowedTopicIds = intersection(allowedTopicIds, topicIds);
    }
  });
  return allowedTopicIds;
}

function getAllowedProductIdsFromSelectedTopics() {
  // Gather the intersection of product ids associated with all selected topics.
  let allowedProductIds = "all";
  document.querySelectorAll(
    '#relevant-topics input[type="checkbox"][name="topics"]:checked'
  ).forEach(function (topic) {
    let productIds = new Set(JSON.parse(topic.dataset.productIds));
    if (allowedProductIds === "all") {
      allowedProductIds = productIds;
    } else {
      allowedProductIds = intersection(allowedProductIds, productIds);
    }
  });
  return allowedProductIds;
}

function updateDisabledMessage(name) {
  let numberDisabled = document.querySelectorAll(
    `#relevant-${name} input[type="checkbox"][name="${name}"]:disabled`
  ).length;
  let message = document.getElementById(`relevant-${name}-disabled-message`);
  if (message) {
    message.hidden = (numberDisabled === 0);
  }
}

function updateSelectedMessage(name) {
  let numberSelected = document.querySelectorAll(
    `#relevant-${name} input[type="checkbox"][name="${name}"]:checked`
  ).length;
  let message = document.getElementById(`relevant-${name}-selected-message`);
  if (numberSelected > 0 && message) {
    message.textContent = interpolate(
      gettext("%(number)s selected"), { number: numberSelected }, true
    );
  }
  document.querySelectorAll(`.relevant-${name}-selected`).forEach(function (element) {
    element.hidden = (numberSelected === 0);
  });
}

function updateMessages(name) {
  updateDisabledMessage(name);
  updateSelectedMessage(name);
}

function updateTopics(allowedTopicIds, allowedProductIds) {
  // Enable/disable topics based on the selected topics and products.
  document.querySelectorAll(
    '#relevant-topics input[type="checkbox"][name="topics"]:not(:checked)'
  ).forEach(function (topic) {
    let topicLabel = document.querySelector(
      `label[for="id_topic_${topic.dataset.topicId}"]`
    );
    let productIds = new Set(JSON.parse(topic.dataset.productIds));
    if (
      ((allowedTopicIds === "all") || allowedTopicIds.has(topic.dataset.topicId)) &&
      ((allowedProductIds === "all") || (intersection(productIds, allowedProductIds).size > 0))
    ) {
      topic.disabled = false;
      topicLabel.classList.remove("disabled");
    } else {
      // This topic is either not associated with every one of the currently
      // selected products, or has no associated products in common with the
      // current set of allowed products, so we should disable it.
      topic.disabled = true;
      topicLabel.classList.add("disabled");
    }
  });
  updateMessages("topics");
}

function updateProducts(allowedTopicIds, allowedProductIds) {
  // Enable/disable products based on the selected topics and products.
  document.querySelectorAll(
    '#relevant-products input[type="checkbox"][name="products"]:not(:checked)'
  ).forEach(function (product) {
    let productLabel = document.querySelector(
      `label[for="id_product_${product.dataset.productId}"]`
    );
    let topicIds = new Set(JSON.parse(product.dataset.topicIds));
    if (
      ((allowedProductIds === "all") || allowedProductIds.has(product.dataset.productId)) &&
      ((allowedTopicIds === "all") || (intersection(topicIds, allowedTopicIds).size > 0))
    ) {
      product.disabled = false;
      productLabel.classList.remove("disabled");
    } else {
      // This product is either not associated with every one of the currently
      // selected topics, or has no associated topics in common with the
      // current set of allowed topics, so we should disable it.
      product.disabled = true;
      productLabel.classList.add("disabled");
    }
  });
  updateMessages("products");
}

function handleUpdate() {
  // Enable/disable topics and products based on the selected topics and products.
  let allowedTopicIds = getAllowedTopicIdsFromSelectedProducts();
  let allowedProductIds = getAllowedProductIdsFromSelectedTopics();
  updateTopics(allowedTopicIds, allowedProductIds);
  updateProducts(allowedTopicIds, allowedProductIds);
}

// Tom Select copies each <option>'s data-* attributes onto its option data.
const isPublicAudience = (data) => data.public === "true";

function audienceBadge(data) {
  const modifier = isPublicAudience(data) ? "public" : "private";
  const text = isPublicAudience(data) ? gettext("Public") : gettext("Private");
  return `<span class="kb-audience-badge kb-audience-badge--${modifier}">${text}</span>`;
}

const AUDIENCE_STATUS_ICONS = { public: "🌐", private: "🔒", mixed: "🌐" };
const MAX_LISTED_AUDIENCES = 3;

function escapeHtml(text) {
  const span = document.createElement("span");
  span.textContent = text;
  return span.innerHTML;
}

const strong = (html) => `<strong>${html}</strong>`;

// Joins names as a list in the page's language. Past three names it reads "A, B and 2 more".
function formatNames(names, type, { bold = false } = {}) {
  const shown = names.length > MAX_LISTED_AUDIENCES ? names.slice(0, MAX_LISTED_AUDIENCES - 1) : names;
  const items = shown.map((name) => (bold ? strong(escapeHtml(name)) : escapeHtml(name)));
  const rest = names.length - shown.length;
  if (rest) {
    items.push(interpolate(ngettext("%(count)s more", "%(count)s more", rest), { count: rest }, true));
  }
  return new Intl.ListFormat(document.documentElement.lang || undefined, { type }).format(items);
}

function sameAudiences(values, saved) {
  return saved !== null && values.length === saved.size && values.every((value) => saved.has(value));
}

// The strings carry no markup: bold parts go in through placeholders, and names are escaped first.
function audienceStatusHtml(state, publicNames, privateNames, isSaved) {
  if (state === "public") {
    return interpolate(
      gettext("%(label)s: everyone can read this article, including signed-out visitors."),
      { label: strong(escapeHtml(gettext("Public"))) },
      true
    );
  }
  if (state === "private") {
    return interpolate(
      gettext(
        "%(label)s: only members of %(names)s, and staff, can read it. It's hidden from search and listings for everyone else."
      ),
      {
        label: strong(escapeHtml(gettext("Restricted"))),
        names: formatNames(privateNames, "disjunction"),
      },
      true
    );
  }
  const heading = isSaved ? gettext("This article is public.") : gettext("This article will be public.");
  const because = interpolate(
    ngettext(
      "Because %(names)s is public, everyone can read it, including signed-out visitors.",
      "Because %(names)s are public, everyone can read it, including signed-out visitors.",
      publicNames.length
    ),
    { names: formatNames(publicNames, "conjunction", { bold: true }) },
    true
  );
  const stays = interpolate(
    ngettext(
      "%(names)s stays assigned but adds no restriction while a public knowledge base is selected.",
      "%(names)s stay assigned but add no restriction while a public knowledge base is selected.",
      privateNames.length
    ),
    { names: formatNames(privateNames, "conjunction", { bold: true }) },
    true
  );
  return `${strong(escapeHtml(heading))} ${because} ${stays}`;
}

function updateAudienceStatus(select, status) {
  const chosen = select.items.map((value) => select.options[value]);
  const publicNames = chosen.filter(isPublicAudience).map((data) => data.text);
  const privateNames = chosen.filter((data) => !isPublicAudience(data)).map((data) => data.text);
  let state = "";
  if (publicNames.length && privateNames.length) {
    state = "mixed";
  } else if (publicNames.length) {
    state = "public";
  } else if (privateNames.length) {
    state = "private";
  }

  status.hidden = !state;
  status.dataset.state = state;
  if (!state) {
    status.replaceChildren();
    return;
  }

  // Only the edit page knows the saved knowledge bases; "is public" means the selection is saved.
  const savedAttr = status.dataset.savedAudiences;
  const saved = savedAttr === undefined ? null : new Set(savedAttr.split(",").filter(Boolean));
  const isSaved = sameAudiences(select.items, saved);

  const icon = document.createElement("span");
  icon.className = "kb-audience-status--icon";
  icon.setAttribute("aria-hidden", "true");
  icon.textContent = AUDIENCE_STATUS_ICONS[state];
  const text = document.createElement("span");
  text.innerHTML = audienceStatusHtml(state, publicNames, privateNames, isSaved);
  status.replaceChildren(icon, text);
}

function clearSelected(name) {
  document.querySelectorAll(
    `#relevant-${name} input[type="checkbox"][name="${name}"]:checked`
  ).forEach(function (checkbox) {
    checkbox.checked = false;
  });
  handleUpdate();
}

// The "DOMContentLoaded" event is guaranteed not to have been
// called by the time the following code is run, because it always
// waits until all deferred scripts have been loaded, and the code
// in this file is always bundled into a script that is deferred.
document.addEventListener("DOMContentLoaded", function () {
  // Enable/disable products and topics based on initial selections.
  handleUpdate();
  document.querySelectorAll(
    '#relevant-topics input[type="checkbox"][name="topics"]'
  ).forEach(function (topic) {
    topic.addEventListener("click", function () {
      handleTopicRelationships(topic);
      handleUpdate();
    });
  });
  document.querySelectorAll(
    '#relevant-products input[type="checkbox"][name="products"]'
  ).forEach(function (product) {
    product.addEventListener("click", function () {
      handleUpdate();
    });
  });
  let clearTopics = document.getElementById("relevant-topics-clear-selected");
  if (clearTopics) {
    clearTopics.addEventListener("click", function (event) {
      event.preventDefault();
      clearSelected("topics");
    });
  }
  let clearProducts = document.getElementById("relevant-products-clear-selected");
  if (clearProducts) {
    clearProducts.addEventListener("click", function (event) {
      event.preventDefault();
      clearSelected("products");
    });
  }

  if (document.getElementById("id_audiences")) {
    const audienceStatus = document.getElementById("kb-audience-status");
    new TomSelect("select[id='id_audiences']", {
      closeAfterSelect: true,
      plugins: {
        remove_button: {
          title: gettext("Remove Item")
        },
      },
      placeholder: gettext("Select audiences"),
      persist: false,
      create: false,
      render: {
        option: (data, escape) => `<div>${escape(data.text)} ${audienceBadge(data)}</div>`,
        item: (data, escape) => `<div>${escape(data.text)} ${audienceBadge(data)}</div>`,
      },
      onInitialize() {
        if (audienceStatus) updateAudienceStatus(this, audienceStatus);
      },
      onChange() {
        if (audienceStatus) updateAudienceStatus(this, audienceStatus);
      },
    });
  }
});
