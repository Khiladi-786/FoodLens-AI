/* ==========================================================================
   FoodLens AI — Interactive Client-Side JavaScript Application
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Theme Toggle Management
    initThemeToggle();

    // 2. Password Visibility Toggle
    initPasswordToggle();

    // 3. Drag and Drop File Upload Preview
    initDragAndDrop();

    // 4. Copy Text Clipboard Helper
    initCopyButtons();
});

/* --- Theme Management --- */
function initThemeToggle() {
    const themeBtn = document.getElementById('theme-toggle');
    const storedTheme = localStorage.getItem('foodlens_theme') || 'dark';
    
    document.documentElement.setAttribute('data-theme', storedTheme);
    updateThemeIcon(storedTheme);

    if (themeBtn) {
        themeBtn.addEventListener('click', () => {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('foodlens_theme', newTheme);
            updateThemeIcon(newTheme);
        });
    }
}

function updateThemeIcon(theme) {
    const themeBtn = document.getElementById('theme-toggle');
    if (themeBtn) {
        themeBtn.innerHTML = theme === 'light' ? '🌙' : '☀️';
        themeBtn.setAttribute('title', `Switch to ${theme === 'light' ? 'Dark' : 'Light'} Mode`);
    }
}

/* --- Password Toggle Helper --- */
function initPasswordToggle() {
    const toggleBtns = document.querySelectorAll('.password-toggle-btn');
    toggleBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const input = btn.previousElementSibling || document.getElementById(btn.dataset.target);
            if (input && input.type === 'password') {
                input.type = 'text';
                btn.textContent = 'Hide';
            } else if (input) {
                input.type = 'password';
                btn.textContent = 'Show';
            }
        });
    });
}

/* --- Drag and Drop Upload Preview --- */
function initDragAndDrop() {
    const dropzone = document.getElementById('upload-dropzone');
    const fileInput = document.getElementById('file-upload');
    const previewContainer = document.getElementById('preview-container');
    const previewImage = document.getElementById('preview-image');

    if (!dropzone || !fileInput) return;

    ['dragenter', 'dragover'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.add('dragover');
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.remove('dragover');
        }, false);
    });

    dropzone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files && files.length > 0) {
            fileInput.files = files;
            previewFile(files[0]);
        }
    });

    fileInput.addEventListener('change', function () {
        if (this.files && this.files[0]) {
            previewFile(this.files[0]);
        }
    });

    function previewFile(file) {
        if (previewImage && previewContainer) {
            const reader = new FileReader();
            reader.onload = function (e) {
                previewImage.src = e.target.result;
                previewContainer.style.display = 'block';
            };
            reader.readAsDataURL(file);
        }
    }
}

/* --- Global Camera Stream Management --- */
let activeCameraStream = null;

function openCameraModal() {
    const modal = document.getElementById('camera-modal');
    const video = document.getElementById('camera-feed');
    if (!modal || !video) return;

    navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } })
        .then(function (stream) {
            activeCameraStream = stream;
            video.srcObject = stream;
            modal.classList.add('active');
            document.addEventListener('keydown', handleCameraKeydown);
        })
        .catch(function (error) {
            alert("Camera access denied or unavailable: " + error);
        });
}

function closeCameraModal() {
    const modal = document.getElementById('camera-modal');
    if (activeCameraStream) {
        activeCameraStream.getTracks().forEach(track => track.stop());
        activeCameraStream = null;
    }
    if (modal) {
        modal.classList.remove('active');
    }
    document.removeEventListener('keydown', handleCameraKeydown);
}

function handleCameraKeydown(event) {
    if (event.code === 'Space') {
        event.preventDefault();
        captureCameraFrame();
    } else if (event.code === 'Escape') {
        closeCameraModal();
    }
}

function captureCameraFrame() {
    const video = document.getElementById('camera-feed');
    const canvas = document.getElementById('camera-canvas');
    const preview = document.getElementById('preview-image');
    const previewContainer = document.getElementById('preview-container');
    const capturedInput = document.getElementById('captured-image');
    const form = document.getElementById('upload-form');

    if (!video || !canvas || !form) return;

    const context = canvas.getContext('2d');
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    context.drawImage(video, 0, 0, canvas.width, canvas.height);

    const imageDataURL = canvas.toDataURL('image/png');

    if (preview) preview.src = imageDataURL;
    if (previewContainer) previewContainer.style.display = 'block';
    if (capturedInput) capturedInput.value = imageDataURL;

    closeCameraModal();

    // Automatically submit form after capture
    form.submit();
}

/* --- Clipboard Copy Utility --- */
function initCopyButtons() {
    const copyBtns = document.querySelectorAll('.copy-text-btn');
    copyBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetId = btn.dataset.target;
            const targetEl = document.getElementById(targetId);
            if (targetEl) {
                navigator.clipboard.writeText(targetEl.textContent.strip ? targetEl.textContent.strip() : targetEl.textContent).then(() => {
                    const origText = btn.textContent;
                    btn.textContent = 'Copied!';
                    setTimeout(() => { btn.textContent = origText; }, 2000);
                });
            }
        });
    });
}
