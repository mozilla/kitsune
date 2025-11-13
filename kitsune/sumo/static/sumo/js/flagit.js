import TomSelect from 'tom-select';

document.addEventListener('DOMContentLoaded', () => {
    const csrfToken = document.querySelector('input[name=csrfmiddlewaretoken]')?.value;

    // Disable all update buttons initially
    function disableUpdateStatusButtons() {
        document.querySelectorAll('form.update.inline-form input[type="submit"]').forEach(button => {
            button.disabled = true;
        });
    }
    disableUpdateStatusButtons();

    async function fetchData(url, options = {}) {
        try {
            const headers = {
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/json',
                ...options.headers
            };

            if (options.method && options.method !== 'GET' && csrfToken) {
                headers['X-CSRFToken'] = csrfToken;
            }

            const response = await fetch(url, {
                method: options.method || 'GET',
                headers,
                body: options.body ? JSON.stringify(options.body) : null
            });

            if (!response.ok) {
                throw new Error(`Error: ${response.statusText}`);
            }

            const contentType = response.headers.get('Content-Type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            }

            return response;  // Return raw response if not JSON
        } catch (error) {
            console.error('Error in fetchData:', error);
            return null;
        }
    }

    function findUpdateButton(questionId) {
        return document.querySelector(`form.update.inline-form input[id="update-status-button-${questionId}"]`);
    }

    function updateStatusSelect(updateButton) {
        const statusDropdown = updateButton?.previousElementSibling;
        if (statusDropdown && statusDropdown.tagName === 'SELECT') {
            statusDropdown.value = '1';
        }
    }

    function enableUpdateButton(updateButton) {
        if (updateButton) {
            updateButton.disabled = false;
        }
    }

    function initializeDropdownsAndTags() {
        document.querySelectorAll('.topic-dropdown, .tag-select, select[name="status"]').forEach(dropdown => {
            const questionId = dropdown.dataset.questionId;

            dropdown.addEventListener('change', async function () {
                const form = this.closest('form');
                const updateButton = findUpdateButton(questionId);

                enableUpdateButton(updateButton);

                // Update topic
                if (this.classList.contains('topic-dropdown')) {
                    const url = `/en-US/questions/${questionId}/edit`;
                    const response = await fetchData(url, { method: 'POST', body: { topic: this.value } });
                    if (response) {
                        const currentTopic = document.getElementById(`current-topic-${questionId}`);
                        currentTopic.textContent = response.updated_topic;
                        currentTopic.classList.add('updated');
                        updateStatusSelect(updateButton);
                    }
                }

                // Update tags
                if (this.classList.contains('tag-select')) {
                    const selectedTags = Array.from(this.selectedOptions).map(option => option.value);
                    const url = `/en-US/questions/${questionId}/add-tag-async`;
                    const response = await fetchData(url, { method: 'POST', body: { tags: selectedTags } });
                    if (response) {
                        updateStatusSelect(updateButton);
                    }
                }
            });

            if (dropdown.classList.contains('tag-select')) {
                new TomSelect(dropdown, {
                    plugins: ['remove_button'],
                    maxItems: null,
                    maxOptions: null,
                    dropdownParent: 'body',
                    create: false,
                    onItemRemove: async (tagId) => {
                        const url = `/en-US/questions/${questionId}/remove-tag-async`;
                        const response = await fetchData(url, { method: 'POST', body: { tagId } });
                        if (response) {
                            const updateButton = findUpdateButton(questionId);
                            updateStatusSelect(updateButton);
                            enableUpdateButton(updateButton);
                        }
                    }
                });
            }

            if (dropdown.name === 'status') {
                dropdown.addEventListener('change', function () {
                    const form = this.closest('form');
                    const updateButton = form.querySelector('input[type="submit"]');
                    if (this.value) {
                        updateButton.disabled = false;
                    } else {
                        updateButton.disabled = true;
                    }
                });
            }
        });
    }

    const myQueueTools = document.getElementById('my-queue-tools');
    const myQueueUnassign = document.getElementById('my-queue-unassign');
    const flaggedQueue = document.getElementById('flagged-queue');
    initializeFilterDropdown('flagit-reason-filter', 'reason');
    initializeFilterDropdown('flagit-content-type-filter', 'content_type');
    initializeFilterDropdown('flagit-product-filter', 'product');
    initializeFilterDropdown('flagit-assignee-filter', 'assignee', (selectedValue) => {
        myQueueTools.hidden = selectedValue !== myQueueTools.dataset.currentUsername;
    });

    document.body.addEventListener('htmx:beforeRequest', function(evt) {
        if (evt.detail.elt === myQueueUnassign) {
            // We're going to remove all of the user's assigned items,
            // so it doesn't make any sense to keep the page parameter.
            const url = new URL(window.location.href);
            url.searchParams.delete('page');
            window.history.pushState({}, '', url);
        }
    });

    function initializeFilterDropdown(filterId, queryParam, postChangeFunction) {
        const filterElement = document.getElementById(filterId);
        if (!filterElement) return;

        const currentFilter = new URL(window.location.href).searchParams.get(queryParam);
        if (currentFilter) {
            filterElement.value = currentFilter;
        }

        filterElement.addEventListener('change', async () => {
            const selectedValue = filterElement.value;
            const url = new URL(window.location.href);

            // Remove the page parameter since we'll show a new queue of items.
            url.searchParams.delete('page');

            if (selectedValue) {
                url.searchParams.set(queryParam, selectedValue);
            } else {
                url.searchParams.delete(queryParam);
            }
            window.history.pushState({}, '', url);

            const response = await fetchData(url);
            if (response) {
                const parser = new DOMParser();
                const doc = parser.parseFromString(await response.text(), 'text/html');
                flaggedQueue.innerHTML = doc.querySelector('#flagged-queue').innerHTML;
                disableUpdateStatusButtons();
                initializeDropdownsAndTags();
                htmx.process(flaggedQueue);
            }
            if (postChangeFunction) {
                postChangeFunction(selectedValue);
            }
        });
    }

    initializeDropdownsAndTags();
});
