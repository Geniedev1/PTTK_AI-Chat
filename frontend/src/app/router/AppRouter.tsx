import { Navigate, createBrowserRouter, RouterProvider } from "react-router-dom"
import { AppShell } from "../layout/AppShell"
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
      { path: "admin/login", element: <AdminLoginPage /> },
      { path: "admin/products", element: <AdminProductsPage /> },
      { path: "admin/orders", element: <AdminOrdersPage /> },
      { path: "admin/interactions", element: <AdminInteractionsPage /> },
      { path: "admin/graph", element: <AdminGraphPage /> },
      { path: "admin/model-status", element: <AdminModelStatusPage /> },
      { path: "*", element: <Navigate to="/" replace /> },
    ],
  },
])

export function AppRouter() {
  return <RouterProvider router={router} />
}
