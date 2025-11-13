/**
 * Hijri/Gregorian Date Synchronization
 * Automatically converts between Gregorian and Hijri calendar dates
 * Uses moment.js with Hijri support
 */
(function() {
  /**
   * Get input field by name
   */
  function getField(name) {
    return document.querySelector('input[name="' + name + '"]');
  }

  /**
   * Convert Gregorian date to Hijri format (YYYY-MM-DD)
   */
  function toHijri(gy, gm, gd) {
    try {
      if (!window.moment) {
        console.warn('moment.js not loaded');
        return '';
      }
      var m = moment([gy, gm - 1, gd]);
      var hy = m.iYear(), hm = m.iMonth() + 1, hd = m.iDate();
      return hy.toString().padStart(4, "0") + "-" +
             hm.toString().padStart(2, "0") + "-" +
             hd.toString().padStart(2, "0");
    } catch (e) {
      console.error('Error converting to Hijri:', e);
      return '';
    }
  }

  /**
   * Convert Hijri date to Gregorian format (YYYY-MM-DD)
   */
  function toGreg(hy, hm, hd) {
    try {
      if (!window.moment) {
        console.warn('moment.js not loaded');
        return '';
      }
      var m = moment().iYear(hy).iMonth(hm - 1).iDate(hd);
      var gy = m.year(), gm = m.month() + 1, gd = m.date();
      return gy.toString().padStart(4, "0") + "-" +
             gm.toString().padStart(2, "0") + "-" +
             gd.toString().padStart(2, "0");
    } catch (e) {
      console.error('Error converting to Gregorian:', e);
      return '';
    }
  }

  /**
   * Sync Gregorian date to Hijri
   */
  function syncFromGreg() {
    var gregField = getField('date_of_birth');
    var hijriField = getField('date_of_birth_hijri');
    if (!gregField || !hijriField || !gregField.value) return;

    var parts = gregField.value.split("-");
    if (parts.length !== 3) return;

    var hijri = toHijri(parseInt(parts[0]), parseInt(parts[1]), parseInt(parts[2]));
    if (hijri) {
      hijriField.value = hijri;
      // Trigger change event to update any dependent fields
      hijriField.dispatchEvent(new Event('change'));
    }
  }

  /**
   * Sync Hijri date to Gregorian
   */
  function syncFromHijri() {
    var gregField = getField('date_of_birth');
    var hijriField = getField('date_of_birth_hijri');
    if (!gregField || !hijriField || !hijriField.value) return;

    var parts = hijriField.value.split("-");
    if (parts.length !== 3) return;

    var greg = toGreg(parseInt(parts[0]), parseInt(parts[1]), parseInt(parts[2]));
    if (greg) {
      gregField.value = greg;
      // Trigger change event to update any dependent fields
      gregField.dispatchEvent(new Event('change'));
    }
  }

  /**
   * Enhance date inputs with type="date" for better UX
   */
  function enhanceDateInputs() {
    var gregField = getField('date_of_birth');
    var hijriField = getField('date_of_birth_hijri');

    if (gregField) {
      gregField.setAttribute('type', 'date');
      gregField.addEventListener('change', syncFromGreg);
      gregField.addEventListener('blur', syncFromGreg);
    }

    if (hijriField) {
      // Hijri field displays as text with format hint
      hijriField.setAttribute('placeholder', 'YYYY-MM-DD');
      hijriField.addEventListener('change', syncFromHijri);
      hijriField.addEventListener('blur', syncFromHijri);
    }
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
  ready(function() {
    // Wait for moment.js to load if not already available
    if (typeof moment === 'undefined') {
      console.warn('moment.js library not loaded. Date sync will not work.');
      return;
    }
    enhanceDateInputs();
  });
})();
