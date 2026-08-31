/**
 * PANAGAH API Client
 * Centralized fetch handler with JWT auth, error normalization, and query string support.
 */

const API_BASE = '/api/v1'

class ApiError extends Error {
  constructor(message, status, data) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.data = data
  }
}

export async function apiClient(endpoint, options = {}) {
  const {
    method = 'GET',
    headers = {},
    body = null,
    params = null,
    ...customConfig
  } = options

  // Build query string if params provided
  let url = `${API_BASE}${endpoint}`
  if (params && typeof params === 'object') {
    const searchParams = new URLSearchParams()
    Object.entries(params).forEach(([key, val]) => {
      if (val !== undefined && val !== null && val !== '') {
        searchParams.append(key, val)
      }
    })
    const qs = searchParams.toString()
    if (qs) {
      url += (url.includes('?') ? '&' : '?') + qs
    }
  }

  const token = localStorage.getItem('panah_auth_token')
  const defaultHeaders = {
    'Accept': 'application/json',
    ...(body && !(body instanceof FormData) ? { 'Content-Type': 'application/json' } : {}),
    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    ...headers,
  }

  const config = {
    method,
    headers: defaultHeaders,
    ...(body ? { body: body instanceof FormData ? body : JSON.stringify(body) } : {}),
    ...customConfig,
  }

  try {
    const response = await fetch(url, config)

    // 204 No Content
    if (response.status === 204) {
      return null
    }

    const contentType = response.headers.get('content-type') || ''
    const isJson = contentType.includes('application/json')
    const data = isJson ? await response.json() : await response.text()

    if (!response.ok) {
      const errorMessage =
        (data && typeof data === 'object' && (data.detail || data.message || data.error)) ||
        `Request failed with status ${response.status}`
      throw new ApiError(errorMessage, response.status, data)
    }

    return data
  } catch (err) {
    if (err instanceof ApiError) {
      throw err
    }
    throw new ApiError(err.message || 'Network error connecting to Panagah server', 0, null)
  }
}
