const configuredApiUrl = import.meta.env.VITE_API_URL || import.meta.env.VITE_API_HOST;
const apiUrl = configuredApiUrl || 'http://127.0.0.1:8000';
export const API_URL = `${/^https?:\/\//i.test(apiUrl) ? '' : 'https://'}${apiUrl}`.replace(/\/+$/, '');
export const DISCLAIMER =
  'For decision support / educational purposes only. Not a substitute for formal diagnostic imaging.';

async function request(path, options = {}) {
  const response = await fetch(`${API_URL}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  });
  if (!response.ok) {
    let detail = `Request failed (${response.status})`;
    try {
      const body = await response.json();
      detail = body.detail || detail;
    } catch {
      /* keep default */
    }
    throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail));
  }
  return response.json();
}

export const getSchema = () => request('/schema');
export const getMetrics = () => request('/metrics');
export const getSamples = () => request('/sample-patients');
export const getHealth = () => request('/health');
export const postPredict = (patient) =>
  request('/predict', { method: 'POST', body: JSON.stringify({ patient }) });
export const postExplain = (patient, target) =>
  request('/explain', { method: 'POST', body: JSON.stringify({ patient, target }) });
export const postCounterfactual = (patient, target) =>
  request('/counterfactual', { method: 'POST', body: JSON.stringify({ patient, target }) });
export const figureUrl = (name) => `${API_URL}/figures/${name}`;
