const API_BASE = import.meta.env.VITE_API_BASE || '/api';

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed: ${res.status}`);
  }
  return res.json();
}

export const api = {
  createFarm: (payload) => request('/farm', { method: 'POST', body: JSON.stringify(payload) }),
  getIntelligence: (farmId) => request(`/intelligence/${farmId}`),
  ask: (farmId, question) => request('/ask', {
    method: 'POST',
    body: JSON.stringify({ farm_id: farmId, question }),
  }),
};
