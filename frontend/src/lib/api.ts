import axios from 'axios';

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api/v1',
  withCredentials: true,
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    return Promise.reject(error);
  }
);

export const createWebSocket = (path: string, token?: string) => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const host = import.meta.env.VITE_WS_URL || window.location.host;
  let url = `${protocol}//${host}/ws${path}`;
  if (token) {
    url += `?token=${token}`;
  }
  return new WebSocket(url);
};
