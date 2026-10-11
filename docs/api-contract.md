# ĐẶC TẢ GIAO DIỆN LẬP TRÌNH ỨNG DỤNG (API SPECIFICATION & CONTRACT)

> **Học phần:** Cloud Computing – Đợt 1, Năm học 2026–2027  
> **Dự án:** Cổng thanh toán giả lập không máy chủ (`serverless-payment`)  
> **Người phụ trách:** Vũ Minh Đức  
> **Phối hợp & Rà soát:** Nguyễn Nguyên  
> **AWS Region:** `us-east-1` · **Phiên bản:** 1.0 (Design)  

## Quy ước API

- HTTPS; HTTP API ở `us-east-1`; base URL chỉ được biết sau khi triển khai.
- `Content-Type: application/json`; tiền VND lưu số nguyên; không nhận số thực, chuỗi, boolean làm `amount`.
- Mỗi `POST /transfers` yêu cầu `Authorization: Bearer <JWT>` và `Idempotency-Key` (khuyến nghị UUID v4 của client).
- `userId` lấy từ `sub` của JWT, không lấy từ body do client cung cấp.

## POST /token — cấp JWT demo

Không yêu cầu JWT sẵn, nhưng **bắt buộc kiểm tra mã demo bí mật** và allowlist user trước khi cấp token; không được cấp JWT tùy ý theo userId client khai.

Request minh họa:

```json
{"userId":"user-a","demoCode":"spg-demo-code-2026"}
```

Response 200:

```json
{
  "accessToken":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyLWEiLCJpc3MiOiJzZXJ2ZXJsZXNzLXBheW1lbnQtZGVtbyIsImF1ZCI6InBheW1lbnQtYXBpIiwiZXhwIjoxNzkxNjc3NzAwLCJpYXQiOjE3OTE2NzY4MDB9.sample_signature_hash",
  "tokenType":"Bearer",
  "expiresIn":900
}
```

Lỗi: `400 INVALID_REQUEST`, `401 INVALID_CREDENTIALS`, `429 TOO_MANY_REQUESTS` nếu áp dụng throttling.

## POST /transfers — chuyển tiền

Request minh họa:

```http
POST /transfers
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Idempotency-Key: 4c7d3e65-1f10-47c7-b6f3-e99c91ba00d1
Content-Type: application/json
```

```json
{"fromWalletId":"W001","toWalletId":"W002","amount":30000}
```

Response 201 (thành công lần đầu):

```json
{
  "transactionId":"txn-example-001",
  "fromWalletId":"W001",
  "toWalletId":"W002",
  "amount":30000,
  "currency":"VND",
  "status":"SUCCESS",
  "replayed":false,
  "createdAt":"2026-10-11T00:00:00Z"
}
```

Response 200 (gửi lại cùng key, cùng dữ liệu): cùng `transactionId`, `replayed=true`, không cập nhật lại số dư.

Response 409 (cùng key nhưng payload khác):

```json
{"error":{"code":"IDEMPOTENCY_KEY_CONFLICT","message":"Key already used for another request."}}
```

Response 409 (không đủ tiền):

```json
{"error":{"code":"INSUFFICIENT_FUNDS","message":"Insufficient balance."}}
```

## Danh mục mã lỗi và trạng thái HTTP (HTTP Status Codes)

| HTTP | Ý nghĩa |
|---|---|
| 200 | Replay của giao dịch thành công (cùng key, cùng payload) |
| 201 | Giao dịch thực thi thành công lần đầu |
| 400 | Body, amount, walletIds hoặc Idempotency-Key không hợp lệ |
| 401 | Thiếu Authorization identity source |
| 403 | JWT bị Authorizer từ chối (`isAuthorized=false`) hoặc không phải chủ ví nguồn |
| 404 | Ví nguồn hoặc ví đích không tồn tại |
| 409 | Không đủ số dư / ví bị khóa / idempotency key xung đột |
| 429 | Vượt quá hạn mức lưu lượng (Rate Limiting / Throttling từ API Gateway) |
| 503 | Xung đột DynamoDB tạm thời sau khi đã retry có giới hạn |
| 500 | Lỗi máy chủ không mong đợi (Tự động chuyển tiếp vào Amazon SQS DLQ) |

Với HTTP API Lambda Authorizer `REQUEST` trả simple response `isAuthorized=false`, API Gateway tự động trả **403 Forbidden**; khi thiếu identity source, API Gateway trả **401 Unauthorized**.

## GET /transactions/{id} — Endpoint mở rộng

Endpoint tra cứu lịch sử giao dịch theo `transactionId`. Chức năng này được định nghĩa ở dạng mở rộng và chỉ được kích hoạt sau khi nhóm hoàn tất thiết kế Global Secondary Index (GSI) `transactionId-index` trên DynamoDB ở các tuần tiếp theo.

## Cơ chế xử lý Idempotency & Ràng buộc giao dịch

- **Định dạng Idempotency-Key:** Bắt buộc gửi qua HTTP Header, định dạng chuẩn UUID v4 (36 ký tự).
- **Ràng buộc số tiền (`amount`):** Phải là số nguyên dương VND (`amount > 0`). Trong Python Lambda, kiểm tra chặt chẽ `isinstance(amount, int) and not isinstance(amount, bool)` để ngăn chặn việc ép kiểu boolean.
- **Ràng buộc tài khoản ví:** `fromWalletId` và `toWalletId` phải là chuỗi hợp lệ, không rỗng và khác nhau.
- **Sinh mã giao dịch (`transactionId`):** Được sinh ngẫu nhiên từ server (UUID v4), bảo đảm tính duy nhất tuyệt đối.
- **Phạm vi bảo vệ Idempotency:** Trong phiên bản MVP, bảng `Transactions` chỉ lưu trữ các giao dịch đã commit thành công (`SUCCESS`). Nếu giao dịch bị hủy do thiếu số dư hoặc sai thông tin ví, khóa Idempotency không bị chiếm giữ, cho phép client gửi lại yêu cầu cùng key sau khi đã khắc phục điều kiện. Khi giao dịch đã hoàn tất, việc gửi lại cùng key và payload sẽ trả về kết quả cũ kèm `replayed: true` (HTTP 200 OK), còn gửi khác payload sẽ bị từ chối với lỗi `409 IDEMPOTENCY_KEY_CONFLICT`.

## Cơ chế Kiểm soát lưu lượng (Rate Limiting & Throttling)

Nhằm bảo vệ hệ thống khỏi tấn công từ chối dịch vụ (DoS) và cạn kiệt tài nguyên xử lý trên Learner Lab, API Gateway được cấu hình chính sách kiểm soát lưu lượng tại tầng Ingress:

- **Hạn mức Route `/token`:** Rate Limit = 2 RPS, Burst Limit = 5 requests (ngăn chặn dò quét mã demo).
- **Hạn mức Route `/transfers`:** Rate Limit = 10 RPS, Burst Limit = 20 requests.
- **Phản hồi lỗi 429:** Khi vượt ngưỡng, API Gateway tự động trả về:
  ```json
  {
    "message": "Too Many Requests"
  }
  ```
  Kèm theo HTTP Response Header `Retry-After: <số giây>` yêu cầu client tạm dừng trước khi thử lại. Lỗi này được chặn trực tiếp tại API Gateway, không phát sinh chi phí thực thi Lambda.

## Cơ chế Xử lý sự cố ngoại lệ & Hàng đợi chết (Dead Letter Queue - DLQ)

- Khi Transfer Lambda gặp sự cố ngoại lệ chưa xử lý (unhandled runtime exception, function timeout, hoặc lỗi kết nối DynamoDB nghiêm trọng dẫn tới mã lỗi 500), payload của request lỗi được tự động đẩy vào **Amazon SQS Dead Letter Queue (`serverless-payment-dlq`)**.
- Bản tin trong DLQ lưu trữ đầy đủ thông tin: `timestamp`, `requestId`, `requestPayload`, và mã lỗi ngoại lệ, hỗ trợ quản trị viên đối soát thủ công và khôi phục trạng thái ví mà không làm thất thoát dữ liệu giao dịch của người dùng.
