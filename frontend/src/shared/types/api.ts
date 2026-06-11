export type UserSummary = {
  id: number
  username: string
  email: string
  first_name: string
  last_name: string
}

export type CustomerProfile = {
  id: number
  user: UserSummary
  phone: string
  address: string
  city: string
  country: string
  created_at: string
  updated_at: string
}

export type CustomerLoginResponse = {
  token: string
  customer: CustomerProfile
}

export type StaffProfile = {
  id: number
  user: UserSummary
  name: string
  phone: string
  position: string
  created_at: string
  updated_at: string
}

export type StaffLoginResponse = {
  token: string
  staff: StaffProfile
}

export type CustomerRegisterPayload = {
  username: string
  password: string
  email: string
  phone?: string
  address?: string
  city?: string
  country?: string
}

export type CustomerProfileUpdatePayload = {
  phone?: string
  address?: string
  city?: string
  country?: string
}

export type ProductVariant = {
  id: number
  sku: string
  name: string
  attributes: Record<string, unknown>
  stock: number
  price_override: string | null
  is_default: boolean
}

export type Product = {
  id: number
  name: string
  slug: string
  short_description: string
  description: string
  full_description: string
  category_id: number | null
  brand_id: number | null
  product_type_id: number | null
  base_price: string
  stock: number
  attributes: Record<string, unknown>
  is_active: boolean
  status: string
  tags: string[]
  image_urls: string[]
  has_stock: boolean
  variants: ProductVariant[]
}

export type CartItem = {
  id: number
  session_key: string
  product_id: number
  quantity: number
  price_snapshot: string | null
  created_at: string
  updated_at: string
}

export type CartSummary = {
  session_key: string
  items: CartItem[]
  item_count: number
  total_quantity: number
  subtotal_amount: string
}

export type OrderItem = {
  id: number
  product_id: number
  product_name_snapshot: string
  price_snapshot: string
  quantity: number
  created_at: string
}

export type Order = {
  id: number
  customer_id: number | null
  session_key: string
  status: "PENDING" | "CONFIRMED" | "PAID" | "CANCELLED" | "COMPLETED"
  total_amount: string
  purchase_succeeded: boolean
  purchase_event: string | null
  confirmed_at: string | null
  paid_at: string | null
  completed_at: string | null
  cancelled_at: string | null
  items: OrderItem[]
  created_at: string
  updated_at: string
}

export type CreateOrderResponse = {
  order: Order
  cart_cleared: boolean
}

export type Payment = {
  id: number
  order_id: number
  customer_id: number | null
  session_key: string | null
  amount: string
  currency: string
  provider: string
  provider_reference: string
  status: "PENDING" | "PROCESSING" | "PAID" | "FAILED" | "CANCELLED" | "REFUNDED"
  failure_reason: string
  idempotency_key: string | null
  paid_at: string | null
  failed_at: string | null
  cancelled_at: string | null
  refunded_at: string | null
  created_at: string
  updated_at: string
}

export type CreatePaymentPayload = {
  order_id: number
  customer_id?: number
  session_key?: string
  currency?: string
  provider?: string
  method_type?: string
  masked_account?: string
  idempotency_key?: string
}

export type Shipment = {
  id: number
  order_id: number
  customer_id: number | null
  session_key: string | null
  recipient_name: string
  phone: string
  address: string
  city: string
  country: string
  carrier: string
  tracking_number: string
  shipping_fee: string
  status: "PENDING" | "READY_TO_SHIP" | "SHIPPED" | "DELIVERED" | "FAILED" | "CANCELLED"
  failure_reason: string
  shipped_at: string | null
  delivered_at: string | null
  cancelled_at: string | null
  created_at: string
  updated_at: string
}

export type CreateShipmentPayload = {
  order_id: number
  customer_id?: number
  session_key?: string
  recipient_name: string
  phone: string
  address: string
  city?: string
  country?: string
  carrier?: string
  shipping_fee?: string
}

export type AiRecommendationProduct = {
  id: number
  name: string
  slug: string
  short_description: string
  category_id: number | null
  brand_id: number | null
  base_price: string
  stock: number
  has_stock: boolean
  tags: string[]
  image_urls?: string[]
}

export type AiRecommendationItem = {
  product: AiRecommendationProduct
  score: number
  deep_model_score?: number | null
  reason_codes: string[]
  source_signals?: Record<string, unknown>
}

export type AiRecommendResponse = {
  context: Record<string, unknown>
  items: AiRecommendationItem[]
}

export type AiModelStatus = {
  recommendation_limit_default?: number
  recommendation_limit_max?: number
  deep_model?: {
    enabled: boolean
    loaded: boolean
    model_version: string
    artifact_dir: string
    alpha: number
    fallback_mode: string
    error?: string | null
  }
  [key: string]: unknown
}

export type InteractionGraphStatus = {
  enabled: boolean
  connected?: boolean
  graph_sync_on_write?: boolean
  node_counts?: Record<string, number>
  relationship_counts?: Record<string, number>
}

export type AiChatSource = {
  source_type: string
  source_id: string
  title: string
  excerpt: string
}

export type AiChatResponse = {
  answer: string
  sources: AiChatSource[]
  used_realtime_api: boolean
  used_graph_context: boolean
  retrieval_mode: string
  profile_snapshot?: Record<string, unknown>
}
