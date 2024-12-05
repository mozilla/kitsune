import TomSelect from 'tom-select';

document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.tag-select').forEach(dropdown => {
    const addUrl = dropdown.dataset.addUrl;
    const removeUrl = dropdown.dataset.removeUrl;
    const csrfToken = document.querySelector('input[name=csrfmiddlewaretoken]')?.value;

    new TomSelect(dropdown, {
      plugins: ['remove_button'],
      maxOptions: null,
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
      },
      render: {
        item: (data, escape) => {
          const url = data.url || '#';
          return `<div>
                    <a href="${escape(url)}" class="tag-name">${escape(data.text)}</a>
                  </div>`;
        },
        option: (data, escape) => {
          return `<div>${escape(data.text)}</div>`;
        }
      },
      onInitialize() {
        Array.from(dropdown.options).forEach(option => {
          if (!this.options[option.value]) {
            this.addOption({
              value: option.value,
              text: option.text,
              url: option.dataset.url || '#'
            });
          }
        });

        const container = this.control; // The container for selected items
        container.addEventListener('click', (event) => {
          if (event.target.tagName === 'A' && event.target.classList.contains('tag-name')) {
            event.stopPropagation(); // Prevent Tom Select from intercepting
            window.location.href = event.target.href;
          }
        });
      }
    });
  });
});