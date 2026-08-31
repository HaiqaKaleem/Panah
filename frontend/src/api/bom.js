import { apiClient } from './client'

export const bomApi = {
  getBOM: (projectId, siteId, designId) =>
    apiClient(`/projects/${projectId}/sites/${siteId}/generated-designs/${designId}/bom`),

  downloadCsvUrl: (projectId, siteId, designId) =>
    `/api/v1/projects/${projectId}/sites/${siteId}/generated-designs/${designId}/bom/csv`,

  downloadCsvBlob: async (projectId, siteId, designId) => {
    const token = localStorage.getItem('panah_auth_token')
    const response = await fetch(
      `/api/v1/projects/${projectId}/sites/${siteId}/generated-designs/${designId}/bom/csv`,
      {
        headers: token ? { 'Authorization': `Bearer ${token}` } : {},
      }
    )
    if (!response.ok) {
      throw new Error('Failed to download BOM CSV')
    }
    return await response.blob()
  },
}
