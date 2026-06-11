import { Link, NavLink, Outlet, useLocation } from "react-router-dom"
import { GlobalChatWidget } from "../../modules/chat-widget/components/GlobalChatWidget"
import { useSessionStore } from "../../shared/stores/sessionStore"

const navItems = [
  { to: "/", label: "Home" },
  { to: "/products", label: "Products" },
  { to: "/cart", label: "Cart" },
  { to: "/orders", label: "Orders" },
  { to: "/assistant", label: "Assistant" },
]

export function CustomerShell() {
  const location = useLocation()
  const customerToken = useSessionStore((state) => state.customerToken)
  const customerUsername = useSessionStore((state) => state.customerUsername)
  const clearAuth = useSessionStore((state) => state.clearAuth)
  const showChat = !location.pathname.startsWith("/auth")

  return (
    <div className="app-shell customer-shell">
      <header className="topbar">
        <Link to="/" className="brand">
          Aiva Commerce
        </Link>
        <nav className="topnav" aria-label="Customer navigation">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) => (isActive ? "topnav-link active" : "topnav-link")}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="topbar-actions">
          {customerToken ? (
            <>
              <NavLink to="/account" className={({ isActive }) => (isActive ? "topnav-link active" : "topnav-link")}>
                {customerUsername ?? "Account"}
              </NavLink>
              <button className="topnav-button" onClick={clearAuth}>
                Logout
              </button>
            </>
          ) : (
            <>
              <NavLink to="/auth/login" className={({ isActive }) => (isActive ? "topnav-link active" : "topnav-link")}>
                Login
              </NavLink>
              <NavLink
                to="/auth/register"
                className={({ isActive }) => (isActive ? "topnav-link active" : "topnav-link")}
              >
                Register
              </NavLink>
            </>
          )}
          <Link className="admin-entry" to="/admin/overview">
            Admin
          </Link>
        </div>
      </header>
      <main className="content">
        <Outlet />
      </main>
      {showChat ? <GlobalChatWidget /> : null}
    </div>
  )
}
