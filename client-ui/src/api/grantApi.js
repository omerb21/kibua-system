import axios from 'axios';

export function getGrants(clientId) {
  return axios.get(`/api/clients/${clientId}/grants`);
}

export function createGrant(clientId, data) {
  return axios.post(`/api/clients/${clientId}/grants`, data);
}

export function updateGrant(grantId, data) {
  return axios.put(`/api/grants/${grantId}`, data);
}

export function deleteGrant(grantId) {
  return axios.delete(`/api/grants/${grantId}`);
}

export function calculateGrantImpact(data) {
  return axios.post('/api/calculate-grant-impact', data);
}
