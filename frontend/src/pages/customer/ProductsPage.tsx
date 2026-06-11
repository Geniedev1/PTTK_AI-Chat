import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Link, useSearchParams } from "react-router-dom"
import { useMemo, useState } from "react"
import { cartApi, productApi } from "../../shared/api/services"
import {
  Button,
  EmptyState,
  ErrorBanner,
  LoadingState,
  PageHeader,
  Pagination,
  StatusBadge,
  formatCurrency,
  statusTone,
} from "../../shared/components/ui"
import { PRODUCT_PLACEHOLDER_IMAGE } from "../../shared/constants/media"
import { getApiErrorMessage } from "../../shared/utils/apiError"

const PAGE_SIZE_OPTIONS = [8, 12, 24]

export function ProductsPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [searchText, setSearchText] = useState("")
  const [stockOnly, setStockOnly] = useState(true)
  const [sortBy, setSortBy] = useState("name")
  const [pageSize, setPageSize] = useState(12)
  const [page, setPage] = useState(1)
  const queryClient = useQueryClient()

  const categoryParam = searchParams.get("category")
  const categoryFilter = categoryParam ? Number(categoryParam) : null

  const productsQuery = useQuery({
    queryKey: ["products", "catalog"],
    queryFn: () => productApi.list(),
  })

  const addToCartMutation = useMutation({
    mutationFn: (productId: number) => cartApi.addProduct({ product_id: productId, quantity: 1 }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["cart", "current"] })
    },
  })

  const products = productsQuery.data ?? []
  const categories = useMemo(
    () => Array.from(new Set(products.map((product) => product.category_id).filter(Boolean))).sort(),
    [products],
  )

  const filteredProducts = useMemo(() => {
    const normalized = searchText.trim().toLowerCase()
    const next = products
      .filter((product) => {
        if (stockOnly && !product.has_stock) {
          return false
        }
        if (categoryFilter && product.category_id !== categoryFilter) {
          return false
        }
        if (!normalized) {
          return true
        }
        const haystack = [
          product.name,
          product.short_description,
          product.description,
          product.tags.join(" "),
        ]
          .join(" ")
          .toLowerCase()
        return haystack.includes(normalized)
      })
      .sort((a, b) => {
        if (sortBy === "price-asc") {
          return Number(a.base_price) - Number(b.base_price)
        }
        if (sortBy === "price-desc") {
          return Number(b.base_price) - Number(a.base_price)
        }
        if (sortBy === "stock") {
          return b.stock - a.stock
        }
        return a.name.localeCompare(b.name)
      })
    return next
  }, [categoryFilter, products, searchText, sortBy, stockOnly])

  const pageCount = Math.max(1, Math.ceil(filteredProducts.length / pageSize))
  const safePage = Math.min(page, pageCount)
  const pagedProducts = filteredProducts.slice((safePage - 1) * pageSize, safePage * pageSize)

  const setCategory = (categoryId: number | null) => {
    const next = new URLSearchParams(searchParams)
    if (categoryId) {
      next.set("category", String(categoryId))
    } else {
      next.delete("category")
    }
    setSearchParams(next)
    setPage(1)
  }

  return (
    <div className="page-stack">
      <PageHeader
        eyebrow="Catalog"
        title="Shop products"
        description="Search, filter, and add products to your cart without leaving the catalog."
      />

      <section className="catalog-layout">
        <aside className="filter-panel">
          <h2>Filters</h2>
          <label>
            Search
            <input
              className="field"
              value={searchText}
              placeholder="Keyboard, laptop, audio..."
              onChange={(event) => {
                setSearchText(event.target.value)
                setPage(1)
              }}
            />
          </label>
          <label>
            Category
            <select
              className="field"
              value={categoryFilter ?? ""}
              onChange={(event) => setCategory(event.target.value ? Number(event.target.value) : null)}
            >
              <option value="">All categories</option>
              {categories.map((categoryId) => (
                <option key={categoryId} value={categoryId ?? ""}>
                  Category {categoryId}
                </option>
              ))}
            </select>
          </label>
          <label>
            Sort
            <select
              className="field"
              value={sortBy}
              onChange={(event) => {
                setSortBy(event.target.value)
                setPage(1)
              }}
            >
              <option value="name">Name</option>
              <option value="price-asc">Price low to high</option>
              <option value="price-desc">Price high to low</option>
              <option value="stock">Most stock</option>
            </select>
          </label>
          <label className="check-row">
            <input
              type="checkbox"
              checked={stockOnly}
              onChange={(event) => {
                setStockOnly(event.target.checked)
                setPage(1)
              }}
            />
            In stock only
          </label>
          <label>
            Page size
            <select
              className="field"
              value={pageSize}
              onChange={(event) => {
                setPageSize(Number(event.target.value))
                setPage(1)
              }}
            >
              {PAGE_SIZE_OPTIONS.map((option) => (
                <option key={option} value={option}>
                  {option} products
                </option>
              ))}
            </select>
          </label>
        </aside>

        <section className="catalog-results">
          <div className="result-toolbar">
            <strong>{filteredProducts.length} products</strong>
            <span>{stockOnly ? "Only available items" : "Including unavailable items"}</span>
          </div>

          {productsQuery.isLoading ? <LoadingState label="Loading catalog..." /> : null}
          {productsQuery.isError ? <ErrorBanner message={getApiErrorMessage(productsQuery.error)} /> : null}

          {!productsQuery.isLoading && filteredProducts.length === 0 ? (
            <EmptyState title="No products found" description="Try a different search or remove a filter." />
          ) : null}

          {pagedProducts.length > 0 ? (
            <>
              <div className="product-grid">
                {pagedProducts.map((product) => (
                  <article className="product-card" key={product.id}>
                    <img
                      className="product-card-image"
                      src={product.image_urls[0] || PRODUCT_PLACEHOLDER_IMAGE}
                      alt={product.name}
                      onError={(event) => {
                        event.currentTarget.src = PRODUCT_PLACEHOLDER_IMAGE
                      }}
                    />
                    <div>
                      <div className="card-title-row">
                        <h3>{product.name}</h3>
                        <StatusBadge tone={statusTone(product.has_stock ? "ACTIVE" : "OUT_OF_STOCK")}>
                          {product.has_stock ? "In stock" : "Out"}
                        </StatusBadge>
                      </div>
                      <p>{product.short_description || product.description || "No description available."}</p>
                    </div>
                    <div className="product-meta">
                      <span>{formatCurrency(product.base_price)}</span>
                      <span>{product.stock} units</span>
                    </div>
                    <div className="row-actions">
                      <Link className="btn btn-secondary" to={`/products/${product.id}`}>
                        Details
                      </Link>
                      <Button
                        disabled={!product.has_stock || addToCartMutation.isPending}
                        variant="primary"
                        onClick={() => addToCartMutation.mutate(product.id)}
                      >
                        Add
                      </Button>
                    </div>
                  </article>
                ))}
              </div>
              <Pagination
                page={safePage}
                pageCount={pageCount}
                pageSize={pageSize}
                total={filteredProducts.length}
                onPageChange={setPage}
              />
            </>
          ) : null}
        </section>
      </section>

      {addToCartMutation.isError ? <ErrorBanner message={getApiErrorMessage(addToCartMutation.error)} /> : null}
      {addToCartMutation.isSuccess ? <div className="success-banner">Product added to cart.</div> : null}
    </div>
  )
}
