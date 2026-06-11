import { Navigate, createBrowserRouter, RouterProvider } from "react-router-dom"
import { AdminShell } from "../layout/AdminShell"
import { CustomerShell } from "../layout/CustomerShell"
import { AdminGraphPage } from "../../pages/admin/AdminGraphPage"
import { AdminInteractionsPage } from "../../pages/admin/AdminInteractionsPage"
import { AdminLoginPage } from "../../pages/admin/AdminLoginPage"
import { AdminModelStatusPage } from "../../pages/admin/AdminModelStatusPage"
import { AdminOrdersPage } from "../../pages/admin/AdminOrdersPage"
import { AdminOverviewPage } from "../../pages/admin/AdminOverviewPage"
import { AdminPaymentsPage } from "../../pages/admin/AdminPaymentsPage"
import { AdminProductsPage } from "../../pages/admin/AdminProductsPage"
import { AdminShipmentsPage } from "../../pages/admin/AdminShipmentsPage"
import { AssistantPage } from "../../pages/customer/AssistantPage"
import { AuthPage } from "../../pages/customer/AuthPage"
import { CartPage } from "../../pages/customer/CartPage"
import { CheckoutPage } from "../../pages/customer/CheckoutPage"
import { HomePage } from "../../pages/customer/HomePage"
import { OrdersPage } from "../../pages/customer/OrdersPage"
import { ProfilePage } from "../../pages/customer/ProfilePage"
import { ProductDetailPage } from "../../pages/customer/ProductDetailPage"
import { ProductsPage } from "../../pages/customer/ProductsPage"

const router = createBrowserRouter([
  {
    path: "/",
    element: <CustomerShell />,
    children: [
      { index: true, element: <HomePage /> },
      { path: "products", element: <ProductsPage /> },
      { path: "products/:productId", element: <ProductDetailPage /> },
      { path: "cart", element: <CartPage /> },
      { path: "checkout", element: <CheckoutPage /> },
      { path: "orders", element: <OrdersPage /> },
      { path: "orders/:orderId", element: <OrdersPage /> },
      { path: "assistant", element: <AssistantPage /> },
      { path: "auth/login", element: <AuthPage mode="login" /> },
      { path: "auth/register", element: <AuthPage mode="register" /> },
      { path: "profile", element: <ProfilePage /> },
      { path: "account", element: <ProfilePage /> },
      { path: "*", element: <Navigate to="/" replace /> },
    ],
  },
  {
    path: "/admin",
    element: <AdminShell />,
    children: [
      { index: true, element: <Navigate to="/admin/overview" replace /> },
      { path: "login", element: <AdminLoginPage /> },
      { path: "overview", element: <AdminOverviewPage /> },
      { path: "products", element: <AdminProductsPage /> },
      { path: "orders", element: <AdminOrdersPage /> },
      { path: "payments", element: <AdminPaymentsPage /> },
      { path: "shipments", element: <AdminShipmentsPage /> },
      { path: "interactions", element: <AdminInteractionsPage /> },
      { path: "graph", element: <AdminGraphPage /> },
      { path: "model-status", element: <AdminModelStatusPage /> },
      { path: "*", element: <Navigate to="/admin/overview" replace /> },
    ],
  },
])

export function AppRouter() {
  return <RouterProvider router={router} />
}
