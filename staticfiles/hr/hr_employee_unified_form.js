/**
 * Unified Employee Form Handler
 *
 * Features:
 * - Person lookup with searchable list
 * - View/Edit/Delete persons inline
 * - Smart form state management
 * - Progressive tab saving
 * - Automatic person detection on page load
 */

class EmployeeFormManager {
    constructor() {
        this.form = document.getElementById("employee-form");
        this.personIdField = document.getElementById("person-id-field");
        this.employeeIdField = document.getElementById("employee-id-field");

        this.currentPersonId = null;
        this.currentEmployeeId = null;

        this.endpoints = {
            savePersonTab: '/hr/employees/ajax/save-person/',
            saveEmployeeTab: '/hr/employees/ajax/save-employee/',
            savePhonesTab: '/hr/employees/ajax/save-phones/',
            saveEmailsTab: '/hr/employees/ajax/save-emails/',
            saveAddressesTab: '/hr/employees/ajax/save-addresses/',
            getPersonList: '/hr/persons/api/list/',
            getPersonDetail: '/hr/persons/api/',
        };

        this.init();
    }

    /**
     * Initialize the form manager
     */
    init() {
        this.restoreFormState();
        this.attachEventListeners();
        this.setupPersonLookup();
        this.setupChangePersonButtons();
        this.loadPersonListView();
    }

    /**
     * Restore form state from hidden fields
     */
    restoreFormState() {
        const personId = this.personIdField.value;
        const employeeId = this.employeeIdField.value;

        if (personId) {
            this.currentPersonId = parseInt(personId);
            this.updatePersonIndicator(this.currentPersonId);

            // Try to get person name from form fields
            const firstNameEn = this.form.querySelector('[name="first_name_en"]')?.value || '';
            const lastNameEn = this.form.querySelector('[name="last_name_en"]')?.value || '';
            if (firstNameEn || lastNameEn) {
                this.updatePersonNameDisplay(`${firstNameEn} ${lastNameEn}`.trim());
            }
        }

        if (employeeId) {
            this.currentEmployeeId = parseInt(employeeId);
        }
    }

    /**
     * Attach event listeners to save buttons
     */
    attachEventListeners() {
        document.querySelectorAll('.btn-save-tab').forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                const tabName = button.dataset.tab;
                this.saveTab(tabName);
            });
        });
    }

    /**
     * Setup person lookup functionality
     */
    setupPersonLookup() {
        const searchInput = document.getElementById('person-search-input');
        if (!searchInput) return;

        let searchTimeout;
        searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            const query = e.target.value.trim();

            if (query.length < 1) {
                this.loadPersonListView();
                return;
            }

            searchTimeout = setTimeout(() => {
                this.searchPersons(query);
            }, 300);
        });
    }

    /**
     * Load list of all persons for the Person tab view
     */
    async loadPersonListView() {
        try {
            const response = await fetch(`${this.endpoints.getPersonList}`);
            const result = await response.json();

            if (result.success) {
                this.displayPersonList(result.persons);
            }
        } catch (error) {
            console.error('Error loading persons:', error);
        }
    }

    /**
     * Search for persons
     */
    async searchPersons(query) {
        try {
            const response = await fetch(`${this.endpoints.getPersonList}?q=${encodeURIComponent(query)}`);
            const result = await response.json();

            if (result.success) {
                this.displayPersonList(result.persons);
            }
        } catch (error) {
            console.error('Error searching persons:', error);
        }
    }

    /**
     * Display person list in the Person tab
     */
    displayPersonList(persons) {
        const container = document.getElementById('person-list-container');
        if (!container) return;

        if (persons.length === 0) {
            container.innerHTML = `
                <div class="alert alert-info">
                    <i class="bi bi-info-circle me-2"></i>
                    No persons found. Create a new person using the form above.
                </div>
            `;
            return;
        }

        let html = `
            <div class="list-group">
                ${persons.map(person => `
                    <div class="list-group-item list-group-item-action ${this.currentPersonId === person.id ? 'active' : ''}">
                        <div class="d-flex w-100 justify-content-between align-items-start">
                            <div class="flex-grow-1">
                                <h6 class="mb-1 cursor-pointer" onclick="employeeFormManager.selectPerson(${person.id})">
                                    ${person.name}
                                </h6>
                                <p class="mb-1 text-muted small">
                                    <strong>ID:</strong> ${person.national_id}
                                    ${person.iqama_number ? `| <strong>Iqama:</strong> ${person.iqama_number}` : ''}
                                </p>
                                <small class="text-muted">
                                    <i class="bi bi-calendar me-1"></i>${person.created_at}
                                </small>
                            </div>
                            <div class="btn-group btn-group-sm">
                                <button type="button" class="btn btn-outline-primary"
                                        onclick="employeeFormManager.selectPerson(${person.id})"
                                        title="Select this person">
                                    <i class="bi bi-check-lg"></i> Select
                                </button>
                                <button type="button" class="btn btn-outline-info"
                                        onclick="employeeFormManager.viewPerson(${person.id})"
                                        title="View details">
                                    <i class="bi bi-eye"></i> View
                                </button>
                                <button type="button" class="btn btn-outline-warning"
                                        onclick="employeeFormManager.editPerson(${person.id})"
                                        title="Edit person">
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
     * Select a person from the list
     */
    async selectPerson(personId) {
        try {
            // Get person details
            const response = await fetch(`${this.endpoints.getPersonDetail}${personId}/`);
            const result = await response.json();

            if (result.success) {
                const person = result.person;

                // Update form fields with person data
                this.populatePersonForm(person);

                // Update hidden field
                this.personIdField.value = personId;
                this.currentPersonId = personId;

                // Update person name display in contact tabs
                const personName = `${person.first_name_en} ${person.last_name_en}`;
                this.updatePersonNameDisplay(personName);

                // Show success message
                this.showAlert('success', `Selected person: ${personName}`);

                // Update person indicator
                this.updatePersonIndicator(personId);

                // Reload person list to show which one is selected
                this.loadPersonListView();
            }
        } catch (error) {
            console.error('Error selecting person:', error);
            this.showAlert('danger', 'Error selecting person');
        }
    }

    /**
     * Populate person form with data
     */
    populatePersonForm(person) {
        const fields = {
            'first_name_en': person.first_name_en,
            'middle_name_en': person.middle_name_en,
            'last_name_en': person.last_name_en,
            'first_name_ar': person.first_name_ar,
            'middle_name_ar': person.middle_name_ar,
            'last_name_ar': person.last_name_ar,
            'gender': person.gender,
            'date_of_birth': person.date_of_birth,
            'date_of_birth_hijri': person.date_of_birth_hijri,
            'primary_nationality_iso2': person.primary_nationality_iso2,
            'national_id': person.national_id,
            'iqama_number': person.iqama_number,
            'iqama_expiry': person.iqama_expiry,
        };

        Object.entries(fields).forEach(([fieldName, value]) => {
            const input = this.form.querySelector(`[name="${fieldName}"]`);
            if (input && value !== null) {
                input.value = value;
                input.dispatchEvent(new Event('change', { bubbles: true }));
            }
        });

        // Display contact info summary
        this.displayContactInfoSummary(person);
    }

    /**
     * Display summary of existing contact info
     */
    displayContactInfoSummary(person) {
        let summary = '<strong>Existing Contact Info:</strong><br>';

        if (person.phones.length > 0) {
            summary += '<strong>Phones:</strong> ' + person.phones.map(p => p.phone_number).join(', ') + '<br>';
        }

        if (person.emails.length > 0) {
            summary += '<strong>Emails:</strong> ' + person.emails.map(e => e.email).join(', ') + '<br>';
        }

        if (person.addresses.length > 0) {
            summary += '<strong>Addresses:</strong> ' + person.addresses.map(a => a.address_line1).join(', ') + '<br>';
        }

        const summaryDiv = document.getElementById('person-contact-summary');
        if (summaryDiv) {
            summaryDiv.innerHTML = summary;
            summaryDiv.style.display = 'block';
        }
    }

    /**
     * View person details in a modal
     */
    async viewPerson(personId) {
        try {
            const response = await fetch(`${this.endpoints.getPersonDetail}${personId}/`);
            const result = await response.json();

            if (result.success) {
                this.showPersonDetailsModal(result.person);
            }
        } catch (error) {
            console.error('Error viewing person:', error);
            this.showAlert('danger', 'Error loading person details');
        }
    }

    /**
     * Edit person
     */
    editPerson(personId) {
        this.selectPerson(personId);
        this.showAlert('info', 'Edit the form above and click "Save Person Data" to update');
    }

    /**
     * Show person details in modal
     */
    showPersonDetailsModal(person) {
        let modalHtml = `
            <div class="modal fade" id="personDetailsModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Person Details</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="row mb-3">
                                <div class="col-md-6">
                                    <strong>Name (English):</strong>
                                    <p>${person.first_name_en} ${person.middle_name_en} ${person.last_name_en}</p>
                                </div>
                                <div class="col-md-6">
                                    <strong>Name (Arabic):</strong>
                                    <p>${person.first_name_ar} ${person.middle_name_ar} ${person.last_name_ar}</p>
                                </div>
                            </div>

                            <div class="row mb-3">
                                <div class="col-md-6">
                                    <strong>National ID:</strong>
                                    <p>${person.national_id}</p>
                                </div>
                                <div class="col-md-6">
                                    <strong>Iqama Number:</strong>
                                    <p>${person.iqama_number || 'N/A'}</p>
                                </div>
                            </div>

                            <div class="row mb-3">
                                <div class="col-md-6">
                                    <strong>Gender:</strong>
                                    <p>${person.gender}</p>
                                </div>
                                <div class="col-md-6">
                                    <strong>Date of Birth:</strong>
                                    <p>${person.date_of_birth || 'N/A'}</p>
                                </div>
                            </div>

                            <div class="mb-3">
                                <strong>Phone Numbers:</strong>
                                <ul class="list-unstyled">
                                    ${person.phones.map(p => `<li><i class="bi bi-telephone"></i> ${p.phone_number}</li>`).join('')}
                                </ul>
                            </div>

                            <div class="mb-3">
                                <strong>Email Addresses:</strong>
                                <ul class="list-unstyled">
                                    ${person.emails.map(e => `<li><i class="bi bi-envelope"></i> ${e.email}</li>`).join('')}
                                </ul>
                            </div>

                            <div class="mb-3">
                                <strong>Addresses:</strong>
                                <ul class="list-unstyled">
                                    ${person.addresses.map(a => `<li><i class="bi bi-geo-alt"></i> ${a.address_line1}, ${a.city}</li>`).join('')}
                                </ul>
                            </div>

                            <small class="text-muted">
                                Created: ${person.created_at} | Updated: ${person.updated_at}
                            </small>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Remove old modal if exists
        const oldModal = document.getElementById('personDetailsModal');
        if (oldModal) oldModal.remove();

        // Add new modal
        document.body.insertAdjacentHTML('beforeend', modalHtml);

        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('personDetailsModal'));
        modal.show();
    }

    /**
     * Save a tab
     */
    async saveTab(tabName) {
        const endpoint = this.endpoints[`save${tabName.charAt(0).toUpperCase() + tabName.slice(1)}Tab`];
        if (!endpoint) return;

        // Check if person is created for contact tabs (phones, emails, addresses)
        if (['phones', 'emails', 'addresses'].includes(tabName) && !this.currentPersonId) {
            this.showAlert('danger', 'Person must be created first. Please save the Person tab before saving contact information.');
            return false;
        }

        const saveBtn = document.querySelector(`.btn-save-tab[data-tab="${tabName}"]`);
        const statusEl = document.querySelector(`.save-status-${tabName}`);

        if (saveBtn) {
            saveBtn.disabled = true;
            saveBtn.innerHTML = '<i class="bi bi-hourglass-split spinner-border spinner-border-sm me-1"></i> Saving...';
        }

        try {
            const formData = this.getFormDataForTab(tabName);
            const response = await fetch(endpoint, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                }
            });

            const result = await response.json();

            if (result.success) {
                if (result.person_id) {
                    this.personIdField.value = result.person_id;
                    this.currentPersonId = result.person_id;
                }
                if (result.employee_id) {
                    this.employeeIdField.value = result.employee_id;
                    this.currentEmployeeId = result.employee_id;
                }

                // Update person name display in contact tabs
                if (result.full_name) {
                    this.updatePersonNameDisplay(result.full_name);
                }

                this.showAlert('success', result.message || 'Data saved successfully');

                if (saveBtn) {
                    saveBtn.disabled = false;
                    saveBtn.classList.add('btn-success');
                    saveBtn.classList.remove('btn-primary');
                    saveBtn.innerHTML = '<i class="bi bi-check-circle me-1"></i> Save ' + this.capitalizeTab(tabName);
                }

                return true;
            } else if (response.status === 409 && result.existing_person) {
                if (result.person_id) {
                    this.personIdField.value = result.person_id;
                    this.currentPersonId = result.person_id;
                }
                // Update person name display when duplicate is detected
                if (result.full_name) {
                    this.updatePersonNameDisplay(result.full_name);
                }
                this.showAlert('warning', `${result.message}\n\nPerson: ${result.full_name}`);
                return true;
            } else {
                this.showAlert('danger', result.message || 'Save failed');
                if (saveBtn) {
                    saveBtn.disabled = false;
                    saveBtn.classList.add('btn-danger');
                    saveBtn.innerHTML = '<i class="bi bi-check-circle me-1"></i> Save ' + this.capitalizeTab(tabName);
                }
                return false;
            }
        } catch (error) {
            console.error('Error saving tab:', error);
            this.showAlert('danger', 'An error occurred while saving');
            if (saveBtn) {
                saveBtn.disabled = false;
                saveBtn.innerHTML = '<i class="bi bi-check-circle me-1"></i> Save ' + this.capitalizeTab(tabName);
            }
            return false;
        }
    }

    /**
     * Get form data for a specific tab
     */
    getFormDataForTab(tabName) {
        const formData = new FormData(this.form);
        const data = new FormData();

        data.append('csrfmiddlewaretoken', this.form.querySelector('[name="csrfmiddlewaretoken"]').value);

        if (this.currentPersonId) {
            data.append('person_id', this.currentPersonId);
        }
        if (this.currentEmployeeId) {
            data.append('employee_id', this.currentEmployeeId);
        }

        if (tabName === 'person') {
            const personFields = [
                'first_name_en', 'middle_name_en', 'last_name_en',
                'first_name_ar', 'middle_name_ar', 'last_name_ar',
                'gender', 'date_of_birth', 'date_of_birth_hijri',
                'primary_nationality_iso2', 'national_id', 'iqama_number', 'iqama_expiry',
                'photo'
            ];
            personFields.forEach(field => {
                const input = this.form.querySelector(`[name="${field}"]`);
                if (input) {
                    if (input.type === 'file' && input.files.length > 0) {
                        data.append(field, input.files[0]);
                    } else if (input.type !== 'file') {
                        data.append(field, input.value);
                    }
                }
            });
        } else if (tabName === 'employee') {
            const employeeFields = [
                'person', 'user', 'employee_no', 'status',
                'position', 'department', 'report_to',
                'contract_type', 'contract_start_date', 'contract_end_date', 'contract_renewal_date',
                'probation_end_date', 'probation_status',
                'hire_date', 'termination_date',
                'work_days_per_week', 'hours_per_week', 'shift_pattern',
                'salary_grade', 'monthly_salary', 'benefits_eligible', 'overtime_eligible',
                'annual_leave_days', 'sick_leave_days', 'special_leave_days',
                'employment_category', 'employment_status', 'cost_center'
            ];
            employeeFields.forEach(field => {
                const input = this.form.querySelector(`[name="${field}"]`);
                if (input) {
                    data.append(field, input.value);
                }
            });
        } else {
            // For formsets (phones, emails, addresses)
            const prefix = tabName === 'phones' ? 'phones-' : tabName === 'emails' ? 'emails-' : 'addresses-';
            const managementPrefix = prefix.replace('-', '');  // e.g., 'phones' for 'phones-'

            formData.forEach((value, key) => {
                // Include: formset fields, management form fields, CSRF token
                if (key.startsWith(prefix) || key.startsWith(managementPrefix) || key === 'csrfmiddlewaretoken') {
                    data.append(key, value);
                }
            });
        }

        return data;
    }

    /**
     * Update person indicator
     */
    updatePersonIndicator(personId) {
        const indicator = document.getElementById('selected-person-indicator');
        if (indicator && this.currentPersonId) {
            indicator.style.display = 'block';
        }
    }

    /**
     * Update person name display in all contact tabs
     */
    updatePersonNameDisplay(personName) {
        document.querySelectorAll('.person-name-display').forEach(el => {
            el.textContent = personName || 'Not selected';
        });
    }

    /**
     * Handle change person button in contact tabs
     */
    setupChangePersonButtons() {
        document.querySelectorAll('.btn-change-person').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                this.loadPersonListView();
            });
        });
    }

    /**
     * Show alert message
     */
    showAlert(type, message) {
        const alertDiv = this.form.querySelector('.alert');
        let targetDiv = alertDiv;

        const displayMessage = message.replace(/\n/g, '<br>');
        const iconClass = type === 'success' ? 'check-circle' :
                         type === 'warning' ? 'exclamation-circle' : 'exclamation-triangle';

        if (!targetDiv) {
            targetDiv = document.createElement('div');
            targetDiv.className = `alert alert-${type} alert-dismissible fade show`;
            targetDiv.role = 'alert';
            targetDiv.innerHTML = `
                <i class="bi bi-${iconClass}-fill me-2"></i>
                <span>${displayMessage}</span>
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;
            this.form.parentElement.insertBefore(targetDiv, this.form);
        } else {
            targetDiv.className = `alert alert-${type} alert-dismissible fade show`;
            targetDiv.innerHTML = `
                <i class="bi bi-${iconClass}-fill me-2"></i>
                <span>${displayMessage}</span>
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;
        }

        if (type === 'success') {
            setTimeout(() => {
                if (targetDiv.parentElement) {
                    targetDiv.remove();
                }
            }, 5000);
        }
    }

    /**
     * Capitalize tab name
     */
    capitalizeTab(tabName) {
        return tabName.charAt(0).toUpperCase() + tabName.slice(1);
    }
}

// Initialize on document load
document.addEventListener('DOMContentLoaded', () => {
    window.employeeFormManager = new EmployeeFormManager();
});
