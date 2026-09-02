import { apiClient } from './client'

export const standardsApi = {
  getCategories: () => apiClient('/standards/categories'),

  getRules: (category) =>
    apiClient('/standards/rules', {
      params: category ? { category } : undefined,
    }),

  getRuleDetail: (ruleId) => apiClient(`/standards/rules/${ruleId}`),
}
