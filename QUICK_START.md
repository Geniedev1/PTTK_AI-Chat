# Quick Start Guide

## 1. Build và chạy

```bash
docker-compose build
docker-compose up -d
docker-compose ps
```

Container chính mong đợi:

- `api-gateway`
- `staff-service`
- `customer-service`
- `cart-service`
- `product-service`
- `staff-db`
- `customer-db`
- `cart-db`
- `product-db`

## 2. Kiểm tra health

```bash
curl http://localhost/health
```

## 3. Tạo product mẫu

```bash
curl -X POST http://localhost/api/products/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "MacBook Pro 14",
    "description": "Powerful laptop for professionals",
    "base_price": 2000.00,
    "stock": 10,
    "attributes": {
      "ram": "16GB",
      "cpu": "M3 Pro",
      "storage": "512GB SSD"
    }
  }'
```

## 4. Tạo customer mẫu

```bash
curl -X POST http://localhost/api/customers/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "customer1",
    "password": "pass123",
    "email": "customer1@example.com",
    "phone": "0987654321",
    "address": "123 Main St",
    "city": "Hanoi",
    "country": "Vietnam"
  }'
```

## 5. Add product vào cart

```bash
curl -X POST "http://localhost/api/cart/add_product?customer_id=1" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": 1,
    "quantity": 2
  }'
```

## 6. Script test nhanh

```bash
chmod +x curl-examples.sh
./curl-examples.sh
```

Hoặc:

```bash
make test
```

## 7. Lệnh hay dùng

```bash
docker-compose logs -f
docker-compose logs -f product-service
docker-compose exec product-service bash
docker-compose down
docker-compose down -v
```

## 8. Database ports

- `staff-db`: `3306`
- `customer-db`: `3307`
- `cart-db`: `5432`
- `product-db`: `5433`
