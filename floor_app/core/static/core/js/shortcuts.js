/**
 * Floor Management System - Keyboard Shortcuts
 * Global keyboard shortcuts for improved productivity
 */

const KeyboardShortcuts = {
    shortcuts: {},
    enabled: true,
    helpModalShown: false,

    /**
     * Initialize keyboard shortcuts
     */
    init() {
        console.log('Initializing Keyboard Shortcuts...');

        this.registerShortcuts();
        this.initializeEventListeners();
        this.loadUserPreferences();
    },

    /**
     * Register all shortcuts
     */
    registerShortcuts() {
        // Global Navigation
        this.register('g d', 'Go to Dashboard', () => {
            window.location.href = '/dashboard/';
        });

        this.register('g s', 'Go to System Monitor', () => {
            window.location.href = '/system/dashboard/';
        });

        this.register('g a', 'Go to Audit Logs', () => {
            window.location.href = '/system/audit-logs/';
        });

        this.register('g e', 'Go to System Events', () => {
            window.location.href = '/system/events/';
        });

        // Actions
        this.register('n', 'Show Notifications', () => {
            const dropdown = document.querySelector('[data-bs-toggle="dropdown"]');
            if (dropdown) {
                dropdown.click();
            }
        });

        this.register('/', 'Focus Search', (e) => {
            e.preventDefault();
            const searchInput = document.querySelector('input[type="search"], input[name="q"]');
            if (searchInput) {
                searchInput.focus();
                searchInput.select();
            }
        });

        this.register('r', 'Refresh Page', () => {
            const refreshBtn = document.getElementById('refreshDashboard');
            if (refreshBtn) {
                refreshBtn.click();
            } else {
                location.reload();
            }
        });

        this.register('t', 'Toggle Theme', () => {
            const currentTheme = ThemeSystem.currentTheme;
            ThemeSystem.applyTheme(currentTheme === 'light' ? 'dark' : 'light');
        });

        this.register('Escape', 'Close Modals', () => {
            const modal = document.querySelector('.modal.show');
            if (modal) {
                const modalInstance = bootstrap.Modal.getInstance(modal);
                if (modalInstance) {
                    modalInstance.hide();
                }
            }
        });

        // Help
        this.register('?', 'Show Keyboard Shortcuts Help', (e) => {
            e.preventDefault();
            this.showHelp();
        });

        // Accessibility
        this.register('Alt+h', 'Toggle High Contrast', () => {
            const toggle = document.getElementById('high_contrast');
            if (toggle) {
                toggle.checked = !toggle.checked;
                toggle.dispatchEvent(new Event('change'));
            }
        });

        this.register('Alt+m', 'Toggle Reduce Motion', () => {
            const toggle = document.getElementById('reduce_motion');
            if (toggle) {
                toggle.checked = !toggle.checked;
                toggle.dispatchEvent(new Event('change'));
            }
        });
    },

    /**
     * Register a keyboard shortcut
     */
    register(keys, description, callback) {
        this.shortcuts[keys] = {
            description,
            callback
        };
    },

    /**
     * Initialize event listeners
     */
    initializeEventListeners() {
        let sequence = [];
        let timer;

        document.addEventListener('keydown', (e) => {
            if (!this.enabled) return;

            // Don't trigger if user is typing in an input
            if (this.isTyping(e.target)) return;

            // Build key combination
            const key = this.getKeyCombo(e);

            // Check for sequence shortcuts
            sequence.push(key.toLowerCase());

            // Clear sequence after 1 second
            clearTimeout(timer);
            timer = setTimeout(() => {
                sequence = [];
            }, 1000);

            // Check if the current sequence matches any shortcut
            const sequenceStr = sequence.join(' ');

            Object.keys(this.shortcuts).forEach(shortcut => {
                if (sequenceStr.endsWith(shortcut.toLowerCase())) {
                    const handler = this.shortcuts[shortcut];
                    if (handler && handler.callback) {
                        handler.callback(e);
                        sequence = [];
                    }
                }
            });
        });
    },

    /**
     * Get key combination from event
     */
    getKeyCombo(e) {
        const parts = [];

        if (e.ctrlKey) parts.push('Ctrl');
        if (e.altKey) parts.push('Alt');
        if (e.shiftKey) parts.push('Shift');
        if (e.metaKey) parts.push('Meta');

        const key = e.key === ' ' ? 'Space' : e.key;
        if (!['Control', 'Alt', 'Shift', 'Meta'].includes(key)) {
            parts.push(key);
        }

        return parts.join('+');
    },

    /**
     * Check if user is typing in an input
     */
    isTyping(element) {
        const tagName = element.tagName.toLowerCase();
        return tagName === 'input' ||
               tagName === 'textarea' ||
               tagName === 'select' ||
               element.isContentEditable;
    },

    /**
     * Show keyboard shortcuts help modal
     */
    showHelp() {
        if (this.helpModalShown) return;

        const modalHtml = `
            <div class="modal fade" id="shortcutsHelpModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">
                                <i class="bi bi-keyboard me-2"></i>Keyboard Shortcuts
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="row">
                                ${this.getShortcutsHtml()}
                            </div>
                        </div>
                        <div class="modal-footer">
                            <label class="form-check me-auto">
                                <input type="checkbox" class="form-check-input" id="enableShortcuts" ${this.enabled ? 'checked' : ''}>
                                <span class="form-check-label">Enable keyboard shortcuts</span>
                            </label>
                            <button type="button" class="btn btn-primary" data-bs-dismiss="modal">Got it!</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHtml);
        const modalElement = document.getElementById('shortcutsHelpModal');
        const modal = new bootstrap.Modal(modalElement);

        // Enable/disable shortcuts toggle
        document.getElementById('enableShortcuts').addEventListener('change', (e) => {
            this.enabled = e.target.checked;
            localStorage.setItem('shortcutsEnabled', e.target.checked);
        });

        modalElement.addEventListener('hidden.bs.modal', () => {
            modalElement.remove();
            this.helpModalShown = false;
        });

        this.helpModalShown = true;
        modal.show();
    },

    /**
     * Get shortcuts HTML for help modal
     */
    getShortcutsHtml() {
        const categories = {
            'Navigation': ['g d', 'g s', 'g a', 'g e'],
            'Actions': ['n', '/', 'r', 't', 'Escape'],
            'Accessibility': ['Alt+h', 'Alt+m'],
            'Help': ['?']
        };

        return Object.entries(categories).map(([category, shortcuts]) => {
            const items = shortcuts.map(key => {
                const shortcut = this.shortcuts[key];
                if (!shortcut) return '';

                return `
                    <tr>
                        <td>
                            <kbd class="px-2 py-1">${key}</kbd>
                        </td>
                        <td>${shortcut.description}</td>
                    </tr>
                `;
            }).join('');

            return `
                <div class="col-md-6 mb-4">
                    <h6 class="text-primary mb-3">${category}</h6>
                    <table class="table table-sm table-borderless">
                        <tbody>${items}</tbody>
                    </table>
                </div>
            `;
        }).join('');
    },

    /**
     * Load user preferences
     */
    loadUserPreferences() {
        const enabled = localStorage.getItem('shortcutsEnabled');
        if (enabled !== null) {
            this.enabled = enabled === 'true';
        }
    },

    /**
     * Enable shortcuts
     */
    enable() {
        this.enabled = true;
        localStorage.setItem('shortcutsEnabled', 'true');
        FloorMS.notify.success('Keyboard shortcuts enabled');
    },

    /**
     * Disable shortcuts
     */
    disable() {
        this.enabled = false;
        localStorage.setItem('shortcutsEnabled', 'false');
        FloorMS.notify.info('Keyboard shortcuts disabled');
    }
};

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    KeyboardShortcuts.init();
});

// Add CSS for kbd elements
const style = document.createElement('style');
style.textContent = `
    kbd {
        background-color: #f7f7f7;
        border: 1px solid #ccc;
        border-radius: 3px;
        box-shadow: 0 1px 0 rgba(0,0,0,0.2), inset 0 0 0 2px #fff;
        color: #333;
        display: inline-block;
        font-family: 'Courier New', Courier, monospace;
        font-size: 11px;
        line-height: 1.4;
        margin: 0 2px;
        padding: 2px 6px;
        white-space: nowrap;
    }

    [data-theme="dark"] kbd {
        background-color: #2d2d2d;
        border-color: #555;
        color: #fff;
        box-shadow: 0 1px 0 rgba(0,0,0,0.4), inset 0 0 0 2px #444;
    }
`;
document.head.appendChild(style);
