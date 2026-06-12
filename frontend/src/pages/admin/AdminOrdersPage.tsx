import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Fragment, useMemo, useState } from "react"
import { Link } from "react-router-dom"
import { orderApi, paymentApi, shippingApi, staffApi } from "../../shared/api/services"
import type { CreateShipperProfilePayload, CreateShipmentPayload, Order, Payment, Shipment } from "../../shared/types/api"
import { getApiErrorMessage } from "../../shared/utils/apiError"

type ShipmentDraft = {
  recipient_name: string
  phone: string
  address: string
  city: string
  country: string
  delivery_lat: string
  delivery_lng: string
  carrier: string
  shipping_fee: string
}

type ShipperDraft = {
  staff_id: string
  username: string
  password: string
  email: string
  name: string
  phone: string
  current_lat: string
  current_lng: string
}

const canPay = (order: Order) => order.status === "PENDING" || order.status === "CONFIRMED"

const defaultShipmentDraft = (order: Order): ShipmentDraft => ({
  recipient_name: order.customer_id ? `Customer ${order.customer_id}` : "Guest Customer",
  phone: "",
  address: "",
  city: "",
  country: "VN",
  delivery_lat: "",
  delivery_lng: "",
  carrier: "mock",
  shipping_fee: "0.00",
})

const shipmentStatusClass = (shipment: Shipment) => shipment.status.toLowerCase().replaceAll("_", "-")

const paymentStatusClass = (payment: Payment | undefined) => payment?.status.toLowerCase() ?? "missing"

const canAssignShipment = (shipment: Shipment) => shipment.status === "PENDING" || shipment.status === "READY_TO_SHIP"

export function AdminOrdersPage() {
  const queryClient = useQueryClient()
  const [expandedOrderId, setExpandedOrderId] = useState<number | null>(null)
  const [detailOrderId, setDetailOrderId] = useState<number | null>(null)
  const [shipmentDrafts, setShipmentDrafts] = useState<Record<number, ShipmentDraft>>({})
  const [shipperSelections, setShipperSelections] = useState<Record<number, number | "">>({})
  const [shipperDraft, setShipperDraft] = useState<ShipperDraft>({
    staff_id: "",
    username: "",
    password: "",
    email: "",
    name: "",
    phone: "",
    current_lat: "",
    current_lng: "",
  })

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

  const shippersQuery = useQuery({
    queryKey: ["admin", "shippers"],
    queryFn: () => shippingApi.listShippers(),
  })

  const updateStatusMutation = useMutation({
    mutationFn: ({ orderId, status }: { orderId: number; status: Order["status"] }) =>
      orderApi.updateStatus(orderId, status),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["admin", "orders"] })
      void queryClient.invalidateQueries({ queryKey: ["orders"] })
    },
  })

  const createShipmentMutation = useMutation({
    mutationFn: ({ order, draft }: { order: Order; draft: ShipmentDraft }) => {
      const payload: CreateShipmentPayload = {
        order_id: order.id,
        recipient_name: draft.recipient_name.trim(),
        phone: draft.phone.trim(),
        address: draft.address.trim(),
        city: draft.city.trim(),
        country: draft.country.trim(),
        carrier: draft.carrier.trim() || "mock",
        shipping_fee: draft.shipping_fee.trim() || "0.00",
      }

      if (order.customer_id) {
        payload.customer_id = order.customer_id
      } else {
        payload.session_key = order.session_key
      }
      if (draft.delivery_lat.trim()) {
        payload.delivery_lat = draft.delivery_lat.trim()
      }
      if (draft.delivery_lng.trim()) {
        payload.delivery_lng = draft.delivery_lng.trim()
      }
      return shippingApi.createShipment(payload)
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["admin", "shipments"] })
      setExpandedOrderId(null)
    },
  })

  const assignShipperMutation = useMutation({
    mutationFn: ({ shipmentId, shipperId }: { shipmentId: number; shipperId: number }) =>
      shippingApi.assignShipper(shipmentId, shipperId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["admin", "shipments"] })
    },
  })

  const createShipperMutation = useMutation({
    mutationFn: async () => {
      let staffId = Number(shipperDraft.staff_id)
      if (!staffId) {
        const staffPayload = {
          username: shipperDraft.username.trim(),
          password: shipperDraft.password,
          name: shipperDraft.name.trim(),
          email: shipperDraft.email.trim(),
          position: "Shipper",
          roles: ["shipper" as const],
        }
        if (shipperDraft.phone.trim()) {
          Object.assign(staffPayload, { phone: shipperDraft.phone.trim() })
        }
        const staff = await staffApi.adminCreate(staffPayload)
        staffId = staff.id
      }

      const payload: CreateShipperProfilePayload = {
        staff_id: staffId,
        name: shipperDraft.name.trim(),
      }
      if (shipperDraft.phone.trim()) {
        payload.phone = shipperDraft.phone.trim()
      }
      if (shipperDraft.current_lat.trim()) {
        payload.current_lat = shipperDraft.current_lat.trim()
      }
      if (shipperDraft.current_lng.trim()) {
        payload.current_lng = shipperDraft.current_lng.trim()
      }
      return shippingApi.createShipper(payload)
    },
    onSuccess: () => {
      setShipperDraft({
        staff_id: "",
        username: "",
        password: "",
        email: "",
        name: "",
        phone: "",
        current_lat: "",
        current_lng: "",
      })
      void queryClient.invalidateQueries({ queryKey: ["admin", "shippers"] })
    },
  })

  const shipmentActionMutation = useMutation({
    mutationFn: ({ shipment, action }: { shipment: Shipment; action: "ready" | "ship" | "deliver" | "cancel" }) => {
      if (action === "ready") {
        return shippingApi.markReady(shipment.id)
      }
      if (action === "ship") {
        return shippingApi.ship(shipment.id)
      }
      if (action === "deliver") {
        return shippingApi.deliver(shipment.id)
      }
      return shippingApi.cancel(shipment.id)
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["admin", "shipments"] })
      void queryClient.invalidateQueries({ queryKey: ["admin", "orders"] })
      void queryClient.invalidateQueries({ queryKey: ["orders"] })
    },
  })

  const orders = ordersQuery.data ?? []
  const shipmentsByOrder = useMemo(() => {
    const map = new Map<number, Shipment>()
    for (const shipment of shipmentsQuery.data ?? []) {
      map.set(shipment.order_id, shipment)
    }
    return map
  }, [shipmentsQuery.data])
  const paymentsByOrder = useMemo(() => {
    const map = new Map<number, Payment>()
    for (const payment of paymentsQuery.data ?? []) {
      if (!map.has(payment.order_id)) {
        map.set(payment.order_id, payment)
      }
    }
    return map
  }, [paymentsQuery.data])
  const pendingCount = orders.filter((order) => order.status === "PENDING").length
  const confirmedCount = orders.filter((order) => order.status === "CONFIRMED").length
  const paidCount = orders.filter((order) => order.status === "PAID").length
  const completedCount = orders.filter((order) => order.status === "COMPLETED").length

  const openShipmentForm = (order: Order) => {
    setExpandedOrderId((current) => (current === order.id ? null : order.id))
    setShipmentDrafts((current) =>
      current[order.id] ? current : { ...current, [order.id]: defaultShipmentDraft(order) },
    )
  }

  const updateDraft = (orderId: number, patch: Partial<ShipmentDraft>) => {
    setShipmentDrafts((current) => ({
      ...current,
      [orderId]: {
        ...(current[orderId] ?? defaultShipmentDraft(orders.find((order) => order.id === orderId) as Order)),
        ...patch,
      },
    }))
  }

  return (
    <section className="admin-board admin-orders-page">
      <div className="admin-board-header">
        <div>
          <h1>Admin Orders</h1>
          <p className="muted-text">Verify orders and monitor fulfillment state.</p>
        </div>
        <div className="shipper-stats">
          <span>Pending: {pendingCount}</span>
          <span>Confirmed: {confirmedCount}</span>
          <span>Paid: {paidCount}</span>
          <span>Completed: {completedCount}</span>
        </div>
      </div>

      {ordersQuery.isLoading ? <p>Loading orders...</p> : null}
      {ordersQuery.isError ? <p className="error-text">{getApiErrorMessage(ordersQuery.error)}</p> : null}
      {shipmentsQuery.isError ? <p className="error-text">{getApiErrorMessage(shipmentsQuery.error)}</p> : null}
      {shippersQuery.isError ? <p className="error-text">{getApiErrorMessage(shippersQuery.error)}</p> : null}
      {paymentsQuery.isError ? <p className="error-text">{getApiErrorMessage(paymentsQuery.error)}</p> : null}

      <section className="admin-ops-panel">
        <div>
          <h2>Shippers</h2>
          <p className="muted-text">
            {(shippersQuery.data ?? []).length} profile(s) available for assignment.
          </p>
        </div>
        <form
          className="admin-shipper-form"
          onSubmit={(event) => {
            event.preventDefault()
            createShipperMutation.mutate()
          }}
        >
          <input
            className="field"
            value={shipperDraft.staff_id}
            onChange={(event) => setShipperDraft((current) => ({ ...current, staff_id: event.target.value }))}
            placeholder="Existing Staff ID"
          />
          <input
            className="field"
            value={shipperDraft.username}
            onChange={(event) => setShipperDraft((current) => ({ ...current, username: event.target.value }))}
            placeholder="Username"
          />
          <input
            className="field"
            type="password"
            value={shipperDraft.password}
            onChange={(event) => setShipperDraft((current) => ({ ...current, password: event.target.value }))}
            placeholder="Password"
          />
          <input
            className="field"
            value={shipperDraft.email}
            onChange={(event) => setShipperDraft((current) => ({ ...current, email: event.target.value }))}
            placeholder="Email"
          />
          <input
            className="field"
            value={shipperDraft.name}
            onChange={(event) => setShipperDraft((current) => ({ ...current, name: event.target.value }))}
            placeholder="Name"
            required
          />
          <input
            className="field"
            value={shipperDraft.phone}
            onChange={(event) => setShipperDraft((current) => ({ ...current, phone: event.target.value }))}
            placeholder="Phone"
          />
          <input
            className="field"
            value={shipperDraft.current_lat}
            onChange={(event) => setShipperDraft((current) => ({ ...current, current_lat: event.target.value }))}
            placeholder="Lat"
          />
          <input
            className="field"
            value={shipperDraft.current_lng}
            onChange={(event) => setShipperDraft((current) => ({ ...current, current_lng: event.target.value }))}
            placeholder="Lng"
          />
          <button
            className="primary-button"
            disabled={
              createShipperMutation.isPending ||
              !shipperDraft.name.trim() ||
              (!Number(shipperDraft.staff_id) &&
                (!shipperDraft.username.trim() || !shipperDraft.password || !shipperDraft.email.trim()))
            }
          >
            Add Shipper Login
          </button>
        </form>
      </section>

      {orders.length > 0 ? (
        <div className="table-wrap">
          <table className="table admin-table">
            <thead>
              <tr>
                <th>Order</th>
                <th>Customer</th>
                <th>Status</th>
                <th>Payment</th>
                <th>Total</th>
                <th>Created</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {orders.map((order) => {
                  const shipment = shipmentsByOrder.get(order.id)
                  const payment = paymentsByOrder.get(order.id)
                  const draft = shipmentDrafts[order.id] ?? defaultShipmentDraft(order)
                  const selectedShipperId = shipment ? shipperSelections[shipment.id] : ""
                  const assignable = shipment ? canAssignShipment(shipment) : false

                  return (
                  <Fragment key={order.id}>
                    <tr>
                      <td>
                        <Link to={`/orders/${order.id}`}>#{order.id}</Link>
                      </td>
                      <td>{order.customer_id ?? order.session_key}</td>
                      <td>
                        <span className="status-pill">{order.status}</span>
                      </td>
                      <td>
                        <span className={`status-pill payment-${paymentStatusClass(payment)}`}>
                          {payment?.status ?? "UNPAID"}
                        </span>
                      </td>
                      <td>${order.total_amount}</td>
                      <td>{new Date(order.created_at).toLocaleString()}</td>
                      <td>
                        <div className="admin-order-actions">
                          {order.status === "PENDING" ? (
                            <button
                              className="primary-button"
                              onClick={() => updateStatusMutation.mutate({ orderId: order.id, status: "CONFIRMED" })}
                              disabled={updateStatusMutation.isPending}
                            >
                              Verify
                            </button>
                          ) : null}
                          {order.status === "CONFIRMED" ? <span className="muted-text">Waiting for payment</span> : null}
                          {order.status === "PAID" && !shipment ? (
                            <button onClick={() => openShipmentForm(order)}>
                              {expandedOrderId === order.id ? "Close" : "Create Shipment"}
                            </button>
                          ) : null}
                          {order.status === "PAID" && shipment ? (
                            <span className={`status-pill ${shipmentStatusClass(shipment)}`}>{shipment.status}</span>
                          ) : null}
                          {!canPay(order) && order.status !== "PAID" ? <span className="muted-text">No action</span> : null}
                          <button onClick={() => setDetailOrderId((current) => (current === order.id ? null : order.id))}>
                            {detailOrderId === order.id ? "Hide Details" : "Details"}
                          </button>
                        </div>
                      </td>
                    </tr>

                    {shipment ? (
                      <tr className="admin-order-detail-row">
                        <td colSpan={7}>
                          <div className="admin-order-detail">
                            <div>
                              <strong>Shipment #{shipment.id}</strong>
                              <span>Carrier: {shipment.carrier || "N/A"}</span>
                              <span>Tracking: {shipment.tracking_number || "N/A"}</span>
                              <span>Shipper: {shipment.shipper_id ?? "Unassigned"}</span>
                            </div>
                            <div className="admin-inline-form">
                              <select
                                aria-label={`Assign shipper for order ${order.id}`}
                                value={selectedShipperId ?? ""}
                                onChange={(event) =>
                                  setShipperSelections((current) => ({
                                    ...current,
                                    [shipment.id]: event.target.value ? Number(event.target.value) : "",
                                  }))
                                }
                                disabled={!assignable}
                              >
                                <option value="">Select shipper</option>
                                {(shippersQuery.data ?? []).map((shipper) => (
                                  <option key={shipper.id} value={shipper.staff_id}>
                                    {shipper.name} #{shipper.staff_id}
                                  </option>
                                ))}
                              </select>
                              <button
                                onClick={() =>
                                  selectedShipperId
                                    ? assignShipperMutation.mutate({
                                        shipmentId: shipment.id,
                                        shipperId: selectedShipperId,
                                      })
                                    : undefined
                                }
                                disabled={!assignable || !selectedShipperId || assignShipperMutation.isPending}
                              >
                                Assign
                              </button>
                              {!assignable ? <span className="muted-text">Reassignment locked</span> : null}
                              {shipment.status === "PENDING" ? (
                                <button
                                  onClick={() => shipmentActionMutation.mutate({ shipment, action: "ready" })}
                                  disabled={shipmentActionMutation.isPending}
                                >
                                  Mark Ready
                                </button>
                              ) : null}
                              {shipment.status === "PENDING" || shipment.status === "READY_TO_SHIP" ? (
                                <button
                                  className="primary-button"
                                  onClick={() => shipmentActionMutation.mutate({ shipment, action: "ship" })}
                                  disabled={shipmentActionMutation.isPending}
                                >
                                  Start Delivery
                                </button>
                              ) : null}
                              {shipment.status === "SHIPPED" ? (
                                <button
                                  className="primary-button"
                                  onClick={() => shipmentActionMutation.mutate({ shipment, action: "deliver" })}
                                  disabled={shipmentActionMutation.isPending}
                                >
                                  Mark Delivered
                                </button>
                              ) : null}
                              {shipment.status === "DELIVERED" && order.status === "PAID" ? (
                                <button
                                  className="primary-button"
                                  onClick={() => updateStatusMutation.mutate({ orderId: order.id, status: "COMPLETED" })}
                                  disabled={updateStatusMutation.isPending}
                                >
                                  Complete Order
                                </button>
                              ) : null}
                              {shipment.status !== "DELIVERED" && shipment.status !== "CANCELLED" ? (
                                <button
                                  onClick={() => shipmentActionMutation.mutate({ shipment, action: "cancel" })}
                                  disabled={shipmentActionMutation.isPending}
                                >
                                  Cancel
                                </button>
                              ) : null}
                            </div>
                          </div>
                        </td>
                      </tr>
                    ) : null}

                    {detailOrderId === order.id ? (
                      <tr className="admin-order-detail-row">
                        <td colSpan={7}>
                          <div className="admin-order-inspector">
                            <section>
                              <h3>Items</h3>
                              <ul className="admin-detail-list">
                                {order.items.map((item) => (
                                  <li key={item.id}>
                                    <span>
                                      #{item.product_id} - {item.product_name_snapshot}
                                    </span>
                                    <strong>
                                      {item.quantity} x ${item.price_snapshot}
                                    </strong>
                                  </li>
                                ))}
                              </ul>
                            </section>
                            <section>
                              <h3>Payment</h3>
                              {payment ? (
                                <dl className="admin-detail-dl">
                                  <div>
                                    <dt>Status</dt>
                                    <dd>{payment.status}</dd>
                                  </div>
                                  <div>
                                    <dt>Amount</dt>
                                    <dd>
                                      {payment.currency} {payment.amount}
                                    </dd>
                                  </div>
                                  <div>
                                    <dt>Provider</dt>
                                    <dd>{payment.provider}</dd>
                                  </div>
                                  <div>
                                    <dt>Reference</dt>
                                    <dd>{payment.provider_reference || "N/A"}</dd>
                                  </div>
                                </dl>
                              ) : (
                                <p className="muted-text">No payment created yet.</p>
                              )}
                            </section>
                            <section>
                              <h3>Shipment</h3>
                              {shipment ? (
                                <dl className="admin-detail-dl">
                                  <div>
                                    <dt>Status</dt>
                                    <dd>{shipment.status}</dd>
                                  </div>
                                  <div>
                                    <dt>Recipient</dt>
                                    <dd>{shipment.recipient_name}</dd>
                                  </div>
                                  <div>
                                    <dt>Shipper</dt>
                                    <dd>{shipment.assigned_shipper?.name ?? shipment.shipper_id ?? "Unassigned"}</dd>
                                  </div>
                                  <div>
                                    <dt>Tracking</dt>
                                    <dd>{shipment.tracking_number || "N/A"}</dd>
                                  </div>
                                </dl>
                              ) : (
                                <p className="muted-text">No shipment created yet.</p>
                              )}
                            </section>
                            <section>
                              <h3>Order History</h3>
                              <ol className="admin-event-list">
                                {order.status_history.map((event) => (
                                  <li key={event.id}>
                                    <strong>
                                      {event.old_status || "NEW"} {"->"} {event.new_status}
                                    </strong>
                                    <span>{new Date(event.created_at).toLocaleString()}</span>
                                    <small>{event.changed_by}</small>
                                  </li>
                                ))}
                              </ol>
                            </section>
                            <section>
                              <h3>Shipment Events</h3>
                              {shipment && shipment.tracking_events.length > 0 ? (
                                <ol className="admin-event-list">
                                  {shipment.tracking_events.map((event) => (
                                    <li key={event.id}>
                                      <strong>{event.status}</strong>
                                      <span>{new Date(event.event_time).toLocaleString()}</span>
                                      {event.description ? <small>{event.description}</small> : null}
                                    </li>
                                  ))}
                                </ol>
                              ) : (
                                <p className="muted-text">No shipment events yet.</p>
                              )}
                            </section>
                          </div>
                        </td>
                      </tr>
                    ) : null}

                    {expandedOrderId === order.id && !shipment ? (
                      <tr className="admin-order-detail-row">
                        <td colSpan={7}>
                          <form
                            className="admin-shipment-form"
                            onSubmit={(event) => {
                              event.preventDefault()
                              createShipmentMutation.mutate({ order, draft })
                            }}
                          >
                            <label>
                              Recipient
                              <input
                                className="field"
                                value={draft.recipient_name}
                                onChange={(event) => updateDraft(order.id, { recipient_name: event.target.value })}
                                required
                              />
                            </label>
                            <label>
                              Phone
                              <input
                                className="field"
                                value={draft.phone}
                                onChange={(event) => updateDraft(order.id, { phone: event.target.value })}
                                required
                              />
                            </label>
                            <label className="wide-field">
                              Address
                              <input
                                className="field"
                                value={draft.address}
                                onChange={(event) => updateDraft(order.id, { address: event.target.value })}
                                required
                              />
                            </label>
                            <label>
                              City
                              <input
                                className="field"
                                value={draft.city}
                                onChange={(event) => updateDraft(order.id, { city: event.target.value })}
                              />
                            </label>
                            <label>
                              Country
                              <input
                                className="field"
                                value={draft.country}
                                onChange={(event) => updateDraft(order.id, { country: event.target.value })}
                              />
                            </label>
                            <label>
                              Delivery Lat
                              <input
                                className="field"
                                value={draft.delivery_lat}
                                onChange={(event) => updateDraft(order.id, { delivery_lat: event.target.value })}
                              />
                            </label>
                            <label>
                              Delivery Lng
                              <input
                                className="field"
                                value={draft.delivery_lng}
                                onChange={(event) => updateDraft(order.id, { delivery_lng: event.target.value })}
                              />
                            </label>
                            <label>
                              Fee
                              <input
                                className="field"
                                value={draft.shipping_fee}
                                onChange={(event) => updateDraft(order.id, { shipping_fee: event.target.value })}
                              />
                            </label>
                            <button className="primary-button" disabled={createShipmentMutation.isPending}>
                              Save Shipment
                            </button>
                          </form>
                        </td>
                      </tr>
                    ) : null}
                  </Fragment>
                )
              })}
            </tbody>
          </table>
        </div>
      ) : null}

      {ordersQuery.data && orders.length === 0 ? <p>No orders found.</p> : null}
      {updateStatusMutation.isError ? <p className="error-text">{getApiErrorMessage(updateStatusMutation.error)}</p> : null}
      {updateStatusMutation.isSuccess ? <p className="success-text">Order status updated.</p> : null}
      {createShipmentMutation.isError ? <p className="error-text">{getApiErrorMessage(createShipmentMutation.error)}</p> : null}
      {createShipmentMutation.isSuccess ? <p className="success-text">Shipment created.</p> : null}
      {createShipperMutation.isError ? <p className="error-text">{getApiErrorMessage(createShipperMutation.error)}</p> : null}
      {createShipperMutation.isSuccess ? <p className="success-text">Shipper profile created.</p> : null}
      {assignShipperMutation.isError ? <p className="error-text">{getApiErrorMessage(assignShipperMutation.error)}</p> : null}
      {assignShipperMutation.isSuccess ? <p className="success-text">Shipper assignment updated.</p> : null}
      {shipmentActionMutation.isError ? <p className="error-text">{getApiErrorMessage(shipmentActionMutation.error)}</p> : null}
      {shipmentActionMutation.isSuccess ? <p className="success-text">Shipment status updated.</p> : null}
    </section>
  )
}
