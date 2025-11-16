/**
 * Progressive Tab Save Handler for Employee Creation Form
 * Allows saving each tab individually with AJAX requests
 * Auto-matches Phone, Email, and Address data with selected Employee Person
 */

document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("employee-form");
    const personIdField = document.getElementById("person-id-field");
    const employeeIdField = document.getElementById("employee-id-field");

    // Map of tab names to save endpoints
    const saveEndpoints = {
        person: '/hr/employees/ajax/save-person/',
        employee: '/hr/employees/ajax/save-employee/',
        phones: '/hr/employees/ajax/save-phones/',
        emails: '/hr/employees/ajax/save-emails/',
        addresses: '/hr/employees/ajax/save-addresses/',
    };

    /**
     * Get CSRF token from the form
     */
    function getCsrfToken() {
        return document.querySelector('[name="csrfmiddlewaretoken"]').value;
    }

    /**
     * Serialize form data for a specific tab
     */
    function getFormDataForTab(tabName) {
        const formData = new FormData(form);
        const data = new FormData();

        // Add CSRF token
        data.append('csrfmiddlewaretoken', getCsrfToken());

        // Add person and employee IDs
        const personId = personIdField.value;
        const employeeId = employeeIdField.value;

        if (personId) {
            data.append('person_id', personId);
        }
        if (employeeId) {
            data.append('employee_id', employeeId);
        }

        // Filter form data based on tab
        if (tabName === 'person') {
            // Person tab fields
            const personFields = [
                'first_name_en', 'middle_name_en', 'last_name_en',
                'first_name_ar', 'middle_name_ar', 'last_name_ar',
                'gender', 'date_of_birth', 'date_of_birth_hijri',
                'primary_nationality_iso2', 'national_id', 'iqama_number', 'iqama_expiry',
                'photo'
            ];
            personFields.forEach(field => {
                const input = form.querySelector(`[name="${field}"]`);
                if (input) {
                    if (input.type === 'file') {
                        const files = input.files;
                        if (files.length > 0) {
                            data.append(field, files[0]);
                        }
                    } else {
                        data.append(field, input.value);
                    }
                }
            });
        } else if (tabName === 'employee') {
            // Employee tab fields
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
                const input = form.querySelector(`[name="${field}"]`);
                if (input) {
                    data.append(field, input.value);
                }
            });
        } else if (tabName === 'phones') {
            // Phones formset
            const phonePrefix = 'phones-';
            formData.forEach((value, key) => {
                if (key.startsWith(phonePrefix) || key === 'csrfmiddlewaretoken') {
                    data.append(key, value);
                }
            });
        } else if (tabName === 'emails') {
            // Emails formset
            const emailPrefix = 'emails-';
            formData.forEach((value, key) => {
                if (key.startsWith(emailPrefix) || key === 'csrfmiddlewaretoken') {
                    data.append(key, value);
                }
            });
        } else if (tabName === 'addresses') {
            // Addresses formset
            const addressPrefix = 'addresses-';
            formData.forEach((value, key) => {
                if (key.startsWith(addressPrefix) || key === 'csrfmiddlewaretoken') {
                    data.append(key, value);
                }
            });
        }

        return data;
    }

    /**
     * Save a tab's data via AJAX
     */
    async function saveTab(tabName) {
        const endpoint = saveEndpoints[tabName];
        if (!endpoint) return;

        const saveBtn = document.querySelector(`.btn-save-tab[data-tab="${tabName}"]`);
        const statusEl = document.querySelector(`.save-status-${tabName}`);
        const statusText = statusEl?.querySelector('.status-text');

        // Disable button and show loading state
        if (saveBtn) {
            saveBtn.disabled = true;
            saveBtn.innerHTML = '<i class="bi bi-hourglass-split me-1 spinner-border spinner-border-sm"></i> Saving...';
        }

        try {
            const formData = getFormDataForTab(tabName);

            const response = await fetch(endpoint, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                }
            });

            const result = await response.json();

            if (result.success) {
                // Update hidden fields if person or employee was created
                if (result.person_id) {
                    personIdField.value = result.person_id;
                }
                if (result.employee_id) {
                    employeeIdField.value = result.employee_id;
                }

                // Show success message
                if (statusEl && statusText) {
                    statusText.textContent = result.message || 'Saved successfully';
                    statusEl.style.display = 'inline-flex';
                    statusEl.classList.remove('d-none');
                }

                // Reset button
                if (saveBtn) {
                    saveBtn.disabled = false;
                    saveBtn.innerHTML = '<i class="bi bi-check-circle me-1"></i> Save ' + capitalizeTab(tabName);
                    saveBtn.classList.remove('btn-primary');
                    saveBtn.classList.add('btn-success');
                }

                showAlert('success', result.message || 'Data saved successfully');
                return true;
            } else if (response.status === 409 && result.existing_person) {
                // Handle existing person scenario (duplicate national_id)
                if (result.person_id) {
                    personIdField.value = result.person_id;
                }

                // Show warning message
                if (statusEl && statusText) {
                    statusText.textContent = 'Using existing Person record';
                    statusEl.style.display = 'inline-flex';
                    statusEl.classList.remove('d-none');
                }

                // Reset button
                if (saveBtn) {
                    saveBtn.disabled = false;
                    saveBtn.innerHTML = '<i class="bi bi-check-circle me-1"></i> Save ' + capitalizeTab(tabName);
                    saveBtn.classList.add('btn-warning');
                    saveBtn.classList.remove('btn-primary', 'btn-success');
                }

                showAlert('warning', `${result.message}\n\nPerson: ${result.full_name}`);
                return true;
            } else {
                // Handle validation errors
                if (result.errors) {
                    Object.keys(result.errors).forEach(field => {
                        const input = form.querySelector(`[name="${field}"]`);
                        if (input) {
                            input.classList.add('is-invalid');
                            const errorDiv = input.nextElementSibling;
                            if (errorDiv) {
                                errorDiv.textContent = result.errors[field].join(', ');
                            }
                        }
                    });
                }

                showAlert('danger', result.message || 'Validation errors occurred');

                // Reset button
                if (saveBtn) {
                    saveBtn.disabled = false;
                    saveBtn.innerHTML = '<i class="bi bi-check-circle me-1"></i> Save ' + capitalizeTab(tabName);
                    saveBtn.classList.add('btn-danger');
                    saveBtn.classList.remove('btn-success');
                }

                return false;
            }
        } catch (error) {
            console.error('Error saving tab:', error);
            showAlert('danger', 'An error occurred while saving. Please try again.');

            // Reset button
            if (saveBtn) {
                saveBtn.disabled = false;
                saveBtn.innerHTML = '<i class="bi bi-check-circle me-1"></i> Save ' + capitalizeTab(tabName);
            }

            return false;
        }
    }

    /**
     * Show alert message in the form
     */
    function showAlert(type, message) {
        const alertDiv = form.querySelector('.alert');
        let targetDiv = alertDiv;

        // Convert message newlines to <br> for proper display
        const displayMessage = message.replace(/\n/g, '<br>');

        // Select appropriate icon for alert type
        const iconClass = type === 'success' ? 'check-circle' :
                         type === 'warning' ? 'exclamation-circle' : 'exclamation-triangle';

        if (!targetDiv) {
            targetDiv = document.createElement('div');
            targetDiv.className = `alert alert-${type} alert-dismissible fade show`;
            targetDiv.role = 'alert';
            targetDiv.innerHTML = `
                <i class="bi bi-${iconClass}-fill me-2"></i>
                <span>${displayMessage}</span>
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            `;
            form.parentElement.insertBefore(targetDiv, form);
        } else {
            targetDiv.className = `alert alert-${type} alert-dismissible fade show`;
            targetDiv.innerHTML = `
                <i class="bi bi-${iconClass}-fill me-2"></i>
                <span>${displayMessage}</span>
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            `;
        }

        // Auto-dismiss success alerts after 5 seconds
        if (type === 'success') {
            setTimeout(() => {
                if (targetDiv.parentElement) {
                    targetDiv.remove();
                }
            }, 5000);
        }
    }

    /**
     * Capitalize tab name for display
     */
    function capitalizeTab(tabName) {
        return tabName.charAt(0).toUpperCase() + tabName.slice(1);
    }

    /**
     * Attach click handlers to all save buttons
     */
    document.querySelectorAll('.btn-save-tab').forEach(button => {
        button.addEventListener('click', async function (e) {
            e.preventDefault();
            const tabName = this.dataset.tab;
            await saveTab(tabName);
        });
    });

    /**
     * Clear validation errors when user starts typing
     */
    form.addEventListener('change', function (e) {
        if (e.target.classList.contains('is-invalid')) {
            e.target.classList.remove('is-invalid');
        }
    });
});
