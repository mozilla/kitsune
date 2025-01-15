document.addEventListener('alpine:init', () => {
    Alpine.data('surveyForm', () => ({
        selectedReason: '',
        comment: '',
        maxLength: 600,
        hasError: false,
        responseMessage: null,
        formVisible: true,
        isOtherSelected: false,
        isOtherNotSelected: true,
        remainingChars: 600,
        isSubmitDisabled: true,

        setupForm() {
            // Setup radio buttons
            const radioInputs = this.$root.querySelectorAll('input[type="radio"]');
            const textarea = this.$root.querySelector('textarea[name="comment"]');
            const form = this.$root.querySelector('form');

            // Setup radio buttons
            radioInputs.forEach(radio => {
                radio.checked = radio.value === this.selectedReason;

                radio.addEventListener('change', () => {
                    this.selectedReason = radio.value;
                    this.isOtherSelected = radio.value === 'other';
                    this.isOtherNotSelected = radio.value !== 'other';

                    if (textarea) {
                        textarea.disabled = radio.value !== 'other';
                        textarea.required = radio.value === 'other';
                    }

                    this.updateSubmitDisabled();
                });
            });

            // Setup textarea
            if (textarea) {
                textarea.addEventListener('input', (event) => {
                    this.comment = event.target.value;
                    if (this.comment.length > this.maxLength) {
                        this.comment = this.comment.slice(0, this.maxLength);
                        event.target.value = this.comment;
                    }
                    this.remainingChars = this.maxLength - this.comment.length;
                    this.updateSubmitDisabled();
                });
            }

            // Setup form submission
            if (form) {
                form.addEventListener('submit', (event) => {
                    event.preventDefault();
                    if (this.validateForm()) {
                        trackEvent('article_survey_submitted', {
                            survey_type: this.surveyType,
                            reason: this.selectedReason
                        });
                        // Allow HTMX to handle the submission
                        return true;
                    }
                    return false;
                });
            }
        },

        validateForm() {
            this.hasError = this.isOtherSelected && !this.comment.trim();
            return !this.hasError;
        },

        closeSurvey() {
            if (this.surveyType) {
                trackEvent('article_survey_closed', { survey_type: this.surveyType });
            }
            const survey = document.querySelector('.document-vote');
            if (this.responseMessage) {
                setTimeout(() => {
                    survey.remove();
                }, 5000);
            } else {
                survey.remove();
            }
        },

        cancelSurvey() {
            this.formVisible = false;
            this.responseMessage = "Thanks for voting! Your additional feedback wasn't submitted.";
            this.closeSurvey();
        },

        init() {
            this.surveyType = document.querySelector('.survey-container').dataset.surveyType.trim();
            if (this.surveyType) {
                trackEvent('article_survey_opened', { survey_type: this.surveyType });
            }
            this.responseMessage = document.querySelector('[x-ref="messageData"]').value;
            this.formVisible = !this.responseMessage;
            if (this.responseMessage) {
                this.closeSurvey();
            }

            // Setup form after initialization
            this.$nextTick(() => {
                this.setupForm();
            });
        },

        updateSubmitDisabled() {
            const hasValidReason = !!this.selectedReason;
            const hasValidComment = !this.isOtherSelected || (this.isOtherSelected && this.comment.trim());
            this.isSubmitDisabled = !hasValidReason || !hasValidComment;
        }
    }));
});
