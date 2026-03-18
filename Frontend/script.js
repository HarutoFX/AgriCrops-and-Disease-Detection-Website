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
            profilePic: responsePayload.picture,
            role: responsePayload.email === ADMIN_EMAIL ? 'admin' : 'user'
        };

        // Save to Session
        setCurrentUser(googleUser, true);
        localStorage.setItem('user_' + responsePayload.email, JSON.stringify(googleUser));

        // Redirect
        if (typeof Swal !== 'undefined') {
            Swal.fire({
                icon: 'success',
                title: 'Signed in with Google',
                text: `Welcome, ${responsePayload.name}!`,
                timer: 1500,
                showConfirmButton: false
            }).then(() => { window.location.href = hasValidAdminSession(googleUser) ? 'admin.html' : 'dashboard.html'; });
        } else {
            window.location.href = hasValidAdminSession(googleUser) ? 'admin.html' : 'dashboard.html';
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
const ADMIN_EMAIL = 'admin@cropportal.com';
const ADMIN_PASSWORD = 'admin123';
const ADMIN_SESSION_KEY = 'adminSession';

function ensureAdminSeed() {
    const existingAdmin = JSON.parse(localStorage.getItem(`user_${ADMIN_EMAIL}`));
    if (existingAdmin) return;

    const adminUser = {
        name: 'Crop Portal Admin',
        email: ADMIN_EMAIL,
        password: ADMIN_PASSWORD,
        role: 'admin',
        profilePic: ''
    };

    localStorage.setItem(`user_${ADMIN_EMAIL}`, JSON.stringify(adminUser));
}

function getCurrentUser() {
    return JSON.parse(localStorage.getItem('currentUser')) ||
           JSON.parse(sessionStorage.getItem('currentUser'));
}

function setCurrentUser(user, persistent = true) {
    const enrichedUser = {
        role: user.role || (user.email === ADMIN_EMAIL ? 'admin' : 'user'),
        ...user
    };

    if (persistent) {
        localStorage.setItem('currentUser', JSON.stringify(enrichedUser));
        sessionStorage.removeItem('currentUser');
    } else {
        sessionStorage.setItem('currentUser', JSON.stringify(enrichedUser));
        localStorage.removeItem('currentUser');
    }

    if (enrichedUser.role === 'admin' && enrichedUser.email === ADMIN_EMAIL) {
        localStorage.setItem(ADMIN_SESSION_KEY, JSON.stringify({
            email: ADMIN_EMAIL,
            verifiedAt: new Date().toISOString()
        }));
    }
}

function clearCurrentUser() {
    localStorage.removeItem('currentUser');
    sessionStorage.removeItem('currentUser');
    localStorage.removeItem(ADMIN_SESSION_KEY);
}

function isAdminUser(user) {
    return !!user && user.role === 'admin' && user.email === ADMIN_EMAIL;
}

function hasValidAdminSession(user = getCurrentUser()) {
    if (!isAdminUser(user)) return false;

    const adminSession = JSON.parse(localStorage.getItem(ADMIN_SESSION_KEY) || 'null');
    return !!adminSession && adminSession.email === ADMIN_EMAIL;
}

function protectPage({ adminOnly = false } = {}) {
    const currentUser = getCurrentUser();
    if (!currentUser) {
        window.location.href = 'login.html';
        return null;
    }

    if (adminOnly && !hasValidAdminSession(currentUser)) {
        window.location.href = 'dashboard.html';
        return null;
    }

    const welcomeTargets = document.querySelectorAll('.navbar-text, #navWelcomeText');
    welcomeTargets.forEach((target) => {
        if (target) target.textContent = `Welcome, ${currentUser.name}!`;
    });

    document.querySelectorAll('[data-admin-only]').forEach((element) => {
        element.classList.toggle('d-none', !hasValidAdminSession(currentUser));
    });

    document.querySelectorAll('[data-admin-label]').forEach((element) => {
        element.textContent = hasValidAdminSession(currentUser) ? 'Admin Panel' : 'Dashboard';
    });

    return currentUser;
}

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
    ensureAdminSeed();
    requestAnimationFrame(() => {
        document.body.classList.add('page-loaded');
    });
    
    const uploadModalEl = document.getElementById('uploadModal');
    if (uploadModalEl) uploadModalInstance = new bootstrap.Modal(uploadModalEl);
    
    const resultModalEl = document.getElementById('resultModal');
    if (resultModalEl) resultModalInstance = new bootstrap.Modal(resultModalEl);

    initHeroLoader();
    initHeroMotion();
    initLandingFX();
    initMagneticHover();
    initNavbarEffects();
    initScrollReveal();
    initPasswordToggles();
    initCodeInputs();
    initDashboardCharts();
    initDashboardExperience();
    initAdminExperience();
    initImageUpload();
    initAuthEnhancements();
    initAuthNavigation();

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
            userData.role = email.toLowerCase() === ADMIN_EMAIL ? 'admin' : 'user';
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
                    setCurrentUser(storedUser, true);
                    
                    Swal.fire({
                        icon: 'success',
                        title: 'Welcome back!',
                        text: `Redirecting to ${storedUser.role === 'admin' ? 'admin panel' : 'dashboard'}...`,
                        timer: 1500,
                        showConfirmButton: false
                    }).then(() => { window.location.href = hasValidAdminSession(storedUser) ? 'admin.html' : 'dashboard.html'; });
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
        protectPage();
    }

    if (window.location.pathname.includes('admin.html')) {
        protectPage({ adminOnly: true });
    }

    const logoutLinks = document.querySelectorAll('a[href="index.html"]');
    logoutLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            if(link.innerHTML.includes("Logout")) {
                e.preventDefault();
                clearCurrentUser();
                window.location.href = 'index.html';
            }
        });
    });
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

function initHeroMotion() {
    const heroSection = document.querySelector('.hero-section');
    if (!heroSection || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    const heroVisual = heroSection.querySelector('.hero-visual');
    const floatingCards = heroSection.querySelectorAll('.floating-info-card');
    const dashboardCard = heroSection.querySelector('.hero-dashboard-card');

    heroSection.addEventListener('mousemove', (event) => {
        const rect = heroSection.getBoundingClientRect();
        const x = ((event.clientX - rect.left) / rect.width - 0.5) * 10;
        const y = ((event.clientY - rect.top) / rect.height - 0.5) * 10;

        heroSection.style.backgroundPosition = `${50 + x * 0.7}% ${50 + y * 0.7}%`;

        if (heroVisual) {
            heroVisual.style.transform = `translate3d(${x * 0.35}px, ${y * 0.35}px, 0)`;
        }

        if (dashboardCard) {
            dashboardCard.style.transform = `rotateY(${(-10 + x * 0.55).toFixed(2)}deg) rotateX(${(6 - y * 0.45).toFixed(2)}deg) translateY(${(-y * 0.5).toFixed(2)}px)`;
        }

        floatingCards.forEach((card, index) => {
            const depth = index + 1;
            card.style.transform = `translate3d(${x * (0.45 + depth * 0.08)}px, ${y * (0.35 + depth * 0.06)}px, 0)`;
        });
    });

    heroSection.addEventListener('mouseleave', () => {
        heroSection.style.backgroundPosition = 'center';
        if (heroVisual) heroVisual.style.transform = '';
        if (dashboardCard) dashboardCard.style.transform = '';
        floatingCards.forEach((card) => {
            card.style.transform = '';
        });
    });
}

function initLandingFX() {
    const heroSection = document.querySelector('.hero-section');
    if (!heroSection) return;

    const particleContainer = document.getElementById('heroParticles');
    if (particleContainer && !particleContainer.children.length && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        for (let i = 0; i < 22; i += 1) {
            const particle = document.createElement('span');
            particle.className = 'hero-particle';
            particle.style.setProperty('--size', `${Math.random() * 10 + 8}px`);
            particle.style.setProperty('--left', `${Math.random() * 100}%`);
            particle.style.setProperty('--duration', `${Math.random() * 8 + 12}s`);
            particle.style.setProperty('--delay', `${Math.random() * -18}s`);
            particle.style.setProperty('--drift', `${(Math.random() - 0.5) * 120}px`);
            particleContainer.appendChild(particle);
        }
    }

    const counters = heroSection.querySelectorAll('[data-count]');
    if (!counters.length) return;

    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
            if (!entry.isIntersecting) return;

            counters.forEach((counter) => animateCounter(counter));
            observer.disconnect();
        });
    }, { threshold: 0.35 });

    observer.observe(heroSection);
}

function animateCounter(element) {
    if (element.dataset.animated === 'true') return;
    element.dataset.animated = 'true';

    const target = Number(element.dataset.count || 0);
    const duration = 1400;
    const startTime = performance.now();

    const step = (currentTime) => {
        const progress = Math.min((currentTime - startTime) / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        const value = Math.round(target * eased);
        element.textContent = value;

        if (progress < 1) {
            window.requestAnimationFrame(step);
        }
    };

    window.requestAnimationFrame(step);
}

function initNavbarEffects() {
    const navbar = document.querySelector('.navbar');
    if (!navbar) return;

    const syncNavbarState = () => {
        navbar.classList.toggle('is-scrolled', window.scrollY > 12);
    };

    syncNavbarState();
    window.addEventListener('scroll', syncNavbarState, { passive: true });
}

function initScrollReveal() {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

    const revealTargets = [
        ...document.querySelectorAll('.feature-card, .step-card, .advisory-card'),
        ...document.querySelectorAll('.auth-form-box, .custom-upload, #logState, #resultState'),
        ...document.querySelectorAll('.footer-section .col-md-4, .hero-section .btn, .hero-section h1, .hero-section .lead')
    ];

    revealTargets.forEach((element, index) => {
        if (element.classList.contains('reveal-on-scroll')) return;
        element.classList.add('reveal-on-scroll', `reveal-stagger-${(index % 3) + 1}`);
    });

    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
            if (!entry.isIntersecting) return;
            entry.target.classList.add('revealed');
            observer.unobserve(entry.target);
        });
    }, {
        threshold: 0.16,
        rootMargin: '0px 0px -40px 0px'
    });

    document.querySelectorAll('.reveal-on-scroll').forEach((element) => observer.observe(element));
}

function initAuthEnhancements() {
    const forgotForm = document.getElementById('forgotForm');
    const successMessage = document.getElementById('successMessage');

    if (forgotForm && successMessage) {
        forgotForm.addEventListener('submit', (event) => {
            event.preventDefault();

            const submitButton = forgotForm.querySelector('button[type="submit"]');
            const originalText = submitButton.innerHTML;

            submitButton.disabled = true;
            submitButton.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Sending...';

            setTimeout(() => {
                forgotForm.style.display = 'none';
                successMessage.style.display = 'block';
                successMessage.classList.add('reveal-on-scroll', 'revealed');
                submitButton.disabled = false;
                submitButton.innerHTML = originalText;
            }, 1200);
        });
    }
}

function initMagneticHover() {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

    const elements = document.querySelectorAll('.magnetic-hover, .hero-magnetic');
    elements.forEach((element) => {
        element.addEventListener('mousemove', (event) => {
            const rect = element.getBoundingClientRect();
            const x = event.clientX - rect.left - rect.width / 2;
            const y = event.clientY - rect.top - rect.height / 2;
            element.style.transform = `translate(${x * 0.08}px, ${y * 0.08}px)`;
        });

        element.addEventListener('mouseleave', () => {
            element.style.transform = '';
        });
    });
}

function initPasswordToggles() {
    const toggles = document.querySelectorAll('.password-toggle, .password-toggle-icon');
    toggles.forEach(toggle => {
        toggle.addEventListener('click', () => {
            const input = toggle.previousElementSibling || toggle.parentElement?.querySelector('input');
            if (input && input.type) {
                input.type = input.type === 'password' ? 'text' : 'password';
                toggle.classList.toggle('bi-eye');
                toggle.classList.toggle('bi-eye-slash');
            }
        });
    });
}

function initCodeInputs() {
    const codeInput = document.getElementById('verifyCode');
    if (!codeInput) return;

    codeInput.addEventListener('input', () => {
        codeInput.value = codeInput.value.replace(/\D/g, '').slice(0, 6);
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

function initDashboardExperience() {
    const dashboardRoot = document.getElementById('dashboardRoot');
    if (!dashboardRoot) return;

    const currentUser = protectPage();
    if (!currentUser) return;

    const uploads = [
        { crop: 'Potato', filename: 'potato_leaf_01.jpg', disease: 'Early Blight', status: 'warning', date: '2026-03-14', confidence: 92 },
        { crop: 'Tomato', filename: 'tomato_leaf_03.jpg', disease: 'Healthy Crop', status: 'healthy', date: '2026-03-13', confidence: 95 },
        { crop: 'Corn', filename: 'corn_field_02.jpg', disease: 'Corn Common Rust', status: 'risk', date: '2026-03-11', confidence: 84 },
        { crop: 'Rice', filename: 'rice_scan_08.jpg', disease: 'Rice Blast', status: 'risk', date: '2026-03-09', confidence: 88 }
    ];

    const totalUploads = uploads.length;
    const healthyCount = uploads.filter((item) => item.status === 'healthy').length;
    const riskCount = totalUploads - healthyCount;
    const avgConfidence = Math.round(uploads.reduce((sum, item) => sum + item.confidence, 0) / totalUploads);

    const statMap = {
        totalUploads,
        healthyCount,
        riskCount,
        avgConfidence
    };

    Object.entries(statMap).forEach(([key, value]) => {
        const target = document.querySelector(`[data-stat="${key}"]`);
        if (target) target.textContent = value;
    });

    const activityList = document.getElementById('activityFeed');
    if (activityList) {
        activityList.innerHTML = uploads.map((item) => `
            <div class="dashboard-activity-item">
                <div class="dashboard-activity-icon ${item.status}">
                    <i class="bi ${item.status === 'healthy' ? 'bi-check-circle' : 'bi-exclamation-triangle'}"></i>
                </div>
                <div>
                    <strong>${item.crop} scan processed</strong>
                    <p class="mb-0 text-muted small">${item.disease} detected on ${item.date}</p>
                </div>
            </div>
        `).join('');
    }

    const uploadsTable = document.getElementById('recentUploadsBody');
    if (uploadsTable) {
        uploadsTable.innerHTML = uploads.map((item) => `
            <tr>
                <td><span class="dashboard-crop-pill">${item.crop}</span></td>
                <td>${item.filename}</td>
                <td><span class="badge ${item.status === 'healthy' ? 'bg-success' : item.status === 'warning' ? 'bg-danger' : 'bg-warning text-dark'}">${item.disease}</span></td>
                <td>${item.confidence}%</td>
                <td>${item.date}</td>
                <td><a href="analysis.html" class="btn btn-sm btn-outline-success">Review</a></td>
            </tr>
        `).join('');
    }

    const dashboardName = document.getElementById('dashboardUserName');
    if (dashboardName) dashboardName.textContent = currentUser.name;
}

function initAuthNavigation() {
    const authNavLink = document.getElementById('authNavLink');
    if (!authNavLink) return;

    const currentUser = getCurrentUser();
    if (!currentUser) return;

    authNavLink.textContent = hasValidAdminSession(currentUser) ? 'Admin Panel' : 'Dashboard';
    authNavLink.href = hasValidAdminSession(currentUser) ? 'admin.html' : 'dashboard.html';
}

function initAdminExperience() {
    const adminRoot = document.getElementById('adminRoot');
    if (!adminRoot) return;

    const currentUser = protectPage({ adminOnly: true });
    if (!currentUser) return;

    const searchInput = document.getElementById('adminUserSearch');
    const roleFilter = document.getElementById('adminRoleFilter');
    const rows = Array.from(document.querySelectorAll('#adminUserTableBody tr'));

    const filterRows = () => {
        const searchTerm = (searchInput?.value || '').toLowerCase().trim();
        const roleValue = roleFilter?.value || 'all';

        rows.forEach((row) => {
            const matchesSearch = row.dataset.search.includes(searchTerm);
            const matchesRole = roleValue === 'all' || row.dataset.role === roleValue;
            row.classList.toggle('d-none', !(matchesSearch && matchesRole));
        });
    };

    if (searchInput) searchInput.addEventListener('input', filterRows);
    if (roleFilter) roleFilter.addEventListener('change', filterRows);

    document.querySelectorAll('.admin-action-btn, .admin-inline-action').forEach((button) => {
        button.addEventListener('click', () => {
            const action = button.dataset.action || 'complete action';
            if (typeof Swal !== 'undefined') {
                Swal.fire({
                    icon: 'success',
                    title: 'Admin Action Triggered',
                    text: `Ready to ${action}.`,
                    confirmButtonColor: '#2f9e44'
                });
            }
        });
    });
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
