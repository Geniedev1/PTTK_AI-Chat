import { create } from "zustand"

type SessionState = {
  customerToken: string | null
  customerId: number | null
  customerUsername: string | null
  staffToken: string | null
  cartSessionKey: string | null
  requestId: string | null
  setCustomerAuth: (payload: {
    token: string | null
    customerId?: number | null
    customerUsername?: string | null
  }) => void
  setCustomerIdentity: (payload: { customerId?: number | null; customerUsername?: string | null }) => void
  setCustomerToken: (token: string | null) => void
  setStaffToken: (token: string | null) => void
  setCartSessionKey: (key: string | null) => void
  setRequestId: (requestId: string | null) => void
  clearAuth: () => void
}

const STORAGE_KEY = "pttk-fe-session"

type PersistedSession = {
  customerToken: string | null
  customerId: number | null
  customerUsername: string | null
  staffToken: string | null
  cartSessionKey: string | null
}

const readPersisted = (): PersistedSession => {
  if (typeof window === "undefined") {
    return {
      customerToken: null,
      customerId: null,
      customerUsername: null,
      staffToken: null,
      cartSessionKey: null,
    }
  }

  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) {
      return {
        customerToken: null,
        customerId: null,
        customerUsername: null,
        staffToken: null,
        cartSessionKey: null,
      }
    }
    const parsed = JSON.parse(raw) as PersistedSession
    return {
      customerToken: parsed.customerToken ?? null,
      customerId: parsed.customerId ?? null,
      customerUsername: parsed.customerUsername ?? null,
      staffToken: parsed.staffToken ?? null,
      cartSessionKey: parsed.cartSessionKey ?? null,
    }
  } catch {
    return {
      customerToken: null,
      customerId: null,
      customerUsername: null,
      staffToken: null,
      cartSessionKey: null,
    }
  }
}

const writePersisted = (state: PersistedSession) => {
  if (typeof window === "undefined") {
    return
  }

  localStorage.setItem(STORAGE_KEY, JSON.stringify(state))
}

const persisted = readPersisted()

export const useSessionStore = create<SessionState>((set, get) => ({
  customerToken: persisted.customerToken,
  customerId: persisted.customerId,
  customerUsername: persisted.customerUsername,
  staffToken: persisted.staffToken,
  cartSessionKey: persisted.cartSessionKey,
  requestId: null,
  setCustomerAuth: ({ token, customerId = null, customerUsername = null }) => {
    set({ customerToken: token, customerId, customerUsername })
    const state = get()
    writePersisted({
      customerToken: token,
      customerId,
      customerUsername,
      staffToken: state.staffToken,
      cartSessionKey: state.cartSessionKey,
    })
  },
  setCustomerIdentity: ({ customerId = null, customerUsername = null }) => {
    set({ customerId, customerUsername })
    const state = get()
    writePersisted({
      customerToken: state.customerToken,
      customerId,
      customerUsername,
      staffToken: state.staffToken,
      cartSessionKey: state.cartSessionKey,
    })
  },
  setCustomerToken: (token) => {
    set({ customerToken: token })
    const state = get()
    writePersisted({
      customerToken: token,
      customerId: state.customerId,
      customerUsername: state.customerUsername,
      staffToken: state.staffToken,
      cartSessionKey: state.cartSessionKey,
    })
  },
  setStaffToken: (token) => {
    set({ staffToken: token })
    const state = get()
    writePersisted({
      customerToken: state.customerToken,
      customerId: state.customerId,
      customerUsername: state.customerUsername,
      staffToken: token,
      cartSessionKey: state.cartSessionKey,
    })
  },
  setCartSessionKey: (key) => {
    set({ cartSessionKey: key })
    const state = get()
    writePersisted({
      customerToken: state.customerToken,
      customerId: state.customerId,
      customerUsername: state.customerUsername,
      staffToken: state.staffToken,
      cartSessionKey: key,
    })
  },
  setRequestId: (requestId) => set({ requestId }),
  clearAuth: () => {
    set({ customerToken: null, customerId: null, customerUsername: null, staffToken: null })
    const state = get()
    writePersisted({
      customerToken: null,
      customerId: null,
      customerUsername: null,
      staffToken: null,
      cartSessionKey: state.cartSessionKey,
    })
  },
}))
