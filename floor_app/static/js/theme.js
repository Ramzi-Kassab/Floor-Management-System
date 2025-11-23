/**
 * Floor Management System - Enhanced Theme System
 *
 * Complete theme customization system with:
 * - Light/Dark/Auto themes
 * - Custom color controls (primary, accent, background, text)
 * - Font size adjustment
 * - Density/spacing controls
 * - Accessibility options (high contrast, reduced motion)
 * - Color presets
 * - localStorage persistence
 * - Server-side saving for authenticated users
 */

// ========== THEME CONFIGURATION ==========

/**
 * Color presets for quick theme switching
 */
const COLOR_PRESETS = {
    light: {
        primaryColor: '#2563eb',
        accentColor: '#10b981',
        backgroundColor: '#ffffff',
        textColor: '#1f2937'
    },
    dark: {
        primaryColor: '#60a5fa',
        accentColor: '#34d399',
        backgroundColor: '#111827',
        textColor: '#f9fafb'
    },
    blue: {
        primaryColor: '#3b82f6',
        accentColor: '#06b6d4',
        backgroundColor: '#eff6ff',
        textColor: '#1e3a8a'
    },
    green: {
        primaryColor: '#10b981',
        accentColor: '#84cc16',
        backgroundColor: '#f0fdf4',
        textColor: '#14532d'
    },
    purple: {
        primaryColor: '#8b5cf6',
        accentColor: '#d946ef',
        backgroundColor: '#faf5ff',
        textColor: '#581c87'
    }
};

// ========== THEME FUNCTIONS ==========

/**
 * Get current theme preferences from DOM and form controls
 * @returns {Object} Current theme preferences
 */
function getCurrentTheme() {
    const root = document.documentElement;

    return {
        theme: root.dataset.theme || 'light',
        fontSize: root.dataset.fontSize || 'medium',
        density: root.dataset.density || 'comfortable',
        highContrast: root.dataset.highContrast === 'true',
        reduceMotion: root.dataset.reduceMotion === 'true',
        primaryColor: document.getElementById('primaryColorPicker')?.value || '#2563eb',
        accentColor: document.getElementById('accentColorPicker')?.value || '#10b981',
        backgroundColor: document.getElementById('backgroundColorPicker')?.value || '#ffffff',
        textColor: document.getElementById('textColorPicker')?.value || '#1f2937'
    };
}

/**
 * Apply theme preferences to the page
 * Updates DOM, CSS variables, and localStorage
 * @param {Object} preferences - Theme preferences object
 */
function applyTheme(preferences) {
    const html = document.documentElement;

    // Update data attributes
    html.dataset.theme = preferences.theme;
    html.dataset.fontSize = preferences.fontSize;
    html.dataset.density = preferences.density;
    html.dataset.highContrast = preferences.highContrast;
    html.dataset.reduceMotion = preferences.reduceMotion;

    // Apply custom colors as CSS variables
    if (preferences.primaryColor) {
        html.style.setProperty('--primary-color', preferences.primaryColor);
    }
    if (preferences.accentColor) {
        html.style.setProperty('--accent-color', preferences.accentColor);
    }
    if (preferences.backgroundColor) {
        html.style.setProperty('--color-bg-primary', preferences.backgroundColor);
        document.body.style.backgroundColor = preferences.backgroundColor;
    }
    if (preferences.textColor) {
        html.style.setProperty('--color-text-primary', preferences.textColor);
        document.body.style.color = preferences.textColor;
    }

    // Save to localStorage for persistence
    localStorage.setItem('themePreferences', JSON.stringify(preferences));
}

/**
 * Helper function to set both color picker and text input
 * @param {string} name - Color input name (without 'Picker' or 'Text' suffix)
 * @param {string} value - Hex color value
 */
function setColorInput(name, value) {
    const picker = document.getElementById(`${name}Picker`);
    const text = document.getElementById(`${name}Text`);
    if (picker) picker.value = value;
    if (text) text.value = value;
}

/**
 * Initialize theme controls with current values from server or defaults
 * Called on page load
 */
function initThemeControls() {
    const current = getCurrentTheme();

    // Set theme radio buttons
    const themeRadio = document.querySelector(`input[name="theme"][value="${current.theme}"]`);
    if (themeRadio) themeRadio.checked = true;

    // Set font size
    const fontSizeSelector = document.getElementById('fontSizeSelector');
    if (fontSizeSelector) fontSizeSelector.value = current.fontSize;

    // Set density
    const densitySelector = document.getElementById('densitySelector');
    if (densitySelector) densitySelector.value = current.density;

    // Set accessibility toggles
    const highContrastToggle = document.getElementById('highContrastToggle');
    if (highContrastToggle) highContrastToggle.checked = current.highContrast;

    const reduceMotionToggle = document.getElementById('reduceMotionToggle');
    if (reduceMotionToggle) reduceMotionToggle.checked = current.reduceMotion;

    // Initialize color pickers from user preferences (injected by Django template)
    // Note: window.userThemeColors is set by Django in base.html
    if (window.userThemeColors) {
        setColorInput('primaryColor', window.userThemeColors.primary);
        setColorInput('accentColor', window.userThemeColors.accent);
        setColorInput('backgroundColor', window.userThemeColors.background);
        setColorInput('textColor', window.userThemeColors.text);
    }
}

/**
 * Save theme preferences to server via AJAX
 * Only works for authenticated users
 * @param {Object} preferences - Theme preferences object
 */
async function saveThemePreferences(preferences) {
    // Check if user is authenticated (URL is injected by Django)
    if (!window.themeApiUrl) {
        console.warn('Theme save API not available - user not authenticated');
        return;
    }

    try {
        const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
                         getCookie('csrftoken');

        const response = await fetch(window.themeApiUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify(preferences)
        });

        if (response.ok) {
            // Show success feedback
            const saveBtn = document.getElementById('saveThemeBtn');
            if (saveBtn) {
                const originalHTML = saveBtn.innerHTML;
                saveBtn.innerHTML = '<i class="bi bi-check-circle me-1"></i>Saved!';
                saveBtn.classList.add('btn-success');
                saveBtn.classList.remove('btn-primary');

                setTimeout(() => {
                    saveBtn.innerHTML = originalHTML;
                    saveBtn.classList.remove('btn-success');
                    saveBtn.classList.add('btn-primary');
                }, 2000);
            }
        } else {
            console.error('Failed to save theme preferences:', await response.text());
        }
    } catch (error) {
        console.error('Failed to save theme preferences:', error);
    }
}

/**
 * Setup color picker synchronization
 * Syncs color picker input with text input and applies theme on change
 * @param {string} name - Color input name (without 'Picker' or 'Text' suffix)
 */
function setupColorPicker(name) {
    const picker = document.getElementById(`${name}Picker`);
    const text = document.getElementById(`${name}Text`);

    if (picker) {
        picker.addEventListener('input', (e) => {
            if (text) text.value = e.target.value;
            const preferences = getCurrentTheme();
            applyTheme(preferences);
        });
    }

    if (text) {
        text.addEventListener('input', (e) => {
            const value = e.target.value;
            // Validate hex color format
            if (/^#[0-9A-Fa-f]{6}$/.test(value)) {
                if (picker) picker.value = value;
                const preferences = getCurrentTheme();
                applyTheme(preferences);
            }
        });
    }
}

// ========== EVENT LISTENERS ==========

document.addEventListener('DOMContentLoaded', function() {

    // Initialize theme controls
    initThemeControls();

    // ===== THEME SELECTION =====

    // Theme radio buttons (Light/Dark/Auto)
    document.querySelectorAll('input[name="theme"]').forEach(radio => {
        radio.addEventListener('change', (e) => {
            const preferences = getCurrentTheme();
            preferences.theme = e.target.value;
            applyTheme(preferences);
        });
    });

    // ===== TYPOGRAPHY CONTROLS =====

    // Font size selector
    const fontSizeSelector = document.getElementById('fontSizeSelector');
    if (fontSizeSelector) {
        fontSizeSelector.addEventListener('change', (e) => {
            const preferences = getCurrentTheme();
            preferences.fontSize = e.target.value;
            applyTheme(preferences);
        });
    }

    // ===== LAYOUT CONTROLS =====

    // Density/spacing selector
    const densitySelector = document.getElementById('densitySelector');
    if (densitySelector) {
        densitySelector.addEventListener('change', (e) => {
            const preferences = getCurrentTheme();
            preferences.density = e.target.value;
            applyTheme(preferences);
        });
    }

    // ===== ACCESSIBILITY CONTROLS =====

    // High contrast toggle
    const highContrastToggle = document.getElementById('highContrastToggle');
    if (highContrastToggle) {
        highContrastToggle.addEventListener('change', (e) => {
            const preferences = getCurrentTheme();
            preferences.highContrast = e.target.checked;
            applyTheme(preferences);
        });
    }

    // Reduce motion toggle
    const reduceMotionToggle = document.getElementById('reduceMotionToggle');
    if (reduceMotionToggle) {
        reduceMotionToggle.addEventListener('change', (e) => {
            const preferences = getCurrentTheme();
            preferences.reduceMotion = e.target.checked;
            applyTheme(preferences);
        });
    }

    // ===== COLOR CONTROLS =====

    // Setup all color pickers
    setupColorPicker('primaryColor');
    setupColorPicker('accentColor');
    setupColorPicker('backgroundColor');
    setupColorPicker('textColor');

    // ===== COLOR PRESETS =====

    // Color preset buttons
    document.querySelectorAll('[data-preset]').forEach(button => {
        button.addEventListener('click', (e) => {
            const presetName = e.currentTarget.dataset.preset;
            const preset = COLOR_PRESETS[presetName];

            if (preset) {
                setColorInput('primaryColor', preset.primaryColor);
                setColorInput('accentColor', preset.accentColor);
                setColorInput('backgroundColor', preset.backgroundColor);
                setColorInput('textColor', preset.textColor);

                const preferences = getCurrentTheme();
                applyTheme(preferences);
            }
        });
    });

    // ===== SAVE BUTTON =====

    // Save theme preferences button
    const saveThemeBtn = document.getElementById('saveThemeBtn');
    if (saveThemeBtn) {
        saveThemeBtn.addEventListener('click', () => {
            const preferences = getCurrentTheme();
            saveThemePreferences(preferences);
        });
    }
});

// Make theme functions globally available
window.getCurrentTheme = getCurrentTheme;
window.applyTheme = applyTheme;
window.saveThemePreferences = saveThemePreferences;
