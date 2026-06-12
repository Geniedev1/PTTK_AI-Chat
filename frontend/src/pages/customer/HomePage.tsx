import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Link } from "react-router-dom"
import { aiApi, cartApi } from "../../shared/api/services"
import { PRODUCT_PLACEHOLDER_IMAGE } from "../../shared/constants/media"
import { useSessionStore } from "../../shared/stores/sessionStore"
import { getApiErrorMessage } from "../../shared/utils/apiError"

const categories = [
  {
    title: "Electronics",
    image: "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?auto=format&fit=crop&w=480&q=80",
  },
  {
    title: "Fashion",
    image: "https://images.unsplash.com/photo-1523398002811-999ca8dec234?auto=format&fit=crop&w=480&q=80",
  },
  {
    title: "Home",
    image: "https://images.unsplash.com/photo-1540932239986-30128078f3c5?auto=format&fit=crop&w=480&q=80",
  },
]

export function HomePage() {
  const queryClient = useQueryClient()
  const { customerId, cartSessionKey } = useSessionStore()

  const recommendHomeQuery = useQuery({
    queryKey: ["ai", "recommend-home", customerId ?? "guest", cartSessionKey ?? "none"],
    queryFn: () => {
      const params: { user_id?: number; session_id?: string; limit?: number } = { limit: 6 }
      if (customerId) {
        params.user_id = customerId
      }
      if (cartSessionKey) {
        params.session_id = cartSessionKey
      }
      return aiApi.recommendHome(params)
    },
  })

  const addToCartMutation = useMutation({
    mutationFn: (productId: number) => cartApi.addProduct({ product_id: productId, quantity: 1 }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["cart", "current"] })
    },
  })

  return (
    <section className="storefront-page">
      <div className="home-hero">
        <div className="home-hero-copy">
          <h1>Unlock Exclusive AI-Driven Deals!</h1>
          <p>Personalized savings curated just for you. Shop smarter today.</p>
          <Link className="primary-button" to="/products">
            Explore AI Deals
          </Link>
        </div>
        <div className="ai-hero-art" aria-hidden="true">
          <span className="ai-card ai-card-left" />
          <span className="ai-bot">
            <span />
          </span>
          <span className="ai-card ai-card-right" />
        </div>
      </div>

      <section className="store-section">
        <h2>Featured Categories</h2>
        <div className="category-grid">
          {categories.map((category) => (
            <Link className="category-card" to="/products" key={category.title}>
              <div>
                <h3>{category.title}</h3>
                <span>Shop Now -&gt;</span>
              </div>
              <img src={category.image} alt={category.title} loading="lazy" />
            </Link>
          ))}
        </div>
      </section>

      <section className="store-section">
        <h2>Recommended for You</h2>
        {recommendHomeQuery.isLoading ? <p>Loading recommendations...</p> : null}
        {recommendHomeQuery.isError ? (
          <p className="error-text">{getApiErrorMessage(recommendHomeQuery.error)}</p>
        ) : null}
        {recommendHomeQuery.data && recommendHomeQuery.data.items.length === 0 ? (
          <p>No recommendations yet.</p>
        ) : null}

        {recommendHomeQuery.data && recommendHomeQuery.data.items.length > 0 ? (
          <div className="home-product-strip">
            {recommendHomeQuery.data.items.map((item) => (
              <article className="product-card" key={item.product.id}>
                <img
                  className="product-card-image"
                  src={item.product.image_urls?.[0] || PRODUCT_PLACEHOLDER_IMAGE}
                  alt={item.product.name}
                  loading="lazy"
                  onError={(event) => {
                    event.currentTarget.src = PRODUCT_PLACEHOLDER_IMAGE
                  }}
                />
                <h3>{item.product.name}</h3>
                <div className="product-meta">
                  <strong>${item.product.base_price}</strong>
                  <span>Rating 4.8</span>
                </div>
                <div className="row-actions">
                  <button
                    onClick={() => addToCartMutation.mutate(item.product.id)}
                    disabled={addToCartMutation.isPending || !item.product.has_stock}
                  >
                    Add to Cart
                  </button>
                  <Link to={`/products/${item.product.id}`}>View</Link>
                </div>
              </article>
            ))}
          </div>
        ) : null}
        {addToCartMutation.isError ? <p className="error-text">{getApiErrorMessage(addToCartMutation.error)}</p> : null}
        {addToCartMutation.isSuccess ? <p className="success-text">Added product to cart.</p> : null}
      </section>
      <Link className="floating-ai-assistant" to="/assistant">
        <span>AI</span>
        AI Assistant
      </Link>
    </section>
  )
}
