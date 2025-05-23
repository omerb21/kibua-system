import axios from 'axios';

export function getClients() {
  return axios.get('/api/clients');
}

export function getClient(id) {
  return axios.get(`/api/clients/${id}`);
}

export function createClient(data) {
  return axios.post('/api/clients', data);
}

export function updateClient(id, data) {
  return axios.put(`/api/clients/${id}`, data);
}
