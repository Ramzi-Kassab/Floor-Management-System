/**
 * Photo Preview
 * Display photo preview when user selects an image file
 */
(function() {
  /**
   * Initialize photo preview
   */
  function initPhotoPreview() {
    const photoInput = document.querySelector('input[name="photo"]');
    if (!photoInput) return;

    // Create preview container if it doesn't exist
    const previewContainer = createPreviewContainer();
    if (!previewContainer) return;

    photoInput.addEventListener('change', handlePhotoChange);

    // Show existing photo if available
    showExistingPhoto();
  }

  /**
   * Create preview container HTML
   */
  function createPreviewContainer() {
    const formGroup = document.querySelector('input[name="photo"]')?.closest('.form-group');
    if (!formGroup) return null;

    // Check if preview already exists
    if (formGroup.querySelector('.photo-preview-container')) {
      return formGroup.querySelector('.photo-preview-container');
    }

    // Create preview container
    const container = document.createElement('div');
    container.className = 'photo-preview-container mt-3';
    container.innerHTML = `
      <div class="position-relative d-inline-block">
        <img id="photoPreview"
             src=""
             alt="Photo preview"
             class="img-thumbnail rounded"
             style="max-width: 200px; max-height: 200px; display: none; object-fit: cover;">
        <div id="noPhotoPlaceholder"
             class="bg-light border rounded d-flex align-items-center justify-content-center"
             style="width: 200px; height: 200px;">
          <div class="text-center text-muted">
            <i class="bi bi-image" style="font-size: 3rem;"></i>
            <p class="mt-2 small">No photo selected</p>
          </div>
        </div>
        <button type="button"
                id="clearPhotoBtn"
                class="btn btn-sm btn-danger position-absolute top-0 end-0"
                style="display: none;">
          <i class="bi bi-x-lg"></i>
        </button>
      </div>
    `;

    formGroup.appendChild(container);
    return container;
  }

  /**
   * Handle photo file selection
   */
  function handlePhotoChange(event) {
    const file = event.target.files[0];
    const preview = document.getElementById('photoPreview');
    const placeholder = document.getElementById('noPhotoPlaceholder');
    const clearBtn = document.getElementById('clearPhotoBtn');

    if (file && file.type.startsWith('image/')) {
      const reader = new FileReader();

      reader.onload = function(e) {
        preview.src = e.target.result;
        preview.style.display = 'block';
        if (placeholder) placeholder.style.display = 'none';
        if (clearBtn) clearBtn.style.display = 'block';
      };

      reader.readAsDataURL(file);
    } else if (file) {
      // Invalid file type
      alert('Please select a valid image file (JPG, PNG, GIF, etc.)');
      event.target.value = '';
    }
  }

  /**
   * Show existing photo if available
   */
  function showExistingPhoto() {
    const photoInput = document.querySelector('input[name="photo"]');
    if (!photoInput) return;

    // Check if there's an existing image field/link
    const existingImageField = document.querySelector('[data-photo-url]');
    if (!existingImageField) return;

    const photoUrl = existingImageField.getAttribute('data-photo-url');
    if (!photoUrl) return;

    const preview = document.getElementById('photoPreview');
    const placeholder = document.getElementById('noPhotoPlaceholder');
    const clearBtn = document.getElementById('clearPhotoBtn');

    if (preview && photoUrl) {
      preview.src = photoUrl;
      preview.style.display = 'block';
      if (placeholder) placeholder.style.display = 'none';
      if (clearBtn) clearBtn.style.display = 'block';
    }
  }

  /**
   * Clear photo preview
   */
  function handleClearPhoto() {
    const clearBtn = document.getElementById('clearPhotoBtn');
    if (!clearBtn) return;

    clearBtn.addEventListener('click', function(e) {
      e.preventDefault();

      const photoInput = document.querySelector('input[name="photo"]');
      const preview = document.getElementById('photoPreview');
      const placeholder = document.getElementById('noPhotoPlaceholder');

      photoInput.value = '';
      preview.src = '';
      preview.style.display = 'none';
      if (placeholder) placeholder.style.display = 'flex';
      this.style.display = 'none';
    });
  }

  /**
   * Wait for DOM ready
   */
  function ready(fn) {
    if (document.readyState !== 'loading') {
      fn();
    } else {
      document.addEventListener('DOMContentLoaded', fn);
    }
  }

  // Initialize when DOM is ready
  ready(function() {
    initPhotoPreview();
    handleClearPhoto();
  });
})();
