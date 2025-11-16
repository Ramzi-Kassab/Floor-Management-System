/**
 * Conditional ID Field Display
 * Shows/hides National ID and Iqama fields based on primary nationality selection
 *
 * Rules:
 * - Saudis (SA): Show National ID only, hide Iqama
 * - Non-Saudis: Show Iqama Number and Expiry, hide National ID
 */
(function() {
  /**
   * Get form field by name
   */
  function getField(name) {
    return document.querySelector('input[name="' + name + '"], select[name="' + name + '"]');
  }

  /**
   * Get form group wrapper (col-12 ancestor containing the field)
   */
  function getFormGroup(field) {
    if (!field) return null;
    let parent = field.closest('.form-group');
    if (!parent) {
      parent = field.closest('[class*="col-"]');
    }
    return parent || field.parentElement;
  }

  /**
   * Show or hide a form group
   */
  function toggleFormGroup(field, show) {
    if (!field) return;
    const group = getFormGroup(field);
    if (!group) return;

    if (show) {
      group.style.display = '';
      field.disabled = false;
    } else {
      group.style.display = 'none';
      field.disabled = true;
      field.value = '';  // Clear the value when hiding
    }
  }

  /**
   * Update ID fields visibility based on nationality
   */
  function updateIDFields() {
    const nationalityField = getField('primary_nationality_iso2');
    if (!nationalityField) return;

    const nationalIdField = getField('national_id');
    const iqamaField = getField('iqama_number');
    const iqamaExpiryField = getField('iqama_expiry');

    const selectedNationality = nationalityField.value;
    const isSaudi = selectedNationality === 'SA';

    // Toggle National ID (show for Saudis only)
    if (nationalIdField) {
      toggleFormGroup(nationalIdField, isSaudi);
      if (isSaudi) {
        // Mark as required for Saudis
        const label = nationalIdField.closest('.form-group')?.querySelector('label');
        if (label && !label.classList.contains('required')) {
          label.classList.add('required');
        }
      }
    }

    // Toggle Iqama fields (show for non-Saudis only)
    if (iqamaField) {
      toggleFormGroup(iqamaField, !isSaudi);
      if (!isSaudi) {
        // Mark as required for non-Saudis
        const label = iqamaField.closest('.form-group')?.querySelector('label');
        if (label && !label.classList.contains('required')) {
          label.classList.add('required');
        }
      }
    }

    if (iqamaExpiryField) {
      toggleFormGroup(iqamaExpiryField, !isSaudi);
    }
  }

  /**
   * Initialize conditional display
   */
  function init() {
    const nationalityField = getField('primary_nationality_iso2');
    if (!nationalityField) {
      console.warn('Nationality field not found for conditional ID display');
      return;
    }

    // Initial state
    updateIDFields();

    // Update on change
    nationalityField.addEventListener('change', updateIDFields);
  }

  /**
   * Wait for DOM ready
   */
  function ready(fn) {
    /in/.test(document.readyState) ? setTimeout(function() {
      ready(fn);
    }, 50) : fn();
  }

  // Initialize when DOM is ready
  ready(init);
})();
