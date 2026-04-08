document.addEventListener('DOMContentLoaded', () => {
    // Sliders synchronization
    const demandSlider = document.getElementById('sim-demand');
    const demandVal = document.getElementById('sim-demand-val');
    demandSlider.addEventListener('input', (e) => demandVal.textContent = e.target.value);

    const supplySlider = document.getElementById('sim-supply');
    const supplyVal = document.getElementById('sim-supply-val');
    supplySlider.addEventListener('input', (e) => supplyVal.textContent = e.target.value);

    // Chart Setup
    const ctx = document.getElementById('mainChart').getContext('2d');
    
    // Modern gradient for line chart
    const gradientRevenue = ctx.createLinearGradient(0, 0, 0, 300);
    gradientRevenue.addColorStop(0, 'rgba(16, 185, 129, 0.5)');
    gradientRevenue.addColorStop(1, 'rgba(16, 185, 129, 0.0)');

    const chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: Array.from({length: 30}, (_, i) => i + 1),
            datasets: [
                {
                    label: 'Revenue Generated (₹)',
                    borderColor: '#10b981',
                    backgroundColor: gradientRevenue,
                    borderWidth: 2,
                    pointBackgroundColor: '#10b981',
                    pointRadius: 3,
                    pointHoverRadius: 5,
                    fill: true,
                    tension: 0.4,
                    data: []
                },
                {
                    label: 'Predicted Price (₹)',
                    borderColor: '#3b82f6',
                    borderWidth: 2,
                    borderDash: [5, 5],
                    pointBackgroundColor: '#3b82f6',
                    pointRadius: 2,
                    fill: false,
                    tension: 0.4,
                    data: []
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: { color: '#94a3b8', font: { family: 'Outfit' } }
                }
            },
            scales: {
                y: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { color: '#94a3b8', font: { family: 'Outfit' } }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: '#94a3b8', font: { family: 'Outfit' } }
                }
            },
            animation: {
                duration: 800,
                easing: 'easeOutQuart'
            }
        }
    });

    let currentPredictedPrice = 0;

    // Fetch Dashboard Data
    async function refreshDashboard() {
        try {
            const res = await fetch('/dashboard-data');
            const data = await res.json();
            
            if (Object.keys(data).length === 0) return;

            // Update Metrics
            document.getElementById('metric-revenue').textContent = data.metrics.total_revenue.toLocaleString();
            document.getElementById('metric-version').textContent = data.metrics.model_version;
            document.getElementById('metric-rmse').textContent = data.metrics.rmse;
            document.getElementById('metric-samples').textContent = data.metrics.data_points.toLocaleString();

            // Update Chart
            chart.data.datasets[0].data = data.trends.revenue;
            chart.data.datasets[1].data = data.trends.price;
            chart.data.labels = Array.from({length: data.trends.revenue.length}, (_, i) => i + 1);
            chart.update();

            // Update Table
            const tbody = document.querySelector('#logs-table tbody');
            tbody.innerHTML = '';
            // reverse recent activity to show latest first
            const recent = data.recent_activity.reverse();
            recent.forEach(row => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>#${row.id}</td>
                    <td>${row.demand}</td>
                    <td>${row.supply}</td>
                    <td style="text-transform:capitalize">${row.time_of_day}</td>
                    <td style="color:#3b82f6">₹${row.price.toFixed(2)}</td>
                    <td>${row.actual_sales}</td>
                    <td style="color:#10b981;font-weight:600">₹${row.revenue.toFixed(2)}</td>
                `;
                tbody.appendChild(tr);
            });

        } catch (error) {
            console.error("Dashboard fetch error:", error);
        }
    }

    // Predict Price Action
    document.getElementById('simulator-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const btn = document.getElementById('btn-predict');
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Analyzing...';
        btn.disabled = true;

        const payload = {
            demand: parseInt(demandSlider.value),
            supply: parseInt(supplySlider.value),
            time: document.getElementById('sim-time').value
        };

        try {
            const res = await fetch('/predict-price', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            currentPredictedPrice = data.recommended_price;
            
            // Show result
            document.getElementById('prediction-result').classList.remove('hidden');
            document.getElementById('predicted-price').textContent = currentPredictedPrice.toFixed(2);
            
            // Suggest an initial sales based on mock elasticity for user convenience
            const expectedSales = Math.max(0, payload.demand - (currentPredictedPrice * 0.3));
            document.getElementById('sim-sales').value = Math.floor(expectedSales);
            
        } catch(e) {
            console.error(e);
            alert("Error connecting to prediction model.");
        } finally {
            btn.innerHTML = '<i class="fa-solid fa-bolt"></i> Predict Optimal Price';
            btn.disabled = false;
        }
    });

    // Send Feedback Action
    document.getElementById('btn-feedback').addEventListener('click', async () => {
        const btn = document.getElementById('btn-feedback');
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Processing...';
        btn.disabled = true;

        const payload = {
            demand: parseInt(demandSlider.value),
            supply: parseInt(supplySlider.value),
            time: document.getElementById('sim-time').value,
            recommended_price: currentPredictedPrice,
            actual_sales: parseInt(document.getElementById('sim-sales').value)
        };

        try {
            const res = await fetch('/feedback', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(payload)
            });
            
            // Hide result until next prediction
            document.getElementById('prediction-result').classList.add('hidden');
            
            // Add a brief animation on UI
            const dash = document.querySelector('.analytics-panel');
            dash.style.boxShadow = '0 0 30px rgba(16, 185, 129, 0.4)';
            setTimeout(() => { dashboardResetGlow() }, 1000);

            // Refresh dashboard
            await refreshDashboard();

        } catch(e) {
            console.error(e);
            alert("Error sending feedback.");
        } finally {
            btn.innerHTML = '<i class="fa-solid fa-rotate"></i> Send Feedback & Retrain';
            btn.disabled = false;
        }
    });

    function dashboardResetGlow() {
        document.querySelector('.analytics-panel').style.boxShadow = '0 10px 30px rgba(0, 0, 0, 0.2)';
    }

    // Initial load
    refreshDashboard();
    // Auto refresh every 10 seconds just in case
    setInterval(refreshDashboard, 10000);
});
