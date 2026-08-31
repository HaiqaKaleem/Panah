import { apiClient } from './client'

export const searchApi = {
  search: (q, type) =>
    apiClient('/search', {
      params: { q, ...(type ? { type } : {}) },
    }),

  suggest: (q) =>
    apiClient('/search/suggest', {
      params: { q },
    }),
}
