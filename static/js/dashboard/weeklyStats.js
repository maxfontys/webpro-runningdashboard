// static/js/dashboard/weeklyStats.js

export function initializeWeeklyStats() {
    const ctx = document.getElementById('weekly-stats-chart').getContext('2d');
    const weeklyStatsData = document.getElementById('weekly-stats-data');

    // Fetch JSON data from Jinja
    const data = JSON.parse(weeklyStatsData.textContent);
    const labels = data.labels;
    const distances = data.distances;

    // Display capitalized months only (middle of each 4 weeks)
    const displayLabels = labels.map((label, index) => {
        return index % 4 === 1 ? label.split(' ')[0].toUpperCase() : '';
    });

    const maxDistance = Math.ceil(Math.max(...distances));
    const midDistance = Math.ceil(maxDistance / 2);

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: displayLabels,
            datasets: [{
                label: '',
                data: distances,
                borderColor: '#FB5100',
                backgroundColor: 'rgba(254, 211, 191, 0.9)',
                borderWidth: 3.5,
                pointBackgroundColor: function(context) {
                    return context.dataIndex === distances.length - 1 ? '#FB5100' : 'white';
                },
                pointBorderColor: '#FB5100',
                pointBorderWidth: 2.5,
                pointRadius: function(context) {
                    return context.dataIndex === distances.length - 1 ? 6 : 4;
                },
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            layout: {
                padding: {
                    top: 0,    // Extra space at the top
                    right: 0,  // Extra space on the right
                    bottom: 0,
                    left: 0
                }
            },
            plugins: {
                legend: { display: false }
            },
            elements: {
                line: { tension: 0, borderWidth: 3 }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: {
                        color: '#666',
                        font: { family: 'Söhne', size: 12, weight: 400 },
                        padding: 10
                    }
                },
                y: {
                    position: 'right',
                    beginAtZero: true,
                    min: 0,
                    max: maxDistance,
                    ticks: {
                        stepSize: Math.ceil(maxDistance / 2),
                        callback: function(value) {
                            return value + ' km';
                        },
                        color: '#666',
                        font: { family: 'Söhne', size: 12, weight: 400 },
                        padding: 10
                    },
                    grid: {
                        color: '#ddd',
                        drawTicks: false,
                        drawBorder: false
                    }
                }
            }
        },
        plugins: [{
            id: 'customFinalDot',
            beforeDraw: (chart) => {
                const ctx = chart.ctx;
                const dataset = chart.getDatasetMeta(0);
                const lastPoint = dataset.data[dataset.data.length - 1];

                // Draw outside canvas (disable clipping)
                ctx.save();
                ctx.beginPath();
                ctx.arc(lastPoint.x, lastPoint.y, 12, 0, Math.PI * 2);
                ctx.fillStyle = 'rgba(255, 87, 34, 0.4)'; 
                ctx.fill();
                ctx.restore();

                // Final white dot without clipping
                ctx.save();
                ctx.beginPath();
                ctx.arc(lastPoint.x, lastPoint.y, 3, 0, Math.PI * 2);
                ctx.fillStyle = '#FFFFFF';
                ctx.fill();
                ctx.restore();

                // Far-right vertical line
                ctx.save();
                ctx.beginPath();
                ctx.moveTo(lastPoint.x + 1, chart.scales.y.bottom); // Shift the line slightly right by 1px
                ctx.lineTo(lastPoint.x + 0.5, chart.chartArea.top);   // Extend to the top
                ctx.strokeStyle = '#43423E';
                ctx.lineWidth = 3;
                ctx.globalCompositeOperation = 'destination-over';    // Draw the line behind the dot
                ctx.stroke();
                ctx.restore();

            }
        }]
    });
}