/**
 * HTTP Client with Authentication and Error Handling
 */

export class ApiError extends Error {
  constructor(
    public status: number,
    public message: string,
    public data?: any
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

export class HttpClient {
  private getAuthToken(): string | null {
    if (typeof window === 'undefined') return null
    return localStorage.getItem('auth_token')
  }

  private getHeaders(includeAuth: boolean = true): HeadersInit {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    }

    if (includeAuth) {
      const token = this.getAuthToken()
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }
    }

    return headers
  }

  private async handleResponse<T>(response: Response): Promise<T> {
    // Handle 401 Unauthorized - clear auth and redirect to login
    if (response.status === 401) {
      if (typeof window !== 'undefined') {
        localStorage.removeItem('auth_token')
        localStorage.removeItem('user')
        document.cookie = 'auth_token=; path=/; expires=Thu, 01 Jan 1970 00:00:01 GMT'
        window.location.href = '/login'
      }
      throw new ApiError(401, 'Unauthorized - Please login again')
    }

    // Parse response body
    const text = await response.text()
    let data: any
    try {
      data = text ? JSON.parse(text) : null
    } catch {
      data = text
    }

    // Handle non-2xx responses
    if (!response.ok) {
      const message = data?.message || data?.error || `HTTP ${response.status} error`
      throw new ApiError(response.status, message, data)
    }

    return data as T
  }

  async get<T>(url: string, includeAuth: boolean = true): Promise<T> {
    const response = await fetch(url, {
      method: 'GET',
      headers: this.getHeaders(includeAuth),
    })
    return this.handleResponse<T>(response)
  }

  async post<T>(url: string, body?: any, includeAuth: boolean = true): Promise<T> {
    const response = await fetch(url, {
      method: 'POST',
      headers: this.getHeaders(includeAuth),
      body: body ? JSON.stringify(body) : undefined,
    })
    return this.handleResponse<T>(response)
  }

  async patch<T>(url: string, body?: any, includeAuth: boolean = true): Promise<T> {
    const response = await fetch(url, {
      method: 'PATCH',
      headers: this.getHeaders(includeAuth),
      body: body ? JSON.stringify(body) : undefined,
    })
    return this.handleResponse<T>(response)
  }

  async delete<T>(url: string, includeAuth: boolean = true): Promise<T> {
    const response = await fetch(url, {
      method: 'DELETE',
      headers: this.getHeaders(includeAuth),
    })
    return this.handleResponse<T>(response)
  }
}

export const httpClient = new HttpClient()
