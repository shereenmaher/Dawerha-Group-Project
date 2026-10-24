// Collector dashboard

const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

// 1. Accept or reject a request with Fetch (AJAX)
document.querySelectorAll('.status-btn').forEach(function (button) {
    button.addEventListener('click', function () {
        const formData = new FormData();
        formData.append('status', button.dataset.status);

        fetch('/api/requests/' + button.dataset.id + '/status/', {
            method: 'POST',
            headers: { 'X-CSRFToken': csrfToken },
            body: formData
        })
            .then(function (response) {
                return response.json();
            })
            .then(function (data) {
                if (data.error) {
                    showError(data.error);
                } else if (data.status === 'accepted') {
                    // Reload to show the "Complete a pickup" form
                    location.reload();
                } else {
                    // Rejected: remove the row and update the number
                    document.getElementById('request' + data.id).remove();
                    const count = document.getElementById('newCount');
                    count.textContent = parseInt(count.textContent) - 1;
                }
            })
            .catch(function () {
                showError("Something went wrong, please try again");
            });
    });
});

function showError(message) {
    const box = document.getElementById('requestError');
    box.textContent = message;
    box.classList.remove('d-none');
}

// 2. Calculate the amount to pay while the collector types the real weight
document.querySelectorAll('.complete-form').forEach(function (form) {
    function updateAmount() {
        let amount = 0;
        form.querySelectorAll('.real-weight').forEach(function (input) {
            amount += (parseFloat(input.value) || 0) * parseFloat(input.dataset.price);
        });
        form.querySelector('.amount').textContent = amount.toFixed(2);
    }

    form.querySelectorAll('.real-weight').forEach(function (input) {
        input.addEventListener('input', updateAmount);
    });
    updateAmount();
});

// 3. Check the place is in the West Bank, then give it a name
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

// 4. Map for the collector's location (Leaflet + OpenStreetMap)
const latInput = document.getElementById('lat');
const lngInput = document.getElementById('lng');

// Start from the saved location, or Ramallah
let start = [31.9038, 35.2034];
if (latInput.value && lngInput.value) {
    start = [parseFloat(latInput.value), parseFloat(lngInput.value)];
}

const myMap = L.map('myMap').setView(start, 13);
L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; OpenStreetMap contributors',
    referrerPolicy: 'strict-origin-when-cross-origin',
}).addTo(myMap);

const pin = L.marker(start, { draggable: true }).addTo(myMap);

// The last place inside the West Bank
let lastGood = start;

function saveLocation(lat, lng) {
    latInput.value = lat;
    lngInput.value = lng;
}

// Move the pin, check the place and write the address
function movePin(lat, lng) {
    pin.setLatLng([lat, lng]);
    showLocationMsg('Finding the address…', true);

    findAddress(lat, lng, function (address) {
        if (address === null) {
            // Outside the West Bank: go back to the last good place
            pin.setLatLng(lastGood);
            myMap.setView(lastGood);
            showLocationMsg('This place is outside our area. Dawwerha works in the West Bank only.', false);
            return;
        }

        lastGood = [lat, lng];
        saveLocation(lat, lng);

        document.getElementById('cAddress').value = address;
        showLocationMsg('Location set: ' + address + '. Click "Save changes" to keep it.', true);
    });
}

pin.on('dragend', function () {
    const pos = pin.getLatLng();
    movePin(pos.lat, pos.lng);
});

document.getElementById('myLocationBtn').addEventListener('click', function () {
    navigator.geolocation.getCurrentPosition(function (position) {
        const lat = position.coords.latitude;
        const lng = position.coords.longitude;
        myMap.setView([lat, lng], 15);
        movePin(lat, lng);
    });
});