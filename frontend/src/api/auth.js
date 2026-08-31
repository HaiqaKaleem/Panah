import { apiClient } from './client'

export const authApi = {
  login: (email, password) =>
    apiClient('/auth/login', {
      method: 'POST',
      body: { email, password },
    }),

  register: ({ email, password, full_name, role = 'engineer' }) =>
    apiClient('/auth/register', {
      method: 'POST',
      body: { email, password, full_name, role },
    }),

  getMe: () =>
    apiClient('/auth/me'),

  refreshToken: (refreshToken) =>
    apiClient('/auth/refresh', {
      method: 'POST',
      body: { refresh_token: refreshToken },
    }),
}
