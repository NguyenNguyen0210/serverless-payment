# ĐẶC TẢ HỢP ĐỒNG API & HƯỚNG DẪN KIỂM THỬ (API CONTRACT & TESTING GUIDE)

> **Học phần:** Cloud Computing – Đợt 1, Năm học 2026–2027  
> **Dự án:** Cổng thanh toán giả lập không máy chủ (`serverless-payment`)  
> **Người thực hiện:** Vũ Minh Đức & Nguyễn Nguyên  
> **AWS Region:** `us-east-1` · **Nền tảng:** Amazon API Gateway HTTP API v2  
> **Phiên bản:** 2.0 (Toàn bộ 05 Endpoints & Tích hợp cURL mẫu)  

---

## 1. Quy ước chung của hệ thống API

- **Giao thức:** HTTPS qua Amazon API Gateway HTTP API v2 (us-east-1).
- **Định dạng dữ liệu:** `Content-Type: application/json; charset=utf-8`.
- **Đơn vị tiền tệ:** `VND`, lưu trữ dưới dạng **số nguyên dương** (`integer`). Tuyệt đối từ chối `float`, `boolean` hoặc `string`.
- **Bảo mật danh tính (Zero-Trust):** Các endpoint được bảo vệ đều phải gửi header `Authorization: Bearer <JWT>`. Định danh người dùng luôn được trích xuất an toàn từ `context.userId` (từ claim `sub` do Lambda Authorizer giải mã), **không bao giờ tin cậy `userId` do client tự khai trong body**.

```bash
# Thiết lập biến môi trường để chạy thử nghiệm các lệnh cURL
export API_URL="https://abcdef1234.execute-api.us-east-1.amazonaws.com"
export DEMO_CODE="spg-demo-code-2026"
```

---

## 2. Chi tiết 05 Endpoints

### 2.1. Endpoint 1: Cấp JWT thử nghiệm (`POST /auth/token`)
- **Phân quyền:** Public (Không cần JWT, kiểm tra bảo mật phía server).
- **Cơ chế an toàn:** So khớp `demoCode` với giá trị bí mật trong AWS Secrets Manager bằng `hmac.compare_digest` chống timing attack; kiểm tra allowlist (`user-a`, `user-b`).
- **Throttling:** 2 RPS, Burst: 5 (ngăn chặn brute-force).

#### Request:
```http
POST /auth/token HTTP/1.1
Content-Type: application/json

{
  "userId": "user-a",
  "demoCode": "spg-demo-code-2026"
}
```

#### Response thành công (`HTTP 200 OK`):
```json
{
  "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyLWEiLCJpc3MiOiJzZXJ2ZXJsZXNzLXBheW1lbnQtZGVtbyIsImF1ZCI6InBheW1lbnQtYXBpIiwiZXhwIjoxNzkxNjc3NzAwLCJpYXQiOjE3OTE2NzY4MDB9.signature",
  "tokenType": "Bearer",
  "expiresIn": 900
}
```

#### Lệnh cURL thực thi:
```bash
curl -s -X POST "$API_URL/auth/token" \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "user-a",
    "demoCode": "spg-demo-code-2026"
  }' | jq .

# Lưu token nhận được vào biến môi trường
export JWT_TOKEN="<DÁN_ACCESS_TOKEN_VÀO_ĐÂY>"
```

---

### 2.2. Endpoint 2: Chuyển tiền nguyên tử (`POST /transfers`)
- **Phân quyền:** Protected (Bắt buộc Lambda Authorizer).
- **Header bắt buộc:** `Authorization: Bearer <token>`, `Idempotency-Key: <uuid-v4>`.
- **Cơ chế an toàn:** Kiểm tra số dư, trừ tiền ví nguồn, cộng tiền ví đích, ghi nhật ký giao dịch và khóa chống lặp trong một lệnh `TransactWriteItems` duy nhất (4 actions nguyên tử).
- **Throttling:** 10 RPS, Burst: 20.

#### Request:
```http
POST /transfers HTTP/1.1
Authorization: Bearer <JWT_TOKEN>
Idempotency-Key: 4c7d3e65-1f10-47c7-b6f3-e99c91ba00d1
Content-Type: application/json

{
  "fromWalletId": "W001",
  "toWalletId": "W002",
  "amount": 30000
}
```

#### Response lần đầu thành công (`HTTP 201 Created`):
```json
{
  "transactionId": "b1a7d65c-3f24-4f91-88bc-4a0b2d561234",
  "fromWalletId": "W001",
  "toWalletId": "W002",
  "amount": 30000,
  "currency": "VND",
  "status": "SUCCESS",
  "replayed": false,
  "createdAt": "2026-10-22T03:36:22.123456Z"
}
```

#### Response khi gửi lại cùng `Idempotency-Key` (`HTTP 200 OK` - Idempotent Replay):
```json
{
  "transactionId": "b1a7d65c-3f24-4f91-88bc-4a0b2d561234",
  "fromWalletId": "W001",
  "toWalletId": "W002",
  "amount": 30000,
  "currency": "VND",
  "status": "SUCCESS",
  "replayed": true,
  "createdAt": "2026-10-22T03:36:22.123456Z"
}
```

#### Lệnh cURL thực thi:
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

---

### 2.3. Endpoint 3: Tra cứu thông tin & Số dư ví (`GET /wallets/{walletId}`)
- **Phân quyền:** Protected (Bắt buộc Lambda Authorizer).
- **Kiểm soát quyền truy cập:** Chỉ chủ sở hữu ví (`ownerId == context.userId`) mới được phép xem thông tin ví của mình. Nếu người khác truy cập sẽ bị từ chối với mã lỗi `403 WALLET_FORBIDDEN`.

#### Request:
```http
GET /wallets/W001 HTTP/1.1
Authorization: Bearer <JWT_TOKEN>
```

#### Response thành công (`HTTP 200 OK`):
```json
{
  "walletId": "W001",
  "ownerId": "user-a",
  "balance": 70000,
  "currency": "VND",
  "status": "ACTIVE",
  "createdAt": "2026-10-22T00:00:00Z",
  "updatedAt": "2026-10-22T03:36:22Z"
}
```

#### Lệnh cURL thực thi:
```bash
# Tra cứu ví chính chủ (HTTP 200)
curl -s -X GET "$API_URL/wallets/W001" \
  -H "Authorization: Bearer $JWT_TOKEN" | jq .

# Thử nghiệm xem ví người khác (HTTP 403 Forbidden)
curl -s -X GET "$API_URL/wallets/W002" \
  -H "Authorization: Bearer $JWT_TOKEN" | jq .
```

---

### 2.4. Endpoint 4: Tra cứu chi tiết giao dịch (`GET /transactions/{transactionId}`)
- **Phân quyền:** Protected (Bắt buộc Lambda Authorizer).
- **Kiểm soát quyền truy cập:** Chỉ các bên tham gia giao dịch (chủ ví nguồn chuyển đi HOẶC chủ ví đích nhận đến) mới có quyền tra cứu. Người ngoài truy cập sẽ bị từ chối với lỗi `403 TRANSACTION_FORBIDDEN`.

#### Request:
```http
GET /transactions/b1a7d65c-3f24-4f91-88bc-4a0b2d561234 HTTP/1.1
Authorization: Bearer <JWT_TOKEN>
```

#### Response thành công (`HTTP 200 OK`):
```json
{
  "transactionId": "b1a7d65c-3f24-4f91-88bc-4a0b2d561234",
  "fromWalletId": "W001",
  "toWalletId": "W002",
  "amount": 30000,
  "currency": "VND",
  "status": "SUCCESS",
  "createdAt": "2026-10-22T03:36:22.123456Z"
}
```

#### Lệnh cURL thực thi:
```bash
export TX_ID="b1a7d65c-3f24-4f91-88bc-4a0b2d561234"

curl -s -X GET "$API_URL/transactions/$TX_ID" \
  -H "Authorization: Bearer $JWT_TOKEN" | jq .
```

---

### 2.5. Endpoint 5: Lịch sử giao dịch ví có phân trang (`GET /wallets/{walletId}/transactions`)
- **Phân quyền:** Protected (Bắt buộc Lambda Authorizer, chỉ chủ ví được xem).
- **Tham số truy vấn (Query Parameters):**
  - `limit`: Số bản ghi tối đa trả về trên mỗi trang (từ 1 đến 50, mặc định: 10).
  - `nextToken`: Chuỗi mã hóa base64URL an toàn chứa con trỏ phân trang thời gian (`timeKey`). Nếu là `null` thì đã ở trang cuối.
- **Cơ chế kỹ thuật:** Truy vấn song song cả 2 GSIs (`FromWalletIndex` và `ToWalletIndex`), gộp và sắp xếp theo `timeKey` giảm dần (mới nhất lên đầu), gắn nhãn rõ ràng:
  - `type`: `"OUTGOING"` (Chuyển tiền đi) hoặc `"INCOMING"` (Nhận tiền đến).
  - `counterpartyWalletId`: Mã ví đối tác trong giao dịch.

#### Request:
```http
GET /wallets/W001/transactions?limit=10 HTTP/1.1
Authorization: Bearer <JWT_TOKEN>
```

#### Response thành công (`HTTP 200 OK`):
```json
{
  "walletId": "W001",
  "items": [
    {
      "transactionId": "b1a7d65c-3f24-4f91-88bc-4a0b2d561234",
      "type": "OUTGOING",
      "counterpartyWalletId": "W002",
      "amount": 30000,
      "currency": "VND",
      "status": "SUCCESS",
      "createdAt": "2026-10-22T03:36:22.123456Z"
    }
  ],
  "nextToken": "eyJ2IjoxLCJ3IjoiVzAwMSIsInUiOiJ1c2VyLWEiLCJiZWZvcmUiOiIyMDI2LTEwLTIyVDAzOjM2OjIyLjEyMzQ1NlojdHgtMTIzIn0"
}
```

#### Lệnh cURL thực thi:
```bash
# Lấy trang đầu tiên
curl -s -X GET "$API_URL/wallets/W001/transactions?limit=10" \
  -H "Authorization: Bearer $JWT_TOKEN" | jq .

# Lấy trang kế tiếp bằng nextToken
curl -s -X GET "$API_URL/wallets/W001/transactions?limit=10&nextToken=<NEXT_TOKEN_TỪ_RESPONSE_TRƯỚC>" \
  -H "Authorization: Bearer $JWT_TOKEN" | jq .
```

---

## 3. Bảng mã trạng thái HTTP & Chuẩn hóa phản hồi lỗi

Mọi phản hồi lỗi từ hệ thống đều tuân thủ cấu trúc JSON thống nhất:
```json
{
  "error": {
    "code": "ERROR_CODE_STRING",
    "message": "Human readable description."
  }
}
```

| HTTP Status | Error Code | Ý nghĩa & Ngữ cảnh phát sinh |
|:---:|---|---|
| **200 OK** | *(Không có)* | Replay giao dịch thành công hoặc truy vấn dữ liệu thành công |
| **201 Created** | *(Không có)* | Giao dịch chuyển tiền lần đầu được ghi nhận thành công |
| **400 Bad Request** | `INVALID_REQUEST`<br>`INVALID_AMOUNT`<br>`INVALID_WALLET`<br>`INVALID_IDEMPOTENCY_KEY`<br>`INVALID_PAGINATION` | Sai cú pháp JSON, số tiền không hợp lệ ($\le 0$ hoặc float/bool), ví nguồn trùng ví đích, key không phải UUID v4, hoặc tham số phân trang sai |
| **401 Unauthorized** | `UNAUTHORIZED`<br>`INVALID_CREDENTIALS` | Thiếu Authorization header hoặc mã `demoCode` không đúng |
| **403 Forbidden** | `WALLET_FORBIDDEN`<br>`TRANSACTION_FORBIDDEN` | JWT bị Authorizer từ chối, caller không sở hữu ví thao tác, hoặc không có quyền xem giao dịch người khác |
| **404 Not Found** | `WALLET_NOT_FOUND`<br>`TRANSACTION_NOT_FOUND`<br>`ROUTE_NOT_FOUND` | Ví nguồn/đích không tồn tại, mã giao dịch không có trong hệ thống, hoặc sai route URL |
| **409 Conflict** | `INSUFFICIENT_FUNDS`<br>`WALLET_INACTIVE`<br>`IDEMPOTENCY_KEY_CONFLICT`<br>`TRANSACTION_CONFLICT` | Số dư không đủ, ví bị khóa (`SUSPENDED`), gửi trùng key nhưng sửa đổi body chuyển tiền, hoặc xung đột transaction đồng thời |
| **429 Too Many Requests** | `TOO_MANY_REQUESTS` | Vượt ngưỡng Rate Limiting tại tầng Ingress của API Gateway |
| **500 Internal Error** | `INTERNAL_ERROR` | Lỗi máy chủ không mong đợi (Tự động gửi cảnh báo vào Amazon SQS DLQ) |
| **503 Service Unavailable**| `TRANSACTION_CONFLICT` | Tranh chấp DynamoDB tạm thời sau 4 lần retry có backoff |
