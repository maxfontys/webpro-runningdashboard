// static/js/dashboard/filters.js

const sportTypeCache = {};

// Add the button parameter to the function
export async function applyFilters(button) {
    // Remove active class from all buttons
    document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
    button.classList.add('active');

    // Get the sport type from the button ID
    const sportType = button.id.replace('filter-', '');

    // Check if data is already in cache
    if (sportTypeCache[sportType]) {
        updateUI(sportTypeCache[sportType]);
        return;
    }

    try {
        const response = await fetch(`/dashboard?sport_type=${sportType}`);
        const data = await response.json();
        
        // Cache the data
        sportTypeCache[sportType] = data;
        
        updateUI(data);
    } catch (error) {
        console.error('Error fetching filtered data:', error);
    }
}

function updateUI(data) {
    // Update stats
    document.getElementById('stats-distance').innerText = data.weekly_stats.distance;
    document.getElementById('stats-time').innerText = data.weekly_stats.time;
    document.getElementById('stats-elevation').innerText = data.weekly_stats.elevation;

    // Update chart
    const chart = Chart.getChart('weekly-stats-chart');
    if (chart) {
        chart.data.labels = data.weekly_chart.labels.map((label, index) => {
            return index % 4 === 1 ? label.split(' ')[0].toUpperCase() : '';
        });
        chart.data.datasets[0].data = data.weekly_chart.distances;
        chart.update();
    }
}

// Export the function to handle button clicks
export function setActiveButton(button) {
    applyFilters(button);
}