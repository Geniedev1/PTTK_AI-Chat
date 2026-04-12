# Troubleshooting

## Gateway trả `502 Bad Gateway`

Kiểm tra service đích:

```bash
docker-compose ps
docker-compose logs api-gateway
docker-compose logs product-service
```

Test trực tiếp:

```bash
curl http://localhost:8004/api/products/
curl http://localhost/api/products/
```

## Product service không lên

```bash
docker-compose logs product-db
docker-compose logs product-service
docker-compose restart product-db product-service
```

Nếu cần chạy migrate lại:

```bash
docker-compose exec product-service python manage.py migrate
```

## Cart add product báo lỗi

Cart bây giờ chỉ nhận `product_id`.

Payload đúng:

```json
{
  "product_id": 1,
  "quantity": 2
}
```

Kiểm tra product có tồn tại:

```bash
curl http://localhost/api/products/1/
docker-compose exec cart-service curl http://product-service:8004/api/products/1/
```

## Port bị chiếm

```bash
lsof -i :80
lsof -i :8004
```

Sau đó đổi port trong `docker-compose.yml` nếu cần.

## Khởi động sạch từ đầu

```bash
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```
