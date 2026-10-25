# DANH MỤC MINH CHỨNG KỸ THUẬT TUẦN 3 (EVIDENCE CATALOG - WEEK 3)

> **Học phần:** Cloud Computing (Điện toán đám mây) – Đợt 1, Năm học 2026–2027  
> **Dự án:** Cổng thanh toán giả lập không máy chủ (`serverless-payment`)  
> **Nhóm thực hiện:** Serverless (02 thành viên: Vũ Minh Đức & Nguyễn Nguyên)  
> **Nền tảng:** AWS Academy Learner Lab (Vocareum) · **Region:** `us-east-1`  
> **Tài khoản minh chứng:** Nguyễn Nguyên `930162821234` · Vũ Minh Đức `892973274103`  
> **Tuần báo cáo:** Tuần 3 (19/10/2026 – 25/10/2026)  

---

## 1. Cơ cấu phân chia minh chứng theo thành viên

Để bảo đảm tính minh bạch và ghi nhận chính xác khối lượng đóng góp cá nhân (tối thiểu 8 giờ/thành viên/tuần), thư mục minh chứng Tuần 3 được tổ chức phân tách theo từng thành viên:

```
evidence/week03/
├── README.md               # Danh mục minh chứng tổng hợp Tuần 3 (tệp hiện tại)
├── nguyen/                 # Minh chứng của Nguyễn Nguyên (22 ảnh)
│   ├── README.md
│   └── B3-01 -> B3-22...   # Toàn bộ ảnh chụp màn hình AWS Console, CLI & Postman
└── duc/                    # Minh chứng của Vũ Minh Đức (20 ảnh)
    ├── README.md
    └── A3-01 -> A3-20...   # Ảnh AWS Console, CloudShell và Postman
```

---

## 2. Danh mục minh chứng chi tiết của từng thành viên

### 📁 Thư mục [`nguyen/`](nguyen/README.md) – Nguyễn Nguyên (22 ảnh minh chứng)

Đã hoàn thành cấu hình, triển khai và kiểm thử thực tế trên AWS Console, CloudShell và Postman:

- **`B3-01`:** [`B3-01-aws-environment.png`](nguyen/B3-01-aws-environment.png) – Xác thực môi trường Learner Lab qua CloudShell (`sts get-caller-identity`).
- **`B3-02`:** [`B3-02-existing-resources.png`](nguyen/B3-02-existing-resources.png) – Rà soát tài nguyên hiện hữu trước khi nâng cấp Tuần 3.
- **`B3-03`:** [`B3-03-dynamodb-wallets-table.png`](nguyen/B3-03-dynamodb-wallets-table.png) – Khởi tạo bảng `serverless-payment-wallets` On-Demand (PK: `walletId`).
- **`B3-04`:** [`B3-04-dynamodb-transactions-table.png`](nguyen/B3-04-dynamodb-transactions-table.png) – Khởi tạo bảng `serverless-payment-transactions` On-Demand (PK: `transactionId`).
- **`B3-05`:** [`B3-05-dynamodb-idempotency-table.png`](nguyen/B3-05-dynamodb-idempotency-table.png) – Khởi tạo bảng `serverless-payment-idempotency` On-Demand (PK: `userId`, SK: `idempotencyKey`).
- **`B3-06`:** [`B3-06-dynamodb-wallet-seed-data.png`](nguyen/B3-06-dynamodb-wallet-seed-data.png) – Nạp thành công dữ liệu khởi tạo 4 ví mẫu (`W001` – `W004`).
- **`B3-07`:** [`B3-07-lambda-transfer-success.png`](nguyen/B3-07-lambda-transfer-success.png) – Test `serverless-payment-transfer` trên Console: giao dịch thành công (HTTP 201).
- **`B3-08`:** [`B3-08-lambda-transfer-idempotent-replay.png`](nguyen/B3-08-lambda-transfer-idempotent-replay.png) – Test chống lặp giao dịch trên Console: idempotent replay an toàn (HTTP 200).
- **`B3-09`:** [`B3-09-lambda-wallet-query-success.png`](nguyen/B3-09-lambda-wallet-query-success.png) – Test `serverless-payment-wallet-query` trên Console: tra cứu số dư ví (HTTP 200).
- **`B3-10`:** [`B3-10-lambda-transaction-query-success.png`](nguyen/B3-10-lambda-transaction-query-success.png) – Test `serverless-payment-transaction-query` trên Console: xem chi tiết giao dịch (HTTP 200).
- **`B3-11`:** [`B3-11-cloudwatch-log-groups.png`](nguyen/B3-11-cloudwatch-log-groups.png) – Cấu hình CloudWatch Log Groups với Retention 1 tuần cho các Lambda handlers.
- **`B3-12`:** [`B3-12-cloudwatch-metrics.png`](nguyen/B3-12-cloudwatch-metrics.png) – Giám sát CloudWatch Metrics chi tiết của `serverless-payment-transfer`.
- **`B3-13`:** [`B3-13-cloudwatch-dashboard.png`](nguyen/B3-13-cloudwatch-dashboard.png) – Thiết lập CloudWatch Dashboard trực quan hóa hiệu năng và lưu lượng hệ thống.
- **`B3-14`:** [`B3-14-cloudwatch-alarms.png`](nguyen/B3-14-cloudwatch-alarms.png) – Thiết lập CloudWatch Alarms giám sát lỗi Lambda (trạng thái OK).
- **`B3-15`:** [`B3-15-sqs-dead-letter-queue.png`](nguyen/B3-15-sqs-dead-letter-queue.png) – Khởi tạo hàng đợi SQS Dead Letter Queue `serverless-payment-dlq`.
- **`B3-16`:** [`B3-16-sqs-manual-test.png`](nguyen/B3-16-sqs-manual-test.png) – Kiểm thử gửi thông điệp vào SQS DLQ qua CloudShell CLI thành công.
- **`B3-17`:** [`B3-17-api-gateway-five-routes.png`](nguyen/B3-17-api-gateway-five-routes.png) – Cấu hình đầy đủ 5 routes trên API Gateway HTTP API v2 kèm Lambda Authorizer.
- **`B3-18`:** [`B3-18-api-token-success.png`](nguyen/B3-18-api-token-success.png) – Test Postman: `POST /auth/token` cấp JWT Access Token thành công (HTTP 200).
- **`B3-19`:** [`B3-19-api-transfer-success.png`](nguyen/B3-19-api-transfer-success.png) – Test Postman: `POST /transfers` chuyển tiền thành công 10.000 VND (HTTP 201).
- **`B3-20`:** [`B3-20-api-idempotency-replay.png`](nguyen/B3-20-api-idempotency-replay.png) – Test Postman: Gửi lại cùng Idempotency Key, trả kết quả cũ an toàn (HTTP 200).
- **`B3-21`:** [`B3-21-api-authorizer-denied-invalid-jwt.png`](nguyen/B3-21-api-authorizer-denied-invalid-jwt.png) – Test Postman: Authorizer chặn đứng request thiếu/sai JWT token (HTTP 403).
- **`B3-22`:** [`B3-22-api-route-throttling-429.png`](nguyen/B3-22-api-route-throttling-429.png) – Test CloudShell CLI: Bắn tải liên tục kích hoạt Throttling 429 Too Many Requests.

---

### 📁 Thư mục [`duc/`](duc/README.md) – Vũ Minh Đức (20 ảnh minh chứng)

Đã hoàn thành rà soát dữ liệu DynamoDB, cấu hình Transfer Lambda, thiết lập giám sát CloudWatch, kiểm tra SQS DLQ và kiểm thử tích hợp API:

- **`A3-01`:** [`A3-01-aws-environment.png`](duc/A3-01-aws-environment.png) – Xác thực Account ID, Region, AWS CLI và thời gian phiên Learner Lab.
- **`A3-02`:** [`A3-02-dynamodb-existing-single-table.png`](duc/A3-02-dynamodb-existing-single-table.png) – Rà soát bảng DynamoDB Single-Table hiện hữu.
- **`A3-03`:** [`A3-03-dynamodb-wallets-table.png`](duc/A3-03-dynamodb-wallets-table.png) – Xác nhận bảng Wallets hoạt động với khóa `walletId`.
- **`A3-04`:** [`A3-04-dynamodb-transactions-table.png`](duc/A3-04-dynamodb-transactions-table.png) – Xác nhận bảng Transactions hoạt động với khóa `transactionId`.
- **`A3-05`:** [`A3-05-dynamodb-idempotency-table.png`](duc/A3-05-dynamodb-idempotency-table.png) – Xác nhận bảng Idempotency hoạt động với khóa `userId` và `idempotencyKey`.
- **`A3-06`:** [`A3-06-dynamodb-wallet-seed-data.png`](duc/A3-06-dynamodb-wallet-seed-data.png) – Kiểm tra dữ liệu 4 ví mẫu trong DynamoDB.
- **`A3-07`:** [`A3-07-lambda-transfer-environment-variables.png`](duc/A3-07-lambda-transfer-environment-variables.png) – Kiểm tra biến môi trường của Transfer Lambda.
- **`A3-08`:** [`A3-08-lambda-transfer-success.png`](duc/A3-08-lambda-transfer-success.png) – Test Transfer Lambda thành công trên Console (HTTP 201).
- **`A3-09`:** [`A3-09-cloudwatch-log-groups.png`](duc/A3-09-cloudwatch-log-groups.png) – Cấu hình CloudWatch Log Groups với retention 1 tuần.
- **`A3-10`:** [`A3-10-cloudwatch-metrics.png`](duc/A3-10-cloudwatch-metrics.png) – Theo dõi CloudWatch Metrics của các Lambda.
- **`A3-11`:** [`A3-11-cloudwatch-dashboard.png`](duc/A3-11-cloudwatch-dashboard.png) – Kiểm tra CloudWatch Dashboard của hệ thống.
- **`A3-12`:** [`A3-12-cloudwatch-alarms.png`](duc/A3-12-cloudwatch-alarms.png) – Xác nhận CloudWatch Alarm ở trạng thái OK.
- **`A3-13`:** [`A3-13-sqs-dead-letter-queue.png`](duc/A3-13-sqs-dead-letter-queue.png) – Kiểm tra SQS Dead Letter Queue và mã hóa SSE-SQS.
- **`A3-14`:** [`A3-14-sqs-manual-test.png`](duc/A3-14-sqs-manual-test.png) – Gửi thông điệp kiểm thử vào SQS DLQ thành công.
- **`A3-15`:** [`A3-15-api-gateway-five-routes.png`](duc/A3-15-api-gateway-five-routes.png) – Xác nhận 5 routes trên API Gateway và cấu hình authorizer.
- **`A3-16`:** [`A3-16-api-transfer-success-request.png`](duc/A3-16-api-transfer-success-request.png) – Gửi request chuyển tiền hợp lệ qua Postman (HTTP 201).
- **`A3-17`:** [`A3-17-api-transfer-success-response.png`](duc/A3-17-api-transfer-success-response.png) – Xác nhận response giao dịch thành công và `replayed: false`.
- **`A3-18`:** [`A3-18-api-idempotency-replay.png`](duc/A3-18-api-idempotency-replay.png) – Gửi lại cùng key và nhận kết quả cũ an toàn (HTTP 200).
- **`A3-19`:** [`A3-19-api-authorizer-denied-invalid-jwt.png`](duc/A3-19-api-authorizer-denied-invalid-jwt.png) – Authorizer từ chối Bearer token không hợp lệ (HTTP 403).
- **`A3-20`:** [`A3-20-api-route-throttling-429.png`](duc/A3-20-api-route-throttling-429.png) – Kiểm thử tải và ghi nhận HTTP 429 Too Many Requests.

---

## 3. Tiêu chuẩn tính xác thực & Liêm chính học thuật
- Toàn bộ ảnh minh chứng được chụp trực tiếp từ các phiên AWS Academy Learner Lab của từng thành viên, có hiển thị Account ID tương ứng (`930162821234`) và Region `us-east-1`.
- Không chỉnh sửa số liệu hoặc can thiệp thông tin thời gian phiên thực hành.

