
// ===== MAP SETUP =====
const map = L.map('map').setView([13.0827, 80.2707], 10);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap'
}).addTo(map);

// Drawing layer
const drawnItems = new L.FeatureGroup();
map.addLayer(drawnItems);

// Draw control
const drawControl = new L.Control.Draw({
    draw: {
        polygon: {
            allowIntersection: false,
            showArea: true,
            shapeOptions: {
                color: '#2d7a3a',
                weight: 3,
                fillColor: '#2d7a3a',
                fillOpacity: 0.3
            }
        },
        polyline: false,
        rectangle: true,
        circle: false,
        marker: false,
        circlemarker: false
    },
    edit: {
        featureGroup: drawnItems
    }
});

map.addControl(drawControl);

// Calculate area using Turf.js
function calculateArea(layer) {
    const geojson = layer.toGeoJSON();
    const areaSqMeters = turf.area(geojson);
    return areaSqMeters / 10000; // Convert to hectares
}

// When shape is created
map.on(L.Draw.Event.CREATED, function (e) {

    drawnItems.clearLayers();
    const layer = e.layer;
    drawnItems.addLayer(layer);

    const center = layer.getBounds().getCenter();

    document.getElementById('lat').value = center.lat.toFixed(6);
    document.getElementById('lon').value = center.lng.toFixed(6);

    const hectares = calculateArea(layer);
    document.getElementById('area').value = hectares.toFixed(2);

    const badge = document.getElementById('weather-source');
    badge.style.display = 'block';
    badge.innerHTML =
        `📐 Area: ${hectares.toFixed(2)} hectares<br>
         📍 Center: ${center.lat.toFixed(6)}, ${center.lng.toFixed(6)}`;
});

// When edited
map.on(L.Draw.Event.EDITED, function (e) {
    e.layers.eachLayer(function (layer) {
        const center = layer.getBounds().getCenter();
        document.getElementById('lat').value = center.lat.toFixed(6);
        document.getElementById('lon').value = center.lng.toFixed(6);

        const hectares = calculateArea(layer);
        document.getElementById('area').value = hectares.toFixed(2);
    });
});

// When deleted
map.on(L.Draw.Event.DELETED, function () {
    document.getElementById('lat').value = "";
    document.getElementById('lon').value = "";
    document.getElementById('area').value = "";
});

// ===== FETCH WEATHER =====
async function fetchWeather() {
    const lat = document.getElementById('lat').value;
    const lon = document.getElementById('lon').value;

    try {
        const resp = await fetch('/get_weather', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ lat, lon })
        });
        const data = await resp.json();

        document.getElementById('temp').value = data.temperature;
        document.getElementById('humidity').value = data.humidity;
        document.getElementById('rainfall').value = data.rainfall;

        const badge = document.getElementById('weather-source');
        badge.style.display = 'block';
        badge.textContent = `✅ Weather fetched from: ${data.source}`;
    } catch (err) {
        alert('Weather fetch failed. Please enter manually.');
    }
}

// ===== RUN PREDICTION =====
let charts = {};

async function runPrediction() {
    const payload = {
        n: document.getElementById('n').value,
        p: document.getElementById('p').value,
        k: document.getElementById('k').value,
        ph: document.getElementById('ph').value,
        temp: document.getElementById('temp').value,
        humidity: document.getElementById('humidity').value,
        rainfall: document.getElementById('rainfall').value,
        area: document.getElementById('area').value,
        lat: document.getElementById('lat').value,
        lon: document.getElementById('lon').value
    };

    try {
        const resp = await fetch('/predict', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await resp.json();
        displayResults(data);
    } catch (err) {
        alert('Prediction failed: ' + err.message);
    }
}

function displayResults(data) {
    const section = document.getElementById('results-section');
    section.style.display = 'block';
    section.scrollIntoView({ behavior: 'smooth' });

    // Best crop banner
    const banner = document.getElementById('best-crop-banner');
    banner.innerHTML = `
        <h2>🌟 Best Recommendation: ${data.best_crop}</h2>
        <p>Optimally balanced across Yield, Profit, Risk & Sustainability</p>
    `;

    // Crop cards
    const cardsDiv = document.getElementById('crop-cards');
    cardsDiv.innerHTML = '';
    data.results.forEach((crop, i) => {
        const isBest = crop.crop === data.best_crop;
        cardsDiv.innerHTML += `
            <div class="crop-card ${isBest ? 'best' : ''}" style="animation-delay:${i * 0.15}s">
                <h3>${isBest ? '🌟 ' : ''}${i + 1}. ${crop.crop}</h3>
                <span class="score-badge">Score: ${crop.final_score}</span>
                <div class="stat"><span class="stat-label">Probability</span><span class="stat-value">${crop.probability}%</span></div>
                <div class="stat"><span class="stat-label">Yield/ha</span><span class="stat-value">${crop.yield_per_ha} tons</span></div>
                <div class="stat"><span class="stat-label">Total Yield</span><span class="stat-value">${crop.total_yield} tons</span></div>
                <div class="stat"><span class="stat-label">Profit</span><span class="stat-value">₹${crop.profit.toLocaleString()}</span></div>
                <div class="stat"><span class="stat-label">Climate Risk</span><span class="stat-value risk-${crop.risk_label.toLowerCase()}">${crop.risk_label} (${crop.risk})</span></div>
                <div class="stat"><span class="stat-label">Sustainability</span><span class="stat-value">${crop.sustainability_label} (${crop.sustainability})</span></div>
                <div class="confidence">📊 Yield: ${crop.yield_per_ha} ± ${(crop.yield_upper - crop.yield_lower).toFixed(2)} tons/ha (95% CI: ${crop.yield_lower} – ${crop.yield_upper})</div>
            </div>
        `;
    });

    // ===== CHARTS =====
    const crops = data.results.map(r => r.crop);
    const colors = ['#2d7a3a', '#d4a017', '#5c6bc0'];

    // Destroy old charts
    Object.values(charts).forEach(c => c.destroy());

    // Yield Bar Chart
    charts.yield = new Chart(document.getElementById('yieldChart'), {
        type: 'bar',
        data: {
            labels: crops,
            datasets: [{
                label: 'Yield (tons/ha)',
                data: data.results.map(r => r.yield_per_ha),
                backgroundColor: colors,
                borderRadius: 8
            }]
        },
        options: { responsive: true, plugins: { legend: { display: false } } }
    });

    // Profit Bar Chart
    charts.profit = new Chart(document.getElementById('profitChart'), {
        type: 'bar',
        data: {
            labels: crops,
            datasets: [{
                label: 'Profit (₹)',
                data: data.results.map(r => r.profit),
                backgroundColor: colors,
                borderRadius: 8
            }]
        },
        options: { responsive: true, plugins: { legend: { display: false } } }
    });

    // Radar Chart
    charts.radar = new Chart(document.getElementById('radarChart'), {
        type: 'radar',
        data: {
            labels: ['Yield', 'Profit', 'Low Risk', 'Sustainability'],
            datasets: data.results.map((r, i) => ({
                label: r.crop,
                data: [r.yield_score, r.profit_score, 1 - r.risk, r.sustainability],
                borderColor: colors[i],
                backgroundColor: colors[i] + '33',
                borderWidth: 2
            }))
        },
        options: { responsive: true, scales: { r: { min: 0, max: 1 } } }
    });

    // Final Score Doughnut
    charts.final = new Chart(document.getElementById('finalChart'), {
        type: 'doughnut',
        data: {
            labels: crops,
            datasets: [{
                data: data.results.map(r => r.final_score),
                backgroundColor: colors,
                borderWidth: 3,
                borderColor: '#fff'
            }]
        },
        options: { responsive: true }
    });
}
