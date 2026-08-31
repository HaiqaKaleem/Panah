import { apiClient } from './client'

export const designApi = {
  createConstraintSet: (projectId, siteId, payload) =>
    apiClient(`/projects/${projectId}/sites/${siteId}/constraint-sets`, {
      method: 'POST',
      body: payload,
    }),

  listConstraintSets: (projectId, siteId) =>
    apiClient(`/projects/${projectId}/sites/${siteId}/constraint-sets`),

  getConstraintSet: (projectId, siteId, csId) =>
    apiClient(`/projects/${projectId}/sites/${siteId}/constraint-sets/${csId}`),

  generateDesigns: (projectId, siteId, csId, count = 2) =>
    apiClient(`/projects/${projectId}/sites/${siteId}/constraint-sets/${csId}/generate`, {
      method: 'POST',
      body: { count },
    }),

  listGeneratedDesigns: (projectId, siteId) =>
    apiClient(`/projects/${projectId}/sites/${siteId}/generated-designs`),

  getGeneratedDesign: (projectId, siteId, designId) =>
    apiClient(`/projects/${projectId}/sites/${siteId}/generated-designs/${designId}`),

  validateDesign: (projectId, siteId, designId) =>
    apiClient(`/projects/${projectId}/sites/${siteId}/generated-designs/${designId}/validate`, {
      method: 'POST',
    }),

  promoteDesign: (projectId, siteId, designId) =>
    apiClient(`/projects/${projectId}/sites/${siteId}/generated-designs/${designId}/promote`, {
      method: 'POST',
    }),

  getGeometry: (projectId, siteId, designId) =>
    apiClient(`/projects/${projectId}/sites/${siteId}/generated-designs/${designId}/geometry`),
}
