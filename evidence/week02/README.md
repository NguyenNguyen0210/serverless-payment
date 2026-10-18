# DANH MỤC MINH CHỨNG KỸ THUẬT TUẦN 2 (EVIDENCE CATALOG - WEEK 2)

> **Học phần:** Cloud Computing (Điện toán đám mây) – Đợt 1, Năm học 2026–2027  
> **Dự án:** Cổng thanh toán giả lập không máy chủ (`serverless-payment`)  
> **Nhóm thực hiện:** Serverless (02 thành viên: Vũ Minh Đức & Nguyễn Nguyên)  
> **Nền tảng:** AWS Academy Learner Lab (Vocareum) · **Region:** `us-east-1`
> **Tài khoản minh chứng:** Nguyễn Nguyên `930162821234` · Vũ Minh Đức `892973274103`
> **Tuần báo cáo:** Tuần 2 (12/10/2026 – 18/10/2026)  

---

## 1. Cơ cấu phân chia minh chứng theo thành viên

Để bảo đảm tính minh bạch và ghi nhận chính xác khối lượng đóng góp cá nhân (tối thiểu 8 giờ/thành viên/tuần), thư mục minh chứng Tuần 2 được phân tách thành 2 thư mục độc lập:

```
evidence/week02/
├── README.md               # Danh mục minh chứng tổng hợp Tuần 2 (tệp hiện tại)
├── nguyen/                 # Minh chứng của Nguyễn Nguyên (16 ảnh)
│   ├── README.md
│   └── B2-01 -> B2-16...   # Toàn bộ ảnh chụp màn hình AWS Console & CLI
└── duc/                    # Minh chứng của Vũ Minh Đức (24 ảnh)
    ├── README.md
    └── A2-01 -> A2-24...   # Ảnh triển khai, kiểm thử Lambda và API end-to-end
```

---

## 2. Danh mục minh chứng chi tiết của từng thành viên

### 📁 Thư mục [`nguyen/`](nguyen/README.md) – Nguyễn Nguyên (16 ảnh minh chứng)
Đã triển khai, cấu hình và kiểm thử thành công trên AWS Console / CLI:
- **`B2-01`:** [`B2-01-secrets-manager.png`](nguyen/B2-01-secrets-manager.png) – Khởi tạo secret `serverless-payment/jwt-secret` trên Secrets Manager.
- **`B2-02`:** [`B2-02-pyjwt-layer.png`](nguyen/B2-02-pyjwt-layer.png) – Đóng gói và tạo Lambda Layer `pyjwt-layer`.
- **`B2-03`:** [`B2-03-token-lambda.png`](nguyen/B2-03-token-lambda.png) – Cấu hình hàm `serverless-payment-token` trên Lambda.
- **`B2-04`:** [`B2-04-token-test-success.png`](nguyen/B2-04-token-test-success.png) – Test event cấp token JWT thành công (HTTP 200).
- **`B2-05`:** [`B2-05-token-test-invalid.png`](nguyen/B2-05-token-test-invalid.png) – Test event từ chối demo code sai (HTTP 401).
- **`B2-06`:** [`B2-06-dynamodb-table.png`](nguyen/B2-06-dynamodb-table.png) – Khởi tạo bảng DynamoDB `serverless-payment` On-Demand.
- **`B2-07`:** [`B2-07-wallet-seed.png`](nguyen/B2-07-wallet-seed.png) – Chạy script `seed_wallets.py` nạp số dư cho 4 ví mẫu.
- **`B2-08`:** [`B2-08-authorizer-success.png`](nguyen/B2-08-authorizer-success.png) – Test Authorizer xác thực token hợp lệ (`isAuthorized: true`).
- **`B2-09`:** [`B2-09-authorizer-denied.png`](nguyen/B2-09-authorizer-denied.png) – Test Authorizer từ chối token sai (`isAuthorized: false`).
- **`B2-10`:** [`B2-10-transfer-lambda.png`](nguyen/B2-10-transfer-lambda.png) – Cấu hình hàm `serverless-payment-transfer` trên Lambda.
- **`B2-11`:** [`B2-11-transfer-success.png`](nguyen/B2-11-transfer-success.png) – Test chuyển tiền thành công 30.000 VND qua DynamoDB Transaction (HTTP 201).
- **`B2-12`:** [`B2-12-transfer-insufficient-funds.png`](nguyen/B2-12-transfer-insufficient-funds.png) – Test chuyển tiền thất bại do thiếu số dư (HTTP 409).
- **`B2-13`:** [`B2-13-api-routes.png`](nguyen/B2-13-api-routes.png) – Cấu hình các route `POST /token` và `POST /transfers` trên HTTP API.
- **`B2-14`:** [`B2-14-api-authorizer.png`](nguyen/B2-14-api-authorizer.png) – Tích hợp Lambda Authorizer bảo vệ route `POST /transfers`.
- **`B2-15`:** [`B2-15-route-throttling.png`](nguyen/B2-15-route-throttling.png) – Cấu hình Route Throttling (Rate Limit 2 RPS & 10 RPS).
- **`B2-16`:** [`B2-16-sqs-dlq.png`](nguyen/B2-16-sqs-dlq.png) – Khởi tạo hàng đợi Amazon SQS Dead Letter Queue `serverless-payment-dlq`.

### 📁 Thư mục [`duc/`](duc/README.md) – Vũ Minh Đức (24 ảnh minh chứng)
- **`A2-01` đến `A2-05`:** Xác nhận môi trường Learner Lab, Secrets Manager, PyJWT Layer và cấu hình Token Lambda.
- **`A2-06` đến `A2-09`:** Kiểm thử cấp token và Lambda Authorizer với cả trường hợp thành công lẫn bị từ chối.
- **`A2-10` đến `A2-11`:** Xác nhận bảng DynamoDB Single-Table và dữ liệu 4 ví mẫu.
- **`A2-12` đến `A2-16`:** Kiểm thử nghiệp vụ chuyển tiền, thiếu số dư, idempotent replay, xung đột key và sai chủ ví.
- **`A2-17` đến `A2-18`:** Kiểm thử end-to-end hai API `POST /token` và `POST /transfers` bằng Postman.
- **`A2-19` đến `A2-22`:** Xác nhận API Gateway routes, Lambda Authorizer, tích hợp transfer và cấu hình route throttling.
- **`A2-23` đến `A2-24`:** Đối soát CloudWatch Logs và hàng đợi SQS `serverless-payment-dlq`.

---

## 3. Tiêu chuẩn tính xác thực & Liêm chính học thuật
- Toàn bộ ảnh minh chứng được chụp trực tiếp từ các phiên AWS Academy Learner Lab của từng thành viên, có hiển thị Account ID tương ứng và Region `us-east-1`.
- Không chỉnh sửa số liệu hoặc can thiệp thông tin thời gian phiên thực hành.
