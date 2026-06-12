import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useMemo } from "react"
import { Link, useParams } from "react-router-dom"
import { orderApi, paymentApi, shippingApi } from "../../shared/api/services"
import { useSessionStore } from "../../shared/stores/sessionStore"
import type { Order, Shipment } from "../../shared/types/api"
import { getApiErrorMessage } from "../../shared/utils/apiError"

type TimelineState = "complete" | "current" | "pending"

type TimelineStep = {
  key: string
  label: string
  state: TimelineState
  timestamp: string | null
  detail?: string | undefined
}

const formatDateTime = (value: string | null) => (value ? new Date(value).toLocaleString() : "")

const historyTimestamp = (order: Order, status: string) =>
  [...(order.status_history ?? [])]
    .reverse()
    .find((item) => item.new_status === status)?.created_at ?? null

const stepState = (isComplete: boolean, isCurrent: boolean): TimelineState => {
  if (isComplete) {
    return "complete"
  }
  return isCurrent ? "current" : "pending"
}

const canPayOrder = (order: Order) => order.status === "PENDING" || order.status === "CONFIRMED"

const buildTimeline = (order: Order, shipment: Shipment | null): TimelineStep[] => {
  const orderPlacedAt = historyTimestamp(order, "PENDING") ?? order.created_at
  const confirmedAt = order.confirmed_at ?? historyTimestamp(order, "CONFIRMED")
  const paidAt = order.paid_at ?? historyTimestamp(order, "PAID")
  const completedAt = order.completed_at ?? historyTimestamp(order, "COMPLETED")
  const assignedAt =
    shipment?.assigned_at ??
    shipment?.tracking_events.find((event) => event.status === "ASSIGNED_TO_SHIPPER")?.event_time ??
    null
  const shipmentReadyAt =
    shipment?.tracking_events.find((event) => event.status === "READY_TO_SHIP")?.event_time ?? shipment?.created_at ?? null
  const shippedAt =
    shipment?.shipped_at ?? shipment?.tracking_events.find((event) => event.status === "SHIPPED")?.event_time ?? null
  const deliveredAt =
    shipment?.delivered_at ?? shipment?.tracking_events.find((event) => event.status === "DELIVERED")?.event_time ?? null

  return [
    {
      key: "placed",
      label: "Order placed",
      state: "complete",
      timestamp: orderPlacedAt,
    },
    {
      key: "confirmed",
      label: "Confirmed",
      state: stepState(Boolean(confirmedAt || paidAt || completedAt), order.status === "CONFIRMED"),
      timestamp: confirmedAt,
    },
    {
      key: "paid",
      label: "Payment confirmed",
      state: stepState(Boolean(paidAt || completedAt), order.status === "PAID" && !shipment),
      timestamp: paidAt,
    },
    {
      key: "assigned",
      label: "Assigned to shipper",
      state: stepState(Boolean(assignedAt || shippedAt || deliveredAt), Boolean(assignedAt) && shipment?.status === "PENDING"),
      timestamp: assignedAt,
      detail: shipment
        ? `Shipper: ${shipment.assigned_shipper?.name ?? shipment.shipper_id ?? "Pending"}${
            shipment.assigned_shipper?.phone ? `, phone: ${shipment.assigned_shipper.phone}` : ""
          }`
        : undefined,
    },
    {
      key: "ready",
      label: "Ready for delivery",
      state: stepState(Boolean(shipmentReadyAt || shippedAt || deliveredAt), shipment?.status === "READY_TO_SHIP"),
      timestamp: shipmentReadyAt,
      detail: shipment ? `Carrier: ${shipment.carrier || "N/A"}` : undefined,
    },
    {
      key: "shipped",
      label: "Out for delivery",
      state: stepState(Boolean(shippedAt || deliveredAt), shipment?.status === "SHIPPED"),
      timestamp: shippedAt,
      detail: shipment?.tracking_number ? `Tracking: ${shipment.tracking_number}` : undefined,
    },
    {
      key: "delivered",
      label: "Delivered",
      state: stepState(Boolean(deliveredAt || completedAt), shipment?.status === "DELIVERED"),
      timestamp: deliveredAt,
    },
    {
      key: "completed",
      label: "Completed",
      state: stepState(Boolean(completedAt), order.status === "COMPLETED"),
      timestamp: completedAt,
    },
  ]
}

export function OrdersPage() {
  const queryClient = useQueryClient()
  const params = useParams<{ orderId: string }>()
  const customerId = useSessionStore((state) => state.customerId)
  const cartSessionKey = useSessionStore((state) => state.cartSessionKey)

  const hasScope = Boolean(customerId || cartSessionKey)
  const parsedOrderId = params.orderId ? Number(params.orderId) : null
  const selectedOrderId =
    parsedOrderId !== null && Number.isFinite(parsedOrderId) && parsedOrderId > 0 ? parsedOrderId : null

  const ordersQuery = useQuery({
    queryKey: ["orders", customerId ?? "guest", cartSessionKey ?? "none"],
    queryFn: () => orderApi.list(customerId),
    enabled: hasScope,
  })

  const orderDetailQuery = useQuery({
    queryKey: ["orders", "detail", selectedOrderId, customerId ?? "guest", cartSessionKey ?? "none"],
    queryFn: () => orderApi.detail(selectedOrderId as number, customerId),
    enabled: hasScope && selectedOrderId !== null,
  })

  const shipmentParams = useMemo(() => {
    if (selectedOrderId === null) {
      return null
    }
    const params: { order_id: number; customer_id?: number; session_key?: string } = { order_id: selectedOrderId }
    if (customerId) {
      params.customer_id = customerId
    } else if (cartSessionKey) {
      params.session_key = cartSessionKey
    }
    return params
  }, [cartSessionKey, customerId, selectedOrderId])

  const shipmentsQuery = useQuery({
    queryKey: ["shipments", "order", selectedOrderId, customerId ?? "guest", cartSessionKey ?? "none"],
    queryFn: () => shippingApi.listShipments(shipmentParams ?? undefined),
    enabled: hasScope && shipmentParams !== null,
  })

  const selectedShipment = shipmentsQuery.data?.[0] ?? null
  const timeline = orderDetailQuery.data ? buildTimeline(orderDetailQuery.data, selectedShipment) : []

  const payOrderMutation = useMutation({
    mutationFn: async (orderId: number) => {
      const order = ordersQuery.data?.find((item) => item.id === orderId) ?? orderDetailQuery.data
      if (!order) {
        throw new Error("Order is not loaded yet.")
      }
      const paymentPayload = {
        order_id: order.id,
        session_key: order.session_key,
        currency: "USD",
        provider: "mock",
        idempotency_key: `order-${order.id}-mock-payment`,
      }
      const payment = await paymentApi.create(
        order.customer_id ? { ...paymentPayload, customer_id: order.customer_id } : paymentPayload,
      )
      return paymentApi.confirm(payment.id)
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["orders"] })
    },
  })

  return (
    <section className="panel">
      <h1>Orders</h1>

      {!hasScope ? (
        <p>
          No order scope yet. Login as customer or interact with cart first so session header can be used for
          order queries.
        </p>
      ) : null}

      {ordersQuery.isLoading ? <p>Loading orders...</p> : null}
      {ordersQuery.isError ? <p className="error-text">{getApiErrorMessage(ordersQuery.error)}</p> : null}

      {ordersQuery.data ? (
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>Order</th>
                <th>Status</th>
                <th>Total</th>
                <th>Created</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {ordersQuery.data.map((order) => (
                <tr key={order.id}>
                  <td>
                    <Link to={`/orders/${order.id}`}>#{order.id}</Link>
                  </td>
                  <td>{order.status}</td>
                  <td>${order.total_amount}</td>
                  <td>{new Date(order.created_at).toLocaleString()}</td>
                  <td>
                    {canPayOrder(order) ? (
                      <button
                        className="primary-button"
                        onClick={() => payOrderMutation.mutate(order.id)}
                        disabled={payOrderMutation.isPending}
                      >
                        Pay Now
                      </button>
                    ) : null}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}

      {ordersQuery.data && ordersQuery.data.length === 0 ? <p>No orders in this scope.</p> : null}

      {selectedOrderId !== null ? <h2>Order Detail #{selectedOrderId}</h2> : null}

      {orderDetailQuery.isLoading ? <p>Loading order detail...</p> : null}
      {orderDetailQuery.isError ? <p className="error-text">{getApiErrorMessage(orderDetailQuery.error)}</p> : null}

      {orderDetailQuery.data ? (
        <div className="detail-block">
          <p>Status: {orderDetailQuery.data.status}</p>
          <p>Total: ${orderDetailQuery.data.total_amount}</p>
          <p>Session: {orderDetailQuery.data.session_key}</p>
          {canPayOrder(orderDetailQuery.data) ? (
            <button
              className="primary-button"
              onClick={() => payOrderMutation.mutate(orderDetailQuery.data.id)}
              disabled={payOrderMutation.isPending}
            >
              Pay Now
            </button>
          ) : null}
          <h3>Tracking Timeline</h3>
          {shipmentsQuery.isError ? (
            <p className="error-text">{getApiErrorMessage(shipmentsQuery.error)}</p>
          ) : null}
          <ol className="order-timeline">
            {timeline.map((step) => (
              <li className={`timeline-step ${step.state}`} key={step.key}>
                <span className="timeline-marker" />
                <div>
                  <strong>{step.label}</strong>
                  {step.timestamp ? <span>{formatDateTime(step.timestamp)}</span> : <span>Waiting</span>}
                  {step.detail ? <small>{step.detail}</small> : null}
                </div>
              </li>
            ))}
          </ol>
          {selectedShipment ? (
            <div className="shipment-summary">
              <strong>Shipment</strong>
              <span>Status: {selectedShipment.status}</span>
              {selectedShipment.assigned_shipper ? (
                <>
                  <span>Shipper: {selectedShipment.assigned_shipper.name}</span>
                  <span>Shipper phone: {selectedShipment.assigned_shipper.phone || "N/A"}</span>
                </>
              ) : null}
              <span>Recipient: {selectedShipment.recipient_name}</span>
              <span>Address: {selectedShipment.address}</span>
            </div>
          ) : null}
          <h3>Items</h3>
          <ul className="item-list">
            {orderDetailQuery.data.items.map((item) => (
              <li key={item.id}>
                <span>
                  #{item.product_id} - {item.product_name_snapshot}
                </span>
                <span>
                  {item.quantity} x ${item.price_snapshot}
                </span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
      {payOrderMutation.isError ? <p className="error-text">{getApiErrorMessage(payOrderMutation.error)}</p> : null}
      {payOrderMutation.isSuccess ? <p className="success-text">Payment confirmed. Order status will refresh.</p> : null}
    </section>
  )
}
