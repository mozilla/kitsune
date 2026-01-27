import Marky from "sumo/js/markup";
import "sumo/js/libs/jquery.lazyload";

/*
 * JS for Groups app
 */

(function($) {

  'use strict';

  function init() {
    // Marky for information edit:
    var buttons = Marky.allButtons();
    Marky.createCustomToolbar('.editor-tools', '#id_information', buttons);

    initGroupsTree();

    // Initialize lazy loading for images in group information
    $("img.lazy").lazyload();
  }

  function initGroupsTree() {
    const tree = document.querySelector('.group-tree');
    if (!tree) return;

    const toggles = tree.querySelectorAll('.group-tree--toggle');

    toggles.forEach(toggle => {
      toggle.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();

        const nodeId = this.getAttribute('data-node-id');
        const isExpanded = this.classList.contains('expanded');

        if (isExpanded) {
          collapseNode(nodeId);
          this.classList.remove('expanded');
          this.textContent = '▶';
        } else {
          expandNode(nodeId);
          this.classList.add('expanded');
          this.textContent = '▼';
        }
      });
    });

    function expandNode(nodeId) {
      const children = tree.querySelectorAll(`[data-parent-id="${nodeId}"]`);
      children.forEach(child => {
        child.classList.remove('hidden');
      });
    }

    function collapseNode(nodeId) {
      const children = tree.querySelectorAll(`[data-parent-id="${nodeId}"]`);
      children.forEach(child => {
        child.classList.add('hidden');

        const childNodeId = child.getAttribute('data-node-id');
        const childToggle = child.querySelector('.group-tree--toggle');
        if (childToggle && childToggle.classList.contains('expanded')) {
          collapseNode(childNodeId);
          childToggle.classList.remove('expanded');
        }
      });
    }

    const allItems = tree.querySelectorAll('.group-tree--item[data-parent-id]');
    allItems.forEach(item => {
      item.classList.add('hidden');
    });
  }

  $(init);

})(jQuery);
