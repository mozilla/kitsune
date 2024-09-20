document.addEventListener('DOMContentLoaded', () => {
    const { reasonFilter, flaggedQueue, topicDropdown, updateStatusButton } = {
        reasonFilter: document.getElementById('flagit-reason-filter'),
        flaggedQueue: document.getElementById('flagged-queue'),
        topicDropdown: document.getElementById('topic-dropdown'),
        updateStatusButton: document.getElementById('update-status-button'),
    };

    updateStatusButton.disabled = true;
    const reasonDropdown = updateStatusButton.previousElementSibling;

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

    // Handle reason filter change
    reasonFilter.addEventListener('change', async () => {
        const selectedReason = reasonFilter.value;
        const url = new URL(window.location.href);
        url.searchParams.set('reason', selectedReason);

        const response = await fetchData(url);

        if (response) {
            const data = await response.text();
            const parser = new DOMParser();
            const doc = parser.parseFromString(data, 'text/html');
            flaggedQueue.innerHTML = doc.querySelector('#flagged-queue').innerHTML;
        }
    });

    // Handle topic dropdown change
    if (topicDropdown) {
        topicDropdown.addEventListener('change', async function () {
            updateStatusButton.disabled = false;
            const topicId = this.value;
            const questionId = this.getAttribute('data-question-id');
            const csrfToken = document.querySelector('#topic-update-form input[name=csrfmiddlewaretoken]').value;
            const currentTopic = document.getElementById('current-topic');

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
            }
        });
    }
    reasonDropdown.addEventListener('change', () => {
        updateStatusButton.disabled = false;
    })
});