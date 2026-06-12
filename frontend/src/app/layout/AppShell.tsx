import {
  BellOutlined,
  HeartOutlined,
  HomeOutlined,
  LoginOutlined,
  RobotOutlined,
  SearchOutlined,
  ShoppingCartOutlined,
  ShopOutlined,
  UserOutlined,
} from "@ant-design/icons"
import { Link, NavLink, Outlet, useLocation } from "react-router-dom"
import { GlobalChatWidget } from "../../modules/chat-widget/components/GlobalChatWidget"
import { useSessionStore } from "../../shared/stores/sessionStore"

const navItems = [
  { to: "/", label: "Home" },
  { to: "/products", label: "Shop" },
  { to: "/orders", label: "Deals" },
  { to: "/assistant", label: "Support" },
]

export function AppShell() {
  const location = useLocation()
  const isAdminRoute = location.pathname.startsWith("/admin")
  const isShipperRoute = location.pathname.startsWith("/shipper")
  const isStaffWorkspace = isAdminRoute || isShipperRoute
  const isAuthRoute = location.pathname.startsWith("/auth")
  const showChat = !isStaffWorkspace && !isAuthRoute
  const customerToken = useSessionStore((state) => state.customerToken)
  const customerUsername = useSessionStore((state) => state.customerUsername)
  const staffToken = useSessionStore((state) => state.staffToken)
  const staffName = useSessionStore((state) => state.staffName)
  const staffRoles = useSessionStore((state) => state.staffRoles)
  const clearAuth = useSessionStore((state) => state.clearAuth)
  const isStaffSession = Boolean(staffToken)

  return (
    <div className={isStaffWorkspace ? "app-shell admin-shell" : "app-shell"}>
      <header className={isStaffWorkspace ? "topbar admin-topbar" : "topbar"}>
        <Link to="/" className="brand">
          <span className="brand-mark">A</span>
          AuraShop
        </Link>
        {!isStaffWorkspace ? (
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
          </nav>
        ) : null}
        {!isStaffWorkspace && !isAuthRoute ? (
          <div className="top-search" aria-label="Search products">
            <SearchOutlined />
            <span>Search products, brands, and AI recommendations...</span>
          </div>
        ) : null}
        <nav className="top-actions" aria-label="Account and cart actions">
          {isStaffWorkspace ? (
            <>
              <button className="icon-button" aria-label="Notifications">
                <BellOutlined />
                <span className="action-dot" />
              </button>
              <NavLink to="/profile" className="avatar-button" aria-label="Profile">
                <UserOutlined />
              </NavLink>
            </>
          ) : (
            <>
              <NavLink to="/cart" className="icon-button" aria-label="Cart">
                <ShoppingCartOutlined />
              </NavLink>
              <NavLink to="/profile" className="icon-button" aria-label="Profile">
                <UserOutlined />
              </NavLink>
              <button className="icon-button" aria-label="Wishlist">
                <HeartOutlined />
              </button>
            </>
          )}
          {isStaffSession ? (
            <>
              <span className="account-link">
                {staffName ?? "Staff"} {staffRoles.length ? `(${staffRoles.join(", ")})` : null}
              </span>
              <button className="topnav-button" onClick={clearAuth}>
                <LoginOutlined /> Logout
              </button>
            </>
          ) : customerToken ? (
            <>
              <NavLink to="/profile" className="account-link">
                {customerUsername ?? "Profile"}
              </NavLink>
              <button className="topnav-button" onClick={clearAuth}>
                <LoginOutlined /> Logout
              </button>
            </>
          ) : (
            <>
              <NavLink to="/auth/login" className="topnav-button">
                Login
              </NavLink>
            </>
          )}
          {staffRoles.includes("shipper") ? (
            <NavLink to="/shipper/orders" className="topnav-button admin-link">
              <ShoppingCartOutlined /> Shipper
            </NavLink>
          ) : null}
          {staffRoles.includes("admin") || !staffToken ? (
            <NavLink to="/admin" className="topnav-button admin-link">
              <ShopOutlined /> Admin
            </NavLink>
          ) : null}
        </nav>
      </header>
      <main className="content">
        {isAdminRoute ? (
          <aside className="admin-sidebar" aria-label="Admin navigation">
            <NavLink to="/admin" end className={({ isActive }) => (isActive ? "admin-sidebar-item active" : "admin-sidebar-item")}>
              <HomeOutlined /> Dashboard
            </NavLink>
            <NavLink to="/admin/orders" className={({ isActive }) => (isActive ? "admin-sidebar-item active" : "admin-sidebar-item")}>
              <ShoppingCartOutlined /> Orders
            </NavLink>
            <NavLink to="/admin/products" className={({ isActive }) => (isActive ? "admin-sidebar-item active" : "admin-sidebar-item")}>
              <ShopOutlined /> Products
            </NavLink>
            <NavLink to="/admin/interactions" className={({ isActive }) => (isActive ? "admin-sidebar-item active" : "admin-sidebar-item")}>
              <RobotOutlined /> AI Analytics
            </NavLink>
          </aside>
        ) : null}
        {isShipperRoute ? (
          <aside className="admin-sidebar" aria-label="Shipper navigation">
            <NavLink to="/shipper/orders" className={({ isActive }) => (isActive ? "admin-sidebar-item active" : "admin-sidebar-item")}>
              <ShoppingCartOutlined /> Assigned Orders
            </NavLink>
          </aside>
        ) : null}
        <Outlet />
      </main>
      {showChat ? <GlobalChatWidget /> : null}
      {!isStaffWorkspace ? (
        <footer className="site-footer">
          <Link to="/">About Us</Link>
          <Link to="/assistant">Help</Link>
          <Link to="/orders">Shipping</Link>
          <Link to="/orders">Returns</Link>
          <Link to="/profile">Privacy Policy</Link>
          <Link to="/profile">Terms of Service</Link>
        </footer>
      ) : null}
    </div>
  )
}
