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
{"userId":"user-a","demoCode":"PLACEHOLDER_NOT_A_REAL_CODE"}
```

Response 200:

```json
{"accessToken":"PLACEHOLDER_SIGNED_JWT","tokenType":"Bearer","expiresIn":900}
```

Lỗi: `400 INVALID_REQUEST`, `401 INVALID_CREDENTIALS`, `429 TOO_MANY_REQUESTS` nếu áp dụng throttling.

## POST /transfers — chuyển tiền

Request minh họa:

```http
POST /transfers
Authorization: Bearer PLACEHOLDER_JWT
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

## Các HTTP status cần chốt

| HTTP | Ý nghĩa |
|---|---|
| 200 | Replay của giao dịch thành công |
| 201 | Giao dịch thực thi thành công lần đầu |
| 400 | Body, amount, walletIds hoặc Idempotency-Key không hợp lệ |
| 401 | Thiếu Authorization identity source |
| 403 | JWT bị Authorizer từ chối (`isAuthorized=false`) hoặc không phải chủ ví nguồn |
| 404 | Ví nguồn hoặc ví đích không tồn tại |
| 409 | Không đủ số dư / ví bị khóa / idempotency key xung đột |
| 429 | Quá giới hạn gọi API (nếu cấu hình) |
| 503 | Xung đột DynamoDB tạm thời sau khi đã retry có giới hạn |
| 500 | Lỗi máy chủ không mong đợi |

Với HTTP API Lambda Authorizer `REQUEST` trả simple response `isAuthorized=false`, API Gateway thường trả **403 Forbidden**; khi thiếu identity source, API Gateway trả **401 Unauthorized**. Không giả định mọi JWT hết hạn đều trả 401 nếu giữ cấu hình simple responses.

## GET /transactions/{id} — tùy chọn

Chỉ triển khai nếu chốt cơ chế tra cứu theo transactionId: GSI `transactionId-index` hoặc item mapping. GSI eventual consistency; phải kiểm tra quyền đọc lịch sử. **Không đặt endpoint vào phạm vi MVP mặc định** khi chưa thiết kế chỉ mục.

## Checklist A2

- [ ] Chốt route `/token`, `/transfers`, và route tra cứu nếu có.
- [ ] Chốt header, schema request, schema response và trạng thái HTTP.
- [ ] Đảm bảo A1, A2, A3 cùng chính sách request trùng.
- [ ] Thống nhất contract giữa Vũ Minh Đức và Nguyễn Nguyên trước Tuần 2.

## Quyết định thống nhất về request thất bại

MVP chỉ lưu transaction `SUCCESS`: nếu `POST /transfers` không commit vì thiếu tiền/ví lỗi/quyền lỗi, không có transaction thành công và không chiếm key. Một client có thể gửi lại cùng `Idempotency-Key` sau khi điều kiện thay đổi. Khi **đã commit** thì gửi lại cùng key + cùng payload luôn phải replay 200; key + payload khác phải trả 409.

### Header và validation

- `Idempotency-Key`: bắt buộc, UUID v4 ở dạng canonical (ví dụ `d43f24a0-3c7a-49e2-941e-1c99e8752058`); tối đa 36 ký tự.
- `amount`: integer JSON và > 0; Python cần loại cả `bool` vì `bool` kế thừa `int`.
- Hai mã ví phải là chuỗi không rỗng, không trùng nhau.
- `transactionId` sinh từ server, không tin giá trị do client cung cấp.
- Để giảm rủi ro lộ thông tin, lỗi 404/403 cho ví không sở hữu phải theo quy tắc không tiết lộ dữ liệu ngoài quyền; nhóm thống nhất policy trước khi code.

**Nguồn mở rộng:** file `design/openapi.yaml` cho đặc tả máy đọc được và `examples/api-examples.md` cho lệnh curl ví dụ.
