const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
const video = document.getElementById('video');
let stream = null;
 
// When the user picks a photo from the device or the phone camera
document.getElementById('photoInput').addEventListener('change', function () {
    sendPhoto(this.files[0]);
});
 
document.getElementById('cameraInput').addEventListener('change', function () {
    sendPhoto(this.files[0]);
});
 
// Open the live camera (laptop or phone)
document.getElementById('cameraBtn').addEventListener('click', function () {
    if (!navigator.mediaDevices) {
        document.getElementById('cameraInput').click();
        return;
    }
    navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } })
        .then(function (s) {
            stream = s;
            video.srcObject = stream;
            document.getElementById('cameraBox').classList.remove('d-none');
        })
        .catch(function () {
            document.getElementById('cameraInput').click();
        });
});
 
// Take a photo from the live camera
document.getElementById('snapBtn').addEventListener('click', function () {
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d').drawImage(video, 0, 0);
 
    canvas.toBlob(function (blob) {
        const file = new File([blob], 'photo.jpg', { type: 'image/jpeg' });
        closeCamera();
        sendPhoto(file);
    }, 'image/jpeg', 0.9);
});
 
document.getElementById('closeCameraBtn').addEventListener('click', closeCamera);
 
function closeCamera() {
    if (stream) {
        stream.getTracks().forEach(function (track) {
            track.stop();
        });
        stream = null;
    }
    document.getElementById('cameraBox').classList.add('d-none');
}
 
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
 
    resizePhoto(file, uploadPhoto);
}
 
// Make the photo smaller so it uploads faster
function resizePhoto(file, callback) {
    const img = new Image();
    img.onload = function () {
        const max = 800;
        let width = img.width;
        let height = img.height;
 
        if (width > max || height > max) {
            const scale = max / Math.max(width, height);
            width = Math.round(width * scale);
            height = Math.round(height * scale);
        }
 
        const canvas = document.createElement('canvas');
        canvas.width = width;
        canvas.height = height;
        canvas.getContext('2d').drawImage(img, 0, 0, width, height);
 
        canvas.toBlob(function (blob) {
            callback(new File([blob], 'photo.jpg', { type: 'image/jpeg' }));
        }, 'image/jpeg', 0.8);
    };
    img.src = URL.createObjectURL(file);
}
 
// Send the photo to the server
function uploadPhoto(file) {
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
 
    // Reset the bag button for the new result
    const addBtn = document.getElementById('addToBagBtn');
    addBtn.disabled = false;
    addBtn.innerHTML = '<i class="bi bi-bag"></i> Add to recycling bag';
 
    // Recyclable or not
    if (data.recyclable) {
        document.getElementById('recyclableBox').classList.remove('d-none');
        document.getElementById('notRecyclableBox').classList.add('d-none');
        addBtn.classList.remove('d-none');
    } else {
        document.getElementById('recyclableBox').classList.add('d-none');
        document.getElementById('notRecyclableBox').classList.remove('d-none');
        addBtn.classList.add('d-none');
    }
}
 
function showError(message) {
    const box = document.getElementById('errorBox');
    box.textContent = message;
    box.classList.remove('d-none');
}
 
// Add the result to the recycling bag
document.getElementById('addToBagBtn').addEventListener('click', function () {
    const button = this;
    const formData = new FormData();
    formData.append('scan_id', document.getElementById('scanId').value);
 
    button.disabled = true;
 
    fetch('/api/bag/add/', {
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
            if (data.error) {
                button.disabled = false;
                showError(data.error);
            } else {
                button.innerHTML = '<i class="bi bi-check-lg"></i> Added to your bag';
            }
        })
        .catch(function () {
            button.disabled = false;
            showError("Something went wrong, please try again");
        });
});