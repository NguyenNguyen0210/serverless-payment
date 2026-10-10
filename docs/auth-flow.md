# KIẾN TRÚC XÁC THỰC & PHÂN QUYỀN (AUTHENTICATION & AUTHORIZATION FLOW)

> **Học phần:** Cloud Computing – Đợt 1, Năm học 2026–2027  
> **Dự án:** Cổng thanh toán giả lập không máy chủ (`serverless-payment`)  
> **Người phụ trách:** Vũ Minh Đức  
> **Phối hợp & Rà soát:** Nguyễn Nguyên  
> **AWS Region:** `us-east-1` · **Phiên bản:** 1.0 (Design)  

## 1. Luồng xác thực

```text
POST /token (public route)
  → Token Lambda
  → kiểm tra mã demo trong Secrets Manager
  → tạo JWT bằng PyJWT + HS256
  → trả accessToken

POST /transfers (protected route)
  → API Gateway HTTP API
  → Lambda Authorizer REQUEST
  → kiểm tra chữ ký/claims với PyJWT + secret trong Secrets Manager
  → cho phép + context userId, hoặc từ chối
  → Payment Lambda: kiểm tra ownerId ngay trong DynamoDB transaction
```

**Không sử dụng Cognito**, cũng không thay Lambda Authorizer bằng JWT Authorizer tích hợp sẵn của API Gateway.

## 2. JWT payload đề xuất

```json
{
  "sub":"user-a",
  "iss":"serverless-payment-demo",
  "aud":"payment-api",
  "iat":1791676800,
  "exp":1791677700,
  "jti":"example-token-id"
}
```

Đây là payload minh họa, không phải JWT có chữ ký. Thời hạn demo đề xuất 900 giây (15 phút). PyJWT xác minh chữ ký với **thuật toán cố định** `algorithms=["HS256"]`; kiểm tra `exp`, `iss`, `aud`, `sub`, định dạng Bearer và không tin `alg` client tự khai.

## 3. Secrets Manager

Secret đề xuất: `serverless-payment/jwt-demo` tại `us-east-1`:

```json
{
  "jwtSigningKey":"PLACEHOLDER_RANDOM_SECRET",
  "demoAccessCode":"PLACEHOLDER_DEMO_CODE"
}
```

**Chưa tạo secret.** Thay placeholder bằng giá trị ngẫu nhiên được lưu tại Secrets Manager trong Tuần 2. Không commit secret hoặc token lên GitHub. Cấu hình Lambda dùng `LabRole` có sẵn.

## 4. Cấp token demo an toàn ở mức đồ án

1. Client gửi `userId` và `demoCode` đến `/token` qua HTTPS.
2. Token Lambda chỉ cho phép `user-a` hoặc `user-b` (danh sách user demo quản lý phía server).
3. Đọc `demoAccessCode` từ Secrets Manager, so sánh an toàn (`hmac.compare_digest`), không log mã.
4. Nếu hợp lệ: gắn `sub` tương ứng, đặt `iat`, `exp`, `iss`, `aud`, `jti`, ký JWT bằng key bí mật.
5. Nếu không hợp lệ: từ chối `401`. Không để client tự tạo bất kỳ JWT nào thông qua đầu vào tùy ý.
6. Mã demo dùng chung **không phải** mô hình authentication production; báo cáo phải trình bày rõ giới hạn này.

## 5. Lambda Authorizer trên HTTP API

| Cấu hình | Giá trị đề xuất |
|---|---|
| Type | `REQUEST` |
| Payload format | `2.0` |
| Identity source | `$request.header.Authorization` |
| Simple responses | Bật |
| Caching TTL | `0` trong demo |
| Response hợp lệ | `isAuthorized=true`, `context.userId` từ claim `sub` |
| Response không hợp lệ | `isAuthorized=false` (HTTP API simple response thường là 403) |

Response ví dụ:

```json
{"isAuthorized":true,"context":{"userId":"user-a"}}
```

Khi identity source thiếu, API Gateway có thể trả `401` mà không gọi Lambda Authorizer. Payment Lambda phải kiểm tra `ownerId` của ví nguồn trong DynamoDB transaction, không chỉ dựa vào token là hợp lệ.

## 6. Danh sách lỗi xác thực

| Dữ liệu | Kết quả mong đợi |
|---|---|
| Không có Authorization | 401 |
| JWT hết hạn | 403 (simple deny) |
| JWT bị sửa chữ ký | 403 (simple deny) |
| JWT sai iss/aud | 403 (simple deny) |
| JWT hợp lệ, ví không thuộc user | 403 |
| JWT hợp lệ, ví đúng chủ | Cho chạy Payment Lambda |

## 7. Checklist A4 xác thực

- [ ] Chốt claims, TTL token, code demo chỉ tồn tại ở server.
- [ ] Chốt cấu hình Authorizer payload 2.0, REQUEST, cache TTL.
- [ ] Xác nhận cách truyền userId xuống Lambda payment.
- [ ] Chốt danh sách lỗi authn/authz.
- [ ] Phân biệt xác thực JWT và kiểm tra quyền sử dụng ví.

**Tài liệu AWS:** https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-lambda-authorizer.html

## 8. Tích hợp và giới hạn bảo mật ở Tuần 2

- Với HTTP API payload format 2.0 và Lambda proxy, Payment Lambda đọc `userId` đã xác minh qua `event.requestContext.authorizer.lambda.userId` (xem kỹ payload event thật). Không dùng `userId` từ request body.
- Với Lambda Authorizer `REQUEST`, thiết lập identity source `$request.header.Authorization`, TTL cache = 0 trong demo để tránh cache quá hạn token.
- Đảm bảo API Gateway được phép gọi Authorizer Lambda; thiếu quyền có thể dẫn đến HTTP 500.
- `POST /token` công khai về mặt JWT nhưng bắt buộc có mã demo bí mật/allowlist; người có mã demo dùng chung có thể giả mạo người dùng trong danh sách. Đây là giới hạn rõ ràng của mô hình thử nghiệm, **không sử dụng cho môi trường production**.
- Có thể cache secret ngắn hạn trong Lambda để tiết kiệm chi phí; phải xem xét chu kỳ thay đổi/rotation và không cache thông tin xác thực lâu hơn cần thiết.
- CloudWatch ghi requestId, operation, errorCode, latency, transactionId; không ghi `Authorization`, signing key, demo code hoặc nguyên payload nhạy cảm.
