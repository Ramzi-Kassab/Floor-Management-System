/**
 * Floor Management System - Core JavaScript Utilities
 * Version: 1.0.0
 *
 * Provides common utilities, AJAX helpers, and base functionality
 */

const FloorMS = {
    // Configuration
    config: {
        ajaxTimeout: 30000,
        notificationDuration: 5000,
        chartColors: {
            primary: '#007bff',
            success: '#28a745',
            warning: '#ffc107',
            danger: '#dc3545',
            info: '#17a2b8',
            secondary: '#6c757d'
        }
    },

    /**
     * AJAX Request Helper
     */
    ajax: {
        /**
         * Make an AJAX request
         * @param {string} url - The URL to request
         * @param {object} options - Request options
         * @returns {Promise}
         */
        request(url, options = {}) {
            const defaults = {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                credentials: 'same-origin'
            };

            // Add CSRF token for non-GET requests
            if (options.method && options.method !== 'GET') {
                defaults.headers['X-CSRFToken'] = this.getCsrfToken();
            }

            const config = { ...defaults, ...options };

            return fetch(url, config)
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                    }
                    return response.json();
                })
                .catch(error => {
                    console.error('AJAX Error:', error);
                    FloorMS.notify.error('Request failed: ' + error.message);
                    throw error;
                });
        },

        /**
         * GET request
         */
        get(url, params = {}) {
            const queryString = new URLSearchParams(params).toString();
            const fullUrl = queryString ? `${url}?${queryString}` : url;
            return this.request(fullUrl);
        },

        /**
         * POST request
         */
        post(url, data = {}) {
            return this.request(url, {
                method: 'POST',
                body: JSON.stringify(data)
            });
        },

        /**
         * PUT request
         */
        put(url, data = {}) {
            return this.request(url, {
                method: 'PUT',
                body: JSON.stringify(data)
            });
        },

        /**
         * DELETE request
         */
        delete(url) {
            return this.request(url, { method: 'DELETE' });
        },

        /**
         * Get CSRF token from cookie
         */
        getCsrfToken() {
            const name = 'csrftoken';
            let cookieValue = null;
            if (document.cookie && document.cookie !== '') {
                const cookies = document.cookie.split(';');
                for (let i = 0; i < cookies.length; i++) {
                    const cookie = cookies[i].trim();
                    if (cookie.substring(0, name.length + 1) === (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }
            return cookieValue;
        }
    },

    /**
     * Toast Notification System
     */
    notify: {
        container: null,

        /**
         * Initialize notification container
         */
        init() {
            if (!this.container) {
                this.container = document.createElement('div');
                this.container.id = 'toast-container';
                this.container.className = 'position-fixed top-0 end-0 p-3';
                this.container.style.zIndex = '9999';
                document.body.appendChild(this.container);
            }
        },

        /**
         * Show a toast notification
         */
        show(message, type = 'info', duration = 5000) {
            this.init();

            const toast = document.createElement('div');
            toast.className = `toast align-items-center text-white bg-${type} border-0`;
            toast.setAttribute('role', 'alert');
            toast.setAttribute('aria-live', 'assertive');
            toast.setAttribute('aria-atomic', 'true');

            const iconMap = {
                'success': 'bi-check-circle-fill',
                'danger': 'bi-exclamation-circle-fill',
                'warning': 'bi-exclamation-triangle-fill',
                'info': 'bi-info-circle-fill'
            };

            toast.innerHTML = `
                <div class="d-flex">
                    <div class="toast-body">
                        <i class="bi ${iconMap[type] || 'bi-info-circle-fill'} me-2"></i>
                        ${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto"
                            data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
            `;

            this.container.appendChild(toast);

            const bsToast = new bootstrap.Toast(toast, { delay: duration });
            bsToast.show();

            // Remove from DOM after hidden
            toast.addEventListener('hidden.bs.toast', () => {
                toast.remove();
            });
        },

        success(message, duration) {
            this.show(message, 'success', duration);
        },

        error(message, duration) {
            this.show(message, 'danger', duration);
        },

        warning(message, duration) {
            this.show(message, 'warning', duration);
        },

        info(message, duration) {
            this.show(message, 'info', duration);
        }
    },

    /**
     * Loading Spinner Helper
     */
    loading: {
        /**
         * Show loading spinner on element
         */
        show(element, text = 'Loading...') {
            const spinner = document.createElement('div');
            spinner.className = 'floor-loading';
            spinner.innerHTML = `
                <div class="text-center">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">${text}</span>
                    </div>
                    <div class="mt-2">${text}</div>
                </div>
            `;

            element.style.position = 'relative';
            element.style.opacity = '0.5';
            element.appendChild(spinner);
        },

        /**
         * Hide loading spinner
         */
        hide(element) {
            element.style.opacity = '1';
            const spinner = element.querySelector('.floor-loading');
            if (spinner) {
                spinner.remove();
            }
        },

        /**
         * Show button loading state
         */
        button(button, loading = true) {
            if (loading) {
                button.dataset.originalText = button.innerHTML;
                button.disabled = true;
                button.innerHTML = `
                    <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                    Loading...
                `;
            } else {
                button.disabled = false;
                button.innerHTML = button.dataset.originalText || button.innerHTML;
            }
        }
    },

    /**
     * Modal Helper
     */
    modal: {
        /**
         * Show confirmation modal
         */
        confirm(title, message, onConfirm, onCancel = null) {
            const modalId = 'confirmModal-' + Date.now();
            const modalHtml = `
                <div class="modal fade" id="${modalId}" tabindex="-1">
                    <div class="modal-dialog">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title">${title}</h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                            </div>
                            <div class="modal-body">${message}</div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                                <button type="button" class="btn btn-primary" id="${modalId}-confirm">Confirm</button>
                            </div>
                        </div>
                    </div>
                </div>
            `;

            document.body.insertAdjacentHTML('beforeend', modalHtml);
            const modalElement = document.getElementById(modalId);
            const modal = new bootstrap.Modal(modalElement);

            document.getElementById(`${modalId}-confirm`).addEventListener('click', () => {
                modal.hide();
                if (onConfirm) onConfirm();
            });

            modalElement.addEventListener('hidden.bs.modal', () => {
                modalElement.remove();
                if (onCancel) onCancel();
            });

            modal.show();
        },

        /**
         * Show alert modal
         */
        alert(title, message, type = 'info') {
            const modalId = 'alertModal-' + Date.now();
            const iconMap = {
                'success': 'bi-check-circle text-success',
                'danger': 'bi-x-circle text-danger',
                'warning': 'bi-exclamation-triangle text-warning',
                'info': 'bi-info-circle text-info'
            };

            const modalHtml = `
                <div class="modal fade" id="${modalId}" tabindex="-1">
                    <div class="modal-dialog">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title">
                                    <i class="bi ${iconMap[type]} me-2"></i>${title}
                                </h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                            </div>
                            <div class="modal-body">${message}</div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-primary" data-bs-dismiss="modal">OK</button>
                            </div>
                        </div>
                    </div>
                </div>
            `;

            document.body.insertAdjacentHTML('beforeend', modalHtml);
            const modalElement = document.getElementById(modalId);
            const modal = new bootstrap.Modal(modalElement);

            modalElement.addEventListener('hidden.bs.modal', () => {
                modalElement.remove();
            });

            modal.show();
        }
    },

    /**
     * Form Utilities
     */
    form: {
        /**
         * Serialize form data to object
         */
        serialize(form) {
            const formData = new FormData(form);
            const object = {};
            formData.forEach((value, key) => {
                if (object[key]) {
                    if (!Array.isArray(object[key])) {
                        object[key] = [object[key]];
                    }
                    object[key].push(value);
                } else {
                    object[key] = value;
                }
            });
            return object;
        },

        /**
         * Submit form via AJAX
         */
        submitAjax(form, onSuccess, onError) {
            const url = form.action;
            const method = form.method.toUpperCase();
            const data = this.serialize(form);

            FloorMS.loading.button(form.querySelector('[type="submit"]'), true);

            FloorMS.ajax.request(url, {
                method: method,
                body: JSON.stringify(data)
            })
            .then(response => {
                if (onSuccess) onSuccess(response);
                FloorMS.notify.success('Form submitted successfully');
            })
            .catch(error => {
                if (onError) onError(error);
                FloorMS.notify.error('Form submission failed');
            })
            .finally(() => {
                FloorMS.loading.button(form.querySelector('[type="submit"]'), false);
            });
        },

        /**
         * Validate form
         */
        validate(form) {
            let isValid = true;
            const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');

            inputs.forEach(input => {
                if (!input.value.trim()) {
                    isValid = false;
                    input.classList.add('is-invalid');
                    this.showError(input, 'This field is required');
                } else {
                    input.classList.remove('is-invalid');
                    this.hideError(input);
                }
            });

            return isValid;
        },

        /**
         * Show field error
         */
        showError(input, message) {
            this.hideError(input);
            const error = document.createElement('div');
            error.className = 'invalid-feedback';
            error.textContent = message;
            input.parentNode.appendChild(error);
        },

        /**
         * Hide field error
         */
        hideError(input) {
            const error = input.parentNode.querySelector('.invalid-feedback');
            if (error) error.remove();
        }
    },

    /**
     * Utility Functions
     */
    utils: {
        /**
         * Debounce function
         */
        debounce(func, wait = 300) {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    clearTimeout(timeout);
                    func(...args);
                };
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
            };
        },

        /**
         * Throttle function
         */
        throttle(func, limit = 300) {
            let inThrottle;
            return function(...args) {
                if (!inThrottle) {
                    func.apply(this, args);
                    inThrottle = true;
                    setTimeout(() => inThrottle = false, limit);
                }
            };
        },

        /**
         * Format number
         */
        formatNumber(num) {
            return new Intl.NumberFormat().format(num);
        },

        /**
         * Format date
         */
        formatDate(date, options = {}) {
            const defaults = {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            };
            return new Intl.DateTimeFormat('en-US', { ...defaults, ...options }).format(new Date(date));
        },

        /**
         * Copy to clipboard
         */
        copyToClipboard(text) {
            navigator.clipboard.writeText(text).then(() => {
                FloorMS.notify.success('Copied to clipboard');
            }).catch(() => {
                FloorMS.notify.error('Failed to copy');
            });
        }
    }
};

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    console.log('Floor Management System - Core JS Loaded');

    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(el => new bootstrap.Tooltip(el));

    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(el => new bootstrap.Popover(el));
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = FloorMS;
}
