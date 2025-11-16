/**
 * HR Address Map Integration using Leaflet.js + OpenStreetMap
 *
 * Features:
 * - Interactive map with draggable marker
 * - Two-way binding with latitude/longitude form fields
 * - Forward geocoding (address to coordinates)
 * - Reverse geocoding (coordinates to address)
 * - Read-only mode for detail views
 */

class HRAddressMap {
    constructor(options = {}) {
        this.mapContainerId = options.mapContainerId || 'address-map';
        this.latFieldId = options.latFieldId || 'id_latitude';
        this.lngFieldId = options.lngFieldId || 'id_longitude';
        this.addressLine1Id = options.addressLine1Id || 'id_address_line1';
        this.cityId = options.cityId || 'id_city';
        this.stateRegionId = options.stateRegionId || 'id_state_region';
        this.postalCodeId = options.postalCodeId || 'id_postal_code';
        this.countryId = options.countryId || 'id_country_iso2';
        this.streetNameId = options.streetNameId || 'id_street_name';
        this.neighborhoodId = options.neighborhoodId || 'id_neighborhood';

        // Default center (Riyadh, Saudi Arabia)
        this.defaultCenter = options.defaultCenter || [24.7136, 46.6753];
        this.defaultZoom = options.defaultZoom || 12;
        this.readOnly = options.readOnly || false;

        this.map = null;
        this.marker = null;
        this.geocodeTimeout = null;

        this.init();
    }

    init() {
        const mapContainer = document.getElementById(this.mapContainerId);
        if (!mapContainer) {
            console.warn('Map container not found:', this.mapContainerId);
            return;
        }

        // Initialize map
        this.map = L.map(this.mapContainerId).setView(this.defaultCenter, this.defaultZoom);

        // Add OpenStreetMap tiles
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
            maxZoom: 19
        }).addTo(this.map);

        // Check if coordinates already exist
        const existingLat = this.getFieldValue(this.latFieldId);
        const existingLng = this.getFieldValue(this.lngFieldId);

        if (existingLat && existingLng) {
            const lat = parseFloat(existingLat);
            const lng = parseFloat(existingLng);
            if (!isNaN(lat) && !isNaN(lng)) {
                this.map.setView([lat, lng], 15);
                this.addMarker([lat, lng]);
            }
        }

        // Set up event listeners only if not read-only
        if (!this.readOnly) {
            this.setupEventListeners();
        }

        // Fix map rendering issues (common with Bootstrap tabs/modals)
        setTimeout(() => {
            this.map.invalidateSize();
        }, 100);
    }

    setupEventListeners() {
        // Click on map to place/move marker
        this.map.on('click', (e) => {
            this.setMarkerPosition(e.latlng.lat, e.latlng.lng);
            this.updateFormFields(e.latlng.lat, e.latlng.lng);
            this.reverseGeocode(e.latlng.lat, e.latlng.lng);
        });

        // Listen for manual coordinate input changes
        const latField = document.getElementById(this.latFieldId);
        const lngField = document.getElementById(this.lngFieldId);

        if (latField) {
            latField.addEventListener('change', () => this.onCoordinateFieldChange());
            latField.addEventListener('input', () => this.onCoordinateFieldChange());
        }

        if (lngField) {
            lngField.addEventListener('change', () => this.onCoordinateFieldChange());
            lngField.addEventListener('input', () => this.onCoordinateFieldChange());
        }

        // Set up "Find on Map" button if it exists
        const findOnMapBtn = document.getElementById('findOnMapBtn');
        if (findOnMapBtn) {
            findOnMapBtn.addEventListener('click', () => this.forwardGeocode());
        }

        // Set up "Clear Coordinates" button if it exists
        const clearCoordsBtn = document.getElementById('clearCoordsBtn');
        if (clearCoordsBtn) {
            clearCoordsBtn.addEventListener('click', () => this.clearCoordinates());
        }
    }

    getFieldValue(fieldId) {
        const field = document.getElementById(fieldId);
        return field ? field.value : null;
    }

    setFieldValue(fieldId, value) {
        const field = document.getElementById(fieldId);
        if (field) {
            field.value = value;
            // Trigger change event
            field.dispatchEvent(new Event('change', { bubbles: true }));
        }
    }

    addMarker(latlng) {
        if (this.marker) {
            this.marker.setLatLng(latlng);
        } else {
            const markerOptions = {
                draggable: !this.readOnly,
                autoPan: true
            };

            this.marker = L.marker(latlng, markerOptions).addTo(this.map);

            if (!this.readOnly) {
                this.marker.on('dragend', (e) => {
                    const pos = e.target.getLatLng();
                    this.updateFormFields(pos.lat, pos.lng);
                    this.reverseGeocode(pos.lat, pos.lng);
                });
            }

            // Add popup
            this.marker.bindPopup(this.readOnly ? 'Address Location' : 'Drag to adjust location').openPopup();
        }
    }

    setMarkerPosition(lat, lng) {
        if (!this.marker) {
            this.addMarker([lat, lng]);
        } else {
            this.marker.setLatLng([lat, lng]);
        }
    }

    updateFormFields(lat, lng) {
        this.setFieldValue(this.latFieldId, lat.toFixed(6));
        this.setFieldValue(this.lngFieldId, lng.toFixed(6));
        this.updateMapStatus(true);
    }

    onCoordinateFieldChange() {
        const lat = parseFloat(this.getFieldValue(this.latFieldId));
        const lng = parseFloat(this.getFieldValue(this.lngFieldId));

        if (!isNaN(lat) && !isNaN(lng) && lat >= -90 && lat <= 90 && lng >= -180 && lng <= 180) {
            this.setMarkerPosition(lat, lng);
            this.map.setView([lat, lng], Math.max(this.map.getZoom(), 15));
            this.updateMapStatus(true);
        } else {
            this.updateMapStatus(false);
        }
    }

    updateMapStatus(hasCoordinates) {
        const statusBadge = document.getElementById('gpsStatusBadge');
        if (statusBadge) {
            if (hasCoordinates) {
                statusBadge.innerHTML = '<i class="bi bi-geo-alt-fill me-1"></i>GPS Set';
                statusBadge.className = 'badge bg-success';
            } else {
                statusBadge.innerHTML = '<i class="bi bi-geo-alt me-1"></i>No GPS';
                statusBadge.className = 'badge bg-secondary';
            }
        }
    }

    clearCoordinates() {
        this.setFieldValue(this.latFieldId, '');
        this.setFieldValue(this.lngFieldId, '');

        if (this.marker) {
            this.map.removeLayer(this.marker);
            this.marker = null;
        }

        this.map.setView(this.defaultCenter, this.defaultZoom);
        this.updateMapStatus(false);
        this.showNotification('Coordinates cleared', 'info');
    }

    buildAddressString() {
        const parts = [];

        const addressLine1 = this.getFieldValue(this.addressLine1Id);
        const streetName = this.getFieldValue(this.streetNameId);
        const neighborhood = this.getFieldValue(this.neighborhoodId);
        const city = this.getFieldValue(this.cityId);
        const stateRegion = this.getFieldValue(this.stateRegionId);
        const postalCode = this.getFieldValue(this.postalCodeId);
        const countrySelect = document.getElementById(this.countryId);
        const country = countrySelect ? countrySelect.options[countrySelect.selectedIndex]?.text : '';

        if (addressLine1) parts.push(addressLine1);
        if (streetName && !addressLine1) parts.push(streetName);
        if (neighborhood) parts.push(neighborhood);
        if (city) parts.push(city);
        if (stateRegion) parts.push(stateRegion);
        if (postalCode) parts.push(postalCode);
        if (country && country !== '-- Select Country --') parts.push(country);

        return parts.join(', ');
    }

    async forwardGeocode() {
        const addressString = this.buildAddressString();

        if (!addressString || addressString.length < 5) {
            this.showNotification('Please enter address details (city, country, etc.) to search.', 'warning');
            return;
        }

        this.showNotification('Searching for address...', 'info');

        try {
            const encodedAddress = encodeURIComponent(addressString);
            const response = await fetch(
                `https://nominatim.openstreetmap.org/search?format=json&q=${encodedAddress}&limit=1&addressdetails=1`,
                {
                    headers: {
                        'Accept': 'application/json',
                        'User-Agent': 'FloorManagementSystem/1.0'
                    }
                }
            );

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            if (data && data.length > 0) {
                const result = data[0];
                const lat = parseFloat(result.lat);
                const lng = parseFloat(result.lon);

                this.setMarkerPosition(lat, lng);
                this.map.setView([lat, lng], 16);
                this.updateFormFields(lat, lng);

                this.showNotification(`Location found: ${result.display_name.substring(0, 100)}...`, 'success');
            } else {
                this.showNotification('No location found for this address. Try adding more details or adjust manually on the map.', 'warning');
            }
        } catch (error) {
            console.error('Geocoding error:', error);
            this.showNotification('Error searching for address. Please try again or set coordinates manually.', 'danger');
        }
    }

    async reverseGeocode(lat, lng) {
        // Only suggest filling fields if they are empty
        const addressLine1 = this.getFieldValue(this.addressLine1Id);
        if (addressLine1) {
            // Don't overwrite existing address
            return;
        }

        try {
            const response = await fetch(
                `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}&addressdetails=1`,
                {
                    headers: {
                        'Accept': 'application/json',
                        'User-Agent': 'FloorManagementSystem/1.0'
                    }
                }
            );

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            if (data && data.address) {
                const addr = data.address;

                // Build address line 1
                const line1Parts = [];
                if (addr.house_number) line1Parts.push(addr.house_number);
                if (addr.road) line1Parts.push(addr.road);
                if (line1Parts.length > 0) {
                    this.setFieldValue(this.addressLine1Id, line1Parts.join(' '));
                }

                // Fill other fields if empty
                if (!this.getFieldValue(this.cityId) && (addr.city || addr.town || addr.village)) {
                    this.setFieldValue(this.cityId, addr.city || addr.town || addr.village);
                }

                if (!this.getFieldValue(this.stateRegionId) && addr.state) {
                    this.setFieldValue(this.stateRegionId, addr.state);
                }

                if (!this.getFieldValue(this.postalCodeId) && addr.postcode) {
                    this.setFieldValue(this.postalCodeId, addr.postcode);
                }

                if (!this.getFieldValue(this.neighborhoodId) && (addr.suburb || addr.neighbourhood)) {
                    this.setFieldValue(this.neighborhoodId, addr.suburb || addr.neighbourhood);
                }

                this.showNotification('Address fields updated from map location', 'success');
            }
        } catch (error) {
            console.error('Reverse geocoding error:', error);
            // Silently fail for reverse geocoding
        }
    }

    showNotification(message, type = 'info') {
        const notificationArea = document.getElementById('mapNotificationArea');
        if (!notificationArea) return;

        const alertClass = {
            'success': 'alert-success',
            'warning': 'alert-warning',
            'danger': 'alert-danger',
            'info': 'alert-info'
        }[type] || 'alert-info';

        const iconClass = {
            'success': 'bi-check-circle-fill',
            'warning': 'bi-exclamation-triangle-fill',
            'danger': 'bi-x-circle-fill',
            'info': 'bi-info-circle-fill'
        }[type] || 'bi-info-circle-fill';

        notificationArea.innerHTML = `
            <div class="alert ${alertClass} alert-dismissible fade show py-2 mb-2" role="alert">
                <i class="bi ${iconClass} me-2"></i>
                <small>${message}</small>
                <button type="button" class="btn-close btn-close-sm" data-bs-dismiss="alert"></button>
            </div>
        `;

        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            const alert = notificationArea.querySelector('.alert');
            if (alert) {
                alert.classList.remove('show');
                setTimeout(() => {
                    if (notificationArea.contains(alert)) {
                        notificationArea.removeChild(alert);
                    }
                }, 150);
            }
        }, 5000);
    }

    // Method to refresh map size (useful after tab switches)
    refresh() {
        if (this.map) {
            this.map.invalidateSize();
        }
    }
}

// Export for use
window.HRAddressMap = HRAddressMap;
