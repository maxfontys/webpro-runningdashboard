import { initializeMaps } from '/static/js/dashboard/maps.js';
import { initializeHeartRateTrends } from '/static/js/dashboard/heartRateTrends.js';
import { initializeWeeklyStats } from '/static/js/dashboard/weeklyStats.js';
import { initializeChat } from '/static/js/dashboard/chat.js';
import { applyFilters, setActiveButton } from '/static/js/dashboard/filters.js';

// Make setActiveButton available globally
window.setActiveButton = setActiveButton;

document.addEventListener('DOMContentLoaded', () => {
    // Verify the activities-data script is loaded
    const activitiesDataElement = document.getElementById('activities-data');
    if (!activitiesDataElement) {
        console.error("activities-data script not found in the DOM.");
        return;
    }

    const activitiesData = JSON.parse(activitiesDataElement.textContent);

    // Initialize all dashboard components
    try {
        initializeMaps(activitiesData);
        initializeHeartRateTrends();
        initializeWeeklyStats(activitiesData);
        initializeChat();
        // Remove this line since we're using onclick handlers
        // applyFilters();
    } catch (error) {
        console.error('Error initializing dashboard:', error);
    }
});