import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useMemo, useState } from "react"
import { Link, useNavigate } from "react-router-dom"
import { cartApi, orderApi, paymentApi, productApi, shippingApi } from "../../shared/api/services"
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
import { useSessionStore } from "../../shared/stores/sessionStore"
import { getApiErrorMessage } from "../../shared/utils/apiError"

type ShippingForm = {
  recipient_name: string
  phone: string
  address: string
  city: string
  country: string
}

const initialShipping: ShippingForm = {
  recipient_name: "",
  phone: "",
  address: "",
  city: "",
  country: "VN",
}

export function CheckoutPage() {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const customerId = useSessionStore((state) => state.customerId)
  const cartSessionKey = useSessionStore((state) => state.cartSessionKey)
  const [step, setStep] = useState<1 | 2 | 3>(1)
  const [shipping, setShipping] = useState<ShippingForm>(initialShipping)

  const cartQuery = useQuery({
    queryKey: ["cart", "current"],
    queryFn: cartApi.current,
  })

  const productsQuery = useQuery({
    queryKey: ["products", "checkout-lookup"],
    queryFn: () => productApi.list(),
  })

  const productById = useMemo(() => {
    const rows = productsQuery.data ?? []
    return new Map(rows.map((product) => [product.id, product]))
  }, [productsQuery.data])

  const checkoutMutation = useMutation({
    mutationFn: async () => {
      const orderPayload: { customer_id?: number; clear_cart?: boolean } = { clear_cart: true }
      if (customerId) {
        orderPayload.customer_id = customerId
      }
      const orderResult = await orderApi.create(orderPayload)
      const order = orderResult.order
      const sessionKey = order.session_key || cartSessionKey || cartQuery.data?.session_key
      const scopePayload = customerId ? { customer_id: customerId } : { session_key: sessionKey }

      const payment = await paymentApi.create({
        order_id: order.id,
        ...scopePayload,
        provider: "mock",
        method_type: "mock-card",
        idempotency_key: `checkout-${order.id}`,
      })
      const paidPayment = await paymentApi.confirm(payment.id)
      const shipment = await shippingApi.createShipment({
        order_id: order.id,
        ...scopePayload,
        recipient_name: shipping.recipient_name.trim(),
        phone: shipping.phone.trim(),
        address: shipping.address.trim(),
        city: shipping.city.trim(),
        country: shipping.country.trim(),
        carrier: "mock",
        shipping_fee: "4.99",
      })

      return { order, payment: paidPayment, shipment }
    },
    onSuccess: (result) => {
      void queryClient.invalidateQueries({ queryKey: ["cart", "current"] })
      void queryClient.invalidateQueries({ queryKey: ["orders"] })
      void queryClient.invalidateQueries({ queryKey: ["payments"] })
      void queryClient.invalidateQueries({ queryKey: ["shipments"] })
      void navigate(`/orders/${result.order.id}`)
    },
  })

  const cart = cartQuery.data
  const subtotal = Number(cart?.subtotal_amount ?? 0)
  const shippingFee = cart && cart.items.length > 0 ? 4.99 : 0
  const total = subtotal + shippingFee
  const shippingReady = Boolean(shipping.recipient_name.trim() && shipping.phone.trim() && shipping.address.trim())

  return (
    <div className="page-stack">
      <PageHeader
        eyebrow="Checkout"
        title="Complete your order"
        description="Review your cart, confirm delivery details, and pay with the mock checkout flow."
      />

      <div className="checkout-steps">
        <button className={step === 1 ? "active" : ""} onClick={() => setStep(1)}>
          1. Review
        </button>
        <button className={step === 2 ? "active" : ""} onClick={() => setStep(2)} disabled={!cart?.items.length}>
          2. Shipping
        </button>
        <button className={step === 3 ? "active" : ""} onClick={() => setStep(3)} disabled={!shippingReady}>
          3. Payment
        </button>
      </div>

      {cartQuery.isLoading ? <LoadingState label="Loading checkout..." /> : null}
      {cartQuery.isError ? <ErrorBanner message={getApiErrorMessage(cartQuery.error)} /> : null}

      {cart && cart.items.length === 0 ? (
        <EmptyState
          title="Nothing to checkout"
          description="Your cart is empty."
          action={
            <Link className="btn btn-primary" to="/products">
              Browse products
            </Link>
          }
        />
      ) : null}

      {cart && cart.items.length > 0 ? (
        <section className="checkout-layout">
          <div className="checkout-main">
            {step === 1 ? (
              <div className="section-panel">
                <h2>Order review</h2>
                <div className="checkout-items">
                  {cart.items.map((item) => {
                    const product = productById.get(item.product_id)
                    const price = Number(item.price_snapshot ?? product?.base_price ?? 0)
                    return (
                      <div className="checkout-item" key={item.id}>
                        <img
                          src={product?.image_urls[0] || PRODUCT_PLACEHOLDER_IMAGE}
                          alt={product?.name ?? `Product ${item.product_id}`}
                          onError={(event) => {
                            event.currentTarget.src = PRODUCT_PLACEHOLDER_IMAGE
                          }}
                        />
                        <div>
                          <strong>{product?.name ?? `Product #${item.product_id}`}</strong>
                          <span>
                            {item.quantity} x {formatCurrency(price)}
                          </span>
                        </div>
                        <strong>{formatCurrency(price * item.quantity)}</strong>
                      </div>
                    )
                  })}
                </div>
                <div className="row-actions">
                  <Button variant="primary" onClick={() => setStep(2)}>
                    Continue to shipping
                  </Button>
                  <Link className="btn btn-secondary" to="/cart">
                    Edit cart
                  </Link>
                </div>
              </div>
            ) : null}

            {step === 2 ? (
              <div className="section-panel">
                <h2>Shipping details</h2>
                <div className="form-grid">
                  <label>
                    Recipient name
                    <input
                      className="field"
                      value={shipping.recipient_name}
                      onChange={(event) => setShipping((prev) => ({ ...prev, recipient_name: event.target.value }))}
                    />
                  </label>
                  <label>
                    Phone
                    <input
                      className="field"
                      value={shipping.phone}
                      onChange={(event) => setShipping((prev) => ({ ...prev, phone: event.target.value }))}
                    />
                  </label>
                  <label>
                    Address
                    <input
                      className="field"
                      value={shipping.address}
                      onChange={(event) => setShipping((prev) => ({ ...prev, address: event.target.value }))}
                    />
                  </label>
                  <label>
                    City
                    <input
                      className="field"
                      value={shipping.city}
                      onChange={(event) => setShipping((prev) => ({ ...prev, city: event.target.value }))}
                    />
                  </label>
                  <label>
                    Country
                    <input
                      className="field"
                      value={shipping.country}
                      onChange={(event) => setShipping((prev) => ({ ...prev, country: event.target.value }))}
                    />
                  </label>
                </div>
                <div className="row-actions">
                  <Button disabled={!shippingReady} variant="primary" onClick={() => setStep(3)}>
                    Continue to payment
                  </Button>
                  <Button variant="ghost" onClick={() => setStep(1)}>
                    Back
                  </Button>
                </div>
              </div>
            ) : null}

            {step === 3 ? (
              <div className="section-panel">
                <h2>Payment</h2>
                <div className="payment-box">
                  <StatusBadge tone="info">Mock payment</StatusBadge>
                  <p>The demo payment flow creates a payment, confirms it, then opens a pending shipment.</p>
                </div>
                <div className="row-actions">
                  <Button
                    disabled={checkoutMutation.isPending || !shippingReady}
                    variant="primary"
                    onClick={() => checkoutMutation.mutate()}
                  >
                    {checkoutMutation.isPending ? "Processing..." : "Place order"}
                  </Button>
                  <Button variant="ghost" onClick={() => setStep(2)}>
                    Back
                  </Button>
                </div>
                {checkoutMutation.isError ? <ErrorBanner message={getApiErrorMessage(checkoutMutation.error)} /> : null}
              </div>
            ) : null}
          </div>

          <aside className="order-summary">
            <h2>Checkout summary</h2>
            <div className="summary-row">
              <span>Subtotal</span>
              <strong>{formatCurrency(subtotal)}</strong>
            </div>
            <div className="summary-row">
              <span>Shipping</span>
              <strong>{formatCurrency(shippingFee)}</strong>
            </div>
            <div className="summary-row total">
              <span>Total</span>
              <strong>{formatCurrency(total)}</strong>
            </div>
          </aside>
        </section>
      ) : null}
    </div>
  )
}
