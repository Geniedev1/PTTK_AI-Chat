import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Link } from "react-router-dom"
import { useMemo, useState } from "react"
import { cartApi, productApi } from "../../shared/api/services"
import { PRODUCT_PLACEHOLDER_IMAGE } from "../../shared/constants/media"
import { getApiErrorMessage } from "../../shared/utils/apiError"

export function ProductsPage() {
  const [searchText, setSearchText] = useState("")
  const queryClient = useQueryClient()

  const normalizedSearch = useMemo(() => searchText.trim(), [searchText])

  const productsQuery = useQuery({
    queryKey: ["products", normalizedSearch],
    queryFn: () => productApi.list(normalizedSearch ? { search: normalizedSearch } : undefined),
  })

  const addToCartMutation = useMutation({
    mutationFn: (productId: number) => cartApi.addProduct({ product_id: productId, quantity: 1 }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["cart", "current"] })
    },
  })

  return (
    <section className="panel">
      <div className="section-header">
        <h1>Products</h1>
        <input
          value={searchText}
          onChange={(event) => setSearchText(event.target.value)}
          placeholder="Search products"
          className="field"
        />
      </div>

      {productsQuery.isLoading ? <p>Loading products...</p> : null}
      {productsQuery.isError ? <p className="error-text">{getApiErrorMessage(productsQuery.error)}</p> : null}

      {productsQuery.data && productsQuery.data.length === 0 ? <p>No products found.</p> : null}

      {productsQuery.data ? (
        <div className="product-grid">
          {productsQuery.data.map((product) => (
            <article className="product-card" key={product.id}>
              <img
                className="product-card-image"
                src={product.image_urls[0] || PRODUCT_PLACEHOLDER_IMAGE}
                alt={product.name}
                loading="lazy"
                onError={(event) => {
                  event.currentTarget.src = PRODUCT_PLACEHOLDER_IMAGE
                }}
              />
              <h2>{product.name}</h2>
              <p>{product.short_description || product.description || "No description"}</p>
              <div className="product-meta">
                <span>${product.base_price}</span>
                <span>{product.has_stock ? `Stock ${product.stock}` : "Out of stock"}</span>
              </div>
              <div className="row-actions">
                <Link to={`/products/${product.id}`}>Detail</Link>
                <button
                  onClick={() => addToCartMutation.mutate(product.id)}
                  disabled={!product.has_stock || addToCartMutation.isPending}
                >
                  Add To Cart
                </button>
              </div>
            </article>
          ))}
        </div>
      ) : null}

      {addToCartMutation.isError ? <p className="error-text">{getApiErrorMessage(addToCartMutation.error)}</p> : null}
      {addToCartMutation.isSuccess ? <p className="success-text">Added product to cart.</p> : null}
    </section>
  )
}
