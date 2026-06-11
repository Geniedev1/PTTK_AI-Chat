import { useQuery } from "@tanstack/react-query"
import { Link } from "react-router-dom"
import { aiApi, productApi } from "../../shared/api/services"
import { EmptyState, ErrorBanner, LoadingState, MetricCard, formatCurrency } from "../../shared/components/ui"
import { PRODUCT_PLACEHOLDER_IMAGE } from "../../shared/constants/media"
import { useSessionStore } from "../../shared/stores/sessionStore"
import { getApiErrorMessage } from "../../shared/utils/apiError"

export function HomePage() {
  const { customerUsername, customerId, cartSessionKey } = useSessionStore()

  const productsQuery = useQuery({
    queryKey: ["products", "home"],
    queryFn: () => productApi.list({ in_stock: true }),
  })

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

  const products = productsQuery.data ?? []
  const featured = products.slice(0, 6)
  const categories = Array.from(new Set(products.map((product) => product.category_id).filter(Boolean))).slice(0, 5)

  return (
    <div className="page-stack">
      <section className="home-hero">
        <div className="hero-copy">
          <span className="eyebrow">AI assisted shopping</span>
          <h1>Find the right product faster.</h1>
          <p>
            Browse curated electronics, accessories, and lifestyle products with recommendations tuned to your
            recent shopping intent.
          </p>
          <div className="hero-actions">
            <Link className="btn btn-primary" to="/products">
              Browse products
            </Link>
            <Link className="btn btn-secondary" to="/assistant">
              Ask assistant
            </Link>
          </div>
        </div>
        <div className="hero-summary">
          <MetricCard label="Welcome" value={customerUsername ?? "Guest"} hint="Personalized when signed in" />
          <MetricCard label="Available products" value={products.length} hint="Loaded from catalog service" />
          <MetricCard label="Live recommendations" value={recommendHomeQuery.data?.items.length ?? 0} hint="AI ranked" />
        </div>
      </section>

      <section className="section-panel">
        <div className="section-title-row">
          <div>
            <span className="eyebrow">Categories</span>
            <h2>Shop by collection</h2>
          </div>
          <Link to="/products">View catalog</Link>
        </div>
        <div className="category-strip">
          {categories.length > 0 ? (
            categories.map((categoryId) => (
              <Link key={categoryId} className="category-pill" to={`/products?category=${categoryId}`}>
                Category {categoryId}
              </Link>
            ))
          ) : (
            <>
              <Link className="category-pill" to="/products">
                Laptops
              </Link>
              <Link className="category-pill" to="/products">
                Accessories
              </Link>
              <Link className="category-pill" to="/products">
                Audio
              </Link>
            </>
          )}
        </div>
      </section>

      <section className="section-panel">
        <div className="section-title-row">
          <div>
            <span className="eyebrow">Recommended</span>
            <h2>Picked for this session</h2>
          </div>
          <Link to="/products">Explore more</Link>
        </div>
        {recommendHomeQuery.isLoading ? <LoadingState label="Loading recommendations..." /> : null}
        {recommendHomeQuery.isError ? <ErrorBanner message={getApiErrorMessage(recommendHomeQuery.error)} /> : null}
        {recommendHomeQuery.data && recommendHomeQuery.data.items.length === 0 ? (
          <EmptyState title="No recommendations yet" description="Browse a few products to shape your session." />
        ) : null}
        {recommendHomeQuery.data && recommendHomeQuery.data.items.length > 0 ? (
          <div className="product-grid">
            {recommendHomeQuery.data.items.map((item) => (
              <article className="product-card" key={item.product.id}>
                <img
                  className="product-card-image"
                  src={item.product.image_urls?.[0] || PRODUCT_PLACEHOLDER_IMAGE}
                  alt={item.product.name}
                  onError={(event) => {
                    event.currentTarget.src = PRODUCT_PLACEHOLDER_IMAGE
                  }}
                />
                <div>
                  <h3>{item.product.name}</h3>
                  <p>{item.product.short_description || "Recommended product"}</p>
                </div>
                <div className="product-meta">
                  <span>{formatCurrency(item.product.base_price)}</span>
                  <span>Score {item.score.toFixed(2)}</span>
                </div>
                <Link className="btn btn-secondary" to={`/products/${item.product.id}`}>
                  View product
                </Link>
              </article>
            ))}
          </div>
        ) : null}
      </section>

      <section className="section-panel">
        <div className="section-title-row">
          <div>
            <span className="eyebrow">Popular</span>
            <h2>Ready to ship</h2>
          </div>
        </div>
        {productsQuery.isLoading ? <LoadingState label="Loading products..." /> : null}
        {productsQuery.isError ? <ErrorBanner message={getApiErrorMessage(productsQuery.error)} /> : null}
        {featured.length > 0 ? (
          <div className="product-grid compact">
            {featured.map((product) => (
              <article className="product-card" key={product.id}>
                <img
                  className="product-card-image"
                  src={product.image_urls[0] || PRODUCT_PLACEHOLDER_IMAGE}
                  alt={product.name}
                  onError={(event) => {
                    event.currentTarget.src = PRODUCT_PLACEHOLDER_IMAGE
                  }}
                />
                <div>
                  <h3>{product.name}</h3>
                  <p>{product.short_description || product.description || "Available now"}</p>
                </div>
                <div className="product-meta">
                  <span>{formatCurrency(product.base_price)}</span>
                  <span>{product.stock} in stock</span>
                </div>
                <Link className="btn btn-secondary" to={`/products/${product.id}`}>
                  View product
                </Link>
              </article>
            ))}
          </div>
        ) : null}
      </section>
    </div>
  )
}
