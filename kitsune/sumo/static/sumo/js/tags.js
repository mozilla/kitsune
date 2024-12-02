import TomSelect from 'tom-select';

document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.tag-select').forEach(dropdown => {
    const addUrl = dropdown.dataset.addUrl;
    const removeUrl = dropdown.dataset.removeUrl;
    const csrfToken = document.querySelector('input[name=csrfmiddlewaretoken]')?.value;

    new TomSelect(dropdown, {
      plugins: ['remove_button'],
      maxItems: null,
      create: false,
      onItemAdd: async (tagId) => {
        await fetch(addUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
          },
          body: JSON.stringify({ tags: [tagId] })
        });
      },
      onItemRemove: async (tagId) => {
        await fetch(removeUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
          },
          body: JSON.stringify({ tagId })
        });
      }
    });
  });
});
