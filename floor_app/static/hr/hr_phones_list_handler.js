/**
 * Phones List Handler
 *
 * Similar to person lookup in Person tab:
 * - Display all phones in a searchable list
 * - Select a phone to auto-fill the form fields
 * - View phone details
 */

class PhonesListHandler {
    constructor() {
        this.allPhones = [];
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadPhonesList();
    }

    /**
     * Setup event listeners for phone search
     */
    setupEventListeners() {
        const searchInput = document.getElementById('phones-search-input');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => this.searchPhones(e.target.value));
        }
    }

    /**
     * Load all phones from API
     */
    async loadPhonesList() {
        try {
            const response = await fetch('/hr/phones/api/list/');
            const result = await response.json();

            if (result.success) {
                this.allPhones = result.phones;
                this.displayPhonesList(result.phones);
            }
        } catch (error) {
            console.error('Error loading phones:', error);
        }
    }

    /**
     * Search phones by query
     */
    async searchPhones(query) {
        const q = query.toLowerCase().trim();

        if (!q) {
            this.displayPhonesList([]);
            return;
        }

        const filtered = this.allPhones.filter(phone =>
            phone.phone_number.toLowerCase().includes(q) ||
            phone.phone_e164.toLowerCase().includes(q) ||
            phone.person_name.toLowerCase().includes(q)
        );

        this.displayPhonesList(filtered);
    }

    /**
     * Display phones list in the same format as person list
     */
    displayPhonesList(phones) {
        const container = document.getElementById('phones-list-container');
        if (!container) return;

        if (phones.length === 0) {
            container.innerHTML = `
                <div class="alert alert-info">
                    <i class="bi bi-info-circle me-2"></i>
                    No phones found. Add a new phone using the form below.
                </div>
            `;
            return;
        }

        let html = `
            <div class="list-group">
                ${phones.map(phone => `
                    <div class="list-group-item list-group-item-action">
                        <div class="d-flex w-100 justify-content-between align-items-start">
                            <div class="flex-grow-1">
                                <h6 class="mb-1 cursor-pointer" onclick="window.phonesListHandler.selectPhone(${phone.id})">
                                    <i class="bi bi-telephone-fill text-primary me-2"></i>
                                    ${this.escapeHtml(phone.phone_number)}
                                </h6>
                                <p class="mb-1 text-muted small">
                                    <strong>Person:</strong> ${this.escapeHtml(phone.person_name)}
                                    | <strong>Kind:</strong> ${this.escapeHtml(phone.kind)}
                                    | <strong>Use:</strong> ${this.escapeHtml(phone.use)}
                                </p>
                                <small class="text-muted">
                                    <i class="bi bi-calendar me-1"></i>${phone.created_at}
                                </small>
                            </div>
                            <div class="btn-group btn-group-sm">
                                <button type="button" class="btn btn-outline-primary"
                                        onclick="window.phonesListHandler.selectPhone(${phone.id}); event.stopPropagation();"
                                        title="Select this phone number">
                                    <i class="bi bi-check-lg"></i> Select
                                </button>
                                <button type="button" class="btn btn-outline-info"
                                        onclick="window.phonesListHandler.viewPhone(${phone.id}); event.stopPropagation();"
                                        title="View details">
                                    <i class="bi bi-eye"></i> View
                                </button>
                                <button type="button" class="btn btn-outline-warning"
                                        onclick="window.phonesListHandler.editPhone(${phone.id}); event.stopPropagation();"
                                        title="Edit phone">
                                    <i class="bi bi-pencil"></i> Edit
                                </button>
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;

        container.innerHTML = html;
    }

    /**
     * Select a phone and auto-fill the form fields
     */
    async selectPhone(phoneId) {
        const phone = this.allPhones.find(p => p.id === phoneId);
        if (!phone) return;

        try {
            // Find all phone fields in the formset
            const countryFields = document.querySelectorAll('[name*="phones-"][name*="-country_iso2"]');

            if (countryFields.length === 0) {
                window.employeeFormManager.showAlert('warning', 'No phone form found');
                return;
            }

            // Get the first form index from the first field
            const firstField = countryFields[0];
            const match = firstField.name.match(/phones-(\d+)-country_iso2/);

            if (!match) {
                window.employeeFormManager.showAlert('warning', 'Could not determine form structure');
                return;
            }

            const formIndex = match[1]; // Get the actual formset index

            // Populate the form fields with phone data
            this.populatePhoneForm(formIndex, phone);

            // Show success message
            window.employeeFormManager.showAlert('success',
                `Selected phone: ${phone.phone_number} (${phone.person_name})`);

        } catch (error) {
            console.error('Error selecting phone:', error);
            window.employeeFormManager.showAlert('danger', 'Error selecting phone: ' + error.message);
        }
    }

    /**
     * Populate phone form with data from selected phone
     */
    populatePhoneForm(formIndex, phone) {
        try {
            // Extract phone number without country code
            let phoneNumber = phone.phone_number;
            if (phoneNumber.startsWith('+')) {
                // Remove the country code prefix
                phoneNumber = phoneNumber.replace(/^\+\d+/, '').replace(/^\d/, '').trim();
            }

            // Map phone data to form fields
            const fieldMappings = {
                'country_iso2': phone.country,
                'calling_code': phone.calling_code || '+966', // Default to Saudi if not available
                'phone_number': phoneNumber,
                'kind': phone.kind === 'Mobile' ? 'MOBILE' : 'LAND',
                'use': phone.use === 'Personal' ? 'PERSONAL' : 'BUSINESS',
                'channel': this.mapChannelValue(phone.channel),
            };

            console.log('Populating form index:', formIndex, 'with data:', fieldMappings);

            // Get the form and fill fields
            for (const [fieldName, fieldValue] of Object.entries(fieldMappings)) {
                const fieldSelector = `[name="phones-${formIndex}-${fieldName}"]`;
                const field = document.querySelector(fieldSelector);

                if (field) {
                    field.value = fieldValue;
                    // Trigger change event for any dependent fields
                    field.dispatchEvent(new Event('change', { bubbles: true }));
                    console.log(`Filled ${fieldName}:`, fieldValue);
                } else {
                    console.warn(`Field not found: ${fieldSelector}`);
                }
            }

            // Scroll to the phone form section
            const phoneForm = document.querySelector(`.formset-container`);
            if (phoneForm) {
                phoneForm.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }

        } catch (error) {
            console.error('Error populating phone form:', error);
            throw error;
        }
    }

    /**
     * Map channel value to form value
     */
    mapChannelValue(channel) {
        const mapping = {
            'Call': 'CALL',
            'WhatsApp': 'WHATS',
            'Call/Whats': 'BOTH',
            'Call/WhatsApp': 'BOTH'
        };
        return mapping[channel] || 'CALL';
    }

    /**
     * View phone details in modal
     */
    viewPhone(phoneId) {
        const phone = this.allPhones.find(p => p.id === phoneId);
        if (!phone) return;

        const details = `
            <div class="mb-3">
                <strong>Phone Number:</strong><br>
                <code class="bg-light p-2 rounded">${this.escapeHtml(phone.phone_number)}</code>
            </div>
            <div class="mb-3">
                <strong>Person:</strong><br>
                <span class="badge bg-info text-dark">
                    <i class="bi bi-person-circle me-1"></i>
                    ${this.escapeHtml(phone.person_name)}
                </span>
            </div>
            <div class="row">
                <div class="col-6">
                    <strong>Kind:</strong><br>
                    <small>${this.escapeHtml(phone.kind)}</small>
                </div>
                <div class="col-6">
                    <strong>Use:</strong><br>
                    <small>${this.escapeHtml(phone.use)}</small>
                </div>
            </div>
            <div class="row mt-3">
                <div class="col-6">
                    <strong>Channel:</strong><br>
                    <small>${this.escapeHtml(phone.channel)}</small>
                </div>
                <div class="col-6">
                    <strong>Country:</strong><br>
                    <small><code>${phone.country}</code></small>
                </div>
            </div>
            <div class="row mt-3">
                <div class="col-12">
                    <strong>Primary:</strong><br>
                    <small>${phone.is_primary ? 'Yes' : 'No'}</small>
                </div>
            </div>
            <div class="mt-3 pt-3 border-top">
                <small class="text-muted">Created: ${phone.created_at}</small>
            </div>
        `;

        this.showModal('View Phone', details, 'info');
    }

    /**
     * Edit phone (placeholder)
     */
    editPhone(phoneId) {
        const phone = this.allPhones.find(p => p.id === phoneId);
        if (phone) {
            window.employeeFormManager.showAlert('warning',
                `Edit phone: ${phone.phone_number} - Coming soon!`);
        }
    }

    /**
     * Show modal for phone details
     */
    showModal(title, content, type = 'info') {
        const modalHtml = `
            <div class="modal fade" id="phoneDetailsModal" tabindex="-1" aria-hidden="true">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">
                                <i class="bi bi-telephone text-${type} me-2"></i>
                                ${title}
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            ${content}
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Remove old modal if exists
        const oldModal = document.getElementById('phoneDetailsModal');
        if (oldModal) oldModal.remove();

        // Add new modal
        document.body.insertAdjacentHTML('beforeend', modalHtml);

        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('phoneDetailsModal'));
        modal.show();
    }

    /**
     * Escape HTML
     */
    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize on document load
document.addEventListener('DOMContentLoaded', () => {
    window.phonesListHandler = new PhonesListHandler();
});
