import { useMemo } from "react"
import { useQuery } from "@tanstack/react-query"
import { Link } from "react-router-dom"
import { orderApi, paymentApi, shippingApi } from "../../shared/api/services"
import type { Order, Payment, Shipment } from "../../shared/types/api"
import { getApiErrorMessage } from "../../shared/utils/apiError"

const monthLabels = ["Jan", "Feb", "Mar", "April", "May", "June", "July", "Aug", "September", "Oct", "Nov", "Dec"]
const emptyOrders: Order[] = []
const emptyPayments: Payment[] = []
const emptyShipments: Shipment[] = []

const toMoney = (value: number) =>
  new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value)

const statusClass = (value: string) => value.toLowerCase().replaceAll("_", "-")

const latestPaymentByOrder = (payments: Payment[]) => {
  const map = new Map<number, Payment>()
  for (const payment of payments) {
    if (!map.has(payment.order_id)) {
      map.set(payment.order_id, payment)
    }
  }
  return map
}

const shipmentByOrder = (shipments: Shipment[]) => {
  const map = new Map<number, Shipment>()
  for (const shipment of shipments) {
    map.set(shipment.order_id, shipment)
  }
  return map
}

const monthlyPaidRevenue = (payments: Payment[]) => {
  const values = Array.from({ length: 12 }, () => 0)
  for (const payment of payments) {
    if (payment.status !== "PAID") {
      continue
    }
    const month = new Date(payment.paid_at ?? payment.created_at).getMonth()
    if (month >= 0 && month < values.length) {
      values[month] = (values[month] ?? 0) + Number(payment.amount)
    }
  }
  return values
}

const chartPointsFromValues = (values: number[]) => {
  const width = 1045
  const height = 180
  const topPadding = 18
  const maxValue = Math.max(...values, 1)
  return values
    .map((value, index) => {
      const x = Math.round((width / Math.max(values.length - 1, 1)) * index)
      const y = Math.round(topPadding + height - (value / maxValue) * height)
      return `${x},${y}`
    })
    .join(" ")
}

export function AdminDashboardPage() {
  const ordersQuery = useQuery({
    queryKey: ["admin", "orders"],
    queryFn: () => orderApi.list(),
  })

  const shipmentsQuery = useQuery({
    queryKey: ["admin", "shipments"],
    queryFn: () => shippingApi.listShipments(),
  })

  const paymentsQuery = useQuery({
    queryKey: ["admin", "payments"],
    queryFn: () => paymentApi.list(),
  })

  const orders = ordersQuery.data ?? emptyOrders
  const shipments = shipmentsQuery.data ?? emptyShipments
  const payments = paymentsQuery.data ?? emptyPayments

  const paymentsByOrder = useMemo(() => latestPaymentByOrder(payments), [payments])
  const shipmentsByOrder = useMemo(() => shipmentByOrder(shipments), [shipments])
  const monthlyRevenue = useMemo(() => monthlyPaidRevenue(payments), [payments])
  const chartPoints = useMemo(() => chartPointsFromValues(monthlyRevenue), [monthlyRevenue])

  const pendingOrders = orders.filter((order) => order.status === "PENDING")
  const confirmedUnassigned = orders.filter((order) => {
    const shipment = shipmentsByOrder.get(order.id)
    return order.status === "CONFIRMED" || (order.status === "PAID" && !shipment)
  })
  const assignedShipments = shipments.filter((shipment) => shipment.shipper_id !== null && shipment.status !== "DELIVERED")
  const outForDelivery = shipments.filter((shipment) => shipment.status === "SHIPPED")
  const deliveredWaitingCompletion = shipments.filter((shipment) => {
    const order = orders.find((item) => item.id === shipment.order_id)
    return shipment.status === "DELIVERED" && order?.status === "PAID"
  })
  const failedDeliveries = shipments.filter((shipment) => shipment.status === "FAILED")
  const paidRevenue = payments
    .filter((payment) => payment.status === "PAID")
    .reduce((sum, payment) => sum + Number(payment.amount), 0)

  const metrics = [
    { label: "Pending Orders", value: pendingOrders.length, tone: "Review" },
    { label: "Needs Shipment", value: confirmedUnassigned.length, tone: "Assign" },
    { label: "Assigned Active", value: assignedShipments.length, tone: "Assigned" },
    { label: "Out For Delivery", value: outForDelivery.length, tone: "Live" },
    { label: "Delivered Pending Completion", value: deliveredWaitingCompletion.length, tone: "Close" },
    { label: "Failed Deliveries", value: failedDeliveries.length, tone: "Resolve" },
    { label: "Paid Revenue", value: toMoney(paidRevenue), tone: "Paid" },
  ]

  const recentOrders = orders.slice(0, 8)
  const opsQueue = [
    ...pendingOrders.map((order) => ({ order, reason: "Verify order" })),
    ...confirmedUnassigned.map((order) => ({ order, reason: "Create shipment / assign shipper" })),
    ...deliveredWaitingCompletion
      .map((shipment) => orders.find((order) => order.id === shipment.order_id))
      .filter((order): order is Order => Boolean(order))
      .map((order) => ({ order, reason: "Complete order" })),
  ].slice(0, 8)

  const isLoading = ordersQuery.isLoading || shipmentsQuery.isLoading || paymentsQuery.isLoading

  return (
    <section className="admin-dashboard-page">
      {isLoading ? <p>Loading dashboard...</p> : null}
      {ordersQuery.isError ? <p className="error-text">{getApiErrorMessage(ordersQuery.error)}</p> : null}
      {shipmentsQuery.isError ? <p className="error-text">{getApiErrorMessage(shipmentsQuery.error)}</p> : null}
      {paymentsQuery.isError ? <p className="error-text">{getApiErrorMessage(paymentsQuery.error)}</p> : null}

      <div className="admin-metric-grid ops-metric-grid">
        {metrics.map((metric) => (
          <article className="admin-metric-card" key={metric.label}>
            <div>
              <span>{metric.label}</span>
              <strong>{metric.value}</strong>
            </div>
            <em>{metric.tone}</em>
          </article>
        ))}
      </div>

      <section className="admin-board">
        <div className="admin-board-header">
          <div>
            <h1>Paid Revenue</h1>
            <p className="muted-text">Monthly total from confirmed paid transactions.</p>
          </div>
          <strong>{toMoney(paidRevenue)}</strong>
        </div>
        <div className="line-chart" aria-label="Paid revenue line chart">
          <svg viewBox="0 0 1045 220" role="img">
            <g className="chart-grid">
              <line x1="0" x2="1045" y1="20" y2="20" />
              <line x1="0" x2="1045" y1="60" y2="60" />
              <line x1="0" x2="1045" y1="100" y2="100" />
              <line x1="0" x2="1045" y1="140" y2="140" />
              <line x1="0" x2="1045" y1="180" y2="180" />
            </g>
            <polyline points={chartPoints} />
          </svg>
          <div className="chart-months">
            {monthLabels.map((month) => (
              <span key={month}>{month}</span>
            ))}
          </div>
        </div>
      </section>

      <section className="admin-board">
        <div className="admin-board-header">
          <h2>Operations Queue</h2>
          <Link to="/admin/orders" className="topnav-button">
            Open Orders
          </Link>
        </div>
        {opsQueue.length === 0 ? <p className="muted-text">No pending operations.</p> : null}
        {opsQueue.length > 0 ? (
          <div className="table-wrap">
            <table className="table admin-table">
              <thead>
                <tr>
                  <th>Order</th>
                  <th>Reason</th>
                  <th>Status</th>
                  <th>Shipment</th>
                  <th>Payment</th>
                </tr>
              </thead>
              <tbody>
                {opsQueue.map(({ order, reason }) => {
                  const shipment = shipmentsByOrder.get(order.id)
                  const payment = paymentsByOrder.get(order.id)
                  return (
                    <tr key={`${order.id}-${reason}`}>
                      <td>
                        <Link to="/admin/orders">#{order.id}</Link>
                      </td>
                      <td>{reason}</td>
                      <td>
                        <span className={`status-pill ${statusClass(order.status)}`}>{order.status}</span>
                      </td>
                      <td>{shipment?.status ?? "NONE"}</td>
                      <td>{payment?.status ?? "UNPAID"}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        ) : null}
      </section>

      <section className="admin-board">
        <h2>Recent Orders</h2>
        <div className="table-wrap">
          <table className="table admin-table">
            <thead>
              <tr>
                <th>Order ID</th>
                <th>Customer</th>
                <th>Date</th>
                <th>Total</th>
                <th>Payment</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {recentOrders.map((order) => {
                const payment = paymentsByOrder.get(order.id)
                return (
                  <tr key={order.id}>
                    <td>
                      <Link to="/admin/orders">#{order.id}</Link>
                    </td>
                    <td>{order.customer_id ?? order.session_key}</td>
                    <td>{new Date(order.created_at).toLocaleString()}</td>
                    <td>${order.total_amount}</td>
                    <td>{payment?.status ?? "UNPAID"}</td>
                    <td>
                      <span className={`status-pill ${statusClass(order.status)}`}>{order.status}</span>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </section>
    </section>
  )
}
