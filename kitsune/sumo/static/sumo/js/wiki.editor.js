import "@selectize/selectize";

(function($) {
  // Improve the interface for restricting articles.
  $(function () {
    $("select[id='id_restrict_to_groups']").selectize({
      closeAfterSelect: true,
      plugins: ["clear_button", "remove_button"],
      placeholder: "Restrict visibility to selected group(s)   ",
    });
  });
})(jQuery);

function updateProduct(topic) {
  // Reflect the topic checkbox change within its product.
  // If we've checked a subtopic, automatically check its topic.
  if (topic.classList.contains("level-2-topic") && topic.checked) {
    document.getElementById(
      `id_${topic.dataset.productId}_${topic.dataset.parentTopicId}`
    ).checked = true;
  } else if (topic.classList.contains("level-1-topic") && !topic.checked) {
    // If we've unchecked a topic, automatically uncheck its subtopics.
    let subtopicCheckboxes = document.querySelectorAll(
      `#id_checkbox_list_${topic.dataset.productId} ` +
      `input[type="checkbox"][data-parent-topic-id="${topic.dataset.topicId}"]`
    );
    subtopicCheckboxes.forEach(function (subtopicCheckbox) {
      subtopicCheckbox.checked = false;
    });
  }
  // Update the product header to reflect the change(s), and
  // return whether or not this topic change has just enabled
  // a previously-disabled product.
  return updateProductHeader(topic.dataset.productId)
}

function updateProductHeader(productId) {
  // Update the product header to reflect the number of topics selected.
  let productHeader = document.getElementById(`id_${productId}`);
  let previouslyEnabled = productHeader.classList.contains("selected");
  let numTopicsChecked = document.querySelectorAll(
    `#id_checkbox_list_${productId} input[type="checkbox"]:checked`
  ).length
  if (numTopicsChecked > 0) {
    productHeader.classList.add("selected");
  } else {
    productHeader.classList.remove("selected");
  }
  let topicDetails = productHeader.querySelector(
    "span.product-heading-topic-details"
  );
  topicDetails.textContent = interpolate(
    ngettext('%s topic selected', '%s topics selected', numTopicsChecked),
    [numTopicsChecked]
  );
  // Return whether or not this topic change has just enabled a
  // previously-disabled product.
  return (!previouslyEnabled && (numTopicsChecked > 0))
}

function updateOtherProducts(topic) {
  // Reflect the topic checkbox change within all other selected products.
  // The same topic within all other selected products should mirror this
  // change.
  let otherSelectedProductHeaders = document.querySelectorAll(
    `#accordion h3.sumo-card-heading.selected:not(#id_${topic.dataset.productId})`
  );
  otherSelectedProductHeaders.forEach(function(otherSelectedProductHeader) {
    let sameTopic = document.getElementById(
      `id_${otherSelectedProductHeader.dataset.productId}_${topic.dataset.topicId}`
    );
    if (sameTopic && (sameTopic.checked !== topic.checked)) {
      sameTopic.checked = topic.checked;
      updateProduct(sameTopic);
    }
  });
}

function updateProductFromOtherProducts(productId) {
  // If a product has just been enabled, make sure its topics reflect
  // all equivalent topics selected in all other products.
  let productHeaderUpdateNeeded = false;
  let otherSelectedProductHeaders = document.querySelectorAll(
    `#accordion h3.sumo-card-heading.selected:not(#id_${productId})`
  );
  otherSelectedProductHeaders.forEach(function(otherSelectedProductHeader) {
    let otherProductId = otherSelectedProductHeader.dataset.productId;
    document.querySelectorAll(
      `#id_checkbox_list_${otherProductId} input[type="checkbox"]:checked`
    ).forEach(function (topic) {
      let sameTopic = document.getElementById(
        `id_${productId}_${topic.dataset.topicId}`
      );
      if (sameTopic && !sameTopic.checked) {
        sameTopic.checked = true;
        productHeaderUpdateNeeded = true;
      }
    });
  });
  if (productHeaderUpdateNeeded) {
    updateProductHeader(productId);
  }
}

// The "DOMContentLoaded" event is guaranteed not to have been
// called by the time the following code is run, because it always
// waits until all deferred scripts have been loaded, and the code
// in this file is always bundled into a script that is deferred.
document.addEventListener("DOMContentLoaded", function() {
  let topicCheckboxes = document.querySelectorAll(
    '#accordion .checkbox-list input[type="checkbox"]'
  );
  topicCheckboxes.forEach(function(topic) {
    topic.addEventListener("click", function() {
      let justEnabled = updateProduct(topic);
      updateOtherProducts(topic);
      if (justEnabled) {
        updateProductFromOtherProducts(topic.dataset.productId);
      }
    });
  });
});
