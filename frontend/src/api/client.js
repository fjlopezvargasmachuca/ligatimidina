const API_BASE_URL = '/api'

function getCookie(name) {
  const cookies = document.cookie ? document.cookie.split(';') : []

  for (const cookie of cookies) {
    const [key, ...valueParts] = cookie.trim().split('=')

    if (key === name) {
      return decodeURIComponent(valueParts.join('='))
    }
  }

  return null
}

async function ensureCsrfToken() {
  const existingToken = getCookie('csrftoken')

  if (existingToken) {
    return existingToken
  }

  /*
   * El endpoint /accounts/me/ se utiliza también para establecer
   * la cookie CSRF mediante Django.
   *
   * Aunque el usuario no esté autenticado, la petición GET es segura.
   */
  try {
    await fetch(`${API_BASE_URL}/accounts/me/`, {
      method: 'GET',
      credentials: 'include',
      headers: {
        Accept: 'application/json',
      },
    })
  } catch {
    // La petición principal será la que informe del error real.
  }

  return getCookie('csrftoken')
}

async function request(endpoint, options = {}) {
  const {
    method = 'GET',
    body,
    headers = {},
    ...rest
  } = options

  const requestHeaders = {
    Accept: 'application/json',
    ...headers,
  }

  let requestBody = body

  if (body !== undefined && !(body instanceof FormData)) {
    requestHeaders['Content-Type'] = 'application/json'
    requestBody = JSON.stringify(body)
  }

  const unsafeMethods = ['POST', 'PUT', 'PATCH', 'DELETE']

  if (unsafeMethods.includes(method.toUpperCase())) {
    const csrfToken = await ensureCsrfToken()

    if (csrfToken) {
      requestHeaders['X-CSRFToken'] = csrfToken
    }
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    method,
    credentials: 'include',
    headers: requestHeaders,
    body: requestBody,
    ...rest,
  })

  let data = null

  const contentType = response.headers.get('content-type') || ''

  if (contentType.includes('application/json')) {
    data = await response.json()
  } else {
    const text = await response.text()
    data = text || null
  }

  if (!response.ok) {
    const error = new Error(
      data?.detail ||
      data?.message ||
      'Ha ocurrido un error al comunicarse con el servidor.',
    )

    error.status = response.status
    error.data = data

    throw error
  }

  return data
}

export const api = {
  get(endpoint, options = {}) {
    return request(endpoint, {
      ...options,
      method: 'GET',
    })
  },

  post(endpoint, body, options = {}) {
    return request(endpoint, {
      ...options,
      method: 'POST',
      body,
    })
  },

  put(endpoint, body, options = {}) {
    return request(endpoint, {
      ...options,
      method: 'PUT',
      body,
    })
  },

  patch(endpoint, body, options = {}) {
    return request(endpoint, {
      ...options,
      method: 'PATCH',
      body,
    })
  },

  delete(endpoint, options = {}) {
    return request(endpoint, {
      ...options,
      method: 'DELETE',
    })
  },
}