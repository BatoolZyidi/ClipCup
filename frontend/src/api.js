/**
 * API base URL — set VITE_API_BASE_URL in Vercel environment variables
 * to your Render backend URL, e.g. https://clipcup.onrender.com
 * Locally this is empty and Vite's dev proxy forwards /api/* to localhost:8000.
 */
export const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

/**
 * Build a full API URL.
 * apiUrl('/api/jobs') → '/api/jobs' locally, 'https://clipcup.onrender.com/api/jobs' on Vercel
 */
export function apiUrl(path) {
  return `${API_BASE}${path}`;
}
