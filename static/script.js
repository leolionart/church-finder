let map;
let userMarker;
let churchMarkers = [];
let allChurches = [];
let selectedTime = null;

// Initialize map
function initMap() {
    map = L.map('map').setView([10.7769, 106.7009], 13); // Default to Ho Chi Minh City
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: ' OpenStreetMap contributors'
    }).addTo(map);

    // Get user's location
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            (position) => {
                const pos = {
                    lat: position.coords.latitude,
                    lng: position.coords.longitude,
                };
                map.setView([pos.lat, pos.lng], 13);
                if (userMarker) {
                    userMarker.setLatLng([pos.lat, pos.lng]);
                } else {
                    userMarker = L.marker([pos.lat, pos.lng], {
                        icon: L.divIcon({
                            className: 'user-marker',
                            html: '<i class="fas fa-circle"></i>',
                            iconSize: [20, 20]
                        })
                    }).addTo(map);
                }
                // Load default churches after getting user location
                loadDefaultChurches(pos.lat, pos.lng);
            },
            () => {
                console.log("Error: The Geolocation service failed.");
                // Load default churches with Ho Chi Minh City center coordinates
                loadDefaultChurches(10.7769, 106.7009);
            }
        );
    } else {
        // Load default churches with Ho Chi Minh City center coordinates
        loadDefaultChurches(10.7769, 106.7009);
    }
}

// Load default churches
async function loadDefaultChurches(lat, lng) {
    try {
        const response = await fetch('/default-churches', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ lat, lng }),
        });

        const data = await response.json();
        if (data.success) {
            allChurches = data.churches;
            displayChurches(allChurches);
            document.getElementById('resultsTitle').textContent = 'Nhà thờ gần đây';
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

// Filter churches by time
function filterChurches(time) {
    if (!time) {
        displayChurches(allChurches);
        document.getElementById('resultsTitle').textContent = 'Nhà thờ gần đây';
        return;
    }

    const filteredChurches = allChurches.filter(church => {
        if (!church.mass_times) return false;
        const times = church.mass_times.split(', ');
        return times.some(t => {
            const [hour, minute] = t.split(':').map(Number);
            const [filterHour, filterMinute] = time.split(':').map(Number);
            return hour === filterHour && minute === filterMinute;
        });
    });

    displayChurches(filteredChurches);
    document.getElementById('resultsTitle').textContent = 
        `Nhà thờ có lễ lúc ${time} (${filteredChurches.length})`;
}

// Display churches on map and in list
function displayChurches(churches) {
    // Clear existing markers
    churchMarkers.forEach(marker => marker.remove());
    churchMarkers = [];

    // Clear existing list
    const churchList = document.getElementById('churchList');
    churchList.innerHTML = '';

    if (churches.length === 0) {
        churchList.innerHTML = '<div class="no-results">Không tìm thấy nhà thờ nào có giờ lễ phù hợp</div>';
        return;
    }

    // Add new churches
    churches.forEach((church, index) => {
        // Create marker
        const marker = L.marker([church.lat, church.lng], {
            icon: L.divIcon({
                className: 'church-marker',
                html: '<i class="fas fa-church"></i>',
                iconSize: [30, 30]
            })
        }).addTo(map);

        // Add popup to marker
        marker.bindPopup(`
            <div class="church-popup">
                <h3>${church.name}</h3>
                <p><i class="fas fa-map-marker-alt"></i> ${church.address}</p>
                ${church.mass_times ? `<p><i class="fas fa-clock"></i> Giờ lễ: ${church.mass_times}</p>` : ''}
            </div>
        `);

        churchMarkers.push(marker);

        // Create church card
        const card = document.createElement('div');
        card.className = 'church-card';
        card.innerHTML = `
            <h3>${church.name}</h3>
            <p><i class="fas fa-map-marker-alt"></i> ${church.address}</p>
            ${church.mass_times ? `<p><i class="fas fa-clock"></i> Giờ lễ: ${church.mass_times}</p>` : ''}
            <button onclick="focusChurch(${index})" class="focus-btn">
                <i class="fas fa-map-marked-alt"></i> Xem trên bản đồ
            </button>
        `;
        churchList.appendChild(card);
    });

    // Fit map to show all markers if there are any
    if (churchMarkers.length > 0) {
        const group = new L.featureGroup(churchMarkers);
        map.fitBounds(group.getBounds().pad(0.1));
    }
}

// Focus on a specific church
function focusChurch(index) {
    const marker = churchMarkers[index];
    if (marker) {
        map.setView(marker.getLatLng(), 16);
        marker.openPopup();
    }
}

// Initialize time filter functionality
function initTimeFilter() {
    const timePills = document.querySelectorAll('.time-pill');
    const clearFilterBtn = document.getElementById('clearFilter');

    timePills.forEach(pill => {
        pill.addEventListener('click', () => {
            // Remove active class from all pills
            timePills.forEach(p => p.classList.remove('active'));
            // Add active class to clicked pill
            pill.classList.add('active');
            // Filter churches
            selectedTime = pill.dataset.time;
            filterChurches(selectedTime);
        });
    });

    clearFilterBtn.addEventListener('click', () => {
        timePills.forEach(p => p.classList.remove('active'));
        selectedTime = null;
        filterChurches(null);
    });
}

// Initialize everything when the page loads
document.addEventListener('DOMContentLoaded', () => {
    initMap();
    initTimeFilter();
});
