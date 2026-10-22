const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

// When the user picks a photo from the device or the camera
document.getElementById('photoInput').addEventListener('change', function () {
    sendPhoto(this.files[0]);
});

document.getElementById('cameraInput').addEventListener('change', function () {
    sendPhoto(this.files[0]);
});

function sendPhoto(file) {
    if (!file) {
        return;
    }

    // Show the photo
    const preview = document.getElementById('preview');
    preview.src = URL.createObjectURL(file);
    preview.classList.remove('d-none');
    document.getElementById('uploadText').classList.add('d-none');

    // Show loading and hide old results
    document.getElementById('loading').classList.remove('d-none');
    document.getElementById('errorBox').classList.add('d-none');
    document.getElementById('result').classList.add('d-none');

    const formData = new FormData();
    formData.append('image', file);

    fetch('/api/scan/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken
        },
        body: formData
    })
        .then(function (response) {
            return response.json();
        })
        .then(function (data) {
            document.getElementById('loading').classList.add('d-none');

            if (data.error) {
                showError(data.error);
            } else {
                showResult(data);
            }
        })
        .catch(function () {
            document.getElementById('loading').classList.add('d-none');
            showError("Something went wrong, please try again");
        });
}

function showResult(data) {
    document.getElementById('emptyResult').classList.add('d-none');
    document.getElementById('result').classList.remove('d-none');

    document.getElementById('itemName').textContent = data.item_name;
    document.getElementById('materialName').textContent = data.material;
    document.getElementById('itemWeight').textContent =
        Math.round(data.weight_kg * 1000) + ' g';
    document.getElementById('itemTip').textContent = data.tip;
    document.getElementById('scanId').value = data.id;

    // Recyclable or not
    if (data.recyclable) {
        document.getElementById('recyclableBox').classList.remove('d-none');
        document.getElementById('notRecyclableBox').classList.add('d-none');
        document.getElementById('addToBagBtn').classList.remove('d-none');
    } else {
        document.getElementById('recyclableBox').classList.add('d-none');
        document.getElementById('notRecyclableBox').classList.remove('d-none');
        document.getElementById('addToBagBtn').classList.add('d-none');
    }
}

function showError(message) {
    const box = document.getElementById('errorBox');
    box.textContent = message;
    box.classList.remove('d-none');
}