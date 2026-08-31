import { apiClient } from './client'

export const materialsApi = {
  getCatalog: (params) => apiClient('/material-catalog', { params }),

  list: (projectId) => apiClient(`/projects/${projectId}/materials`),

  create: (projectId, data) =>
    apiClient(`/projects/${projectId}/materials`, {
      method: 'POST',
      body: data,
    }),

  getSummary: (projectId) => apiClient(`/projects/${projectId}/materials-summary`),
}
