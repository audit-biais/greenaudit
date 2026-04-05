import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'https://greenaudit-production.up.railway.app/api',
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    if (
      error.response?.status === 402 &&
      error.response?.data?.detail === 'upgrade_required'
    ) {
      window.dispatchEvent(new CustomEvent('upgrade_required'));
    }
    return Promise.reject(error);
  }
);

export default api;
