import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useMemo, useState } from "react"
import { Link } from "react-router-dom"
import { cartApi, productApi } from "../../shared/api/services"
import {
  Button,
  EmptyState,
  ErrorBanner,
  LoadingState,
  PageHeader,
  StatusBadge,
  formatCurrency,
} from "../../shared/components/ui"
import { PRODUCT_PLACEHOLDER_IMAGE } from "../../shared/constants/media"
import { getApiErrorMessage } from "../../shared/utils/apiError"

export function CartPage() {
  const queryClient = useQueryClient()
  const [draftQuantity, setDraftQuantity] = useState<Record<number, number>>({})

  const cartQuery = useQuery({
    queryKey: ["cart", "current"],
    queryFn: cartApi.current,
  })

  const productsQuery = useQuery({
    queryKey: ["products", "cart-lookup"],
    queryFn: () => productApi.list(),
  })

  const productById = useMemo(() => {
    const rows = productsQuery.data ?? []
    return new Map(rows.map((product) => [product.id, product]))
  }, [productsQuery.data])

  const removeMutation = useMutation({
    mutationFn: (productId: number) => cartApi.removeProduct({ product_id: productId }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["cart", "current"] })
    },
  })

  const updateMutation = useMutation({
    mutationFn: (payload: { product_id: number; quantity: number }) => cartApi.updateQuantity(payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["cart", "current"] })
    },
  })

  const clearMutation = useMutation({
    mutationFn: () => cartApi.clear(),
    onSuccess: () => {
      setDraftQuantity({})
      void queryClient.invalidateQueries({ queryKey: ["cart", "current"] })
    },
  })

  const cart = cartQuery.data
  const rowBusy = removeMutation.isPending || updateMutation.isPending || clearMutation.isPending
  const subtotal = Number(cart?.subtotal_amount ?? 0)
  const estimatedShipping = cart && cart.items.length > 0 ? 4.99 : 0
  const total = subtotal + estimatedShipping

  return (
    <div className="page-stack">
      <PageHeader
        eyebrow="Cart"
        title="Review your cart"
        description="Adjust quantities, confirm stock, and continue to checkout when ready."
        actions={
          cart && cart.items.length > 0 ? (
            <Link className="btn btn-primary" to="/checkout">
              Proceed to checkout
            </Link>
          ) : null
        }
      />

      {cartQuery.isLoading ? <LoadingState label="Loading cart..." /> : null}
      {cartQuery.isError ? <ErrorBanner message={getApiErrorMessage(cartQuery.error)} /> : null}
      {productsQuery.isError ? <ErrorBanner message={getApiErrorMessage(productsQuery.error)} /> : null}

      {cart && cart.items.length === 0 ? (
        <EmptyState
          title="Your cart is empty"
          description="Add products from the catalog to start a checkout."
          action={
            <Link className="btn btn-primary" to="/products">
              Browse products
            </Link>
          }
        />
      ) : null}

      {cart && cart.items.length > 0 ? (
        <section className="cart-layout">
          <div className="cart-lines">
            {cart.items.map((item) => {
              const product = productById.get(item.product_id)
              const price = Number(item.price_snapshot ?? product?.base_price ?? 0)
              const quantity = draftQuantity[item.id] ?? item.quantity
              const maxQuantity = Math.max(1, product?.stock ?? 999)

              return (
                <article className="cart-line" key={item.id}>
                  <img
                    src={product?.image_urls[0] || PRODUCT_PLACEHOLDER_IMAGE}
                    alt={product?.name ?? `Product ${item.product_id}`}
                    onError={(event) => {
                      event.currentTarget.src = PRODUCT_PLACEHOLDER_IMAGE
                    }}
                  />
                  <div className="cart-line-main">
                    <div className="card-title-row">
                      <div>
                        <h3>{product?.name ?? `Product #${item.product_id}`}</h3>
                        <p>{product?.short_description || product?.description || "Product snapshot from cart."}</p>
                      </div>
                      <StatusBadge tone={product?.has_stock === false ? "danger" : "success"}>
                        {product?.has_stock === false ? "Unavailable" : "Available"}
                      </StatusBadge>
                    </div>
                    <div className="product-meta">
                      <span>{formatCurrency(price)} each</span>
                      <span>{formatCurrency(price * quantity)} line total</span>
                    </div>
                    <div className="cart-line-actions">
                      <label>
                        Quantity
                        <input
                          type="number"
                          min={1}
                          max={maxQuantity}
                          value={quantity}
                          onChange={(event) => {
                            const next = Number(event.target.value)
                            setDraftQuantity((prev) => ({
                              ...prev,
                              [item.id]: Number.isFinite(next) ? Math.min(Math.max(1, next), maxQuantity) : 1,
                            }))
                          }}
                        />
                      </label>
                      <Button
                        disabled={rowBusy}
                        onClick={() =>
                          updateMutation.mutate({
                            product_id: item.product_id,
                            quantity,
                          })
                        }
                      >
                        Update
                      </Button>
                      <Button disabled={rowBusy} variant="ghost" onClick={() => removeMutation.mutate(item.product_id)}>
                        Remove
                      </Button>
                    </div>
                  </div>
                </article>
              )
            })}
          </div>

          <aside className="order-summary">
            <h2>Summary</h2>
            <div className="summary-row">
              <span>Items</span>
              <strong>{cart.item_count}</strong>
            </div>
            <div className="summary-row">
              <span>Total quantity</span>
              <strong>{cart.total_quantity}</strong>
            </div>
            <div className="summary-row">
              <span>Subtotal</span>
              <strong>{formatCurrency(subtotal)}</strong>
            </div>
            <div className="summary-row">
              <span>Estimated shipping</span>
              <strong>{formatCurrency(estimatedShipping)}</strong>
            </div>
            <div className="summary-row total">
              <span>Total</span>
              <strong>{formatCurrency(total)}</strong>
            </div>
            <Link className="btn btn-primary full-width" to="/checkout">
              Continue checkout
            </Link>
            <Button disabled={rowBusy} variant="ghost" onClick={() => clearMutation.mutate()}>
              Clear cart
            </Button>
          </aside>
        </section>
      ) : null}

      {removeMutation.isError ? <ErrorBanner message={getApiErrorMessage(removeMutation.error)} /> : null}
      {updateMutation.isError ? <ErrorBanner message={getApiErrorMessage(updateMutation.error)} /> : null}
      {clearMutation.isError ? <ErrorBanner message={getApiErrorMessage(clearMutation.error)} /> : null}
    </div>
  )
}
