import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useMemo, useState } from "react"
import { Link } from "react-router-dom"
import { useParams } from "react-router-dom"
import { aiApi, cartApi, productApi } from "../../shared/api/services"
import { PRODUCT_PLACEHOLDER_IMAGE } from "../../shared/constants/media"
import { useSessionStore } from "../../shared/stores/sessionStore"
import { getApiErrorMessage } from "../../shared/utils/apiError"

export function ProductDetailPage() {
  const params = useParams<{ productId: string }>()
  const queryClient = useQueryClient()
  const [quantity, setQuantity] = useState(1)
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
      const params: { product_id: number; user_id?: number; session_id?: string; limit?: number } = {
        product_id: productId as number,
        limit: 4,
      }
      if (customerId) {
        params.user_id = customerId
      }
      if (cartSessionKey) {
        params.session_id = cartSessionKey
      }
      return aiApi.recommendProductDetail(params)
    },
    enabled: productId !== null,
  })

  return (
    <section className="panel">
      <h1>Product Detail</h1>
      {productId === null ? <p className="error-text">Invalid product id.</p> : null}

      {productQuery.isLoading ? <p>Loading product detail...</p> : null}
      {productQuery.isError ? <p className="error-text">{getApiErrorMessage(productQuery.error)}</p> : null}

      {productQuery.data ? (
        <div className="detail-block">
          <img
            className="product-detail-image"
            src={productQuery.data.image_urls[0] || PRODUCT_PLACEHOLDER_IMAGE}
            alt={productQuery.data.name}
            loading="lazy"
            onError={(event) => {
              event.currentTarget.src = PRODUCT_PLACEHOLDER_IMAGE
            }}
          />
          <h2>{productQuery.data.name}</h2>
          <p>{productQuery.data.description || productQuery.data.short_description || "No description"}</p>
          <div className="product-meta">
            <span>Price: ${productQuery.data.base_price}</span>
            <span>{productQuery.data.has_stock ? `Stock ${productQuery.data.stock}` : "Out of stock"}</span>
          </div>
          <label className="field-inline">
            Quantity
            <input
              type="number"
              min={1}
              max={99}
              value={quantity}
              onChange={(event) => {
                const next = Number(event.target.value)
                setQuantity(Number.isFinite(next) && next > 0 ? next : 1)
              }}
            />
          </label>
          <button
            className="primary-button"
            onClick={() => addToCartMutation.mutate()}
            disabled={addToCartMutation.isPending || !productQuery.data.has_stock}
          >
            Add To Cart
          </button>
        </div>
      ) : null}

      {addToCartMutation.isError ? <p className="error-text">{getApiErrorMessage(addToCartMutation.error)}</p> : null}
      {addToCartMutation.isSuccess ? <p className="success-text">Product added to cart.</p> : null}

      <section className="ai-section">
        <h2>Related Recommendations</h2>
        {relatedRecommendQuery.isLoading ? <p>Loading related recommendations...</p> : null}
        {relatedRecommendQuery.isError ? (
          <p className="error-text">{getApiErrorMessage(relatedRecommendQuery.error)}</p>
        ) : null}

        {relatedRecommendQuery.data && relatedRecommendQuery.data.items.length === 0 ? (
          <p>No related recommendations.</p>
        ) : null}

        {relatedRecommendQuery.data && relatedRecommendQuery.data.items.length > 0 ? (
          <div className="product-grid">
            {relatedRecommendQuery.data.items.map((item) => (
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
                <p>{item.product.short_description || "Recommended alternative"}</p>
                <div className="product-meta">
                  <span>${item.product.base_price}</span>
                  <span>Score {item.score.toFixed(2)}</span>
                </div>
                <div className="row-actions">
                  <Link to={`/products/${item.product.id}`}>View</Link>
                </div>
              </article>
            ))}
          </div>
        ) : null}
      </section>
    </section>
  )
}
