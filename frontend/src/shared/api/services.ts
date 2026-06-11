import { endpoints } from "../constants/endpoints"
import type {
  AiChatResponse,
  AiModelStatus,
  AiRecommendResponse,
  CartItem,
  CartSummary,
  CreatePaymentPayload,
  CreateOrderResponse,
  CreateShipmentPayload,
  CustomerLoginResponse,
  CustomerProfile,
  CustomerProfileUpdatePayload,
  CustomerRegisterPayload,
  Order,
  Payment,
  Product,
  Shipment,
  StaffLoginResponse,
  InteractionGraphStatus,
} from "../types/api"
import { httpClient } from "./httpClient"

type ListProductsParams = {
  search?: string
  category_id?: number
  in_stock?: boolean
  min_price?: string
  max_price?: string
  sort_by?: string
  tag?: string
}

const withOptionalCustomerScope = (customerId?: number | null) =>
  customerId
    ? {
        params: { customer_id: customerId },
        headers: { "X-Cart-Session-Key": "" },
      }
    : undefined

export const customerApi = {
  register: async (payload: CustomerRegisterPayload): Promise<{ message: string }> => {
    const { data } = await httpClient.post<{ message: string }>(endpoints.customers.register, payload)
    return data
  },
  login: async (payload: { username: string; password: string }): Promise<CustomerLoginResponse> => {
    const { data } = await httpClient.post<CustomerLoginResponse>(endpoints.customers.login, payload)
    return data
  },
  profile: async (): Promise<CustomerProfile> => {
    const { data } = await httpClient.get<CustomerProfile>(endpoints.customers.profile)
    return data
  },
  updateProfile: async (payload: CustomerProfileUpdatePayload): Promise<CustomerProfile> => {
    const { data } = await httpClient.put<CustomerProfile>(endpoints.customers.updateProfile, payload)
    return data
  },
}

export const staffApi = {
  login: async (payload: { username: string; password: string }): Promise<StaffLoginResponse> => {
    const { data } = await httpClient.post<StaffLoginResponse>(endpoints.staff.login, payload)
    return data
  },
}

export const productApi = {
  list: async (params?: ListProductsParams): Promise<Product[]> => {
    const query: Record<string, string | number | boolean> = {}
    if (params?.search?.trim()) {
      query.search = params.search.trim()
    }
    if (params?.category_id) {
      query.category_id = params.category_id
    }
    if (params?.in_stock !== undefined) {
      query.in_stock = params.in_stock ? "true" : "false"
    }
    if (params?.min_price) {
      query.min_price = params.min_price
    }
    if (params?.max_price) {
      query.max_price = params.max_price
    }
    if (params?.sort_by) {
      query.sort_by = params.sort_by
    }
    if (params?.tag) {
      query.tag = params.tag
    }
    const { data } = await httpClient.get<Product[]>(endpoints.products.list, { params: query })
    return data
  },
  detail: async (productId: number): Promise<Product> => {
    const { data } = await httpClient.get<Product>(endpoints.products.detail(productId))
    return data
  },
}

export const cartApi = {
  current: async (): Promise<CartSummary> => {
    const { data } = await httpClient.get<CartSummary>(endpoints.cart.current)
    return data
  },
  addProduct: async (payload: { product_id: number; quantity?: number }): Promise<CartItem> => {
    const { data } = await httpClient.post<CartItem>(endpoints.cart.addProduct, payload)
    return data
  },
  updateQuantity: async (payload: { product_id: number; quantity: number }): Promise<CartItem> => {
    const { data } = await httpClient.post<CartItem>(endpoints.cart.updateQuantity, payload)
    return data
  },
  removeProduct: async (payload: { product_id: number }): Promise<{ message: string }> => {
    const { data } = await httpClient.post<{ message: string }>(endpoints.cart.removeProduct, payload)
    return data
  },
  clear: async (): Promise<{ message: string }> => {
    const { data } = await httpClient.post<{ message: string }>(endpoints.cart.clear)
    return data
  },
}

export const orderApi = {
  list: async (customerId?: number | null): Promise<Order[]> => {
    const { data } = await httpClient.get<Order[]>(
      endpoints.orders.list,
      withOptionalCustomerScope(customerId),
    )
    return data
  },
  detail: async (orderId: number, customerId?: number | null): Promise<Order> => {
    const { data } = await httpClient.get<Order>(
      endpoints.orders.detail(orderId),
      withOptionalCustomerScope(customerId),
    )
    return data
  },
  create: async (payload: { customer_id?: number; clear_cart?: boolean }): Promise<CreateOrderResponse> => {
    const { data } = await httpClient.post<CreateOrderResponse>(endpoints.orders.create, payload)
    return data
  },
  updateStatus: async (orderId: number, status: string): Promise<Order> => {
    const { data } = await httpClient.post<Order>(endpoints.orders.updateStatus(orderId), { status })
    return data
  },
}

export const paymentApi = {
  list: async (params?: { customer_id?: number; session_key?: string }): Promise<Payment[]> => {
    const { data } = await httpClient.get<Payment[]>(endpoints.payments.list, { params })
    return data
  },
  detail: async (paymentId: number, params?: { customer_id?: number; session_key?: string }): Promise<Payment> => {
    const { data } = await httpClient.get<Payment>(endpoints.payments.detail(paymentId), { params })
    return data
  },
  create: async (payload: CreatePaymentPayload): Promise<Payment> => {
    const { data } = await httpClient.post<Payment>(endpoints.payments.create, payload)
    return data
  },
  confirm: async (paymentId: number): Promise<Payment> => {
    const { data } = await httpClient.post<Payment>(endpoints.payments.confirm(paymentId))
    return data
  },
  fail: async (paymentId: number, failure_reason?: string): Promise<Payment> => {
    const { data } = await httpClient.post<Payment>(endpoints.payments.fail(paymentId), { failure_reason })
    return data
  },
  cancel: async (paymentId: number): Promise<Payment> => {
    const { data } = await httpClient.post<Payment>(endpoints.payments.cancel(paymentId))
    return data
  },
  refund: async (paymentId: number): Promise<Payment> => {
    const { data } = await httpClient.post<Payment>(endpoints.payments.refund(paymentId))
    return data
  },
}

export const shippingApi = {
  listShipments: async (params?: {
    customer_id?: number
    session_key?: string
    tracking_number?: string
  }): Promise<Shipment[]> => {
    const { data } = await httpClient.get<Shipment[]>(endpoints.shipping.shipments, { params })
    return data
  },
  shipmentDetail: async (
    shipmentId: number,
    params?: { customer_id?: number; session_key?: string; tracking_number?: string },
  ): Promise<Shipment> => {
    const { data } = await httpClient.get<Shipment>(endpoints.shipping.shipmentDetail(shipmentId), { params })
    return data
  },
  createShipment: async (payload: CreateShipmentPayload): Promise<Shipment> => {
    const { data } = await httpClient.post<Shipment>(endpoints.shipping.shipments, payload)
    return data
  },
  markReady: async (shipmentId: number): Promise<Shipment> => {
    const { data } = await httpClient.post<Shipment>(endpoints.shipping.markReady(shipmentId))
    return data
  },
  ship: async (shipmentId: number): Promise<Shipment> => {
    const { data } = await httpClient.post<Shipment>(endpoints.shipping.ship(shipmentId))
    return data
  },
  deliver: async (shipmentId: number): Promise<Shipment> => {
    const { data } = await httpClient.post<Shipment>(endpoints.shipping.deliver(shipmentId))
    return data
  },
  cancel: async (shipmentId: number): Promise<Shipment> => {
    const { data } = await httpClient.post<Shipment>(endpoints.shipping.cancel(shipmentId))
    return data
  },
  fail: async (shipmentId: number, failure_reason?: string): Promise<Shipment> => {
    const { data } = await httpClient.post<Shipment>(endpoints.shipping.fail(shipmentId), { failure_reason })
    return data
  },
}

export const aiApi = {
  recommendHome: async (params?: {
    user_id?: number
    session_id?: string
    limit?: number
  }): Promise<AiRecommendResponse> => {
    const { data } = await httpClient.get<AiRecommendResponse>(endpoints.ai.recommendHome, { params })
    return data
  },
  recommendProductDetail: async (params: {
    product_id: number
    user_id?: number
    session_id?: string
    limit?: number
  }): Promise<AiRecommendResponse> => {
    const { data } = await httpClient.get<AiRecommendResponse>(endpoints.ai.recommendProductDetail, {
      params,
    })
    return data
  },
  chat: async (payload: {
    message: string
    user_id?: number
    session_id?: string
    customer_id?: number
    product_id?: number
    order_id?: number
  }): Promise<AiChatResponse> => {
    const { data } = await httpClient.post<AiChatResponse>(endpoints.ai.chat, payload)
    return data
  },
  modelStatus: async (): Promise<AiModelStatus> => {
    const { data } = await httpClient.get<AiModelStatus>(endpoints.ai.modelStatus)
    return data
  },
  profileSnapshot: async (params: { user_id?: number; session_id?: string }): Promise<Record<string, unknown>> => {
    const { data } = await httpClient.get<Record<string, unknown>>(endpoints.ai.profileSnapshot, { params })
    return data
  },
}

export const interactionApi = {
  events: async (params?: Record<string, string | number>): Promise<Record<string, unknown>[]> => {
    const { data } = await httpClient.get<Record<string, unknown>[]>(endpoints.interactions.events, { params })
    return data
  },
  productGaps: async (): Promise<Record<string, unknown>[]> => {
    const { data } = await httpClient.get<Record<string, unknown>[]>(endpoints.interactions.productGaps)
    return data
  },
  topQueries: async (): Promise<Record<string, unknown>[]> => {
    const { data } = await httpClient.get<Record<string, unknown>[]>(endpoints.interactions.topQueries)
    return data
  },
  categoryInterest: async (): Promise<Record<string, unknown>[]> => {
    const { data } = await httpClient.get<Record<string, unknown>[]>(endpoints.interactions.categoryInterest)
    return data
  },
  graphStatus: async (): Promise<InteractionGraphStatus> => {
    const { data } = await httpClient.get<InteractionGraphStatus>(endpoints.interactions.graphStatus)
    return data
  },
  graphRebuild: async (): Promise<Record<string, unknown>> => {
    const { data } = await httpClient.post<Record<string, unknown>>(endpoints.interactions.graphRebuild)
    return data
  },
}
