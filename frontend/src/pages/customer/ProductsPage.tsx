import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Link } from "react-router-dom"
import { useMemo, useState } from "react"
import { cartApi, productApi } from "../../shared/api/services"
import { PRODUCT_PLACEHOLDER_IMAGE } from "../../shared/constants/media"
import { getApiErrorMessage } from "../../shared/utils/apiError"

const categoryKeywords: Record<string, string[]> = {
  clothing: ["clothes", "fashion", "shirt", "hoodie", "pants", "shoes", "sneakers", "wear"],
  electronics: ["electronics", "laptop", "audio", "monitor", "keyboard", "mouse", "headphone", "charger"],
  home: ["home", "desk", "chair", "lamp", "stand", "pot"],
  beauty: ["beauty", "skin", "cream", "care"],
}

export function ProductsPage() {
  const [searchText, setSearchText] = useState("")
  const [selectedTag, setSelectedTag] = useState("")
  const [maxPrice, setMaxPrice] = useState(350)
  const [inStockOnly, setInStockOnly] = useState(false)
  const [sortBy, setSortBy] = useState("relevance")
  const queryClient = useQueryClient()

  const normalizedSearch = useMemo(() => searchText.trim(), [searchText])
  const productParams = useMemo(
    () => ({
      search: normalizedSearch || undefined,
      max_price: maxPrice < 350 ? maxPrice : undefined,
      sort_by: sortBy === "relevance" ? undefined : sortBy,
      in_stock: inStockOnly || undefined,
    }),
    [inStockOnly, maxPrice, normalizedSearch, sortBy],
  )

  const productsQuery = useQuery({
    queryKey: ["products", productParams],
    queryFn: () => productApi.list(productParams),
  })

  const addToCartMutation = useMutation({
    mutationFn: (productId: number) => cartApi.addProduct({ product_id: productId, quantity: 1 }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["cart", "current"] })
    },
  })

  const visibleProducts = useMemo(() => {
    const products = productsQuery.data ?? []
    if (!selectedTag) {
      return products
    }
    const keywords = categoryKeywords[selectedTag] ?? [selectedTag]
    return products.filter((product) => {
      const haystack = [
        product.name,
        product.short_description,
        product.description,
        ...product.tags,
        ...Object.values(product.attributes).map(String),
      ]
        .join(" ")
        .toLowerCase()
      return keywords.some((keyword) => haystack.includes(keyword))
    })
  }, [productsQuery.data, selectedTag])

  return (
    <section className="shop-page">
      <aside className="shop-filters">
        <h1>Filters</h1>
        <div className="filter-group">
          <h2>Category</h2>
          {[
            { label: "Clothing", tag: "clothing" },
            { label: "Electronics", tag: "electronics" },
            { label: "Home & Living", tag: "home" },
            { label: "Beauty", tag: "beauty" },
          ].map((item) => (
            <label className="check-row" key={item.label}>
              <input
                type="checkbox"
                checked={selectedTag === item.tag}
                onChange={() => setSelectedTag((current) => (current === item.tag ? "" : item.tag))}
              />
              {item.label}
            </label>
          ))}
        </div>
        <div className="filter-group">
          <h2>Price</h2>
          <input
            className="range-field"
            type="range"
            min={20}
            max={350}
            value={maxPrice}
            onChange={(event) => setMaxPrice(Number(event.target.value))}
          />
          <div className="price-row">
            <span>$20</span>
            <span>$20 - ${maxPrice}</span>
            <span>$350</span>
          </div>
        </div>
        <div className="filter-group">
          <h2>Rating</h2>
          {["4 stars & up", "3 stars & up", "2 stars & up"].map((label) => (
            <label className="check-row" key={label}>
              <input type="checkbox" />
              {label}
            </label>
          ))}
          <label className="check-row">
            <input type="checkbox" checked={inStockOnly} onChange={(event) => setInStockOnly(event.target.checked)} />
            In stock only
          </label>
        </div>
        <div className="filter-group">
          <h2>Color</h2>
          {[
            ["Black", "#050505"],
            ["White", "#f8f8f8"],
            ["Terracotta", "#b76548"],
            ["Blue", "#415cc7"],
            ["Green", "#5a9a62"],
          ].map(([label, color]) => (
            <label className="swatch-row" key={label}>
              <span style={{ background: color }} />
              {label}
            </label>
          ))}
        </div>
      </aside>

      <div className="shop-main">
        <div className="shop-toolbar">
          <span>Showing {visibleProducts.length ? `1-${Math.min(12, visibleProducts.length)}` : "0"} of {visibleProducts.length} products</span>
          <input
            value={searchText}
            onChange={(event) => setSearchText(event.target.value)}
            placeholder="Search products"
            className="field shop-search"
          />
          <label>
            Sort by:
            <select value={sortBy} onChange={(event) => setSortBy(event.target.value)}>
              <option value="relevance">Relevance</option>
              <option value="price_asc">Price low to high</option>
              <option value="price_desc">Price high to low</option>
              <option value="name_asc">Name</option>
            </select>
          </label>
        </div>

      {productsQuery.isLoading ? <p>Loading products...</p> : null}
      {productsQuery.isError ? <p className="error-text">{getApiErrorMessage(productsQuery.error)}</p> : null}

      {productsQuery.data && visibleProducts.length === 0 ? <p>No products found.</p> : null}

      {productsQuery.data ? (
        <div className="shop-product-grid">
          {visibleProducts.map((product, index) => (
            <article className="product-card shop-card" key={product.id}>
              {index === 0 || index === 2 || index === 6 ? <span className="ai-badge">AI-Recommended</span> : null}
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
              <div className="product-meta">
                <strong>${product.base_price}</strong>
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
      </div>
    </section>
  )
}
