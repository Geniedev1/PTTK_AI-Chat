# API Documentation

## Gateway Routes

- `/api/staff/`
- `/api/customers/`
- `/api/cart/`
- `/api/products/`

## Product Service

Base URL: `/api/products/`

### Create product

`POST /api/products/`

Body:

```json
{
  "name": "MacBook Pro 14",
  "description": "Powerful laptop for professionals",
  "base_price": 2000.0,
  "stock": 10,
  "category_id": null,
  "brand_id": null,
  "product_type_id": null,
  "attributes": {
    "ram": "16GB",
    "cpu": "M3 Pro",
    "storage": "512GB SSD"
  },
  "is_active": true
}
```

### List products

`GET /api/products/`

Query hỗ trợ:

- `category_id`
- `product_type_id`
- `brand_id`
- `in_stock=true`
- `search=keyword`
- `include_inactive=true`

### Get product

`GET /api/products/{id}/`

### Update product

`PUT /api/products/{id}/`

### Delete product

`DELETE /api/products/{id}/`

### In-stock products

`GET /api/products/in_stock/`

### Create variant

`POST /api/products/{id}/variants/`

Body:

```json
{
  "sku": "MBP14-16-512",
  "name": "16GB / 512GB",
  "attributes": {
    "ram": "16GB",
    "storage": "512GB SSD"
  },
  "stock": 5,
  "price_override": 2100.0,
  "is_default": true
}
```

### Categories

- `GET /api/products/categories/`
- `GET /api/products/categories/{id}/`

## Cart Service

Base URL: `/api/cart/`

### Add product to cart

`POST /api/cart/add_product?customer_id=1`

Body:

```json
{
  "product_id": 1,
  "quantity": 2
}
```

### Update quantity

`POST /api/cart/update_quantity?customer_id=1`

Body:

```json
{
  "product_id": 1,
  "quantity": 3
}
```

### Remove product

`POST /api/cart/remove_product?customer_id=1`

Body:

```json
{
  "product_id": 1
}
```

### Other cart endpoints

- `GET /api/cart/`
- `GET /api/cart/by_customer?customer_id=1`
- `POST /api/cart/clear_cart?customer_id=1`

## Staff Service

- `POST /api/staff/`
- `GET /api/staff/`
- `GET /api/staff/{id}/`
- `PUT /api/staff/{id}/`
- `DELETE /api/staff/{id}/`
- `POST /api/staff/login/`
- `GET /api/staff/me/`

## Customer Service

- `POST /api/customers/register/`
- `POST /api/customers/login/`
- `GET /api/customers/profile/`
- `PUT /api/customers/update_profile/`
- `GET /api/customers/`
- `GET /api/customers/{id}/`
