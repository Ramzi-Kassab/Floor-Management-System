/**
 * Floor Management System - Global Application JavaScript
 *
 * Contains global utilities and helpers used throughout the application.
 *
 * Features:
 * - CSRF token management
 * - Bootstrap tooltips initialization
 * - Smooth scrolling for anchor links
 * - Auto-hiding alerts
 * - Global search keyboard shortcuts
 */

// ========== CSRF TOKEN HELPER ==========

/**
 * Get CSRF token from cookies
 * Used for AJAX requests that modify data
 * @param {string} name - Cookie name (usually 'csrftoken')
 * @returns {string|null} CSRF token value
 */
function getCookie(name) {
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

// Make getCookie globally available
window.getCookie = getCookie;

// ========== INITIALIZATION ==========

document.addEventListener('DOMContentLoaded', function() {

    // ========== BOOTSTRAP TOOLTIPS ==========

    /**
     * Initialize Bootstrap tooltips on all elements with data-bs-toggle="tooltip"
     */
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // ========== SMOOTH SCROLLING ==========

    /**
     * Add smooth scrolling behavior to all anchor links
     */
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // ========== AUTO-HIDE ALERTS ==========

    /**
     * Auto-hide Bootstrap alerts after 5 seconds
     * Alerts with .alert-permanent class will not auto-hide
     */
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
        alerts.forEach(function(alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);

    // ========== GLOBAL SEARCH KEYBOARD SHORTCUT ==========

    /**
     * Enable Ctrl+K (or Cmd+K on Mac) to focus global search
     */
    document.addEventListener('keydown', function(e) {
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            const searchInput = document.getElementById('globalSearchInput') ||
                              document.querySelector('.search-input');
            if (searchInput) {
                searchInput.focus();
                searchInput.select();
            }
        }
    });

    // ========== FORM UTILITIES ==========

    /**
     * Add confirmation to all delete forms/buttons
     */
    document.querySelectorAll('[data-confirm]').forEach(element => {
        element.addEventListener('click', function(e) {
            const message = this.dataset.confirm || 'Are you sure you want to proceed?';
            if (!confirm(message)) {
                e.preventDefault();
                return false;
            }
        });
    });

    // ========== TABLE UTILITIES ==========

    /**
     * Make table rows clickable if they have data-href attribute
     */
    document.querySelectorAll('tr[data-href]').forEach(row => {
        row.style.cursor = 'pointer';
        row.addEventListener('click', function(e) {
            // Don't trigger if clicking on a link or button
            if (e.target.tagName !== 'A' && e.target.tagName !== 'BUTTON' &&
                !e.target.closest('a') && !e.target.closest('button')) {
                window.location.href = this.dataset.href;
            }
        });
    });
});

// ========== UTILITY FUNCTIONS ==========

/**
 * Format numbers with thousands separators
 * @param {number} num - Number to format
 * @returns {string} Formatted number
 */
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

/**
 * Debounce function to limit execution rate
 * @param {Function} func - Function to debounce
 * @param {number} wait - Milliseconds to wait
 * @returns {Function} Debounced function
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Show toast notification (if toast system exists)
 * @param {string} message - Message to display
 * @param {string} type - Type of toast (success, error, info, warning)
 */
function showToast(message, type = 'info') {
    // This is a placeholder - implement with your preferred toast library
    console.log(`[${type.toUpperCase()}] ${message}`);
}

// Make utility functions globally available
window.formatNumber = formatNumber;
window.debounce = debounce;
window.showToast = showToast;
