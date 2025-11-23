/**
 * Floor Management System - Form Validation
 * Client-side form validation with real-time feedback
 */

const FormValidation = {
    validators: {},

    /**
     * Initialize form validation
     */
    init() {
        console.log('Initializing Form Validation...');

        this.registerValidators();
        this.initializeEventHandlers();
    },

    /**
     * Register built-in validators
     */
    registerValidators() {
        this.validators = {
            required: (value) => {
                return value.trim() !== '';
            },

            email: (value) => {
                const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                return emailRegex.test(value);
            },

            minLength: (value, min) => {
                return value.length >= parseInt(min);
            },

            maxLength: (value, max) => {
                return value.length <= parseInt(max);
            },

            pattern: (value, pattern) => {
                const regex = new RegExp(pattern);
                return regex.test(value);
            },

            number: (value) => {
                return !isNaN(parseFloat(value)) && isFinite(value);
            },

            min: (value, min) => {
                return parseFloat(value) >= parseFloat(min);
            },

            max: (value, max) => {
                return parseFloat(value) <= parseFloat(max);
            },

            url: (value) => {
                try {
                    new URL(value);
                    return true;
                } catch {
                    return false;
                }
            },

            date: (value) => {
                const date = new Date(value);
                return date instanceof Date && !isNaN(date);
            },

            match: (value, fieldId) => {
                const matchField = document.getElementById(fieldId);
                return matchField && value === matchField.value;
            }
        };
    },

    /**
     * Initialize event handlers
     */
    initializeEventHandlers() {
        // Validate on form submit
        document.querySelectorAll('form[data-validate="true"]').forEach(form => {
            form.addEventListener('submit', (e) => {
                if (!this.validateForm(form)) {
                    e.preventDefault();
                    FloorMS.notify.error('Please fix the errors in the form');
                }
            });
        });

        // Real-time validation on input
        document.querySelectorAll('[data-validate-field]').forEach(field => {
            field.addEventListener('blur', () => {
                this.validateField(field);
            });

            field.addEventListener('input', FloorMS.utils.debounce(() => {
                if (field.classList.contains('is-invalid')) {
                    this.validateField(field);
                }
            }, 500));
        });
    },

    /**
     * Validate entire form
     */
    validateForm(form) {
        let isValid = true;

        form.querySelectorAll('[data-validate-field]').forEach(field => {
            if (!this.validateField(field)) {
                isValid = false;
            }
        });

        return isValid;
    },

    /**
     * Validate single field
     */
    validateField(field) {
        const rules = field.dataset.validateField.split('|');
        let isValid = true;
        let errorMessage = '';

        for (const rule of rules) {
            const [validatorName, param] = rule.split(':');
            const validator = this.validators[validatorName];

            if (validator) {
                if (!validator(field.value, param)) {
                    isValid = false;
                    errorMessage = this.getErrorMessage(validatorName, field.name, param);
                    break;
                }
            }
        }

        if (isValid) {
            field.classList.remove('is-invalid');
            field.classList.add('is-valid');
            this.removeError(field);
        } else {
            field.classList.remove('is-valid');
            field.classList.add('is-invalid');
            this.showError(field, errorMessage);
        }

        return isValid;
    },

    /**
     * Get error message for validation rule
     */
    getErrorMessage(rule, fieldName, param) {
        const messages = {
            required: `${fieldName} is required`,
            email: 'Please enter a valid email address',
            minLength: `Minimum ${param} characters required`,
            maxLength: `Maximum ${param} characters allowed`,
            number: 'Please enter a valid number',
            min: `Value must be at least ${param}`,
            max: `Value must be at most ${param}`,
            url: 'Please enter a valid URL',
            date: 'Please enter a valid date',
            match: 'Fields do not match'
        };

        return messages[rule] || 'Invalid input';
    },

    /**
     * Show error message
     */
    showError(field, message) {
        this.removeError(field);

        const error = document.createElement('div');
        error.className = 'invalid-feedback';
        error.textContent = message;
        field.parentNode.appendChild(error);
    },

    /**
     * Remove error message
     */
    removeError(field) {
        const error = field.parentNode.querySelector('.invalid-feedback');
        if (error) {
            error.remove();
        }
    }
};

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    FormValidation.init();
});
