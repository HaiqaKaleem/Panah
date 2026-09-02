import { apiClient } from './client'

export const sitesApi = {
  list: (projectId) => apiClient(`/projects/${projectId}/sites`),

  create: (projectId, data) =>
    apiClient(`/projects/${projectId}/sites`, {
      method: 'POST',
      body: data,
    }),

  get: (projectId, siteId) => apiClient(`/projects/${projectId}/sites/${siteId}`),
}
