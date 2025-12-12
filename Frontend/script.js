/**
 * 🌿 Crop Portal - Main Application Script
 * Version: Final (With Real Google Auth)
 */

// ==========================================
// 🌍 REAL GOOGLE AUTHENTICATION LOGIC
// ==========================================

// 1. Decode Google Token
function decodeJwtResponse(token) {
    var base64Url = token.split('.')[1];
    var base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    var jsonPayload = decodeURIComponent(window.atob(base64).split('').map(function(c) {
        return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
    }).join(''));
    return JSON.parse(jsonPayload);
}

// 2. Handle Google Success
function handleCredentialResponse(response) {
    console.log("Google Response Received.");
    try {
        const responsePayload = decodeJwtResponse(response.credential);

        // Create User Object
        const googleUser = {
            name: responsePayload.name,
            email: responsePayload.email,
            password: "google-oauth-login", 
            profilePic: responsePayload.picture 
        };

        // Save to Session
        localStorage.setItem('currentUser', JSON.stringify(googleUser));
        localStorage.setItem('user_' + responsePayload.email, JSON.stringify(googleUser));

        // Redirect
        if (typeof Swal !== 'undefined') {
            Swal.fire({
                icon: 'success',
                title: 'Signed in with Google',
                text: `Welcome, ${responsePayload.name}!`,
                timer: 1500,
                showConfirmButton: false
            }).then(() => { window.location.href = 'dashboard.html'; });
        } else {
            window.location.href = 'dashboard.html';
        }

    } catch (error) {
        console.error("Google Auth Error:", error);
        alert("Login failed. Please try again.");
    }
}

// --- CONFIGURATION ---
const CONFIG = {
    API_URL: 'http://127.0.0.1:5000',
    DEMO_MODE: true, 
    ANIMATION_SPEED: 2000,
    MAX_FILE_SIZE: 5 * 1024 * 1024, // 5MB
    ALLOWED_FORMATS: ['image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/bmp']
};

let uploadModalInstance, resultModalInstance;
let lastUploadedFile = null;

// ==========================================
// 🖼️ IMAGE UPLOAD & ANALYSIS MODULE
// ==========================================

function initImageUpload() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    const previewArea = document.getElementById('previewArea');
    const imagePreview = document.getElementById('imagePreview');
    const analyzeButton = document.getElementById('analyzeButton');
    const analysisSpinner = document.getElementById('analysisSpinner');

    if (!uploadArea || !fileInput) return; // Skip if elements don't exist

    // Drag & Drop Handlers
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = '#28a745';
        uploadArea.style.backgroundColor = 'rgba(40, 167, 69, 0.05)';
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.style.borderColor = '#dee2e6';
        uploadArea.style.backgroundColor = 'transparent';
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = '#dee2e6';
        uploadArea.style.backgroundColor = 'transparent';
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFileSelect(files[0]);
        }
    });

    // Click to Upload
    uploadArea.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileSelect(e.target.files[0]);
        }
    });

    function handleFileSelect(file) {
        // Validate file type
        if (!CONFIG.ALLOWED_FORMATS.includes(file.type)) {
            Swal.fire({
                icon: 'error',
                title: 'Invalid Format',
                text: 'Please upload an image (PNG, JPG, GIF, BMP)',
                confirmButtonColor: '#28a745'
            });
            return;
        }

        // Validate file size
        if (file.size > CONFIG.MAX_FILE_SIZE) {
            Swal.fire({
                icon: 'error',
                title: 'File Too Large',
                text: 'Maximum file size is 5MB',
                confirmButtonColor: '#28a745'
            });
            return;
        }

        lastUploadedFile = file;

        // Show preview
        const reader = new FileReader();
        reader.onload = (e) => {
            imagePreview.src = e.target.result;
            uploadArea.style.display = 'none';
            previewArea.classList.remove('d-none');
        };
        reader.readAsDataURL(file);
    }

    // Analyze Button Handler
    if (analyzeButton) {
        analyzeButton.addEventListener('click', async () => {
            if (!lastUploadedFile) {
                Swal.fire({
                    icon: 'warning',
                    title: 'No File Selected',
                    text: 'Please upload an image first',
                    confirmButtonColor: '#28a745'
                });
                return;
            }

            // Show spinner, hide button
            analyzeButton.style.display = 'none';
            analysisSpinner.classList.remove('d-none');

            try {
                const formData = new FormData();
                formData.append('imageFile', lastUploadedFile);

                const response = await fetch(`${CONFIG.API_URL}/api/detect`, {
                    method: 'POST',
                    body: formData
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.error || 'Analysis failed');
                }

                const result = await response.json();

                // Display results
                displayResults(result);

            } catch (error) {
                console.error('Error:', error);
                Swal.fire({
                    icon: 'error',
                    title: 'Analysis Failed',
                    text: error.message || 'Failed to analyze image. Please try again.',
                    confirmButtonColor: '#dc3545'
                });
            } finally {
                // Reset UI
                analyzeButton.style.display = 'block';
                analysisSpinner.classList.add('d-none');
            }
        });
    }
}

function displayResults(result) {
    const resultImage = document.getElementById('resultImage');
    const resultDisease = document.getElementById('resultDisease');
    const confidenceBadge = document.getElementById('confidenceBadge');
    const resultDescription = document.getElementById('resultDescription');
    const resultTreatment = document.getElementById('resultTreatment');

    if (!resultImage) return;

    // Populate result modal
    resultImage.src = lastUploadedFile ? URL.createObjectURL(lastUploadedFile) : '';
    resultDisease.textContent = result.disease || 'Unknown';
    confidenceBadge.textContent = `${Math.round((result.confidence || 0) * 100)}% Confidence`;
    resultDescription.textContent = result.description || 'No description available';

    // Clear and populate treatment list
    resultTreatment.innerHTML = '';
    if (result.treatment && Array.isArray(result.treatment)) {
        result.treatment.forEach(treatment => {
            const li = document.createElement('li');
            li.className = 'list-group-item';
            li.textContent = treatment;
            resultTreatment.appendChild(li);
        });
    }

    // Show result modal
    if (resultModalInstance) {
        // Close upload modal first
        if (uploadModalInstance) uploadModalInstance.hide();
        
        // Show results
        resultModalInstance.show();
    }
}

// ==========================================
// 1. INITIALIZATION & DOM EVENTS
// ==========================================
document.addEventListener('DOMContentLoaded', () => {
    
    const uploadModalEl = document.getElementById('uploadModal');
    if (uploadModalEl) uploadModalInstance = new bootstrap.Modal(uploadModalEl);
    
    const resultModalEl = document.getElementById('resultModal');
    if (resultModalEl) resultModalInstance = new bootstrap.Modal(resultModalEl);

    initHeroLoader();
    initPasswordToggles();
    initDashboardCharts();
    initImageUpload();

    // --- A. REGISTER PAGE LOGIC ---
    const regNameInput = document.getElementById('regName');
    const regButton = document.querySelector('.auth-form-side button.btn-success');

    if (regNameInput && regButton) {
        regButton.removeAttribute('onclick');
        regButton.addEventListener('click', (e) => {
            e.preventDefault();
            const name = document.getElementById('regName').value;
            const email = document.getElementById('regEmail').value;
            const pass = document.getElementById('regPass').value;

            if(!name || !email || !pass) {
                Swal.fire({ icon: 'error', title: 'Oops...', text: 'Please fill in all fields!', confirmButtonColor: '#28a745' });
                return;
            }

            const userData = { name: name, email: email, password: pass };
            localStorage.setItem('user_' + email, JSON.stringify(userData));

            regButton.disabled = true;
            regButton.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Creating Account...';
            
            setTimeout(() => {
                Swal.fire({
                    icon: 'success',
                    title: 'Account Created!',
                    text: 'You can now log in.',
                    confirmButtonColor: '#28a745'
                }).then(() => { window.location.href = 'login.html'; });
            }, 1500);
        });
    }

    // --- B. LOGIN PAGE LOGIC (Standard Email/Pass) ---
    const loginForm = document.getElementById('loginForm');

    if (loginForm) {
        loginForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const email = document.getElementById('loginEmail').value;
            const password = document.getElementById('loginPassword').value;
            const rememberMe = document.getElementById('rememberMe')?.checked;
            const btn = loginForm.querySelector('button[type="submit"]');
            const originalText = btn.innerHTML;

            if (!email || !password) {
                Swal.fire({ icon: 'warning', text: 'Please fill in both fields.', confirmButtonColor: '#28a745' });
                return;
            }

            btn.disabled = true;
            btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Verifying...';

            setTimeout(() => {
                const storedUser = JSON.parse(localStorage.getItem('user_' + email));

                if (storedUser && storedUser.password === password) {
                    if (rememberMe) {
                        localStorage.setItem('currentUser', JSON.stringify(storedUser));
                    } else {
                        sessionStorage.setItem('currentUser', JSON.stringify(storedUser));
                    }
                    
                    Swal.fire({
                        icon: 'success',
                        title: 'Welcome back!',
                        text: 'Redirecting to dashboard...',
                        timer: 1500,
                        showConfirmButton: false
                    }).then(() => { window.location.href = 'dashboard.html'; });
                } else {
                    btn.disabled = false;
                    btn.innerHTML = originalText;
                    Swal.fire({
                        icon: 'error',
                        title: 'Login Failed',
                        text: 'Invalid email or password.',
                        confirmButtonColor: '#dc3545'
                    });
                }
            }, 1500);
        });
    }

    // --- C. DASHBOARD PROTECTION ---
    if (window.location.pathname.includes('dashboard.html') || window.location.pathname.includes('profile.html')) {
        const currentUser = JSON.parse(localStorage.getItem('currentUser')) || 
                            JSON.parse(sessionStorage.getItem('currentUser'));
        
        if (!currentUser) {
            window.location.href = 'login.html';
        } else {
            const welcomeText = document.querySelector('.navbar-text');
            if(welcomeText) welcomeText.textContent = `Welcome, ${currentUser.name}!`;
        }
        
        const logoutLinks = document.querySelectorAll('a[href="index.html"]');
        logoutLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                if(link.innerHTML.includes("Logout")) {
                    e.preventDefault();
                    localStorage.removeItem('currentUser');
                    sessionStorage.removeItem('currentUser');
                    window.location.href = 'index.html';
                }
            });
        });
    }
});

// --- UTILS ---
const themeToggle = document.getElementById("themeToggle");
const html = document.documentElement;
if (themeToggle) {
    const icon = themeToggle.querySelector("i");
    const savedTheme = localStorage.getItem("theme") || "light";
    html.setAttribute("data-theme", savedTheme);
    updateThemeIcon(savedTheme, icon);

    themeToggle.addEventListener("click", () => {
        const currentTheme = html.getAttribute("data-theme");
        const newTheme = currentTheme === "light" ? "dark" : "light";
        html.setAttribute("data-theme", newTheme);
        localStorage.setItem("theme", newTheme);
        updateThemeIcon(newTheme, icon);
    });
}

function updateThemeIcon(theme, icon) {
    if(!icon) return;
    if (theme === "dark") {
        icon.classList.remove("bi-brightness-high-fill");
        icon.classList.add("bi-moon-stars-fill");
    } else {
        icon.classList.remove("bi-moon-stars-fill");
        icon.classList.add("bi-brightness-high-fill");
    }
}

function initHeroLoader() {
    const heroSection = document.querySelector('.hero-section');
    if (heroSection && heroSection.dataset.bg) {
        const img = new Image();
        img.src = heroSection.dataset.bg;
        img.onload = () => heroSection.style.setProperty('--bg-image', `url(${heroSection.dataset.bg})`);
    }
}

function initPasswordToggles() {
    const toggles = document.querySelectorAll('.password-toggle');
    toggles.forEach(toggle => {
        toggle.addEventListener('click', () => {
            const input = toggle.previousElementSibling;
            if (input && input.type) {
                input.type = input.type === 'password' ? 'text' : 'password';
                toggle.classList.toggle('bi-eye');
                toggle.classList.toggle('bi-eye-slash');
            }
        });
    });
}

function initDashboardCharts() {
    const ctx = document.getElementById('diseaseChart');
    if (ctx && typeof Chart !== 'undefined') {
        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Healthy', 'Early Blight', 'Common Rust', 'Mosaic Virus'],
                datasets: [{ data: [12, 5, 3, 2], backgroundColor: ['#28a745', '#dc3545', '#ffc107', '#17a2b8'], borderWidth: 0 }]
            },
            options: { responsive: true, plugins: { legend: { position: 'bottom' } } }
        });
    }
}

const supportForm = document.getElementById('supportPageForm');
if (supportForm) {
    supportForm.addEventListener('submit', (e) => {
        e.preventDefault(); 
        const btn = supportForm.querySelector('button[type="submit"]');
        const originalText = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Sending Ticket...';

        setTimeout(() => {
            supportForm.reset();
            btn.disabled = false;
            btn.innerHTML = '<i class="bi bi-check-circle"></i> Sent!';
            setTimeout(() => { btn.innerHTML = originalText; }, 3000);
            
            const isDarkMode = document.documentElement.getAttribute('data-theme') === 'dark';
            if(typeof Swal !== 'undefined') {
                Swal.fire({
                    title: 'Ticket Created!',
                    text: 'Ticket #2938 has been submitted.',
                    icon: 'success',
                    confirmButtonColor: '#28a745',
                    background: isDarkMode ? '#2d2d2d' : '#ffffff',
                    color: isDarkMode ? '#ffffff' : '#545454'
                });
            }
        }, 1500);
    });
}