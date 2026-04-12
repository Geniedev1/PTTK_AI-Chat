#!/bin/bash

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

BASE_URL="http://localhost"

echo -e "${BLUE}=== MICROSERVICE E-COMMERCE API TEST ===${NC}\n"

echo -e "${GREEN}1. Testing API Gateway Health${NC}"
curl -s "$BASE_URL/health" | head -c 80
echo -e "\n"

echo -e "${BLUE}--- STAFF SERVICE TESTS ---${NC}\n"
STAFF_RESPONSE=$(curl -s -X POST "$BASE_URL/api/staff/" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "manager1",
    "password": "secret123",
    "name": "John Manager",
    "email": "john@example.com",
    "phone": "0123456789",
    "position": "Manager"
  }')
echo "$STAFF_RESPONSE" | head -c 120
echo -e "\n"

echo -e "${BLUE}--- CUSTOMER SERVICE TESTS ---${NC}\n"
CUSTOMER_RESPONSE=$(curl -s -X POST "$BASE_URL/api/customers/register/" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "customer1",
    "password": "pass123",
    "email": "customer1@example.com",
    "phone": "0987654321",
    "address": "123 Main St",
    "city": "Hanoi",
    "country": "Vietnam"
  }')
echo "$CUSTOMER_RESPONSE" | head -c 120
echo -e "\n"

echo -e "${BLUE}--- PRODUCT SERVICE TESTS ---${NC}\n"
PRODUCT_RESPONSE=$(curl -s -X POST "$BASE_URL/api/products/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "MacBook Pro 14",
    "description": "Powerful laptop for professionals",
    "base_price": 2000.00,
    "stock": 10,
    "attributes": {
      "ram": "16GB",
      "cpu": "M3 Pro",
      "storage": "512GB SSD",
      "category_hint": "Laptop"
    }
  }')
echo "$PRODUCT_RESPONSE"
PRODUCT_ID=$(echo "$PRODUCT_RESPONSE" | grep -o '"id":[0-9]*' | head -1 | grep -o '[0-9]*')
echo -e "\n"

echo -e "${GREEN}Listing products${NC}"
curl -s -X GET "$BASE_URL/api/products/" | head -c 200
echo -e "\n"

echo -e "${GREEN}Listing in-stock products${NC}"
curl -s -X GET "$BASE_URL/api/products/in_stock/" | head -c 200
echo -e "\n"

echo -e "${BLUE}--- CART SERVICE TESTS ---${NC}\n"
CUSTOMER_ID=1

echo -e "${GREEN}Adding product to cart${NC}"
if [ ! -z "$PRODUCT_ID" ]; then
  curl -s -X POST "$BASE_URL/api/cart/add_product?customer_id=$CUSTOMER_ID" \
    -H "Content-Type: application/json" \
    -d "{
      \"product_id\": $PRODUCT_ID,
      \"quantity\": 2
    }" | head -c 200
else
  echo "Product ID not found, skipping..."
fi
echo -e "\n"

echo -e "${GREEN}Getting customer cart${NC}"
curl -s -X GET "$BASE_URL/api/cart/by_customer?customer_id=$CUSTOMER_ID" | head -c 200
echo -e "\n"

echo -e "${GREEN}Updating cart quantity${NC}"
if [ ! -z "$PRODUCT_ID" ]; then
  curl -s -X POST "$BASE_URL/api/cart/update_quantity?customer_id=$CUSTOMER_ID" \
    -H "Content-Type: application/json" \
    -d "{
      \"product_id\": $PRODUCT_ID,
      \"quantity\": 3
    }" | head -c 200
fi
echo -e "\n"

echo -e "${GREEN}Removing product from cart${NC}"
if [ ! -z "$PRODUCT_ID" ]; then
  curl -s -X POST "$BASE_URL/api/cart/remove_product?customer_id=$CUSTOMER_ID" \
    -H "Content-Type: application/json" \
    -d "{
      \"product_id\": $PRODUCT_ID
    }" | head -c 200
fi
echo -e "\n"

echo -e "${GREEN}=== TEST COMPLETED ===${NC}\n"
