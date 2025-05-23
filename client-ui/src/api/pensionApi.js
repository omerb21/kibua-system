import axios from 'axios';

export function getPensions(clientId) {
  return axios.get(`/api/clients/${clientId}/pensions`);
}

export function createPension(clientId, data) {
  return axios.post(`/api/clients/${clientId}/pensions`, data);
}

export function updatePension(pensionId, data) {
  return axios.put(`/api/pensions/${pensionId}`, data);
}

export function deletePension(pensionId) {
  return axios.delete(`/api/pensions/${pensionId}`);
}

export function getCommutations(pensionId) {
  return axios.get(`/api/pensions/${pensionId}/commutations`);
}

export function createCommutation(pensionId, data) {
  return axios.post(`/api/pensions/${pensionId}/commutations`, data);
}

export function updateCommutation(commutationId, data) {
  return axios.put(`/api/commutations/${commutationId}`, data);
}

export function deleteCommutation(commutationId) {
  return axios.delete(`/api/commutations/${commutationId}`);
}
