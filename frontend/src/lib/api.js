/**
 * Centralized API configuration.
 * 
 * In production, set VITE_API_URL (or VITE_API_BASE_URL) to your Render backend URL
 * (e.g. https://your-app.onrender.com).
 * Locally, it defaults to http://localhost:8000.
 */
const API_URL = import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

/** Base URL for HTTP API calls (e.g. axios.get(`${API_BASE}/api/wells/nearby`)) */
export const API_BASE = API_URL;

/** Base URL for WebSocket connections (auto-converts http→ws, https→wss) */
export const WS_BASE = API_URL.replace(/^http/, 'ws');
