import { apiClient } from './client'

export const engineeringApi = {
  calculateWindLoad: (data) =>
    apiClient('/engineering/wind-load', {
      method: 'POST',
      body: data,
    }),

  calculateSeismicLoad: (data) =>
    apiClient('/engineering/seismic-load', {
      method: 'POST',
      body: data,
    }),

  optimize: (candidates, weights = {}) =>
    apiClient('/engineering/optimize', {
      method: 'POST',
      body: {
        candidates,
        ...weights,
      },
    }),

  estimateCost: (data) =>
    apiClient('/engineering/cost-estimate', {
      method: 'POST',
      body: data,
    }),

  calculateSafetyFactors: (data) =>
    apiClient('/engineering/safety-factors', {
      method: 'POST',
      body: data,
    }),

  recommendSubstitutions: (materialType, maxRecommendations = 3) =>
    apiClient('/engineering/material-substitution', {
      method: 'POST',
      body: { material_type: materialType, max_recommendations: maxRecommendations },
    }),

  listTemplates: (climate) =>
    apiClient('/engineering/templates', {
      params: climate ? { climate } : undefined,
    }),

  getTemplate: (templateId) =>
    apiClient(`/engineering/templates/${templateId}`),

  generateReport: async (data) => {
    const token = localStorage.getItem('panah_auth_token')
    const response = await fetch('/api/v1/engineering/generate-report', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(data),
    })
    if (!response.ok) {
      throw new Error('Failed to generate PDF report')
    }
    return await response.blob()
  },
}
