import axios from 'axios';

export function calculateEligibilityAge(data) {
  return axios.post('/api/calculate-eligibility-age', data);
}

export function calculateIndexedGrant(data) {
  return axios.post('/api/calculate-indexed-grant', data);
}

export function calculateExemptionSummary(clientId) {
  return axios.post('/api/calculate-exemption-summary', { client_id: clientId });
}

export function fillForm161d(clientId) {
  return axios.post('/api/fill-161d-pdf', { client_id: clientId });
}
