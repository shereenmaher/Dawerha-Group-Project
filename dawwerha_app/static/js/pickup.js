// Pickup page maps (Leaflet + OpenStreetMap)

// Default map center: Ramallah
const START = [31.9038, 35.2034];

function addTiles(map) {
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; OpenStreetMap contributors',
        referrerPolicy: 'strict-origin-when-cross-origin',
    }).addTo(map);
}

// 1. Show the chosen collector in the summary
function showSelected(radio) {
    document.getElementById('selectedCollector').textContent = radio.dataset.name;
    document.getElementById('selectedAmount').textContent = '₪' + radio.dataset.amount;
}

document.querySelectorAll('input[name="collector"]').forEach(function (radio) {
    radio.addEventListener('change', function () {
        showSelected(radio);
    });
});

// 2. Check the place is in the West Bank, then give it a name
// OpenStreetMap tells us the country, and our list (places.js) gives the name.
// Returns null if the place is outside the West Bank.
function findAddress(lat, lng, done) {
    const url = 'https://nominatim.openstreetmap.org/reverse?format=json&zoom=10&lat=' + lat + '&lon=' + lng;

    fetch(url)
        .then(function (response) {
            return response.json();
        })
        .then(function (data) {
            const country = (data.address || {}).country_code;

            // Palestine has the code "ps". Gaza is west of 34.6, so we skip it.
            if (country !== 'ps' || lng < 34.6) {
                done(null);
            } else {
                done(nearestPlace(lat, lng));
            }
        })
        .catch(function () {
            // No internet for the check: just give the name
            done(nearestPlace(lat, lng));
        });
}

// Show a green or red message under the map
function showLocationMsg(text, ok) {
    const msg = document.getElementById('locationMsg');
    msg.textContent = text;
    msg.className = 'small mb-3 ' + (ok ? 'text-success' : 'text-danger fw-semibold');
}

// 3. Address map with a pin the user can drag
const addressMap = L.map('addressMap').setView(START, 13);
addTiles(addressMap);

const homePin = L.marker(START, { draggable: true }).addTo(addressMap);
homePin.bindPopup('Drag me to your home').openPopup();

// The last place inside the West Bank
let lastGood = START;

// Save the pin location in the hidden inputs
function saveLocation(lat, lng) {
    document.getElementById('lat').value = lat;
    document.getElementById('lng').value = lng;
}

// Move the pin, check the place and write the address
function movePin(lat, lng) {
    homePin.setLatLng([lat, lng]);
    showLocationMsg('Finding the address…', true);

    findAddress(lat, lng, function (address) {
        if (address === null) {
            // Outside the West Bank: go back to the last good place
            homePin.setLatLng(lastGood);
            addressMap.setView(lastGood);
            showLocationMsg('This place is outside our area. Dawwerha works in the West Bank only.', false);
            return;
        }

        lastGood = [lat, lng];
        saveLocation(lat, lng);

        document.getElementById('address').value = address;
        showLocationMsg('Location set: ' + address, true);
    });
}

saveLocation(START[0], START[1]);

homePin.on('dragend', function () {
    const pos = homePin.getLatLng();
    movePin(pos.lat, pos.lng);
});

// Use my current location button
document.getElementById('myLocationBtn').addEventListener('click', function () {
    navigator.geolocation.getCurrentPosition(function (position) {
        const lat = position.coords.latitude;
        const lng = position.coords.longitude;
        addressMap.setView([lat, lng], 15);
        movePin(lat, lng);
    });
});

// 4. Collectors map
const collectorsMap = L.map('collectorsMap').setView(START, 12);
addTiles(collectorsMap);

const points = JSON.parse(document.getElementById('mapPoints').textContent);

points.forEach(function (point) {
    const marker = L.marker([point.lat, point.lng]).addTo(collectorsMap);
    marker.bindPopup(point.name);

    // Clicking a collector on the map chooses him
    marker.on('click', function () {
        const radio = document.getElementById('collector' + point.id);
        if (radio) {
            radio.checked = true;
            showSelected(radio);
        }
    });
});