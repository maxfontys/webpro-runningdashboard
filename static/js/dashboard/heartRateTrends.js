// static/js/dashboard/heartRateTrends.js

export function initializeHeartRateTrends() {
    const paceTrends = JSON.parse(document.getElementById('pace-trends-data').textContent);
    const ctx = document.getElementById('heartRateTrendsChart').getContext('2d');
    const dropdown = document.querySelector('.pace-dropdown-btn');
    let currentPaceGroup = dropdown.value;

    if (!(currentPaceGroup in paceTrends)) {
        currentPaceGroup = Object.keys(paceTrends)[0];
    }

    function updateChart(paceGroup) {
        const heartRateData = paceTrends[paceGroup] || [];
        const months = heartRateData.map(item => item.month_year);
        const bpmValues = heartRateData.map(item => Math.min(item.bpm, 200));

        const minBpm = Math.floor((Math.min(...bpmValues) - 10) / 10) * 10; // Rounded down to nearest 10
        const maxBpm = 200;

        heartRateChart.options.scales.y.min = minBpm;
        heartRateChart.options.scales.y.max = maxBpm;
        heartRateChart.data.labels = months;
        heartRateChart.data.datasets[0].data = bpmValues;

        heartRateChart.update();
    }

    const heartRateChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Average Heart Rate',
                data: [],
                borderColor: '#FF0808',
                backgroundColor: 'rgba(255, 8, 8, 0.2)',
                borderWidth: 2,
                pointRadius: function(context) {
                    return context.dataIndex === context.dataset.data.length - 1 ? 6 : 0; // Final point always visible
                },
                pointBackgroundColor: '#FF0808',
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: { duration: 1000 }, // Smooth animation for the chart
            layout: {
                padding: { left: 0, right: 0, top: 0, bottom: 10 }
            },
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: {
                    grid: { drawOnChartArea: false, drawTicks: false },
                    ticks: {
                        callback: function(value, index) {
                            return index % 3 === 0 ? this.getLabelForValue(value) : ''; // Every 3rd month
                        },
                        align: 'start',
                        padding: 10,
                        font: { family: 'Söhne', weight: '400', size: 12 },
                        color: '#666',
                        maxRotation: 0,
                        minRotation: 0
                    }
                },
                y: {
                    position: 'right',
                    grid: {
                        drawOnChartArea: true,
                        color: '#ddd',
                        drawTicks: false
                    },
                    ticks: {
                        stepSize: 10,
                        padding: 10,
                        font: { family: 'Söhne', weight: '400', size: 12 },
                        color: '#666',
                        callback: value => `${value} bpm`
                    }
                }
            },
        },
        plugins: [
            {
                // Draw the far-right line FIRST
                id: 'drawFarRightLine',
                beforeDraw: (chart) => {
                    const ctx = chart.ctx;
                    const xAxis = chart.scales.x;
                    const yAxis = chart.scales.y;

                    const farRightX = xAxis.right; // Far-right position fixed

                    // Draw the vertical line
                    ctx.save();
                    ctx.beginPath();
                    ctx.moveTo(farRightX, yAxis.top);
                    ctx.lineTo(farRightX, yAxis.bottom);
                    ctx.strokeStyle = '#43423E';
                    ctx.lineWidth = 3;
                    ctx.stroke();
                    ctx.restore();
                }
            },
            {
                // Radar effect & final point are drawn AFTER the far-right line
                id: 'radarEffect',
                afterDraw: (chart) => {
                    const ctx = chart.ctx;
                    const dataset = chart.getDatasetMeta(0);
                    const finalPoint = dataset.data[dataset.data.length - 1]; // Final data point

                    if (finalPoint) {
                        // Draw the radar effect
                        ctx.save();
                        ctx.beginPath();
                        ctx.arc(finalPoint.x, finalPoint.y, 12, 0, Math.PI * 2); // Larger transparent circle
                        ctx.fillStyle = 'rgba(255, 8, 8, 0.2)'; // Semi-transparent red
                        ctx.fill();
                        ctx.restore();

                        // Draw the final dot on top
                        ctx.save();
                        ctx.beginPath();
                        ctx.arc(finalPoint.x, finalPoint.y, 6, 0, Math.PI * 2);
                        ctx.fillStyle = '#FF0808';
                        ctx.fill();
                        ctx.restore();
                    }
                }
            }
        ]
    });

    dropdown.addEventListener('change', function () {
        currentPaceGroup = this.value;
        updateChart(currentPaceGroup);
    });

    updateChart(currentPaceGroup);
}