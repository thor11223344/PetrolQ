/**
 * Centralized API configuration.
 * 
 * In production, set VITE_API_URL to your SnapDeploy backend URL
 * (e.g. https://petrolq-api.snapdeploy.app).
 * Locally, it defaults to http://localhost:8000.
 */
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/** Base URL for HTTP API calls (e.g. axios.get(`${API_BASE}/api/wells/nearby`)) */
export const API_BASE = API_URL;

/** Base URL for WebSocket connections (auto-converts http→ws, https→wss) */
export const WS_BASE = API_URL.replace(/^http/, 'ws');
