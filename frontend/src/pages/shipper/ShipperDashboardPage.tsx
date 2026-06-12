import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"
import { Link, useParams } from "react-router-dom"
import { shippingApi } from "../../shared/api/services"
import { useSessionStore } from "../../shared/stores/sessionStore"
import type { Shipment } from "../../shared/types/api"
import { getApiErrorMessage } from "../../shared/utils/apiError"

const actionLabel = (shipment: Shipment) => {
  if (shipment.status === "PENDING" || shipment.status === "READY_TO_SHIP") {
    return "Start Delivery"
  }
  if (shipment.status === "SHIPPED") {
    return "Mark Delivered"
  }
  return null
}

const isActionable = (shipment: Shipment) => ["PENDING", "READY_TO_SHIP", "SHIPPED"].includes(shipment.status)

export function ShipperDashboardPage() {
  const queryClient = useQueryClient()
  const params = useParams<{ orderId: string }>()
  const staffId = useSessionStore((state) => state.staffId)
  const staffName = useSessionStore((state) => state.staffName)
  const selectedOrderId = params.orderId ? Number(params.orderId) : null
  const [locationDraft, setLocationDraft] = useState({ current_lat: "", current_lng: "", is_available: true })

  const shipmentsQuery = useQuery({
    queryKey: ["shipper", "shipments", staffId],
    queryFn: () => shippingApi.listShipments({ shipper_id: staffId as number }),
    enabled: Boolean(staffId),
  })

  const shipperProfileQuery = useQuery({
    queryKey: ["shipper", "profile", staffId],
    queryFn: () => shippingApi.listShippers(),
    enabled: Boolean(staffId),
  })

  const advanceMutation = useMutation({
    mutationFn: (shipment: Shipment) => {
      if (shipment.status === "SHIPPED") {
        return shippingApi.deliver(shipment.id)
      }
      return shippingApi.ship(shipment.id)
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["shipper", "shipments"] })
    },
  })

  const failMutation = useMutation({
    mutationFn: (shipment: Shipment) => shippingApi.fail(shipment.id, "Reported by shipper"),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["shipper", "shipments"] })
    },
  })

  const locationMutation = useMutation({
    mutationFn: () => {
      const profile = shipperProfileQuery.data?.[0]
      if (!profile) {
        throw new Error("Shipper profile is not loaded.")
      }
      const currentLat = locationDraft.current_lat.trim() || profile.current_lat || ""
      const currentLng = locationDraft.current_lng.trim() || profile.current_lng || ""
      return shippingApi.updateShipperLocation(profile.id, {
        current_lat: currentLat,
        current_lng: currentLng,
        is_available: locationDraft.is_available,
      })
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["shipper", "profile"] })
    },
  })

  const shipments = shipmentsQuery.data ?? []
  const shipperProfile = shipperProfileQuery.data?.[0] ?? null
  const selectedShipment =
    selectedOrderId && Number.isFinite(selectedOrderId)
      ? shipments.find((shipment) => shipment.order_id === selectedOrderId) ?? null
      : null
  const activeCount = shipments.filter((shipment) => shipment.status !== "DELIVERED" && shipment.status !== "CANCELLED").length
  const deliveredCount = shipments.filter((shipment) => shipment.status === "DELIVERED").length

  return (
    <section className="shipper-page">
      <div className="shipper-header">
        <div>
          <h1>Shipper Workspace</h1>
          <p className="muted-text">{staffName ? `Signed in as ${staffName}` : "Assigned deliveries"}</p>
        </div>
        <div className="shipper-stats">
          <span>Assigned: {shipments.length}</span>
          <span>Active: {activeCount}</span>
          <span>Delivered: {deliveredCount}</span>
        </div>
      </div>

      <section className="shipper-location-panel">
        <div>
          <h2>Current Location</h2>
          <p className="muted-text">
            {shipperProfile?.last_location_at
              ? `Updated ${new Date(shipperProfile.last_location_at).toLocaleString()}`
              : "No location update yet"}
          </p>
        </div>
        <form
          className="shipper-location-form"
          onSubmit={(event) => {
            event.preventDefault()
            locationMutation.mutate()
          }}
        >
          <input
            className="field"
            value={locationDraft.current_lat || shipperProfile?.current_lat || ""}
            onChange={(event) => setLocationDraft((current) => ({ ...current, current_lat: event.target.value }))}
            placeholder="Latitude"
            required
          />
          <input
            className="field"
            value={locationDraft.current_lng || shipperProfile?.current_lng || ""}
            onChange={(event) => setLocationDraft((current) => ({ ...current, current_lng: event.target.value }))}
            placeholder="Longitude"
            required
          />
          <label className="check-row">
            <input
              type="checkbox"
              checked={locationDraft.is_available}
              onChange={(event) => setLocationDraft((current) => ({ ...current, is_available: event.target.checked }))}
            />
            Available
          </label>
          <button className="primary-button" disabled={locationMutation.isPending || !shipperProfile}>
            Update Location
          </button>
        </form>
      </section>

      {shipmentsQuery.isLoading ? <p>Loading assigned shipments...</p> : null}
      {shipmentsQuery.isError ? <p className="error-text">{getApiErrorMessage(shipmentsQuery.error)}</p> : null}
      {shipperProfileQuery.isError ? <p className="error-text">{getApiErrorMessage(shipperProfileQuery.error)}</p> : null}
      {!staffId ? <p className="error-text">Missing shipper identity. Login again as shipper.</p> : null}
      {staffId && shipperProfileQuery.data && !shipperProfile ? (
        <p className="warning-text">No shipper profile found for this staff account.</p>
      ) : null}
      {shipmentsQuery.data && shipments.length === 0 ? <p>No assigned shipments.</p> : null}

      <div className="shipper-grid">
        {shipments.map((shipment) => (
          <article className="shipper-card" key={shipment.id}>
            <div className="shipper-card-head">
              <strong>Order #{shipment.order_id}</strong>
              <span className="status-pill">{shipment.status}</span>
            </div>
            <dl className="shipper-details">
              <div>
                <dt>Recipient</dt>
                <dd>{shipment.recipient_name}</dd>
              </div>
              <div>
                <dt>Phone</dt>
                <dd>{shipment.phone}</dd>
              </div>
              <div>
                <dt>Address</dt>
                <dd>{shipment.address}</dd>
              </div>
              <div>
                <dt>Distance</dt>
                <dd>{shipment.distance_km_snapshot ? `${shipment.distance_km_snapshot} km` : "N/A"}</dd>
              </div>
            </dl>
            <div className="row-actions">
              <Link to={`/shipper/orders/${shipment.order_id}`}>Open</Link>
              {isActionable(shipment) ? (
                <button
                  className="primary-button"
                  onClick={() => advanceMutation.mutate(shipment)}
                  disabled={advanceMutation.isPending || failMutation.isPending}
                >
                  {actionLabel(shipment)}
                </button>
              ) : null}
              {shipment.status === "SHIPPED" ? (
                <button
                  onClick={() => failMutation.mutate(shipment)}
                  disabled={advanceMutation.isPending || failMutation.isPending}
                >
                  Report Failed
                </button>
              ) : null}
            </div>
          </article>
        ))}
      </div>

      {selectedOrderId ? (
        <section className="shipper-detail-panel">
          <div className="shipper-card-head">
            <h2>Order #{selectedOrderId}</h2>
            <Link to="/shipper/orders">Close</Link>
          </div>
          {shipmentsQuery.isLoading ? <p>Loading shipment detail...</p> : null}
          {!shipmentsQuery.isLoading && !selectedShipment ? <p className="error-text">Assigned shipment not found.</p> : null}
          {selectedShipment ? (
            <div className="shipper-detail-grid">
              <dl className="shipper-details">
                <div>
                  <dt>Status</dt>
                  <dd>{selectedShipment.status}</dd>
                </div>
                <div>
                  <dt>Recipient</dt>
                  <dd>{selectedShipment.recipient_name}</dd>
                </div>
                <div>
                  <dt>Phone</dt>
                  <dd>{selectedShipment.phone}</dd>
                </div>
                <div>
                  <dt>Address</dt>
                  <dd>{selectedShipment.address}</dd>
                </div>
                <div>
                  <dt>Tracking</dt>
                  <dd>{selectedShipment.tracking_number || "N/A"}</dd>
                </div>
              </dl>
              <div>
                <h3>Events</h3>
                <ol className="order-timeline">
                  {selectedShipment.tracking_events.map((event) => (
                    <li className="timeline-step complete" key={event.id}>
                      <span className="timeline-marker" />
                      <div>
                        <strong>{event.status}</strong>
                        <span>{new Date(event.event_time).toLocaleString()}</span>
                        {event.description ? <small>{event.description}</small> : null}
                      </div>
                    </li>
                  ))}
                </ol>
              </div>
              <div className="row-actions">
                {isActionable(selectedShipment) ? (
                  <button
                    className="primary-button"
                    onClick={() => advanceMutation.mutate(selectedShipment)}
                    disabled={advanceMutation.isPending || failMutation.isPending}
                  >
                    {actionLabel(selectedShipment)}
                  </button>
                ) : null}
                {selectedShipment.status === "SHIPPED" ? (
                  <button
                    onClick={() => failMutation.mutate(selectedShipment)}
                    disabled={advanceMutation.isPending || failMutation.isPending}
                  >
                    Report Failed
                  </button>
                ) : null}
              </div>
            </div>
          ) : null}
        </section>
      ) : null}

      {advanceMutation.isError ? <p className="error-text">{getApiErrorMessage(advanceMutation.error)}</p> : null}
      {failMutation.isError ? <p className="error-text">{getApiErrorMessage(failMutation.error)}</p> : null}
      {locationMutation.isError ? <p className="error-text">{getApiErrorMessage(locationMutation.error)}</p> : null}
      {locationMutation.isSuccess ? <p className="success-text">Location updated.</p> : null}
    </section>
  )
}
