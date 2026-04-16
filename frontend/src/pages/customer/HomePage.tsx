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
    <div className="home-page">
      <section className="panel home-hero">
        <p className="eyebrow">Smart Commerce Platform</p>
        <h1>Professional storefront for business-ready online selling</h1>
        <p className="lead">
          Manage customer sessions, product discovery, cart flow, order creation, and AI recommendations in one
          unified experience.
        </p>
        <div className="hero-actions">
          <Link to="/products">Explore Catalog</Link>
          <Link to="/assistant">Talk to AI Assistant</Link>
          {!customerToken ? <Link to="/auth/login">Customer Login</Link> : <Link to="/profile">Open Profile</Link>}
        </div>
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
      </section>

      <section className="panel">
        <h2>Why businesses choose this frontend</h2>
        <div className="feature-grid">
          <div className="feature-card">
            <h3>Reliable order workflow</h3>
            <p>From product listing to checkout and order tracking, the full core purchase flow is connected.</p>
          </div>
          <div className="feature-card">
            <h3>AI-driven engagement</h3>
            <p>Support product discovery with recommendation endpoints and conversational assistant features.</p>
          </div>
          <div className="feature-card">
            <h3>Customer-first UX</h3>
            <p>Provide login, profile management, and persistent cart context for a better shopping journey.</p>
          </div>
        </div>
      </section>

      <section className="panel ai-section">
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
    </div>
  )
}
