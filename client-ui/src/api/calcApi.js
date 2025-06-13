import axios from 'axios';

export function calculateEligibilityAge(data) {
  return axios.post('/api/calculate-eligibility-age', data);
}

export function calculateIndexedGrant(data) {
  return axios.post('/api/calculate-indexed-grant', data);
}

export function calculateExemptionSummary(clientId, forceRecalculation = false) {
  return axios.post('/api/calculate-exemption-summary', { 
    client_id: clientId,
    force_recalculation: forceRecalculation 
  });
}

// Download filled 161d PDF as Blob
export function download161d(clientId) {
  return axios.get(`/api/clients/${clientId}/161d`, {
    responseType: 'blob',
  });
}

export function generateGrantsAppendix(clientId) {
  return axios.post('/api/generate-grants-appendix', { client_id: clientId });
}

export function generateCommutationsAppendix(clientId) {
  return axios.post('/api/generate-commutations-appendix', { client_id: clientId });
}
