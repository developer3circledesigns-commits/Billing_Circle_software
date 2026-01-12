// Configure Axios Base URL
// Configure Axios Base URL
// API_URL is defined in base.html


// Auth Utilities
const auth = {
    setToken: (token) => localStorage.setItem('access_token', token),
    getToken: () => localStorage.getItem('access_token'),
    removeToken: () => localStorage.removeItem('access_token'),
    isAuthenticated: () => !!localStorage.getItem('access_token'),
    logout: () => {
        auth.removeToken();
        window.location.href = '/';
    }
};

// Add auth header to requests
axios.interceptors.request.use(
    config => {
        const token = auth.getToken();
        if (token) {
            config.headers['Authorization'] = 'Bearer ' + token;
        }
        return config;
    },
    error => {
        return Promise.reject(error);
    }
);

// Handle 401 errors
axios.interceptors.response.use(
    response => response,
    error => {
        if (error.response && error.response.status === 401) {
            // Only redirect if not already on login/signup page
            if (!window.location.pathname.match(/^\/($|signup)/)) {
                auth.logout();
            }
        }
        return Promise.reject(error);
    }
);
