/**
 * Centralized API & Hybrid Dual-Mode Connectivity Configuration.
 * 
 * Supports both Cloud (Render/Vercel) and Local Rig Edge Appliance (localhost:8000).
 * Automatically handles network dropouts and seamless offline switching.
 */

const DEFAULT_LOCAL = 'http://localhost:8000';

function resolveApiBase() {
  if (typeof window !== 'undefined') {
    const host = window.location.hostname;
    // When running in a local doghouse appliance or dev mode on localhost
    if (host === 'localhost' || host === '127.0.0.1' || host === '0.0.0.0') {
      return DEFAULT_LOCAL;
    }
  }
  return import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE_URL || DEFAULT_LOCAL;
}

const CONFIGURED_URL = resolveApiBase();

/** Base URL for HTTP API calls */
export const API_BASE = CONFIGURED_URL;

/** Base URL for WebSocket connections */
export const WS_BASE = CONFIGURED_URL.replace(/^http/, 'ws');

/** Local fallback endpoint for rig doghouse appliances */
export const LOCAL_API_BASE = DEFAULT_LOCAL;
export const LOCAL_WS_BASE = DEFAULT_LOCAL.replace(/^http/, 'ws');

/**
 * Checks if the browser has an active network connection.
 */
export function isOnline() {
  return typeof navigator !== 'undefined' ? navigator.onLine : true;
}

/**
 * Subscribes to browser online/offline network transition events.
 */
export function subscribeNetworkStatus(onChange) {
  if (typeof window === 'undefined') return () => {};

  const handleOnline = () => onChange(true);
  const handleOffline = () => onChange(false);

  window.addEventListener('online', handleOnline);
  window.addEventListener('offline', handleOffline);

  return () => {
    window.removeEventListener('online', handleOnline);
    window.removeEventListener('offline', handleOffline);
  };
}
