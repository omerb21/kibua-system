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

export function fillForm161d(clientId) {
  return axios.post('/api/fill-161d-pdf', { client_id: clientId });
}

export function generateGrantsAppendix(clientId) {
  return axios.post('/api/generate-grants-appendix', { client_id: clientId });
}

export function generateCommutationsAppendix(clientId) {
  return axios.post('/api/generate-commutations-appendix', { client_id: clientId });
}
