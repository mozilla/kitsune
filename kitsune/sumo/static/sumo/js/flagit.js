document.addEventListener('DOMContentLoaded', () => {
    const { reasonFilter, flaggedQueue, topicDropdown, updateStatusButton } = {
        reasonFilter: document.getElementById('flagit-reason-filter'),
        flaggedQueue: document.getElementById('flagged-queue'),
    };


    function disableUpdateStatusButtons() {
        const updateStatusButtons = document.querySelectorAll('form.update.inline-form input[type="submit"]');
        updateStatusButtons.forEach(button => {
            button.disabled = true;
        })
    }
    disableUpdateStatusButtons();

    function updateUrlParameter(action, param, value) {
        const url = new URL(window.location.href);

        if (action === 'set') {
            if (value) {
                url.searchParams.set(param, value);
                window.history.pushState({}, '', url);
            } else {
                url.searchParams.delete(param);
                window.history.replaceState({}, '', url.pathname);
            }
        }
        else if (action === 'get') {
            return url.searchParams.get(param);
        }
    }

    async function fetchData(url, options = {}) {
        try {
            const response = await fetch(url, {
                method: options.method || 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    ...options.headers
                },
                body: options.body || null
            });
            if (!response.ok) {
                throw new Error(`Error: ${response.statusText}`);
            }
            return response;
        } catch (error) {
            console.error('Error:', error);
            return null;
        }
    }

    const reason = updateUrlParameter('get', 'reason');
    if (reason) {
        reasonFilter.value = reason;
    }
    reasonFilter.addEventListener('change', async () => {
        const selectedReason = reasonFilter.value;
        updateUrlParameter('set', 'reason', selectedReason);

        const url = new URL(window.location.href);
        const response = await fetchData(url);

        if (response) {
            const data = await response.text();
            const parser = new DOMParser();
            const doc = parser.parseFromString(data, 'text/html');
            flaggedQueue.innerHTML = doc.querySelector('#flagged-queue').innerHTML;
            disableUpdateStatusButtons();
            handleDropdownChange();
        }
    });

    function handleDropdownChange() {
        const dropdowns = document.querySelectorAll('.topic-dropdown, select[name="status"]');
        dropdowns.forEach(dropdown => {
            dropdown.addEventListener('change', async function () {
                const form = this.closest('form');
                const questionId = this.getAttribute('data-question-id');
                const updateButton = document.getElementById(`update-status-button-${questionId}`) || form.querySelector('input[type="submit"]');

                if (!this.value || this.value === "") {
                    updateButton.disabled = true;
                    return;
                }
                updateButton.disabled = false;

                if (this.classList.contains('topic-dropdown')) {
                    const topicId = this.value;
                    const csrfToken = form.querySelector('input[name=csrfmiddlewaretoken]').value;
                    const currentTopic = document.getElementById(`current-topic-${questionId}`);

                    const response = await fetchData(`/en-US/questions/${questionId}/edit`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': csrfToken
                        },
                        body: JSON.stringify({ 'topic': topicId })
                    });

                    if (response) {
                        const data = await response.json();
                        currentTopic.textContent = data.updated_topic;
                        currentTopic.classList.add('updated');
                        const updateStatusSelect = updateButton.previousElementSibling;
                        if (updateStatusSelect && updateStatusSelect.tagName === 'SELECT') {
                            updateStatusSelect.value = '1';
                        }
                    }
                }
            });
        })
    }
    handleDropdownChange();
});
