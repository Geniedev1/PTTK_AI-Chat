import axios from "axios"
import { endpoints } from "../constants/endpoints"
import { useSessionStore } from "../stores/sessionStore"

const REQUEST_TIMEOUT_MS = 10_000

const generateRequestId = () => {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID()
  }
  return `req-${Date.now()}-${Math.random().toString(16).slice(2)}`
}

export const httpClient = axios.create({
  baseURL: endpoints.baseUrl,
  timeout: REQUEST_TIMEOUT_MS,
})

httpClient.interceptors.request.use((config) => {
  const state = useSessionStore.getState()
  const requestId = state.requestId ?? generateRequestId()

  config.headers = config.headers ?? {}
  config.headers["X-Request-ID"] = requestId

  const authToken = state.customerToken ?? state.staffToken
  if (authToken) {
    config.headers.Authorization = `Token ${authToken}`
  }

  if (state.staffToken && state.staffRoles.length > 0) {
    config.headers["X-Staff-Role"] = state.staffRoles.join(",")
    config.headers["X-User-Role"] = state.staffRoles.join(",")
    if (state.staffId) {
      config.headers["X-Staff-ID"] = String(state.staffId)
    }
  } else if (state.customerToken) {
    config.headers["X-User-Role"] = "customer"
  }

  const hasCartHeader =
    config.headers["X-Cart-Session-Key"] !== undefined ||
    config.headers["x-cart-session-key"] !== undefined

  if (!hasCartHeader && state.cartSessionKey) {
    config.headers["X-Cart-Session-Key"] = state.cartSessionKey
  }

  useSessionStore.getState().setRequestId(requestId)
  return config
})

httpClient.interceptors.response.use(
  (response) => {
    const cartSessionHeader = response.headers["x-cart-session-key"] as string | undefined
    const requestHeader = response.headers["x-request-id"] as string | undefined

    if (cartSessionHeader) {
      useSessionStore.getState().setCartSessionKey(cartSessionHeader)
    }

    if (requestHeader) {
      useSessionStore.getState().setRequestId(requestHeader)
    }

    return response
  },
  (error) => {
    const statusCode = error?.response?.status as number | undefined
    if (statusCode === 401) {
      useSessionStore.getState().clearAuth()
    }
    return Promise.reject(error)
  },
)
