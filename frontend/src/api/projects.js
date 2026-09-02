import { apiClient } from './client'

export const projectsApi = {
  list: () => apiClient('/projects'),

  create: (data) =>
    apiClient('/projects', {
      method: 'POST',
      body: data,
    }),

  get: (id) => apiClient(`/projects/${id}`),

  update: (id, data) =>
    apiClient(`/projects/${id}`, {
      method: 'PATCH',
      body: data,
    }),

  delete: (id) =>
    apiClient(`/projects/${id}`, {
      method: 'DELETE',
    }),

  getStats: (id) => apiClient(`/projects/${id}/stats`),

  getDashboardStats: () => apiClient('/dashboard/stats'),

  getHistory: (params) => apiClient('/projects-history', { params }),

  getActivity: (projectId) => apiClient(`/projects/${projectId}/activity`),
}
