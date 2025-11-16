/**
 * Select2 Dropdown Initialization
 * Makes dropdown selections searchable with better UX
 */
(function() {
  /**
   * Initialize Select2 on specific fields
   */
  function initSelect2() {
    // List of fields to enhance with Select2
    const selectFields = [
      'primary_nationality_iso2',  // Nationality dropdown
      'gender',                      // Gender dropdown
      'team',                        // Team/Department dropdown
      'status',                      // Status dropdown
      'employee_type',               // Employee type dropdown
      'person',                      // Person (OneToOne) dropdown
      'user',                        // User dropdown
    ];

    selectFields.forEach(function(fieldName) {
      const field = document.querySelector('select[name="' + fieldName + '"]');
      if (field && typeof $ !== 'undefined' && $.fn.select2) {
        $(field).select2({
          width: '100%',
          placeholder: 'Select ' + fieldName.replace(/_/g, ' '),
          allowClear: !field.required,
          theme: 'bootstrap-5',
          dropdownAutoWidth: false,
          minimumInputLength: 0,  // Show all options initially
          templateResult: formatResult,
          templateSelection: formatSelection,
        });
      }
    });
  }

  /**
   * Format result items in dropdown with icons
   */
  function formatResult(data) {
    if (!data.id) return data.text;

    var icon = getIconForValue(data.id, data.text);
    return $('<span><i class="' + icon + ' me-2"></i>' + data.text + '</span>');
  }

  /**
   * Format selected item
   */
  function formatSelection(data) {
    if (!data.id) return data.text;
    var icon = getIconForValue(data.id, data.text);
    return $('<span><i class="' + icon + ' me-2"></i>' + data.text + '</span>');
  }

  /**
   * Get Bootstrap icon class based on value
   */
  function getIconForValue(value, text) {
    // Gender icons
    if (text === 'Male') return 'bi bi-person-fill';
    if (text === 'Female') return 'bi bi-person-fill';

    // Status icons
    if (text === 'ACTIVE') return 'bi bi-check-circle-fill text-success';
    if (text === 'ON_LEAVE') return 'bi bi-clock-history text-warning';
    if (text === 'SUSPENDED') return 'bi bi-exclamation-circle-fill text-danger';
    if (text === 'TERMINATED') return 'bi bi-x-circle-fill text-secondary';

    // Employee type icons
    if (text === 'OPERATOR' || text.includes('Operator')) return 'bi bi-person-badge text-primary';
    if (text === 'SUPERVISOR' || text.includes('Supervisor')) return 'bi bi-person-check text-info';
    if (text === 'MANAGER' || text.includes('Manager')) return 'bi bi-person-lines-fill text-success';
    if (text === 'ENGINEER' || text.includes('Engineer')) return 'bi bi-tools text-warning';
    if (text === 'ADMIN' || text.includes('Administrative')) return 'bi bi-gear text-secondary';

    // Default icons
    if (text.includes('National') || text.includes('ID')) return 'bi bi-hash';
    if (text.includes('Team') || text.includes('Department')) return 'bi bi-people-fill';

    return 'bi bi-check-lg';
  }

  /**
   * Wait for DOM and jQuery ready
   */
  function ready(fn) {
    if (document.readyState !== 'loading') {
      fn();
    } else {
      document.addEventListener('DOMContentLoaded', fn);
    }
  }

  // Initialize when DOM and jQuery are ready
  ready(function() {
    if (typeof jQuery === 'undefined') {
      console.warn('jQuery not loaded. Select2 will not be initialized.');
      return;
    }
    // Wait a bit for jQuery to fully load
    setTimeout(initSelect2, 100);
  });
})();
