/**
 * Address Form Dynamic Handler
 *
 * Handles:
 * - Conditional field visibility based on address_kind (STREET vs PO_BOX)
 * - Saudi-specific field requirements based on country selection
 * - Dynamic required field indicators
 */

class AddressFormHandler {
    constructor() {
        this.init();
    }

    init() {
        // Initialize handlers for each address form in the formset
        this.setupFormsetHandlers();
    }

    /**
     * Setup event listeners for all address forms in the formset
     */
    setupFormsetHandlers() {
        const addressCards = document.querySelectorAll('.formset-card');
        addressCards.forEach((card, index) => {
            this.setupCardHandlers(card, index);
        });
    }

    /**
     * Setup handlers for a single address card
     */
    setupCardHandlers(card, index) {
        const addressKindField = card.querySelector('[name*="address_kind"]');
        const countryField = card.querySelector('[name*="country_iso2"]');

        if (addressKindField) {
            addressKindField.addEventListener('change', () => {
                this.updateAddressTypeDisplay(card);
            });
            // Initialize on load
            this.updateAddressTypeDisplay(card);
        }

        if (countryField) {
            countryField.addEventListener('change', () => {
                this.updateCountryDisplay(card);
            });
            // Initialize on load
            this.updateCountryDisplay(card);
        }
    }

    /**
     * Update form display based on selected address type (STREET or PO_BOX)
     */
    updateAddressTypeDisplay(card) {
        const addressKindField = card.querySelector('[name*="address_kind"]');
        const poboxSection = card.querySelector('.address-pobox-section');
        const streetSection = card.querySelector('.address-street-section');
        const addressPoboxRequired = card.querySelectorAll('.address-pobox-required');
        const addressStreetRequired = card.querySelectorAll('.address-street-required');

        if (!addressKindField) return;

        const isPoBox = addressKindField.value === 'PO_BOX';

        // Show/hide sections
        if (poboxSection) poboxSection.style.display = isPoBox ? 'block' : 'none';
        if (streetSection) streetSection.style.display = isPoBox ? 'none' : 'block';

        // Update required indicators
        addressPoboxRequired.forEach(el => {
            el.style.display = isPoBox ? 'inline' : 'none';
        });
        addressStreetRequired.forEach(el => {
            el.style.display = isPoBox ? 'none' : 'inline';
        });

        // Update validation messages
        this.updateCountryDisplay(card);
    }

    /**
     * Update form display based on selected country (Saudi vs non-Saudi)
     */
    updateCountryDisplay(card) {
        const countryField = card.querySelector('[name*="country_iso2"]');
        const saudiSection = card.querySelector('.address-saudi-section');
        const saudiRequired = card.querySelectorAll('.address-saudi-required');

        if (!countryField) return;

        const isSaudi = (countryField.value || '').toUpperCase() === 'SA';

        // Show/hide Saudi section
        if (saudiSection) saudiSection.style.display = isSaudi ? 'block' : 'none';

        // Update required indicators for Saudi fields
        saudiRequired.forEach(el => {
            el.style.display = isSaudi ? 'inline' : 'none';
        });

        // Update help text for postal code
        const postalCodeField = card.querySelector('[name*="postal_code"]');
        if (postalCodeField) {
            const helpText = postalCodeField.closest('.form-group')?.querySelector('.form-text');
            if (helpText) {
                helpText.textContent = isSaudi ? 'Saudi: 5 digits only' : '';
            }
        }

        // Update help text for additional number
        const additionalNumberField = card.querySelector('[name*="additional_number"]');
        if (additionalNumberField) {
            const helpText = additionalNumberField.closest('.form-group')?.querySelector('.form-text');
            if (helpText) {
                helpText.textContent = isSaudi ? 'Exactly 4 digits' : '';
            }
        }
    }
}

// Initialize on document load
document.addEventListener('DOMContentLoaded', () => {
    window.addressFormHandler = new AddressFormHandler();

    // Watch for dynamically added formset rows (using MutationObserver)
    const container = document.querySelector('.formset-container');
    if (container) {
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.addedNodes.length) {
                    // Re-initialize handlers when new form is added
                    window.addressFormHandler.setupFormsetHandlers();
                }
            });
        });

        observer.observe(container, {
            childList: true,
            subtree: false
        });
    }
});
