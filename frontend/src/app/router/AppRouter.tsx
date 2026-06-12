import type { ReactNode } from "react"
import { Navigate, createBrowserRouter, RouterProvider } from "react-router-dom"
import { AppShell } from "../layout/AppShell"
import { AdminDashboardPage } from "../../pages/admin/AdminDashboardPage"
import { AdminGraphPage } from "../../pages/admin/AdminGraphPage"
import { AdminInteractionsPage } from "../../pages/admin/AdminInteractionsPage"
import { AdminLoginPage } from "../../pages/admin/AdminLoginPage"
import { AdminModelStatusPage } from "../../pages/admin/AdminModelStatusPage"
import { AdminOrdersPage } from "../../pages/admin/AdminOrdersPage"
import { AdminProductsPage } from "../../pages/admin/AdminProductsPage"
import { AssistantPage } from "../../pages/customer/AssistantPage"
import { AuthPage } from "../../pages/customer/AuthPage"
import { CartPage } from "../../pages/customer/CartPage"
import { HomePage } from "../../pages/customer/HomePage"
import { OrdersPage } from "../../pages/customer/OrdersPage"
import { ProfilePage } from "../../pages/customer/ProfilePage"
import { ProductDetailPage } from "../../pages/customer/ProductDetailPage"
import { ProductsPage } from "../../pages/customer/ProductsPage"
import { ShipperDashboardPage } from "../../pages/shipper/ShipperDashboardPage"
import { useSessionStore } from "../../shared/stores/sessionStore"

function RequireStaffRole({ allowedRoles, children }: { allowedRoles: string[]; children: ReactNode }) {
  const staffToken = useSessionStore((state) => state.staffToken)
  const staffRoles = useSessionStore((state) => state.staffRoles)

  if (!staffToken) {
    return <Navigate to="/admin/login" replace />
  }

  if (!allowedRoles.some((role) => staffRoles.includes(role))) {
    return <Navigate to="/" replace />
  }

  return <>{children}</>
}

const router = createBrowserRouter([
  {
    path: "/",
    element: <AppShell />,
    children: [
      { index: true, element: <HomePage /> },
      { path: "products", element: <ProductsPage /> },
      { path: "products/:productId", element: <ProductDetailPage /> },
      { path: "cart", element: <CartPage /> },
      { path: "checkout", element: <CartPage /> },
      { path: "orders", element: <OrdersPage /> },
      { path: "orders/:orderId", element: <OrdersPage /> },
      { path: "assistant", element: <AssistantPage /> },
      { path: "auth/login", element: <AuthPage mode="login" /> },
      { path: "auth/register", element: <AuthPage mode="register" /> },
      { path: "profile", element: <ProfilePage /> },
      { path: "admin", element: <RequireStaffRole allowedRoles={["admin"]}><AdminDashboardPage /></RequireStaffRole> },
      { path: "admin/login", element: <AdminLoginPage /> },
      { path: "admin/products", element: <RequireStaffRole allowedRoles={["admin"]}><AdminProductsPage /></RequireStaffRole> },
      { path: "admin/orders", element: <RequireStaffRole allowedRoles={["admin"]}><AdminOrdersPage /></RequireStaffRole> },
      { path: "admin/interactions", element: <RequireStaffRole allowedRoles={["admin"]}><AdminInteractionsPage /></RequireStaffRole> },
      { path: "admin/graph", element: <RequireStaffRole allowedRoles={["admin"]}><AdminGraphPage /></RequireStaffRole> },
      { path: "admin/model-status", element: <RequireStaffRole allowedRoles={["admin"]}><AdminModelStatusPage /></RequireStaffRole> },
      { path: "shipper", element: <RequireStaffRole allowedRoles={["shipper"]}><ShipperDashboardPage /></RequireStaffRole> },
      { path: "shipper/orders", element: <RequireStaffRole allowedRoles={["shipper"]}><ShipperDashboardPage /></RequireStaffRole> },
      { path: "shipper/orders/:orderId", element: <RequireStaffRole allowedRoles={["shipper"]}><ShipperDashboardPage /></RequireStaffRole> },
      { path: "*", element: <Navigate to="/" replace /> },
    ],
  },
])

export function AppRouter() {
  return <RouterProvider router={router} />
}
