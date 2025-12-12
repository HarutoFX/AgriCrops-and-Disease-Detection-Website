// API Configuration
// Change this to your deployed backend URL after deployment

const CONFIG = {
    // Development
    API_URL_DEV: 'http://127.0.0.1:5000',
    
    // Production - Update this after deploying backend
    API_URL_PROD: 'https://your-backend-app.onrender.com',
    
    // Auto-detect environment
    get API_URL() {
        return window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
            ? this.API_URL_DEV
            : this.API_URL_PROD;
    }
};

// Export for use in other scripts
window.API_CONFIG = CONFIG;
