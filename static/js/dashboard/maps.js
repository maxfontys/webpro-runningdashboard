// static/js/dashboard/maps.js

export function initializeMaps(activitiesData) {

    // Loop through the activities and render maps
    activitiesData.forEach((activity, index) => {
        if (activity.polyline && activity.start_latlng && activity.start_latlng[0] !== 0) {
            // Dynamically render a small map for each activity
            const map = L.map(`map-${index + 1}`, {
                zoomControl: false, // Disable zoom controls
                dragging: false, // Disable dragging
                scrollWheelZoom: false, // Disable scroll wheel zoom
                attributionControl: false // Hide attribution
            }).setView(activity.start_latlng, 13); // Set initial view based on start_latlng

            // Add OpenStreetMap tiles
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap contributors'
            }).addTo(map);

            // Decode polyline and add to map
            const decodedPolyline = polyline.decode(activity.polyline);
            const polylineLayer = L.polyline(decodedPolyline, { color: '#FB5201', weight: 2 }); // Updated color
            polylineLayer.addTo(map);

            // Fit map bounds to polyline
            map.fitBounds(polylineLayer.getBounds());
        } else {
            console.warn(`No valid polyline or coordinates for activity: ${activity.name}`);
        }
    });
}