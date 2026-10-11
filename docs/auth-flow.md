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

## 3. Quản lý khóa bí mật trên AWS Secrets Manager

Secret định danh: `serverless-payment/jwt-secret` tại Region `us-east-1`. Cấu trúc JSON lưu trữ:

```json
{
  "jwtSigningKey": "c3VwZXItc2VjcmV0LWtleS1mb3Itc2VydmVybGVzcy1wYXltZW50LTIwMjY=",
  "demoAccessCode": "spg-demo-code-2026"
}
```

Khóa bí mật ký token và mã demo được quản lý tập trung trên AWS Secrets Manager. Mã nguồn Lambda truy xuất trực tiếp qua AWS SDK (`boto3`) sử dụng quyền của `LabRole`. Không lưu trữ chuỗi bí mật trong mã nguồn hoặc đẩy lên Git repository.

## 4. Cơ chế cấp token demo cho kiểm thử

1. Client gửi yêu cầu kèm `userId` và `demoCode` đến endpoint `/token` qua HTTPS.
2. Token Lambda kiểm tra tính hợp lệ: chỉ chấp nhận các tài khoản demo được đăng ký trước (`user-a`, `user-b`).
3. Truy xuất `demoAccessCode` từ Secrets Manager và so sánh bằng thuật toán an toàn `hmac.compare_digest` để chống tấn công phân tích thời gian (timing attack).
4. Nếu hợp lệ: sinh token JWT với các claims chuẩn (`sub`, `iss`, `aud`, `iat`, `exp`, `jti`) và ký bằng thuật toán HS256.
5. Nếu không hợp lệ: trả về lỗi `401 INVALID_CREDENTIALS`. Client không thể tự tạo token với các claim tùy ý.
6. **Lưu ý kiến trúc:** Cơ chế mã demo dùng chung được thiết kế riêng cho mục đích thử nghiệm và chấm điểm đồ án học phần; trong môi trường sản xuất thực tế sẽ thay thế bằng luồng xác thực người dùng chuẩn (OAuth2 / OIDC).

## 5. Cấu hình Lambda Authorizer trên HTTP API

| Tham số cấu hình | Giá trị thiết lập | Mục đích kỹ thuật |
|---|---|---|
| **Authorizer Type** | `REQUEST` | Đọc toàn bộ request context bao gồm HTTP headers |
| **Payload Format** | `2.0` | Tối ưu hóa định dạng cho HTTP API v2 |
| **Identity Source** | `$request.header.Authorization` | API Gateway tự động kích hoạt khi có header |
| **Simple Responses** | Enabled | Trả về định dạng gọn nhẹ `{"isAuthorized": true/false}` |
| **Authorizer Caching** | Disabled (TTL = 0) | Tránh rủi ro cache token hết hạn trong lúc kiểm thử |
| **Context Payload** | `context.userId = sub` | Truyền an toàn định danh người dùng sang backend Lambda |

Phản hồi mẫu khi ủy quyền thành công:

```json
{
  "isAuthorized": true,
  "context": {
    "userId": "user-a"
  }
}
```

Backend Lambda (Transfer Lambda) tiếp nhận định danh người dùng đã xác minh qua đường dẫn `event["requestContext"]["authorizer"]["lambda"]["userId"]`. Hệ thống tuyệt đối không tin cậy `userId` do client tự gửi trong body.

## 6. Ma trận xử lý lỗi xác thực và phân quyền

| Kịch bản kiểm thử | Hành vi hệ thống | HTTP Status Code |
|---|---|---|
| Không gửi header `Authorization` | API Gateway từ chối ngay lập tức | `401 Unauthorized` |
| Token hết hạn (`exp` quá hạn) | Lambda Authorizer xác thực thất bại | `403 Forbidden` |
| Chữ ký HMAC không khớp (bị chỉnh sửa) | Lambda Authorizer phát hiện chữ ký lỗi | `403 Forbidden` |
| Token sai Audience hoặc Issuer | Lambda Authorizer từ chối ủy quyền | `403 Forbidden` |
| Token hợp lệ nhưng chuyển từ ví người khác | Transfer Lambda kiểm tra `ownerId != userId` | `403 Forbidden` |
| Token hợp lệ, ví nguồn chính chủ | Chuyển tiếp vào giao dịch DynamoDB | Cho phép thực thi |
