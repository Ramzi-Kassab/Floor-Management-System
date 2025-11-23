/**
 * Floor Management System - Theme System
 * Live theme preview and customization
 */

const ThemeSystem = {
    config: {
        themes: {
            light: {
                bgPrimary: '#ffffff',
                bgSecondary: '#f8f9fa',
                textPrimary: '#212529',
                textSecondary: '#6c757d'
            },
            dark: {
                bgPrimary: '#212529',
                bgSecondary: '#343a40',
                textPrimary: '#f8f9fa',
                textSecondary: '#adb5bd'
            }
        },
        colorSchemes: {
            blue: {
                primary: '#007bff',
                secondary: '#0056b3'
            },
            green: {
                primary: '#28a745',
                secondary: '#1e7e34'
            },
            purple: {
                primary: '#6f42c1',
                secondary: '#5a32a3'
            },
            orange: {
                primary: '#fd7e14',
                secondary: '#dc6502'
            },
            red: {
                primary: '#dc3545',
                secondary: '#bd2130'
            },
            teal: {
                primary: '#20c997',
                secondary: '#17a673'
            }
        },
        fontSizes: {
            small: '14px',
            medium: '16px',
            large: '18px',
            'extra-large': '20px'
        }
    },

    currentTheme: 'light',
    currentColorScheme: 'blue',
    currentFontSize: 'medium',

    /**
     * Initialize theme system
     */
    init() {
        console.log('Initializing Theme System...');

        this.loadSavedTheme();
        this.initializeEventHandlers();
        this.setupLivePreview();
        this.detectSystemTheme();
    },

    /**
     * Load saved theme from localStorage or server
     */
    loadSavedTheme() {
        const savedTheme = localStorage.getItem('theme') || this.currentTheme;
        const savedScheme = localStorage.getItem('colorScheme') || this.currentColorScheme;
        const savedFontSize = localStorage.getItem('fontSize') || this.currentFontSize;

        this.applyTheme(savedTheme);
        this.applyColorScheme(savedScheme);
        this.applyFontSize(savedFontSize);
    },

    /**
     * Apply theme (light/dark)
     */
    applyTheme(theme) {
        this.currentTheme = theme;
        document.documentElement.setAttribute('data-theme', theme);

        const colors = this.config.themes[theme];
        if (colors) {
            Object.entries(colors).forEach(([key, value]) => {
                document.documentElement.style.setProperty(`--${key}`, value);
            });
        }

        // Update Bootstrap theme
        if (theme === 'dark') {
            document.body.classList.add('dark-mode');
        } else {
            document.body.classList.remove('dark-mode');
        }

        localStorage.setItem('theme', theme);
    },

    /**
     * Apply color scheme
     */
    applyColorScheme(scheme) {
        this.currentColorScheme = scheme;
        document.documentElement.setAttribute('data-color-scheme', scheme);

        const colors = this.config.colorSchemes[scheme];
        if (colors) {
            document.documentElement.style.setProperty('--color-primary', colors.primary);
            document.documentElement.style.setProperty('--color-secondary', colors.secondary);

            // Update Bootstrap primary color
            document.documentElement.style.setProperty('--bs-primary', colors.primary);
            document.documentElement.style.setProperty('--bs-primary-rgb', this.hexToRgb(colors.primary));
        }

        localStorage.setItem('colorScheme', scheme);
    },

    /**
     * Apply font size
     */
    applyFontSize(size) {
        this.currentFontSize = size;
        document.documentElement.setAttribute('data-font-size', size);

        const fontSize = this.config.fontSizes[size];
        if (fontSize) {
            document.documentElement.style.setProperty('--font-size-base', fontSize);
        }

        localStorage.setItem('fontSize', size);
    },

    /**
     * Apply high contrast mode
     */
    applyHighContrast(enabled) {
        if (enabled) {
            document.body.classList.add('high-contrast');
            document.documentElement.style.setProperty('--contrast-ratio', '7:1');
        } else {
            document.body.classList.remove('high-contrast');
            document.documentElement.style.setProperty('--contrast-ratio', '4.5:1');
        }

        localStorage.setItem('highContrast', enabled);
    },

    /**
     * Apply reduce motion
     */
    applyReduceMotion(enabled) {
        if (enabled) {
            document.body.classList.add('reduce-motion');
            document.documentElement.style.setProperty('--transition-speed', '0ms');
        } else {
            document.body.classList.remove('reduce-motion');
            document.documentElement.style.setProperty('--transition-speed', '200ms');
        }

        localStorage.setItem('reduceMotion', enabled);
    },

    /**
     * Apply dyslexia-friendly font
     */
    applyDyslexiaFont(enabled) {
        if (enabled) {
            document.body.classList.add('dyslexia-friendly');
            document.documentElement.style.setProperty('--font-family', 'OpenDyslexic, Arial, sans-serif');
        } else {
            document.body.classList.remove('dyslexia-friendly');
            document.documentElement.style.setProperty('--font-family', '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif');
        }

        localStorage.setItem('dyslexiaFont', enabled);
    },

    /**
     * Setup live preview
     */
    setupLivePreview() {
        // Theme radio buttons
        document.querySelectorAll('input[name="theme"]').forEach(input => {
            input.addEventListener('change', (e) => {
                this.applyTheme(e.target.value);
                this.showPreviewMessage('Theme updated');
            });
        });

        // Color scheme radio buttons
        document.querySelectorAll('input[name="color_scheme"]').forEach(input => {
            input.addEventListener('change', (e) => {
                this.applyColorScheme(e.target.value);
                this.showPreviewMessage('Color scheme updated');
            });
        });

        // Font size select
        const fontSizeSelect = document.getElementById('font_size');
        if (fontSizeSelect) {
            fontSizeSelect.addEventListener('change', (e) => {
                this.applyFontSize(e.target.value);
                this.showPreviewMessage('Font size updated');
            });
        }

        // Accessibility toggles
        this.setupToggle('high_contrast', (enabled) => {
            this.applyHighContrast(enabled);
            this.showPreviewMessage('High contrast ' + (enabled ? 'enabled' : 'disabled'));
        });

        this.setupToggle('reduce_motion', (enabled) => {
            this.applyReduceMotion(enabled);
            this.showPreviewMessage('Reduce motion ' + (enabled ? 'enabled' : 'disabled'));
        });

        this.setupToggle('dyslexia_friendly', (enabled) => {
            this.applyDyslexiaFont(enabled);
            this.showPreviewMessage('Dyslexia-friendly font ' + (enabled ? 'enabled' : 'disabled'));
        });
    },

    /**
     * Setup toggle event
     */
    setupToggle(id, callback) {
        const toggle = document.getElementById(id);
        if (toggle) {
            toggle.addEventListener('change', (e) => {
                callback(e.target.checked);
            });

            // Load saved state
            const saved = localStorage.getItem(id);
            if (saved !== null) {
                toggle.checked = saved === 'true';
                callback(toggle.checked);
            }
        }
    },

    /**
     * Show preview message
     */
    showPreviewMessage(message) {
        const preview = document.getElementById('themePreview');
        if (preview) {
            const alert = preview.querySelector('.alert');
            if (alert) {
                // Flash animation
                alert.classList.add('flash-animation');
                setTimeout(() => alert.classList.remove('flash-animation'), 500);
            }
        }

        // Show toast for immediate feedback
        FloorMS.notify.info(message, 2000);
    },

    /**
     * Detect and apply system theme
     */
    detectSystemTheme() {
        if (window.matchMedia) {
            const darkModeQuery = window.matchMedia('(prefers-color-scheme: dark)');

            // Check if auto mode is selected
            const autoThemeRadio = document.querySelector('input[name="theme"][value="auto"]');
            if (autoThemeRadio && autoThemeRadio.checked) {
                this.applyTheme(darkModeQuery.matches ? 'dark' : 'light');

                // Listen for system theme changes
                darkModeQuery.addEventListener('change', (e) => {
                    if (autoThemeRadio.checked) {
                        this.applyTheme(e.matches ? 'dark' : 'light');
                    }
                });
            }
        }
    },

    /**
     * Initialize event handlers
     */
    initializeEventHandlers() {
        // Theme settings form submit
        const themeForm = document.querySelector('form[action*="theme-settings"]');
        if (themeForm) {
            themeForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.saveThemeToServer(new FormData(themeForm));
            });
        }

        // Reset button
        const resetBtn = themeForm?.querySelector('[type="reset"]');
        if (resetBtn) {
            resetBtn.addEventListener('click', () => {
                setTimeout(() => {
                    this.loadSavedTheme();
                    FloorMS.notify.info('Theme reset to saved values');
                }, 100);
            });
        }

        // Quick theme switcher in navbar
        const themeSwitcher = document.getElementById('quickThemeSwitcher');
        if (themeSwitcher) {
            themeSwitcher.addEventListener('click', () => {
                const newTheme = this.currentTheme === 'light' ? 'dark' : 'light';
                this.applyTheme(newTheme);
                this.showPreviewMessage(`Switched to ${newTheme} mode`);
            });
        }
    },

    /**
     * Save theme to server
     */
    saveThemeToServer(formData) {
        const submitBtn = document.querySelector('form[action*="theme-settings"] [type="submit"]');
        FloorMS.loading.button(submitBtn, true);

        fetch('/system/theme-settings/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': FloorMS.ajax.getCsrfToken()
            }
        })
        .then(response => {
            if (response.ok) {
                FloorMS.notify.success('Theme settings saved successfully');
            } else {
                throw new Error('Failed to save settings');
            }
        })
        .catch(error => {
            FloorMS.notify.error('Failed to save theme settings');
            console.error(error);
        })
        .finally(() => {
            FloorMS.loading.button(submitBtn, false);
        });
    },

    /**
     * Convert hex color to RGB
     */
    hexToRgb(hex) {
        const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
        return result
            ? `${parseInt(result[1], 16)}, ${parseInt(result[2], 16)}, ${parseInt(result[3], 16)}`
            : '0, 0, 0';
    },

    /**
     * Export theme configuration
     */
    exportTheme() {
        const config = {
            theme: this.currentTheme,
            colorScheme: this.currentColorScheme,
            fontSize: this.currentFontSize,
            highContrast: localStorage.getItem('highContrast') === 'true',
            reduceMotion: localStorage.getItem('reduceMotion') === 'true',
            dyslexiaFont: localStorage.getItem('dyslexiaFont') === 'true'
        };

        const blob = new Blob([JSON.stringify(config, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'theme-config.json';
        a.click();
        URL.revokeObjectURL(url);

        FloorMS.notify.success('Theme configuration exported');
    },

    /**
     * Import theme configuration
     */
    importTheme(file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            try {
                const config = JSON.parse(e.target.result);
                this.applyTheme(config.theme);
                this.applyColorScheme(config.colorScheme);
                this.applyFontSize(config.fontSize);
                this.applyHighContrast(config.highContrast);
                this.applyReduceMotion(config.reduceMotion);
                this.applyDyslexiaFont(config.dyslexiaFont);

                FloorMS.notify.success('Theme configuration imported');
            } catch (error) {
                FloorMS.notify.error('Invalid theme configuration file');
                console.error(error);
            }
        };
        reader.readAsText(file);
    }
};

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    ThemeSystem.init();
});

// Add CSS for animations
const style = document.createElement('style');
style.textContent = `
    .flash-animation {
        animation: flash 0.5s ease-in-out;
    }

    @keyframes flash {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }

    .badge-pulse {
        animation: pulse 2s infinite;
    }

    @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.1); }
    }

    .dark-mode {
        background-color: #212529;
        color: #f8f9fa;
    }

    .high-contrast {
        filter: contrast(1.2);
    }

    .reduce-motion * {
        transition: none !important;
        animation: none !important;
    }

    .dyslexia-friendly {
        letter-spacing: 0.05em;
        word-spacing: 0.1em;
        line-height: 1.8;
    }
`;
document.head.appendChild(style);
