/**
 * API client for backend communication
 */
import axios from 'axios';

// Base URL for API (update if your backend runs on different port)
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001';

// Get API key from environment variable
const API_KEY = import.meta.env.VITE_API_KEY || '';

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': API_KEY,
  },
});

export default apiClient;