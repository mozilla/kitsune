import TomSelect from "tom-select";

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
  document.getElementById(
    `relevant-${name}-disabled-message`
  ).hidden = (numberDisabled === 0);
}

function updateSelectedMessage(name) {
  let numberSelected = document.querySelectorAll(
    `#relevant-${name} input[type="checkbox"][name="${name}"]:checked`
  ).length;
  if (numberSelected > 0) {
    document.getElementById(
      `relevant-${name}-selected-message`
    ).textContent = interpolate(
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
  document.getElementById(
    "relevant-topics-clear-selected"
  ).addEventListener("click", function (event) {
    event.preventDefault();
    clearSelected("topics");
  });
  document.getElementById(
    "relevant-products-clear-selected"
  ).addEventListener("click", function (event) {
    event.preventDefault();
    clearSelected("products");
  });

  new TomSelect("select[id='id_restrict_to_groups']", {
    closeAfterSelect: true,
    plugins: {
      remove_button: {
        title: "Remove Item"
      },
    },
    placeholder: "Restrict visibility to selected group(s)",
    persist: false,
    create: true,
  });
});
