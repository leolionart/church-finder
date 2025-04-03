let map;
let userMarker;
let userLocation = null;
let watchId = null;
let churchMarkers = [];
let allChurches = [];
let selectedTime = null;
let isPanelVisible = false;
const defaultLocation = { lat: 10.7769, lng: 106.7009 }; // Ho Chi Minh City center

// Calculate distance between two points in km
function calculateDistance(lat1, lon1, lat2, lon2) {
    const R = 6371; // Radius of the earth in km
    const dLat = deg2rad(lat2 - lat1);
    const dLon = deg2rad(lon2 - lon1);
    const a = 
        Math.sin(dLat/2) * Math.sin(dLat/2) +
        Math.cos(deg2rad(lat1)) * Math.cos(deg2rad(lat2)) * 
        Math.sin(dLon/2) * Math.sin(dLon/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    return R * c;
}

function deg2rad(deg) {
    return deg * (Math.PI/180);
}

// Format distance
function formatDistance(distance) {
    if (distance < 1) {
        return Math.round(distance * 1000) + 'm';
    }
    return Math.round(distance * 10) / 10 + 'km';
}

// Initialize map
function initMap() {
    map = L.map('map').setView([defaultLocation.lat, defaultLocation.lng], 13);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: ' OpenStreetMap contributors'
    }).addTo(map);

    // Start watching user's location
    startLocationWatch();
}

// Start watching user's location
function startLocationWatch() {
    if (!navigator.geolocation) {
        console.log("Geolocation is not supported by this browser.");
        loadDefaultChurches(defaultLocation.lat, defaultLocation.lng);
        return;
    }

    // Options for high accuracy
    const options = {
        enableHighAccuracy: true,
        timeout: 5000,
        maximumAge: 0
    };

    // Watch position
    watchId = navigator.geolocation.watchPosition(
        updateUserLocation,
        handleLocationError,
        options
    );
}

// Update user location
function updateUserLocation(position) {
    const pos = {
        lat: position.coords.latitude,
        lng: position.coords.longitude,
        accuracy: position.coords.accuracy
    };

    userLocation = pos;

    // Update or create user marker with accuracy circle
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

        // Add popup to user marker
        userMarker.bindPopup('Vị trí của bạn');
    }

    // Center map on first location fix
    if (!map.userLocationInitialized) {
        map.setView([pos.lat, pos.lng], 15);
        map.userLocationInitialized = true;
    }

    // Load and sort churches by distance
    loadDefaultChurches(pos.lat, pos.lng);
}

// Handle location errors
function handleLocationError(error) {
    console.log("Error getting location:", error);
    loadDefaultChurches(defaultLocation.lat, defaultLocation.lng);
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
            allChurches = data.churches.map(church => ({
                ...church,
                distance: calculateDistance(lat, lng, church.lat, church.lng)
            }));
            
            // Sort churches by distance
            allChurches.sort((a, b) => a.distance - b.distance);
            
            if (selectedTime) {
                filterChurches(selectedTime);
            } else {
                displayChurches(allChurches);
            }
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

// Refresh church data
async function refreshChurchData() {
    const refreshBtn = document.getElementById('refreshData');
    refreshBtn.classList.add('loading');
    refreshBtn.disabled = true;

    try {
        const response = await fetch('/refresh-data', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });

        const data = await response.json();
        if (data.success) {
            if (userLocation) {
                allChurches = data.churches.map(church => ({
                    ...church,
                    distance: calculateDistance(userLocation.lat, userLocation.lng, church.lat, church.lng)
                }));
                allChurches.sort((a, b) => a.distance - b.distance);
            } else {
                allChurches = data.churches;
            }

            if (selectedTime) {
                filterChurches(selectedTime);
            } else {
                displayChurches(allChurches);
            }
            alert('Dữ liệu đã được cập nhật thành công!');
        } else {
            throw new Error(data.error || 'Không thể cập nhật dữ liệu');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Lỗi khi cập nhật dữ liệu: ' + error.message);
    } finally {
        refreshBtn.classList.remove('loading');
        refreshBtn.disabled = false;
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
                ${church.distance ? `<p><i class="fas fa-route"></i> Cách ${formatDistance(church.distance)}</p>` : ''}
                ${church.mass_times ? `<p><i class="fas fa-clock"></i> Giờ lễ: ${church.mass_times}</p>` : ''}
                ${church.last_updated ? `<p><i class="fas fa-calendar-alt"></i> Cập nhật: ${church.last_updated}</p>` : ''}
            </div>
        `);

        churchMarkers.push(marker);

        // Create church card
        const card = document.createElement('div');
        card.className = 'church-card';
        card.innerHTML = `
            <h3>${church.name}</h3>
            <p><i class="fas fa-map-marker-alt"></i> ${church.address}</p>
            ${church.distance ? `<p><i class="fas fa-route"></i> Cách ${formatDistance(church.distance)}</p>` : ''}
            ${church.mass_times ? `<p><i class="fas fa-clock"></i> Giờ lễ: ${church.mass_times}</p>` : ''}
            ${church.last_updated ? `<p><i class="fas fa-calendar-alt"></i> Cập nhật: ${church.last_updated}</p>` : ''}
            <button onclick="focusChurch(${index})" class="focus-btn">
                <i class="fas fa-map-marked-alt"></i> Xem trên bản đồ
            </button>
        `;
        churchList.appendChild(card);
    });

    // Update results title with distance if available
    if (userLocation) {
        document.getElementById('resultsTitle').textContent = 
            selectedTime ? 
            `Nhà thờ có lễ lúc ${selectedTime} (${churches.length})` :
            `Nhà thờ gần bạn (${churches.length})`;
    }

    // Fit map to show all markers and user location if available
    if (churchMarkers.length > 0) {
        const markers = [...churchMarkers];
        if (userMarker) markers.push(userMarker);
        const group = new L.featureGroup(markers);
        map.fitBounds(group.getBounds().pad(0.1));
    }
}

// Focus on a specific church
function focusChurch(index) {
    const marker = churchMarkers[index];
    if (marker) {
        map.setView(marker.getLatLng(), 16);
        marker.openPopup();
        // On mobile, close the panel after focusing
        if (window.innerWidth <= 768) {
            togglePanel();
        }
    }
}

// Toggle panel visibility on mobile
function togglePanel() {
    const panel = document.getElementById('churchesPanel');
    const toggleBtn = document.getElementById('togglePanel');
    isPanelVisible = !isPanelVisible;
    
    if (isPanelVisible) {
        panel.classList.add('active');
        toggleBtn.innerHTML = '<i class="fas fa-times"></i>';
    } else {
        panel.classList.remove('active');
        toggleBtn.innerHTML = '<i class="fas fa-list"></i>';
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

// Clean up when page unloads
window.addEventListener('beforeunload', () => {
    if (watchId !== null) {
        navigator.geolocation.clearWatch(watchId);
    }
});

// Initialize everything when the page loads
document.addEventListener('DOMContentLoaded', () => {
    initMap();
    initTimeFilter();
    
    // Add refresh button handler
    const refreshBtn = document.getElementById('refreshData');
    refreshBtn.addEventListener('click', refreshChurchData);

    // Add toggle panel button handler
    const toggleBtn = document.getElementById('togglePanel');
    toggleBtn.addEventListener('click', togglePanel);

    // Handle window resize
    window.addEventListener('resize', () => {
        if (window.innerWidth > 768 && isPanelVisible) {
            document.getElementById('churchesPanel').classList.remove('active');
            toggleBtn.innerHTML = '<i class="fas fa-list"></i>';
            isPanelVisible = false;
        }
    });
});
