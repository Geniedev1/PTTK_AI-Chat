import { Link } from "react-router-dom"

type Props = {
  title: string
  description: string
}

export function PagePlaceholder({ title, description }: Props) {
  return (
    <section className="panel">
      <h1>{title}</h1>
      <p>{description}</p>
      <div className="quick-links">
        <Link to="/products">Products</Link>
        <Link to="/cart">Cart</Link>
        <Link to="/orders">Orders</Link>
        <Link to="/assistant">AI Assistant</Link>
      </div>
    </section>
  )
}
