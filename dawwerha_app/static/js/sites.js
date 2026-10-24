// Recycling sites map (Leaflet + OpenStreetMap)

// 1. Read the sites that the view sent to the page
const sites = JSON.parse(
    document.getElementById('mapData').textContent
);

// Find a site quickly by its id
const sitesById = {};

sites.forEach(function (site) {
    sitesById[site.id] = site;
});

// 2. Create the map, centered on Ramallah
const map = L.map('map').setView([31.9038, 35.2034], 13);

L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; OpenStreetMap contributors',
    // OpenStreetMap needs to know which website is asking for the map images
    referrerPolicy: 'strict-origin-when-cross-origin',
}).addTo(map);

// 3. Green recycle icon for the sites
const siteIcon = L.divIcon({
    className: '',
    html: '<span class="d-inline-block bg-success text-white rounded-2 p-2 lh-1 shadow"><i class="bi bi-recycle"></i></span>',
    iconSize: [32, 32],
    iconAnchor: [16, 32],
    popupAnchor: [0, -32],
});

// Make text safe before putting it inside the popup
function safeText(text) {
    const div = document.createElement('div');
    div.textContent = text || '';
    return div.innerHTML;
}

// What shows when you click a site on the map
function popupContent(site) {
    return `
        <div class="fw-bold">${safeText(site.name)}</div>

        <div class="bg-success bg-opacity-10 rounded-3 p-2 my-2 small">
            <div>
                <strong>Address:</strong> ${safeText(site.address)}
            </div>

            <div>
                <strong>Hours:</strong> ${safeText(site.hours)}
            </div>

            <div>
                <strong>Accepts:</strong> ${safeText(site.accepts.join(', ') || 'Not set yet')}
            </div>
        </div>

        <button type="button"
                class="btn btn-warning btn-sm w-100"
                data-directions="${site.id}">
            <i class="bi bi-sign-turn-right"></i> Directions
        </button>
    `;
}

// Give the chosen site's card a green border
function selectCard(siteId) {
    document.querySelectorAll('.site-card').forEach(function (card) {
        card.classList.remove('border-success', 'border-2');
    });

    const card = document.getElementById('site-' + siteId);

    if (card) {
        card.classList.add('border-success', 'border-2');
    }
}

// 4. Put a marker on the map for every site
const markers = {};

sites.forEach(function (site) {
    const marker = L.marker(
        [site.lat, site.lng],
        { icon: siteIcon }
    )
        .addTo(map)
        .bindPopup(popupContent(site));

    marker.on('click', function () {
        selectCard(site.id);
    });

    markers[site.id] = marker;
});

// Zoom the map so all the sites fit
if (sites.length > 0) {
    map.fitBounds(
        sites.map(function (site) {
            return [site.lat, site.lng];
        }),
        {
            padding: [40, 40],
            maxZoom: 14,
        }
    );
}

// 5. "Show on map" buttons: move to the site and open its popup
document.querySelectorAll('[data-show-site]').forEach(function (button) {
    button.addEventListener('click', function () {
        const marker = markers[button.dataset.showSite];

        if (marker) {
            map.setView(marker.getLatLng(), 15);
            marker.openPopup();
            selectCard(button.dataset.showSite);
        }
    });
});

// 6. Small key in the corner of the map
const legend = L.control({
    position: 'bottomleft'
});

legend.onAdd = function () {
    const div = L.DomUtil.create(
        'div',
        'bg-white rounded-pill shadow-sm px-3 py-1 small'
    );

    div.innerHTML =
        '<i class="bi bi-circle-fill text-primary"></i> You are here ' +
        '<i class="bi bi-square-fill text-success ms-2"></i> Recycling site';

    return div;
};

legend.addTo(map);

// 7. The user's location: blue dot and the distance to each site
let userLocation = null;

function showUserLocation(here) {
    L.circle(here, {
        radius: 300,
        weight: 0,
        fillColor: '#0d6efd',
        fillOpacity: 0.15
    }).addTo(map);

    L.circleMarker(here, {
        radius: 8,
        color: '#ffffff',
        weight: 3,
        fillColor: '#0d6efd',
        fillOpacity: 1
    })
        .addTo(map)
        .bindPopup('You are here');

    sites.forEach(function (site) {
        const km = map.distance(
            here,
            [site.lat, site.lng]
        ) / 1000;

        const distanceText = document.querySelector(
            '[data-distance="' + site.id + '"]'
        );

        if (distanceText) {
            distanceText.textContent =
                ' · ' + km.toFixed(1) + ' km';
        }
    });
}

// Get the user's location, then run "whenReady" with it
function getUserLocation(whenReady) {
    if (userLocation) {
        whenReady(userLocation);
        return;
    }

    if (!navigator.geolocation) {
        showRouteText(
            "Your browser can't share your location, so we can't show directions.",
            false
        );
        return;
    }

    navigator.geolocation.getCurrentPosition(
        function (position) {
            userLocation = [
                position.coords.latitude,
                position.coords.longitude
            ];

            showUserLocation(userLocation);
            whenReady(userLocation);
        },
        function () {
            showRouteText(
                'Please allow location access to see directions.',
                false
            );
        }
    );
}

// Ask for the location as soon as the page opens
getUserLocation(function () {});

// 8. Directions drawn on the map
const routeBox = document.getElementById('routeBox');
const routeText = document.getElementById('routeText');
const clearRouteButton = document.getElementById('clearRoute');

let routeLine = null;

// Show a message under the map
function showRouteText(text, showClearButton) {
    routeBox.classList.remove('d-none');
    routeText.textContent = text;

    if (showClearButton) {
        clearRouteButton.classList.remove('d-none');
    } else {
        clearRouteButton.classList.add('d-none');
    }
}

// Remove the route from the map
function clearRoute() {
    if (routeLine) {
        map.removeLayer(routeLine);
        routeLine = null;
    }

    routeBox.classList.add('d-none');
}

clearRouteButton.addEventListener('click', clearRoute);

// Ask OSRM for the driving route and draw it on the map
function showDirections(site) {
    getUserLocation(function (here) {
        showRouteText(
            'Finding the route to ' + site.name + '…',
            false
        );

        // OSRM wants the points as longitude,latitude
        const url =
            'https://router.project-osrm.org/route/v1/driving/' +
            here[1] + ',' + here[0] + ';' +
            site.lng + ',' + site.lat +
            '?overview=full&geometries=geojson';

        fetch(url)
            .then(function (response) {
                return response.json();
            })
            .then(function (data) {
                if (data.code !== 'Ok' || data.routes.length === 0) {
                    showRouteText(
                        "We couldn't find a route to " + site.name + '.',
                        false
                    );
                    return;
                }

                const route = data.routes[0];

                if (routeLine) {
                    map.removeLayer(routeLine);
                }

                routeLine = L.geoJSON(
                    route.geometry,
                    {
                        style: {
                            color: '#198754',
                            weight: 6,
                            opacity: 0.85
                        },
                    }
                ).addTo(map);

                map.closePopup();

                map.fitBounds(
                    routeLine.getBounds(),
                    {
                        padding: [40, 40]
                    }
                );

                selectCard(site.id);

                const km = (route.distance / 1000).toFixed(1);
                const minutes = Math.round(route.duration / 60);

                showRouteText(
                    'Route to ' + site.name + ': ' +
                    km + ' km, about ' +
                    minutes + ' min by car.',
                    true
                );
            })
            .catch(function () {
                showRouteText(
                    "We couldn't load the route. Please try again.",
                    false
                );
            });
    });
}

// Every "Directions" button (in the cards and in the map popups)
document.addEventListener('click', function (event) {
    const button = event.target.closest('[data-directions]');

    if (button) {
        const site = sitesById[button.dataset.directions];

        if (site) {
            showDirections(site);
        }
    }
});