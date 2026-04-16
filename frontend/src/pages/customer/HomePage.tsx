import { useQuery } from "@tanstack/react-query"
import { Link } from "react-router-dom"
import { aiApi } from "../../shared/api/services"
import { useSessionStore } from "../../shared/stores/sessionStore"
import { getApiErrorMessage } from "../../shared/utils/apiError"

export function HomePage() {
  const { customerToken, customerUsername, customerId, cartSessionKey } = useSessionStore()

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

  return (
    <section className="panel">
      <h1>Commerce Frontend</h1>
      <p>
        Core Phase B flow is live: customer auth, products, cart, and order creation through gateway-backed
        APIs.
      </p>
      <div className="status-grid">
        <div className="status-item">
          <strong>Auth</strong>
          <span>{customerToken ? `Logged in as ${customerUsername ?? "customer"}` : "Guest mode"}</span>
        </div>
        <div className="status-item">
          <strong>Customer ID Scope</strong>
          <span>{customerId ?? "Not set"}</span>
        </div>
        <div className="status-item">
          <strong>Cart Session</strong>
          <span>{cartSessionKey ?? "Will be created on first cart call"}</span>
        </div>
      </div>
      <div className="quick-links">
        <Link to="/auth/login">Login</Link>
        <Link to="/auth/register">Register</Link>
        <Link to="/products">Browse Products</Link>
        <Link to="/cart">Open Cart</Link>
        <Link to="/orders">View Orders</Link>
        <Link to="/profile">Profile</Link>
      </div>

      <section className="ai-section">
        <h2>AI Home Recommendations</h2>
        {recommendHomeQuery.isLoading ? <p>Loading recommendations...</p> : null}
        {recommendHomeQuery.isError ? (
          <p className="error-text">{getApiErrorMessage(recommendHomeQuery.error)}</p>
        ) : null}
        {recommendHomeQuery.data && recommendHomeQuery.data.items.length === 0 ? (
          <p>No recommendations yet.</p>
        ) : null}

        {recommendHomeQuery.data && recommendHomeQuery.data.items.length > 0 ? (
          <div className="product-grid">
            {recommendHomeQuery.data.items.map((item) => (
              <article className="product-card" key={item.product.id}>
                <h3>{item.product.name}</h3>
                <p>{item.product.short_description || "Recommended for you"}</p>
                <div className="product-meta">
                  <span>${item.product.base_price}</span>
                  <span>Score {item.score.toFixed(2)}</span>
                </div>
                <div className="row-actions">
                  <Link to={`/products/${item.product.id}`}>Open Product</Link>
                </div>
              </article>
            ))}
          </div>
        ) : null}
      </section>
    </section>
  )
}
