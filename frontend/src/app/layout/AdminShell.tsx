import { Link, NavLink, Outlet } from "react-router-dom"
import { useSessionStore } from "../../shared/stores/sessionStore"

const adminNav = [
  { to: "/admin/overview", label: "Overview" },
  { to: "/admin/products", label: "Products" },
  { to: "/admin/orders", label: "Orders" },
  { to: "/admin/payments", label: "Payments" },
  { to: "/admin/shipments", label: "Shipments" },
  { to: "/admin/interactions", label: "Interactions" },
  { to: "/admin/graph", label: "Graph" },
  { to: "/admin/model-status", label: "AI Model" },
]

export function AdminShell() {
  const staffToken = useSessionStore((state) => state.staffToken)
  const clearAuth = useSessionStore((state) => state.clearAuth)

  return (
    <div className="admin-shell">
      <aside className="admin-sidebar">
        <Link to="/admin/overview" className="brand admin-brand">
          Aiva Admin
        </Link>
        <nav className="admin-nav" aria-label="Admin navigation">
          {adminNav.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) => (isActive ? "admin-nav-link active" : "admin-nav-link")}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="admin-sidebar-footer">
          <span>{staffToken ? "Staff session active" : "Staff login required"}</span>
          {staffToken ? (
            <button className="topnav-button" onClick={clearAuth}>
              Logout
            </button>
          ) : (
            <Link className="btn btn-secondary" to="/admin/login">
              Login
            </Link>
          )}
          <Link to="/" className="admin-back-link">
            Customer site
          </Link>
        </div>
      </aside>
      <main className="admin-content">
        <Outlet />
      </main>
    </div>
  )
}
