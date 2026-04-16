const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost"

const paths = {
  staff: {
    login: "/api/staff/login/",
    me: "/api/staff/me/",
    register: "/api/staff/register/",
  },
  customers: {
    register: "/api/customers/register/",
    login: "/api/customers/login/",
    profile: "/api/customers/profile/",
    updateProfile: "/api/customers/update_profile/",
  },
  products: {
    list: "/api/products/",
    search: "/api/products/search/",
    inStock: "/api/products/in_stock/",
    detail: (id: string | number) => `/api/products/${id}/`,
    categories: "/api/products/categories/",
    categoryDetail: (id: string | number) => `/api/products/categories/${id}/`,
    create: "/api/products/",
    update: (id: string | number) => `/api/products/${id}/`,
    remove: (id: string | number) => `/api/products/${id}/`,
    variants: (id: string | number) => `/api/products/${id}/variants/`,
  },
  cart: {
    current: "/api/cart/current",
    addProduct: "/api/cart/add_product",
    removeProduct: "/api/cart/remove_product",
    updateQuantity: "/api/cart/update_quantity",
    clear: "/api/cart/clear_cart",
  },
  orders: {
    list: "/api/orders",
    detail: (id: string | number) => `/api/orders/${id}`,
    create: "/api/orders",
    updateStatus: (id: string | number) => `/api/orders/${id}/update_status`,
  },
  interactions: {
    events: "/api/interactions/events",
    dataQuality: "/api/interactions/events/data_quality",
    topQueries: "/api/interactions/events/top_queries",
    productGaps: "/api/interactions/events/product_gaps",
    abandonedCarts: "/api/interactions/events/abandoned_carts",
    categoryInterest: "/api/interactions/events/category_interest",
    signalWeights: "/api/interactions/events/signal_weights",
    graphStatus: "/api/interactions/graph/status",
    graphRebuild: "/api/interactions/graph/rebuild",
    userInterest: "/api/interactions/graph/user_interest",
    productNeighbors: "/api/interactions/graph/product_neighbors",
    queryPaths: "/api/interactions/graph/query_paths",
    similarUsers: "/api/interactions/graph/similar_users",
  },
  ai: {
    recommendHome: "/api/ai/recommend/home",
    recommendProductDetail: "/api/ai/recommend/product-detail",
    recommendCart: "/api/ai/recommend/cart",
    recommendProfileSnapshot: "/api/ai/recommend/profile/snapshot",
    profileSnapshot: "/api/ai/profile/snapshot",
    modelStatus: "/api/ai/models/status",
    chat: "/api/ai/chat",
    chatRetrieve: "/api/ai/chat/retrieve",
  },
}

export const endpoints = {
  baseUrl: API_BASE_URL,
  ...paths,
}
