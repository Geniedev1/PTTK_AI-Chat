import { useQuery } from "@tanstack/react-query"
import { Link, useParams } from "react-router-dom"
import { useMemo, useState } from "react"
import { orderApi, paymentApi, shippingApi } from "../../shared/api/services"
import {
  EmptyState,
  ErrorBanner,
  LoadingState,
  PageHeader,
  Pagination,
  StatusBadge,
  formatCurrency,
  formatDateTime,
  statusTone,
} from "../../shared/components/ui"
import { useSessionStore } from "../../shared/stores/sessionStore"
import { getApiErrorMessage } from "../../shared/utils/apiError"

const PAGE_SIZE = 8

export function OrdersPage() {
  const params = useParams<{ orderId: string }>()
  const customerId = useSessionStore((state) => state.customerId)
  const cartSessionKey = useSessionStore((state) => state.cartSessionKey)
  const [statusFilter, setStatusFilter] = useState("")
  const [page, setPage] = useState(1)

  const hasScope = Boolean(customerId || cartSessionKey)
  const selectedOrderId = params.orderId && Number.isFinite(Number(params.orderId)) ? Number(params.orderId) : null
  const scopeParams = customerId ? { customer_id: customerId } : cartSessionKey ? { session_key: cartSessionKey } : undefined

  const ordersQuery = useQuery({
    queryKey: ["orders", customerId ?? "guest", cartSessionKey ?? "none"],
    queryFn: () => orderApi.list(customerId),
    enabled: hasScope,
  })

  const paymentsQuery = useQuery({
    queryKey: ["payments", customerId ?? "guest", cartSessionKey ?? "none"],
    queryFn: () => paymentApi.list(scopeParams),
    enabled: hasScope,
  })

  const shipmentsQuery = useQuery({
    queryKey: ["shipments", customerId ?? "guest", cartSessionKey ?? "none"],
    queryFn: () => shippingApi.listShipments(scopeParams),
    enabled: hasScope,
  })

  const orderDetailQuery = useQuery({
    queryKey: ["orders", "detail", selectedOrderId, customerId ?? "guest", cartSessionKey ?? "none"],
    queryFn: () => orderApi.detail(selectedOrderId as number, customerId),
    enabled: hasScope && selectedOrderId !== null,
  })

  const paymentsByOrder = useMemo(() => {
    const rows = paymentsQuery.data ?? []
    return new Map(rows.map((payment) => [payment.order_id, payment]))
  }, [paymentsQuery.data])

  const shipmentsByOrder = useMemo(() => {
    const rows = shipmentsQuery.data ?? []
    return new Map(rows.map((shipment) => [shipment.order_id, shipment]))
  }, [shipmentsQuery.data])

  const orders = ordersQuery.data ?? []
  const filteredOrders = orders.filter((order) => !statusFilter || order.status === statusFilter)
  const pageCount = Math.max(1, Math.ceil(filteredOrders.length / PAGE_SIZE))
  const safePage = Math.min(page, pageCount)
  const pagedOrders = filteredOrders.slice((safePage - 1) * PAGE_SIZE, safePage * PAGE_SIZE)
  const detail = orderDetailQuery.data
  const detailPayment = detail ? paymentsByOrder.get(detail.id) : null
  const detailShipment = detail ? shipmentsByOrder.get(detail.id) : null

  return (
    <div className="page-stack">
      <PageHeader
        eyebrow="Orders"
        title="Your order history"
        description="Track order status, payment confirmation, and shipment progress from one place."
      />

      {!hasScope ? (
        <EmptyState
          title="No order scope yet"
          description="Log in or add an item to cart so the app can load your order history."
          action={
            <Link className="btn btn-primary" to="/products">
              Browse products
            </Link>
          }
        />
      ) : null}

      {ordersQuery.isLoading ? <LoadingState label="Loading orders..." /> : null}
      {ordersQuery.isError ? <ErrorBanner message={getApiErrorMessage(ordersQuery.error)} /> : null}

      {hasScope && orders.length > 0 ? (
        <section className="section-panel">
          <div className="result-toolbar">
            <strong>{filteredOrders.length} orders</strong>
            <select
              className="field compact-field"
              value={statusFilter}
              onChange={(event) => {
                setStatusFilter(event.target.value)
                setPage(1)
              }}
            >
              <option value="">All statuses</option>
              <option value="PENDING">Pending</option>
              <option value="CONFIRMED">Confirmed</option>
              <option value="PAID">Paid</option>
              <option value="COMPLETED">Completed</option>
              <option value="CANCELLED">Cancelled</option>
            </select>
          </div>

          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Order</th>
                  <th>Status</th>
                  <th>Payment</th>
                  <th>Shipment</th>
                  <th>Total</th>
                  <th>Created</th>
                </tr>
              </thead>
              <tbody>
                {pagedOrders.map((order) => {
                  const payment = paymentsByOrder.get(order.id)
                  const shipment = shipmentsByOrder.get(order.id)
                  return (
                    <tr key={order.id}>
                      <td>
                        <Link to={`/orders/${order.id}`}>#{order.id}</Link>
                      </td>
                      <td>
                        <StatusBadge tone={statusTone(order.status)}>{order.status}</StatusBadge>
                      </td>
                      <td>
                        {payment ? (
                          <StatusBadge tone={statusTone(payment.status)}>{payment.status}</StatusBadge>
                        ) : (
                          <StatusBadge>Not created</StatusBadge>
                        )}
                      </td>
                      <td>
                        {shipment ? (
                          <StatusBadge tone={statusTone(shipment.status)}>{shipment.status}</StatusBadge>
                        ) : (
                          <StatusBadge>Not created</StatusBadge>
                        )}
                      </td>
                      <td>{formatCurrency(order.total_amount)}</td>
                      <td>{formatDateTime(order.created_at)}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>

          <Pagination
            page={safePage}
            pageCount={pageCount}
            pageSize={PAGE_SIZE}
            total={filteredOrders.length}
            onPageChange={setPage}
          />
        </section>
      ) : null}

      {hasScope && !ordersQuery.isLoading && orders.length === 0 ? (
        <EmptyState title="No orders yet" description="Your completed checkouts will appear here." />
      ) : null}

      {selectedOrderId !== null ? (
        <section className="section-panel">
          <div className="section-title-row">
            <div>
              <span className="eyebrow">Order detail</span>
              <h2>Order #{selectedOrderId}</h2>
            </div>
          </div>
          {orderDetailQuery.isLoading ? <LoadingState label="Loading order detail..." /> : null}
          {orderDetailQuery.isError ? <ErrorBanner message={getApiErrorMessage(orderDetailQuery.error)} /> : null}
          {detail ? (
            <div className="order-detail-grid">
              <div className="detail-card">
                <h3>Status timeline</h3>
                <ol className="timeline">
                  <li className="done">Created {formatDateTime(detail.created_at)}</li>
                  <li className={detail.paid_at ? "done" : ""}>Paid {formatDateTime(detail.paid_at)}</li>
                  <li className={detailShipment?.shipped_at ? "done" : ""}>Shipped {formatDateTime(detailShipment?.shipped_at)}</li>
                  <li className={detail.completed_at ? "done" : ""}>Completed {formatDateTime(detail.completed_at)}</li>
                </ol>
              </div>
              <div className="detail-card">
                <h3>Payment</h3>
                {detailPayment ? (
                  <>
                    <StatusBadge tone={statusTone(detailPayment.status)}>{detailPayment.status}</StatusBadge>
                    <p>{formatCurrency(detailPayment.amount)}</p>
                    <small>{detailPayment.provider_reference || detailPayment.provider}</small>
                  </>
                ) : (
                  <p>No payment record for this order.</p>
                )}
              </div>
              <div className="detail-card">
                <h3>Shipment</h3>
                {detailShipment ? (
                  <>
                    <StatusBadge tone={statusTone(detailShipment.status)}>{detailShipment.status}</StatusBadge>
                    <p>{detailShipment.tracking_number || "Tracking pending"}</p>
                    <small>
                      {detailShipment.city} {detailShipment.country}
                    </small>
                  </>
                ) : (
                  <p>No shipment record for this order.</p>
                )}
              </div>
              <div className="detail-card wide">
                <h3>Items</h3>
                <ul className="item-list">
                  {detail.items.map((item) => (
                    <li key={item.id}>
                      <span>
                        #{item.product_id} - {item.product_name_snapshot}
                      </span>
                      <span>
                        {item.quantity} x {formatCurrency(item.price_snapshot)}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          ) : null}
        </section>
      ) : null}
    </div>
  )
}
