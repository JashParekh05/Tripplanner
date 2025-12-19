// Tripplanner Dashboard JavaScript

const API_BASE = window.location.origin + '/api';

// Tab Switching
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const tabName = btn.dataset.tab;

        // Update button states
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        // Update content visibility
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        document.getElementById(tabName).classList.add('active');

        // Load data for the active tab
        switch(tabName) {
            case 'deals':
                loadDeals();
                break;
            case 'config':
                loadConfig();
                loadDataSources();
                break;
            case 'stats':
                loadStatistics();
                break;
        }
    });
});

// Load Statistics Summary Bar
async function loadStatsBar() {
    try {
        const response = await fetch(`${API_BASE}/stats`);
        const data = await response.json();

        if (data.success) {
            const stats = data.stats;
            document.getElementById('totalDeals').textContent = stats.total_deals;
            document.getElementById('goodDeals').textContent = stats.good_deals;
            document.getElementById('lowestPrice').textContent = stats.lowest_price ? `$${stats.lowest_price}` : '-';
            document.getElementById('alertsSent').textContent = stats.alerts_sent;
        }
    } catch (error) {
        console.error('Error loading stats bar:', error);
    }
}

// Load Deals
async function loadDeals() {
    const container = document.getElementById('dealsContainer');
    const loading = document.getElementById('dealsLoading');
    const errorDiv = document.getElementById('dealsError');

    loading.style.display = 'block';
    errorDiv.style.display = 'none';
    container.innerHTML = '';

    try {
        const maxPrice = document.getElementById('maxPriceFilter').value || 600;
        const response = await fetch(`${API_BASE}/deals?max_price=${maxPrice}&limit=100`);
        const data = await response.json();

        loading.style.display = 'none';

        if (!data.success) {
            errorDiv.textContent = `Error: ${data.error}`;
            errorDiv.style.display = 'block';
            return;
        }

        let deals = data.deals;
        const sourceFilter = document.getElementById('sourceFilter').value;

        // Filter by data source
        if (sourceFilter !== 'all') {
            deals = deals.filter(deal => deal.data_source === sourceFilter);
        }

        if (deals.length === 0) {
            container.innerHTML = '<p class="loading">No deals found matching your criteria.</p>';
            return;
        }

        deals.forEach(deal => {
            container.appendChild(createDealCard(deal));
        });

        // Reload stats bar
        loadStatsBar();

    } catch (error) {
        loading.style.display = 'none';
        errorDiv.textContent = `Error loading deals: ${error.message}`;
        errorDiv.style.display = 'block';
    }
}

// Create Deal Card
function createDealCard(deal) {
    const card = document.createElement('div');
    card.className = 'deal-card';

    const source = deal.data_source || 'serpapi';
    const isMultiLeg = deal.is_multi_leg ? true : false;

    card.innerHTML = `
        <div class="deal-header">
            <div class="deal-route">${deal.origin} → ${deal.destination}</div>
            <div class="deal-price">$${deal.price}</div>
        </div>
        <div class="deal-info">
            <div class="deal-info-item">
                <span class="deal-info-label">Departure:</span>
                <span class="deal-info-value">${deal.departure_date}</span>
            </div>
            ${deal.return_date ? `
            <div class="deal-info-item">
                <span class="deal-info-label">Return:</span>
                <span class="deal-info-value">${deal.return_date}</span>
            </div>
            ` : ''}
            <div class="deal-info-item">
                <span class="deal-info-label">Airline:</span>
                <span class="deal-info-value">${deal.airline || 'N/A'}</span>
            </div>
            <div class="deal-info-item">
                <span class="deal-info-label">Stops:</span>
                <span class="deal-info-value">${deal.stops}</span>
            </div>
            <div class="deal-info-item">
                <span class="deal-info-label">Found:</span>
                <span class="deal-info-value">${formatDate(deal.found_at)}</span>
            </div>
        </div>
        <div>
            <span class="deal-badge badge-${source}">${source.toUpperCase()}</span>
            ${isMultiLeg ? '<span class="deal-badge badge-multi-leg">MULTI-LEG</span>' : ''}
        </div>
        ${deal.leg_details ? `<div style="margin-top: 10px; font-size: 0.85em; color: var(--text-secondary);">${deal.leg_details}</div>` : ''}
    `;

    return card;
}

// Load Configuration
async function loadConfig() {
    const form = document.getElementById('configForm');
    const loading = document.getElementById('configLoading');
    const errorDiv = document.getElementById('configError');

    loading.style.display = 'block';
    errorDiv.style.display = 'none';
    form.style.display = 'none';

    try {
        const response = await fetch(`${API_BASE}/config`);
        const data = await response.json();

        loading.style.display = 'none';

        if (!data.success) {
            errorDiv.textContent = `Error: ${data.error}`;
            errorDiv.style.display = 'block';
            return;
        }

        const config = data.config;

        // Populate form
        document.getElementById('configOrigin').value = config.origin_airport;
        document.getElementById('configDestinations').value = config.destination_airports.join(',');
        document.getElementById('configHubs').value = config.eu_hub_airports.join(',');
        document.getElementById('configDepartureDate').value = config.departure_date;
        document.getElementById('configReturnDate').value = config.return_date;
        document.getElementById('configFlexibility').value = config.date_flexibility;
        document.getElementById('configMaxPrice').value = config.max_price;
        document.getElementById('configInterval').value = config.check_interval_hours;
        document.getElementById('configThreshold').value = config.price_drop_threshold;
        document.getElementById('configMultiLeg').checked = config.enable_multi_leg_search;

        form.style.display = 'block';

    } catch (error) {
        loading.style.display = 'none';
        errorDiv.textContent = `Error loading configuration: ${error.message}`;
        errorDiv.style.display = 'block';
    }
}

// Load Data Sources Status
async function loadDataSources() {
    try {
        const response = await fetch(`${API_BASE}/data-sources`);
        const data = await response.json();

        if (data.success) {
            const container = document.getElementById('dataSourcesStatus');
            container.innerHTML = '';

            Object.entries(data.sources).forEach(([key, source]) => {
                const item = document.createElement('div');
                item.className = 'data-source-item';
                item.innerHTML = `
                    <span>${source.name}</span>
                    <span class="source-status ${source.enabled ? 'status-active' : 'status-disabled'}">
                        ${source.status.toUpperCase()}
                    </span>
                `;
                container.appendChild(item);
            });
        }
    } catch (error) {
        console.error('Error loading data sources:', error);
    }
}

// Save Configuration
document.getElementById('configForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const formData = {
        origin_airport: document.getElementById('configOrigin').value,
        destination_airports: document.getElementById('configDestinations').value.split(',').map(s => s.trim()),
        eu_hub_airports: document.getElementById('configHubs').value.split(',').map(s => s.trim()),
        departure_date: document.getElementById('configDepartureDate').value,
        return_date: document.getElementById('configReturnDate').value,
        date_flexibility: parseInt(document.getElementById('configFlexibility').value),
        max_price: parseInt(document.getElementById('configMaxPrice').value),
        check_interval_hours: parseInt(document.getElementById('configInterval').value),
        price_drop_threshold: parseInt(document.getElementById('configThreshold').value),
        enable_multi_leg_search: document.getElementById('configMultiLeg').checked
    };

    try {
        const response = await fetch(`${API_BASE}/config`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        const data = await response.json();

        if (data.success) {
            alert('Configuration saved successfully! Restart the monitoring service to apply changes.');
        } else {
            alert(`Error saving configuration: ${data.error}`);
        }

    } catch (error) {
        alert(`Error saving configuration: ${error.message}`);
    }
});

// Manual Search
async function manualSearch() {
    const origin = document.getElementById('searchOrigin').value;
    const destination = document.getElementById('searchDestination').value;
    const departureDate = document.getElementById('searchDepartureDate').value;
    const returnDate = document.getElementById('searchReturnDate').value;

    if (!origin || !destination || !departureDate) {
        alert('Please fill in origin, destination, and departure date');
        return;
    }

    const resultsDiv = document.getElementById('searchResults');
    resultsDiv.style.display = 'block';
    resultsDiv.innerHTML = '<p class="loading">Searching for flights...</p>';

    try {
        const response = await fetch(`${API_BASE}/search/manual`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                origin,
                destination,
                departure_date: departureDate,
                return_date: returnDate || null
            })
        });

        const data = await response.json();

        if (data.success) {
            resultsDiv.innerHTML = `
                <div class="success">
                    ${data.message}
                    <p style="margin-top: 10px;">Check the "Flight Deals" tab in a few moments to see results.</p>
                </div>
            `;

            // Reload deals after 3 seconds
            setTimeout(() => {
                document.querySelector('[data-tab="deals"]').click();
            }, 3000);

        } else {
            resultsDiv.innerHTML = `<div class="error">Error: ${data.error}</div>`;
        }

    } catch (error) {
        resultsDiv.innerHTML = `<div class="error">Error: ${error.message}</div>`;
    }
}

// Load Statistics
async function loadStatistics() {
    try {
        const response = await fetch(`${API_BASE}/stats`);
        const data = await response.json();

        if (data.success) {
            const stats = data.stats;

            document.getElementById('statTotalDeals').textContent = stats.total_deals;
            document.getElementById('statGoodDeals').textContent = stats.good_deals;
            document.getElementById('statLowestPrice').textContent = stats.lowest_price ? `$${stats.lowest_price}` : '-';
            document.getElementById('statAvgPrice').textContent = stats.average_price ? `$${stats.average_price}` : '-';
            document.getElementById('statAlertsSent').textContent = stats.alerts_sent;
            document.getElementById('statRecentSearches').textContent = stats.recent_searches_24h;
        }
    } catch (error) {
        console.error('Error loading statistics:', error);
    }
}

// Utility Functions
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    loadDeals();
    loadStatsBar();

    // Set default search dates to config dates
    const today = new Date();
    const nextWeek = new Date(today.getTime() + 7 * 24 * 60 * 60 * 1000);
    document.getElementById('searchDepartureDate').value = today.toISOString().split('T')[0];
    document.getElementById('searchReturnDate').value = nextWeek.toISOString().split('T')[0];
});

// Auto-refresh deals every 5 minutes
setInterval(() => {
    if (document.querySelector('.tab-btn[data-tab="deals"]').classList.contains('active')) {
        loadDeals();
    }
    loadStatsBar();
}, 5 * 60 * 1000);
