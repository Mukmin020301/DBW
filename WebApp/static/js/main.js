const throttleSlider = document.getElementById('throttleSlider');
const throttleValue = document.getElementById('throttleValue');
const tps1Value = document.getElementById('tps1Value');
const tps2Value = document.getElementById('tps2Value');
const daqStatusBadge = document.getElementById('daqStatusBadge');

// Initialize Chart.js for real-time visualization
const ctx = document.getElementById('tpsChart').getContext('2d');
const tpsChart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: Array(30).fill(''),
        datasets: [
            {
                label: 'TPS 1 (V)',
                data: Array(30).fill(0),
                borderColor: '#66fcf1',
                backgroundColor: 'rgba(102, 252, 241, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointRadius: 0
            },
            {
                label: 'TPS 2 (V)',
                data: Array(30).fill(0),
                borderColor: '#a64dff',
                backgroundColor: 'rgba(166, 77, 255, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointRadius: 0
            }
        ]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            y: {
                min: 0,
                max: 5,
                grid: { color: 'rgba(255,255,255,0.05)' },
                ticks: { color: '#c5c6c7' }
            },
            x: {
                grid: { display: false },
                ticks: { display: false }
            }
        },
        plugins: {
            legend: {
                labels: { color: '#ffffff', font: { family: 'Outfit' } }
            }
        },
        animation: false
    }
});

let debounceTimer;

// Handle slider input
throttleSlider.addEventListener('input', (e) => {
    const val = parseFloat(e.target.value).toFixed(2);
    throttleValue.innerText = val;
    
    // Debounce API calls to prevent flooding
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
        fetch('/api/set_throttle', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ voltage: val })
        }).catch(err => console.error("Error setting throttle:", err));
    }, 20); // 20ms debounce for smooth but responsive feel
});

// Polling for TPS values from board
setInterval(() => {
    fetch('/api/get_tps')
        .then(res => res.json())
        .then(data => {
            // Update DAQ Status Badge
            if (data.daq_connected) {
                daqStatusBadge.textContent = 'DAQ Connected';
                daqStatusBadge.className = 'status-badge connected';
            } else {
                daqStatusBadge.textContent = 'DAQ Disconnected';
                daqStatusBadge.className = 'status-badge disconnected';
            }

            // Update UI gauges
            tps1Value.innerText = data.tps1.toFixed(2);
            tps2Value.innerText = data.tps2.toFixed(2);

            // Update Chart
            tpsChart.data.datasets[0].data.shift();
            tpsChart.data.datasets[0].data.push(data.tps1);
            
            tpsChart.data.datasets[1].data.shift();
            tpsChart.data.datasets[1].data.push(data.tps2);
            
            tpsChart.update();
        })
        .catch(err => console.error("Error reading TPS:", err));
}, 100); // 100ms polling rate
