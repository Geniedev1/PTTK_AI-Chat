import { Link, NavLink, Outlet, useLocation } from "react-router-dom"
import { GlobalChatWidget } from "../../modules/chat-widget/components/GlobalChatWidget"
import { useSessionStore } from "../../shared/stores/sessionStore"

const navItems = [
  { to: "/products", label: "Catalog" },
  { to: "/cart", label: "Cart" },
  { to: "/orders", label: "Orders" },
  { to: "/assistant", label: "AI Assistant" },
]

export function AppShell() {
  const location = useLocation()
  const showChat = !location.pathname.startsWith("/admin")
  const customerToken = useSessionStore((state) => state.customerToken)
  const customerUsername = useSessionStore((state) => state.customerUsername)
  const clearAuth = useSessionStore((state) => state.clearAuth)

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="topbar-inner">
          <Link to="/" className="brand">
            <span className="brand-title">Genie Commerce</span>
            <span className="brand-subtitle">AI-powered business storefront</span>
          </Link>
          <nav className="topnav">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) => (isActive ? "topnav-link active" : "topnav-link")}
              >
                {item.label}
              </NavLink>
            ))}
            <NavLink to="/admin/login" className={({ isActive }) => (isActive ? "topnav-link active" : "topnav-link")}>
              Admin
            </NavLink>
            {customerToken ? (
              <>
                <NavLink to="/profile" className={({ isActive }) => (isActive ? "topnav-link active" : "topnav-link")}>
                  {customerUsername ? `Profile (${customerUsername})` : "Profile"}
                </NavLink>
                <button className="topnav-button" onClick={clearAuth}>Logout</button>
              </>
            ) : (
              <>
                <NavLink
                  to="/auth/login"
                  className={({ isActive }) => (isActive ? "topnav-link active" : "topnav-link")}
                >
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
          </nav>
        </div>
      </header>
      <main className="content">
        <Outlet />
      </main>
      <footer className="site-footer">
        <p>© {new Date().getFullYear()} Genie Commerce. Smart shopping experiences for modern businesses.</p>
      </footer>
      {showChat ? <GlobalChatWidget /> : null}
    </div>
  )
}
