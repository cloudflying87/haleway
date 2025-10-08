/**
 * Mapbox Address Autocomplete
 * Provides address search and autocomplete functionality using Mapbox Geocoding API
 */

class AddressAutocomplete {
    constructor(options = {}) {
        this.accessToken = options.accessToken;
        this.searchInputId = options.searchInputId || 'address-search';
        this.resultsContainerId = options.resultsContainerId || 'address-results';
        this.fieldMapping = options.fieldMapping || {};
        this.onSelect = options.onSelect || null;

        this.searchInput = null;
        this.resultsContainer = null;
        this.debounceTimer = null;

        this.init();
    }

    init() {
        this.searchInput = document.getElementById(this.searchInputId);
        this.resultsContainer = document.getElementById(this.resultsContainerId);

        if (!this.searchInput) {
            console.error(`Search input with id '${this.searchInputId}' not found`);
            return;
        }

        if (!this.accessToken) {
            console.error('Mapbox access token is required');
            return;
        }

        // Create results container if it doesn't exist
        if (!this.resultsContainer) {
            this.resultsContainer = document.createElement('div');
            this.resultsContainer.id = this.resultsContainerId;
            this.resultsContainer.className = 'address-autocomplete-results';
            this.searchInput.parentNode.appendChild(this.resultsContainer);
        }

        // Attach event listeners
        this.searchInput.addEventListener('input', (e) => this.handleInput(e));
        this.searchInput.addEventListener('focus', (e) => this.handleFocus(e));

        // Close results when clicking outside
        document.addEventListener('click', (e) => {
            if (!this.searchInput.contains(e.target) && !this.resultsContainer.contains(e.target)) {
                this.hideResults();
            }
        });
    }

    handleInput(e) {
        const query = e.target.value.trim();

        // Clear previous timer
        clearTimeout(this.debounceTimer);

        if (query.length < 3) {
            this.hideResults();
            return;
        }

        // Debounce API calls (wait 300ms after user stops typing)
        this.debounceTimer = setTimeout(() => {
            this.search(query);
        }, 300);
    }

    handleFocus(e) {
        const query = e.target.value.trim();
        if (query.length >= 3) {
            this.search(query);
        }
    }

    async search(query) {
        try {
            const url = `https://api.mapbox.com/geocoding/v5/mapbox.places/${encodeURIComponent(query)}.json?access_token=${this.accessToken}&types=address,poi&limit=5`;

            const response = await fetch(url);
            if (!response.ok) {
                throw new Error('Geocoding API request failed');
            }

            const data = await response.json();
            this.displayResults(data.features);
        } catch (error) {
            console.error('Error searching addresses:', error);
            this.showError('Failed to search addresses. Please try again.');
        }
    }

    displayResults(features) {
        if (features.length === 0) {
            this.showNoResults();
            return;
        }

        this.resultsContainer.innerHTML = '';

        features.forEach(feature => {
            const resultItem = document.createElement('div');
            resultItem.className = 'address-result-item';
            resultItem.textContent = feature.place_name;
            resultItem.addEventListener('click', () => this.selectAddress(feature));

            this.resultsContainer.appendChild(resultItem);
        });

        this.showResults();
    }

    selectAddress(feature) {
        // Extract address components
        const addressData = this.parseMapboxFeature(feature);

        // Populate form fields
        this.populateFields(addressData);

        // Update search input
        this.searchInput.value = feature.place_name;

        // Hide results
        this.hideResults();

        // Call onSelect callback if provided
        if (this.onSelect && typeof this.onSelect === 'function') {
            this.onSelect(addressData);
        }
    }

    parseMapboxFeature(feature) {
        const context = feature.context || [];
        const addressData = {
            full_address: feature.place_name,
            address_line1: '',
            address_line2: '',
            city: '',
            state: '',
            zip_code: '',
            latitude: feature.center[1],
            longitude: feature.center[0]
        };

        // Extract address number and street
        if (feature.address && feature.text) {
            addressData.address_line1 = `${feature.address} ${feature.text}`;
        } else if (feature.text) {
            addressData.address_line1 = feature.text;
        }

        // Extract city, state, zip from context
        context.forEach(item => {
            if (item.id.startsWith('postcode')) {
                addressData.zip_code = item.text;
            } else if (item.id.startsWith('place')) {
                addressData.city = item.text;
            } else if (item.id.startsWith('region')) {
                addressData.state = item.short_code ? item.short_code.split('-')[1] : item.text;
            }
        });

        return addressData;
    }

    populateFields(addressData) {
        // Populate fields based on field mapping
        Object.keys(this.fieldMapping).forEach(key => {
            const fieldId = this.fieldMapping[key];
            const field = document.getElementById(fieldId);

            if (field && addressData[key] !== undefined) {
                field.value = addressData[key];

                // Trigger change event for any listeners
                field.dispatchEvent(new Event('change', { bubbles: true }));
            }
        });
    }

    showResults() {
        this.resultsContainer.style.display = 'block';
    }

    hideResults() {
        this.resultsContainer.style.display = 'none';
    }

    showNoResults() {
        this.resultsContainer.innerHTML = '<div class="address-result-item no-results">No addresses found</div>';
        this.showResults();
    }

    showError(message) {
        this.resultsContainer.innerHTML = `<div class="address-result-item error">${message}</div>`;
        this.showResults();
    }
}

/**
 * Calculate distance between two coordinates using Haversine formula
 * @param {number} lat1 - Latitude of point 1
 * @param {number} lon1 - Longitude of point 1
 * @param {number} lat2 - Latitude of point 2
 * @param {number} lon2 - Longitude of point 2
 * @returns {number} - Distance in miles
 */
function calculateDistance(lat1, lon1, lat2, lon2) {
    const R = 3959; // Earth's radius in miles

    const dLat = toRadians(lat2 - lat1);
    const dLon = toRadians(lon2 - lon1);

    const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
              Math.cos(toRadians(lat1)) * Math.cos(toRadians(lat2)) *
              Math.sin(dLon / 2) * Math.sin(dLon / 2);

    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    const distance = R * c;

    return Math.round(distance * 100) / 100; // Round to 2 decimal places
}

/**
 * Calculate estimated travel time based on distance
 * @param {number} distance - Distance in miles
 * @param {number} avgSpeed - Average speed in mph (default: 40)
 * @returns {number} - Travel time in minutes
 */
function calculateTravelTime(distance, avgSpeed = 40) {
    // Calculate travel time in minutes
    // Formula: (distance / speed) * 60 = minutes
    const travelTimeMinutes = (distance / avgSpeed) * 60;
    return Math.round(travelTimeMinutes);
}

function toRadians(degrees) {
    return degrees * (Math.PI / 180);
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { AddressAutocomplete, calculateDistance };
}
