import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useMemo, useState } from "react"
import { Link, useParams } from "react-router-dom"
import { aiApi, cartApi, productApi } from "../../shared/api/services"
import {
  Button,
  EmptyState,
  ErrorBanner,
  LoadingState,
  PageHeader,
  StatusBadge,
  formatCurrency,
  statusTone,
} from "../../shared/components/ui"
import { PRODUCT_PLACEHOLDER_IMAGE } from "../../shared/constants/media"
import { useSessionStore } from "../../shared/stores/sessionStore"
import { getApiErrorMessage } from "../../shared/utils/apiError"

export function ProductDetailPage() {
  const params = useParams<{ productId: string }>()
  const queryClient = useQueryClient()
  const [quantity, setQuantity] = useState(1)
  const [tab, setTab] = useState<"details" | "specs" | "recommendations">("details")
  const customerId = useSessionStore((state) => state.customerId)
  const cartSessionKey = useSessionStore((state) => state.cartSessionKey)

  const productId = useMemo(() => {
    const parsed = Number(params.productId)
    return Number.isFinite(parsed) && parsed > 0 ? parsed : null
  }, [params.productId])

  const productQuery = useQuery({
    queryKey: ["product", productId],
    queryFn: () => productApi.detail(productId as number),
    enabled: productId !== null,
  })

  const addToCartMutation = useMutation({
    mutationFn: () => cartApi.addProduct({ product_id: productId as number, quantity }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["cart", "current"] })
    },
  })

  const relatedRecommendQuery = useQuery({
    queryKey: ["ai", "recommend-product", productId, customerId ?? "guest", cartSessionKey ?? "none"],
    queryFn: () => {
      const recommendationParams: { product_id: number; user_id?: number; session_id?: string; limit?: number } = {
        product_id: productId as number,
        limit: 4,
      }
      if (customerId) {
        recommendationParams.user_id = customerId
      }
      if (cartSessionKey) {
        recommendationParams.session_id = cartSessionKey
      }
      return aiApi.recommendProductDetail(recommendationParams)
    },
    enabled: productId !== null,
  })

  const product = productQuery.data
  const maxQuantity = Math.max(1, product?.stock ?? 1)

  return (
    <div className="page-stack">
      <PageHeader
        eyebrow="Product detail"
        title={product?.name ?? "Product"}
        description="Review stock, specifications, and related recommendations before adding to cart."
      />

      {productId === null ? <ErrorBanner message="Invalid product id." /> : null}
      {productQuery.isLoading ? <LoadingState label="Loading product..." /> : null}
      {productQuery.isError ? <ErrorBanner message={getApiErrorMessage(productQuery.error)} /> : null}

      {product ? (
        <section className="product-detail-layout">
          <div className="product-media-panel">
            <img
              className="product-detail-image"
              src={product.image_urls[0] || PRODUCT_PLACEHOLDER_IMAGE}
              alt={product.name}
              onError={(event) => {
                event.currentTarget.src = PRODUCT_PLACEHOLDER_IMAGE
              }}
            />
            <div className="thumbnail-row">
              {(product.image_urls.length > 0 ? product.image_urls : [PRODUCT_PLACEHOLDER_IMAGE]).slice(0, 4).map((image, index) => (
                <img
                  key={`${image}-${index}`}
                  src={image || PRODUCT_PLACEHOLDER_IMAGE}
                  alt={`${product.name} preview ${index + 1}`}
                  onError={(event) => {
                    event.currentTarget.src = PRODUCT_PLACEHOLDER_IMAGE
                  }}
                />
              ))}
            </div>
          </div>

          <div className="product-buy-panel">
            <div className="card-title-row">
              <h2>{product.name}</h2>
              <StatusBadge tone={statusTone(product.has_stock ? "ACTIVE" : "OUT_OF_STOCK")}>
                {product.has_stock ? "In stock" : "Unavailable"}
              </StatusBadge>
            </div>
            <p>{product.short_description || product.description || "No product description available."}</p>
            <strong className="price-display">{formatCurrency(product.base_price)}</strong>
            <div className="product-meta">
              <span>Stock {product.stock}</span>
              {product.category_id ? <span>Category {product.category_id}</span> : null}
              {product.brand_id ? <span>Brand {product.brand_id}</span> : null}
            </div>

            <label className="field-inline">
              Quantity
              <input
                type="number"
                min={1}
                max={maxQuantity}
                value={quantity}
                onChange={(event) => {
                  const next = Number(event.target.value)
                  setQuantity(Number.isFinite(next) ? Math.min(Math.max(1, next), maxQuantity) : 1)
                }}
              />
            </label>

            <div className="row-actions">
              <Button
                disabled={addToCartMutation.isPending || !product.has_stock}
                variant="primary"
                onClick={() => addToCartMutation.mutate()}
              >
                Add to cart
              </Button>
              <Link className="btn btn-secondary" to="/checkout">
                Checkout
              </Link>
            </div>

            {addToCartMutation.isError ? <ErrorBanner message={getApiErrorMessage(addToCartMutation.error)} /> : null}
            {addToCartMutation.isSuccess ? <div className="success-banner">Product added to cart.</div> : null}
          </div>
        </section>
      ) : null}

      {product ? (
        <section className="section-panel">
          <div className="tabs">
            <button className={tab === "details" ? "active" : ""} onClick={() => setTab("details")}>
              Details
            </button>
            <button className={tab === "specs" ? "active" : ""} onClick={() => setTab("specs")}>
              Specifications
            </button>
            <button className={tab === "recommendations" ? "active" : ""} onClick={() => setTab("recommendations")}>
              Recommendations
            </button>
          </div>

          {tab === "details" ? (
            <div className="copy-block">
              <p>{product.full_description || product.description || product.short_description || "No detail copy available."}</p>
            </div>
          ) : null}

          {tab === "specs" ? (
            <div className="spec-grid">
              {Object.entries(product.attributes || {}).length > 0 ? (
                Object.entries(product.attributes).map(([key, value]) => (
                  <div key={key}>
                    <span>{key}</span>
                    <strong>{String(value)}</strong>
                  </div>
                ))
              ) : (
                <EmptyState title="No specifications" description="This product does not expose structured specs yet." />
              )}
            </div>
          ) : null}

          {tab === "recommendations" ? (
            <>
              {relatedRecommendQuery.isLoading ? <LoadingState label="Loading related products..." /> : null}
              {relatedRecommendQuery.isError ? <ErrorBanner message={getApiErrorMessage(relatedRecommendQuery.error)} /> : null}
              {relatedRecommendQuery.data && relatedRecommendQuery.data.items.length === 0 ? (
                <EmptyState title="No related recommendations" />
              ) : null}
              {relatedRecommendQuery.data && relatedRecommendQuery.data.items.length > 0 ? (
                <div className="product-grid compact">
                  {relatedRecommendQuery.data.items.map((item) => (
                    <article className="product-card" key={item.product.id}>
                      <img
                        className="product-card-image"
                        src={item.product.image_urls?.[0] || PRODUCT_PLACEHOLDER_IMAGE}
                        alt={item.product.name}
                        onError={(event) => {
                          event.currentTarget.src = PRODUCT_PLACEHOLDER_IMAGE
                        }}
                      />
                      <h3>{item.product.name}</h3>
                      <div className="product-meta">
                        <span>{formatCurrency(item.product.base_price)}</span>
                        <span>Score {item.score.toFixed(2)}</span>
                      </div>
                      <Link className="btn btn-secondary" to={`/products/${item.product.id}`}>
                        View
                      </Link>
                    </article>
                  ))}
                </div>
              ) : null}
            </>
          ) : null}
        </section>
      ) : null}
    </div>
  )
}
