// Live updates: ask the server every 10 seconds if something changed
// (a new request, accepted, rejected, completed...). If yes, reload the page.

// Only these pages show data that other people can change
const LIVE_PAGES = ['/', '/collector/', '/my-requests/'];

let lastKey = null;
let typing = false;

// Don't reload while the person is filling a form
document.addEventListener('input', function () {
    typing = true;
});

function checkUpdates() {
    fetch('/api/updates/')
        .then(function (response) {
            return response.json();
        })
        .then(function (data) {
            if (lastKey === null) {
                // First time: just remember the key
                lastKey = data.key;
            } else if (data.key !== lastKey && !typing) {
                location.reload();
            }
        })
        .catch(function () {
            // No internet for a moment: try again next time
        });
}

if (LIVE_PAGES.includes(location.pathname)) {
    checkUpdates();
    setInterval(checkUpdates, 10000);
}