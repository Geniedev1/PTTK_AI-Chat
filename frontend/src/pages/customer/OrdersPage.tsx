import { useQuery } from "@tanstack/react-query"
import { Link, useParams } from "react-router-dom"
import { orderApi } from "../../shared/api/services"
import { useSessionStore } from "../../shared/stores/sessionStore"
import { getApiErrorMessage } from "../../shared/utils/apiError"

export function OrdersPage() {
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
    </section>
  )
}
