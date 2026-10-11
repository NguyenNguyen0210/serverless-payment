# HƯỚNG DẪN KIỂM THỬ API BẰNG CURL (API TESTING EXAMPLES)

> **Dự án:** Cổng thanh toán giả lập không máy chủ (`serverless-payment`)  
> **Mục đích:** Cung cấp bộ lệnh cURL mẫu để kiểm thử nhanh các luồng API của hệ thống từ terminal máy trạm hoặc AWS CloudShell.  

---

## 1. Thiết lập biến môi trường kiểm thử

Trước khi thực thi các lệnh gọi API, thiết lập các biến môi trường cần thiết trong terminal của bạn:

```bash
# Thay thế URL bên dưới bằng Invoke URL của API Gateway sau khi triển khai
export API_URL="https://abcdef1234.execute-api.us-east-1.amazonaws.com"

# Mã truy cập demo đã cấu hình trong AWS Secrets Manager
export DEMO_CODE="spg-demo-code-2026"
```

---

## 2. Bước 1: Yêu cầu cấp token JWT (`POST /token`)

Gửi yêu cầu cấp token thử nghiệm cho tài khoản `user-a`:

```bash
curl -s -X POST "$API_URL/token" \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "user-a",
    "demoCode": "'"$DEMO_CODE"'"
  }' | jq .
```

**Phản hồi thành công (HTTP 200 OK):**

```json
{
  "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "tokenType": "Bearer",
  "expiresIn": 900
}
```

Lưu token nhận được vào biến môi trường để sử dụng cho các yêu cầu tiếp theo:

```bash
export JWT_TOKEN="<DÁN_ACCESS_TOKEN_VÀO_ĐÂY>"
```

---

## 3. Bước 2: Thực hiện giao dịch chuyển tiền (`POST /transfers`)

Chuyển 30.000 VND từ ví `W001` (thuộc sở hữu của `user-a`) sang ví `W002` (thuộc sở hữu của `user-b`):

```bash
export IDEMPOTENCY_KEY="4c7d3e65-1f10-47c7-b6f3-e99c91ba00d1"

curl -s -X POST "$API_URL/transfers" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Idempotency-Key: $IDEMPOTENCY_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "fromWalletId": "W001",
    "toWalletId": "W002",
    "amount": 30000
  }' | jq .
```

**Phản hồi thành công lần đầu (HTTP 201 Created):**

```json
{
  "transactionId": "txn-8f4b63a2-09c1-42e7-a9a3-f027e02b11cd",
  "fromWalletId": "W001",
  "toWalletId": "W002",
  "amount": 30000,
  "currency": "VND",
  "status": "SUCCESS",
  "replayed": false,
  "createdAt": "2026-10-11T10:15:30Z"
}
```

---

## 4. Bước 3: Kiểm tra cơ chế chống lặp (Idempotent Replay)

Thực hiện gửi lại chính xác yêu cầu trên với cùng `Idempotency-Key`:

```bash
curl -s -X POST "$API_URL/transfers" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Idempotency-Key: $IDEMPOTENCY_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "fromWalletId": "W001",
    "toWalletId": "W002",
    "amount": 30000
  }' | jq .
```

**Phản hồi kiểm tra (HTTP 200 OK):**
- Hệ thống trả về `replayed: true` kèm đúng `transactionId` ban đầu.
- Số dư của hai ví không bị trừ thêm lần nào.

```json
{
  "transactionId": "txn-8f4b63a2-09c1-42e7-a9a3-f027e02b11cd",
  "fromWalletId": "W001",
  "toWalletId": "W002",
  "amount": 30000,
  "currency": "VND",
  "status": "SUCCESS",
  "replayed": true,
  "createdAt": "2026-10-11T10:15:30Z"
}
```

---

## 5. Bước 4: Kiểm tra phát hiện xung đột khóa (Payload Conflict)

Tái sử dụng cùng `Idempotency-Key` nhưng sửa đổi số tiền thành 50.000 VND:

```bash
curl -s -i -X POST "$API_URL/transfers" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Idempotency-Key: $IDEMPOTENCY_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "fromWalletId": "W001",
    "toWalletId": "W002",
    "amount": 50000
  }'
```

**Phản hồi kỳ vọng (HTTP 409 Conflict):**

```json
{
  "error": {
    "code": "IDEMPOTENCY_KEY_CONFLICT",
    "message": "Idempotency key has already been used with different request parameters."
  }
}
```

---

## 6. Bước 5: Kiểm tra lớp bảo vệ xác thực (Lambda Authorizer)

Gửi yêu cầu khi không truyền header `Authorization` hoặc truyền token không hợp lệ:

```bash
# Không có Authorization header -> HTTP 401
curl -s -i -X POST "$API_URL/transfers" \
  -H "Idempotency-Key: 7b8c9d0e-1a2b-3c4d-5e6f-7a8b9c0d1e2f" \
  -H "Content-Type: application/json" \
  -d '{"fromWalletId":"W001","toWalletId":"W002","amount":10000}'

# Token sai chữ ký HMAC -> HTTP 403 Forbidden
curl -s -i -X POST "$API_URL/transfers" \
  -H "Authorization: Bearer invalid.token.signature" \
  -H "Idempotency-Key: 7b8c9d0e-1a2b-3c4d-5e6f-7a8b9c0d1e2f" \
  -H "Content-Type: application/json" \
  -d '{"fromWalletId":"W001","toWalletId":"W002","amount":10000}'
```

---

## 7. Đối soát dữ liệu trên DynamoDB qua AWS CLI

Sau khi chạy các lệnh kiểm thử, kiểm tra trực tiếp trạng thái số dư và lịch sử giao dịch:

```bash
# Kiểm tra số dư ví W001
aws dynamodb get-item \
  --table-name Wallets \
  --key '{"walletId": {"S": "W001"}}' \
  --consistent-read \
  --region us-east-1

# Tra cứu bản ghi Idempotency trong bảng Transactions
aws dynamodb get-item \
  --table-name Transactions \
  --key '{
    "userId": {"S": "user-a"},
    "idempotencyKey": {"S": "'"$IDEMPOTENCY_KEY"'"}
  }' \
  --consistent-read \
  --region us-east-1
```

---

## 8. Bước 6: Kiểm tra cơ chế Rate Limiting (HTTP 429)

Gửi liên tiếp một đợt request dồn dập (burst > 20 requests) để kích hoạt cơ chế Throttling trên API Gateway:

```bash
# Bắn 25 requests liên tục
for i in {1..25}; do
  curl -s -o /dev/null -w "%{http_code}\n" -X POST "$API_URL/transfers" \
    -H "Authorization: Bearer $JWT_TOKEN" \
    -H "Idempotency-Key: $(uuidgen)" \
    -H "Content-Type: application/json" \
    -d '{"fromWalletId":"W001","toWalletId":"W002","amount":1000}'
done
```

**Kết quả quan sát:**
- Khoảng 10–20 requests đầu tiên được tiếp nhận xử lý (`201` hoặc `409` tùy số dư).
- Các requests vượt ngưỡng Rate Limit bị API Gateway từ chối ngay lập tức với mã HTTP **`429`** (kèm header `Retry-After`), không kích hoạt hàm Lambda backend.

---

## 9. Bước 7: Đối soát hàng đợi chết (Amazon SQS DLQ) qua AWS CLI

Kiểm tra số lượng thông điệp lỗi được chuyển tiếp vào SQS DLQ khi hệ thống phát sinh ngoại lệ không mong đợi:

```bash
# Lấy URL của Dead Letter Queue
QUEUE_URL=$(aws sqs get-queue-url --queue-name serverless-payment-dlq --query 'QueueUrl' --output text --region us-east-1)

# Kiểm tra số lượng bản tin lỗi trong DLQ
aws sqs get-queue-attributes \
  --queue-url "$QUEUE_URL" \
  --attribute-names ApproximateNumberOfMessages ApproximateNumberOfMessagesNotVisible \
  --region us-east-1

# Đọc thử thông điệp lỗi trong DLQ để đối soát (nếu có)
aws sqs receive-message \
  --queue-url "$QUEUE_URL" \
  --max-number-of-messages 1 \
  --region us-east-1
```
