import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useMemo, useState } from "react"
import { useNavigate } from "react-router-dom"
import { cartApi, orderApi } from "../../shared/api/services"
import { useSessionStore } from "../../shared/stores/sessionStore"
import { getApiErrorMessage } from "../../shared/utils/apiError"

export function CartPage() {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const customerId = useSessionStore((state) => state.customerId)
  const [draftQuantity, setDraftQuantity] = useState<Record<number, number>>({})
  const [checkoutWarning, setCheckoutWarning] = useState<string | null>(null)

  const cartQuery = useQuery({
    queryKey: ["cart", "current"],
    queryFn: cartApi.current,
  })

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
      void queryClient.invalidateQueries({ queryKey: ["cart", "current"] })
    },
  })

  const createOrderMutation = useMutation({
    mutationFn: () => {
      const payload: { customer_id?: number; clear_cart?: boolean } = { clear_cart: true }
      if (customerId) {
        payload.customer_id = customerId
      }
      return orderApi.create(payload)
    },
    onSuccess: async (response) => {
      setDraftQuantity({})
      setCheckoutWarning(
        response.cart_cleared ? null : "Order was created, but cart clearing failed. Refresh cart before checkout again.",
      )
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["cart", "current"] }),
        queryClient.invalidateQueries({ queryKey: ["orders"] }),
      ])
      navigate(`/orders/${response.order.id}`)
    },
  })

  const rowBusy = useMemo(
    () => removeMutation.isPending || updateMutation.isPending || clearMutation.isPending,
    [clearMutation.isPending, removeMutation.isPending, updateMutation.isPending],
  )

  return (
    <section className="panel">
      <h1>Cart</h1>
      <p className="muted-text">Review your items, then checkout to create an order.</p>
      {cartQuery.isLoading ? <p>Loading cart...</p> : null}
      {cartQuery.isError ? <p className="error-text">{getApiErrorMessage(cartQuery.error)}</p> : null}

      {cartQuery.data ? (
        <>
          <div className="cart-summary">
            <span>Session: {cartQuery.data.session_key}</span>
            <span>Items: {cartQuery.data.item_count}</span>
            <span>Total Qty: {cartQuery.data.total_quantity}</span>
            <span>Subtotal: ${cartQuery.data.subtotal_amount}</span>
          </div>

          {cartQuery.data.items.length === 0 ? <p>Your cart is empty.</p> : null}

          {cartQuery.data.items.length > 0 ? (
            <div className="table-wrap">
              <table className="table">
                <thead>
                  <tr>
                    <th>Product</th>
                    <th>Price Snapshot</th>
                    <th>Quantity</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {cartQuery.data.items.map((item) => (
                    <tr key={item.id}>
                      <td>#{item.product_id}</td>
                      <td>{item.price_snapshot ?? "N/A"}</td>
                      <td>
                        <input
                          type="number"
                          min={1}
                          max={999}
                          value={draftQuantity[item.id] ?? item.quantity}
                          onChange={(event) => {
                            const next = Number(event.target.value)
                            setDraftQuantity((prev) => ({
                              ...prev,
                              [item.id]: Number.isFinite(next) && next > 0 ? next : 1,
                            }))
                          }}
                        />
                      </td>
                      <td>
                        <div className="row-actions">
                          <button
                            onClick={() =>
                              updateMutation.mutate({
                                product_id: item.product_id,
                                quantity: draftQuantity[item.id] ?? item.quantity,
                              })
                            }
                            disabled={rowBusy}
                          >
                            Update
                          </button>
                          <button
                            onClick={() => removeMutation.mutate(item.product_id)}
                            disabled={rowBusy}
                          >
                            Remove
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : null}

          <div className="row-actions">
            <button onClick={() => clearMutation.mutate()} disabled={rowBusy || cartQuery.data.items.length === 0}>
              Clear Cart
            </button>
            <button
              className="primary-button"
              onClick={() => createOrderMutation.mutate()}
              disabled={rowBusy || createOrderMutation.isPending || cartQuery.data.items.length === 0}
            >
              Checkout
            </button>
          </div>
        </>
      ) : null}

      {removeMutation.isError ? <p className="error-text">{getApiErrorMessage(removeMutation.error)}</p> : null}
      {updateMutation.isError ? <p className="error-text">{getApiErrorMessage(updateMutation.error)}</p> : null}
      {clearMutation.isError ? <p className="error-text">{getApiErrorMessage(clearMutation.error)}</p> : null}
      {createOrderMutation.isError ? <p className="error-text">{getApiErrorMessage(createOrderMutation.error)}</p> : null}
      {checkoutWarning ? <p className="warning-text">{checkoutWarning}</p> : null}
      {createOrderMutation.isSuccess ? (
        <p className="success-text">Order #{createOrderMutation.data.order.id} created. Opening order detail.</p>
      ) : null}
    </section>
  )
}
