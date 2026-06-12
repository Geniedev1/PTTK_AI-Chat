import { endpoints } from "../constants/endpoints"
import type {
  AiChatResponse,
  AiRecommendResponse,
  CartItem,
  CartSummary,
  CreatePaymentPayload,
  CreateOrderResponse,
  CreateShipperProfilePayload,
  CreateShipmentPayload,
  CustomerLoginResponse,
  CustomerProfile,
  CustomerProfileUpdatePayload,
  CustomerRegisterPayload,
  StaffLoginResponse,
  Order,
  Payment,
  Product,
  Shipment,
  ShipperProfile,
  StaffCreatePayload,
} from "../types/api"
import { httpClient } from "./httpClient"

type ListProductsParams = {
  search?: string | undefined
  tag?: string | undefined
  min_price?: number | undefined
  max_price?: number | undefined
  sort_by?: string | undefined
  in_stock?: boolean | undefined
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
  me: async (): Promise<StaffLoginResponse["staff"]> => {
    const { data } = await httpClient.get<StaffLoginResponse["staff"]>(endpoints.staff.me)
    return data
  },
  adminCreate: async (payload: StaffCreatePayload): Promise<StaffLoginResponse["staff"]> => {
    const { data } = await httpClient.post<StaffLoginResponse["staff"]>(endpoints.staff.adminCreate, payload)
    return data
  },
}

export const productApi = {
  list: async (params?: ListProductsParams): Promise<Product[]> => {
    const query = {
      ...params,
      search: params?.search?.trim() || undefined,
      in_stock: params?.in_stock ? "true" : undefined,
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
  updateStatus: async (orderId: number, status: Order["status"]): Promise<Order> => {
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
    order_id?: number
    shipper_id?: number
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
  assignShipper: async (shipmentId: number, shipperId: number): Promise<Shipment> => {
    const { data } = await httpClient.post<Shipment>(endpoints.shipping.assignShipper(shipmentId), {
      shipper_id: shipperId,
    })
    return data
  },
  listShippers: async (): Promise<ShipperProfile[]> => {
    const { data } = await httpClient.get<ShipperProfile[]>(endpoints.shipping.shippers)
    return data
  },
  createShipper: async (payload: CreateShipperProfilePayload): Promise<ShipperProfile> => {
    const { data } = await httpClient.post<ShipperProfile>(endpoints.shipping.shippers, payload)
    return data
  },
  updateShipperLocation: async (
    shipperId: number,
    payload: { current_lat: string; current_lng: string; is_available?: boolean },
  ): Promise<ShipperProfile> => {
    const { data } = await httpClient.post<ShipperProfile>(endpoints.shipping.shipperLocation(shipperId), payload)
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
}
