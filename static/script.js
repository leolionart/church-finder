let map;
let userMarker;
let churchMarkers = [];
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
            displayChurches(data.churches);
            document.getElementById('resultsTitle').textContent = 'Nhà thờ gần đây';
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

// Handle search panel visibility
function toggleSearchPanel() {
    const searchPanel = document.getElementById('searchPanel');
    searchPanel.classList.toggle('hidden');
}

// Handle time selection
function initTimeSelection() {
    const timePills = document.querySelectorAll('.time-pill');
    const timeInput = document.getElementById('timeSlot');

    timePills.forEach(pill => {
        pill.addEventListener('click', () => {
            // Remove active class from all pills
            timePills.forEach(p => p.classList.remove('active'));
            // Add active class to clicked pill
            pill.classList.add('active');
            // Set the time input value
            timeInput.value = pill.dataset.time;
            selectedTime = pill.dataset.time;
        });
    });

    timeInput.addEventListener('change', () => {
        selectedTime = timeInput.value;
        // Remove active class from all pills
        timePills.forEach(pill => pill.classList.remove('active'));
    });

    // Initialize search toggle
    document.getElementById('searchToggle').addEventListener('click', toggleSearchPanel);
}

// Search for churches
async function searchChurches() {
    if (!selectedTime && !document.getElementById('timeSlot').value) {
        alert('Vui lòng chọn giờ lễ');
        return;
    }

    const timeSlot = selectedTime || document.getElementById('timeSlot').value;
    const pos = userMarker.getLatLng();

    try {
        const response = await fetch('/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                time_slot: timeSlot,
                lat: pos.lat,
                lng: pos.lng
            }),
        });

        const data = await response.json();
        if (data.success) {
            displayChurches(data.churches);
            document.getElementById('resultsTitle').textContent = 
                `Kết quả tìm kiếm (${data.churches.length})`;
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Có lỗi xảy ra khi tìm kiếm nhà thờ');
    }
}

// Display churches on map and in list
function displayChurches(churches) {
    // Clear existing markers
    churchMarkers.forEach(marker => marker.remove());
    churchMarkers = [];
    
    // Clear church list
    const churchList = document.getElementById('churchList');
    churchList.innerHTML = '';
    
    if (churches.length === 0) {
        churchList.innerHTML = '<div class="no-results"><i class="fas fa-church"></i><p>Không tìm thấy nhà thờ nào trong khoảng thời gian này</p></div>';
        return;
    }

    churches.forEach(church => {
        // Add marker to map
        if (church.lat && church.lng) {
            const marker = L.marker([church.lat, church.lng])
                .bindPopup(`
                    <strong>${church.name}</strong><br>
                    ${church.address}<br>
                    <strong>Giờ lễ:</strong> ${church.mass_times.join(', ')}
                `)
                .addTo(map);
            churchMarkers.push(marker);
        }

        // Add to list
        const churchElement = document.createElement('div');
        churchElement.className = 'church-item';
        churchElement.innerHTML = `
            <div class="church-image">
                <i class="fas fa-church"></i>
            </div>
            <div class="church-info">
                <h5>${church.name}</h5>
                <p><i class="fas fa-map-marker-alt"></i> ${church.address}</p>
                <p><i class="fas fa-clock"></i> Giờ lễ: ${church.mass_times.join(', ')}</p>
                <p><i class="fas fa-road"></i> Cách ${church.distance} km</p>
            </div>
        `;
        
        // Add click event to center map on church
        churchElement.addEventListener('click', () => {
            if (church.lat && church.lng) {
                map.setView([church.lat, church.lng], 15);
                const marker = churchMarkers.find(m => 
                    m.getLatLng().lat === church.lat && 
                    m.getLatLng().lng === church.lng
                );
                if (marker) {
                    marker.openPopup();
                }
            }
        });
        
        churchList.appendChild(churchElement);
    });

    // Fit map bounds to show all markers
    if (churchMarkers.length > 0) {
        const group = new L.featureGroup(churchMarkers);
        map.fitBounds(group.getBounds().pad(0.1));
    }
}

// Initialize everything when the page loads
document.addEventListener('DOMContentLoaded', () => {
    initMap();
    initTimeSelection();
});
