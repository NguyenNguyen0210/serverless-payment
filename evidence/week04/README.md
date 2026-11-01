# DANH MỤC MINH CHỨNG KỸ THUẬT TUẦN 4 (EVIDENCE CATALOG - WEEK 4)

> **Học phần:** Cloud Computing (Điện toán đám mây) – Đợt 1, Năm học 2026–2027  
> **Dự án:** Cổng thanh toán giả lập không máy chủ (`serverless-payment`)  
> **Nhóm thực hiện:** Serverless (02 thành viên: Vũ Minh Đức & Nguyễn Nguyên)  
> **Nền tảng:** AWS Academy Learner Lab (Vocareum) · **Region:** `us-east-1`  
> **Tài khoản minh chứng:** Nguyễn Nguyên `930162821234` · Vũ Minh Đức `487906062447`
> **Tuần báo cáo:** Tuần 4 (26/10/2026 – 01/11/2026) – Kiểm thử tổng thể, bảo mật, độ tin cậy, giám sát, chi phí & nghiệm thu cuối kỳ.  

---

## 🎥 Video Demo nghiệm thu cuối kỳ
- **Liên kết Google Drive:** [Video Demo Cổng thanh toán Serverless Payment](https://drive.google.com/drive/folders/1FnaAXXF94_mIkvJ5nLq5XsgekHrrIcKa?usp=drive_link)

---

## 1. Cơ cấu phân chia minh chứng theo thành viên

Để bảo đảm tính minh bạch và ghi nhận chính xác khối lượng đóng góp cá nhân (tối thiểu 8 giờ/thành viên/tuần), thư mục minh chứng Tuần 4 được tổ chức phân tách theo từng thành viên:

```
evidence/week04/
├── README.md               # Danh mục minh chứng tổng hợp Tuần 4 (tệp hiện tại)
├── nguyen/                 # Minh chứng của Nguyễn Nguyên (19 ảnh)
│   ├── README.md
│   ├── CLOUDSHELL-COMMANDS.md
│   └── B4-01 -> B4-19...   # Toàn bộ ảnh chụp màn hình AWS Console, CloudShell CLI & Postman
└── duc/                    # Minh chứng của Vũ Minh Đức (19 ảnh)
    ├── README.md
    ├── CLOUDSHELL-COMMANDS.md
    └── A4-01 -> A4-19...   # AWS Console, CloudShell CLI & Postman
```

---

## 2. Danh mục minh chứng chi tiết của từng thành viên

### 📁 Thư mục [`nguyen/`](nguyen/README.md) – Nguyễn Nguyên (19 ảnh minh chứng)

Đã hoàn thành kiểm thử tích hợp 5 endpoints qua Postman, kiểm tra phân quyền JWT/IAM, xác thực Secrets Manager, kiểm thử chống lặp giao dịch (Replay & Conflict), kiểm thử concurrency, giám sát CloudWatch (Logs retention 7 ngày, Dashboard, Alarms), kiểm thử SQS DLQ và Route Throttling (HTTP 429):

- **`B4-01`:** [`B4-01-aws-environment-and-resources.png`](nguyen/B4-01-aws-environment-and-resources.png) – Xác thực môi trường Learner Lab qua CloudShell: STS Caller Identity (`930162821234`), 5 Lambdas, 3 bảng DynamoDB, HTTP API.
- **`B4-02`:** [`B4-02-api-gateway-five-routes.png`](nguyen/B4-02-api-gateway-five-routes.png) – Xác nhận cấu hình 5 Routes trên Amazon API Gateway HTTP API v2 (`i7t9xqlrx7`) kèm Lambda Authorizer.
- **`B4-03`:** [`B4-03-api-auth-token-success.png`](nguyen/B4-03-api-auth-token-success.png) – Test Postman: `POST /auth/token` xác thực `demoCode` và cấp JWT Access Token thành công (HTTP 200 OK, `expiresIn: 900`).
- **`B4-04`:** [`B4-04-api-wallet-query-owner-success.png`](nguyen/B4-04-api-wallet-query-owner-success.png) – Test Postman: `GET /wallets/W001` tra cứu số dư ví chính chủ với Bearer JWT thành công (HTTP 200 OK).
- **`B4-05`:** [`B4-05-api-wallet-query-forbidden.png`](nguyen/B4-05-api-wallet-query-forbidden.png) – Test Postman: `GET /wallets/W002` từ chối khi xem ví người khác, trả về HTTP 403 `WALLET_FORBIDDEN`.
- **`B4-06`:** [`B4-06-api-transfer-success.png`](nguyen/B4-06-api-transfer-success.png) – Test Postman: `POST /transfers` chuyển tiền thành công 10.000 VND qua DynamoDB Transaction (HTTP 201 Created).
- **`B4-07`:** [`B4-07-api-transaction-query-detail.png`](nguyen/B4-07-api-transaction-query-detail.png) – Test Postman: `GET /transactions/{id}` tra cứu chi tiết giao dịch thành công theo transaction ID (HTTP 200 OK).
- **`B4-08`:** [`B4-08-api-wallet-transactions-history.png`](nguyen/B4-08-api-wallet-transactions-history.png) – Test Postman: `GET /wallets/W001/transactions` truy vấn lịch sử giao dịch của ví qua GSIs (HTTP 200 OK).
- **`B4-09`:** [`B4-09-dynamodb-wallets-balance-reconciliation.png`](nguyen/B4-09-dynamodb-wallets-balance-reconciliation.png) – Đối soát số dư trên DynamoDB Console: ví `W001` bị trừ đúng 10.000 VND và ví `W002` nhận đủ 10.000 VND.
- **`B4-10`:** [`B4-10-api-idempotency-replay-success.png`](nguyen/B4-10-api-idempotency-replay-success.png) – Test Postman: Gửi lại cùng Idempotency Key, hệ thống nhận diện và trả kết quả cũ an toàn (HTTP 200 OK, `replayed: true`).
- **`B4-11`:** [`B4-11-api-idempotency-conflict.png`](nguyen/B4-11-api-idempotency-conflict.png) – Test Postman: Tái sử dụng key cũ với payload khác, hệ thống chặn đứng với HTTP 409 `IDEMPOTENCY_KEY_CONFLICT`.
- **`B4-12`:** [`B4-12-test-concurrency-parallel-requests.png`](nguyen/B4-12-test-concurrency-parallel-requests.png) – Test Concurrency: Bắn 5 requests song song cùng `CONCURRENT_KEY`, không gây trừ tiền hai lần.
- **`B4-13`:** [`B4-13-secrets-manager-and-iam-labrole.png`](nguyen/B4-13-secrets-manager-and-iam-labrole.png) – Xác thực cấu hình Secrets Manager `serverless-payment/jwt-secret` an toàn và Lambda Authorizer IAM `LabRole`.
- **`B4-14`:** [`B4-14-cloudwatch-log-groups-retention.png`](nguyen/B4-14-cloudwatch-log-groups-retention.png) – Kiểm tra CloudWatch Log Groups: xác nhận chính sách lưu trữ (Retention) 7 ngày chuẩn hóa.
- **`B4-15`:** [`B4-15-cloudwatch-dashboard-metrics.png`](nguyen/B4-15-cloudwatch-dashboard-metrics.png) – Giám sát toàn diện trên CloudWatch Dashboard `serverless-payment`: Count, 5xx (0), Duration (449.3 ms), Errors (0), Invocations (2).
- **`B4-16`:** [`B4-16-cloudwatch-alarm-lambda-errors.png`](nguyen/B4-16-cloudwatch-alarm-lambda-errors.png) – Xác nhận CloudWatch Alarm `serverless-payment-lambda-errors` ở trạng thái hoạt động bình thường (`OK`).
- **`B4-17`:** [`B4-17-sqs-dead-letter-queue-test.png`](nguyen/B4-17-sqs-dead-letter-queue-test.png) – Kiểm tra hàng đợi SQS Dead Letter Queue `serverless-payment-dlq` và gửi message kiểm thử `MANUAL_WEEK4_TEST`.
- **`B4-18`:** [`B4-18-api-throttling-auth-token-test.png`](nguyen/B4-18-api-throttling-auth-token-test.png) – Kiểm thử giới hạn tải (Route Throttling) trên endpoint `/auth/token` bằng vòng lặp 30 requests cURL.
- **`B4-19`:** [`B4-19-api-throttling-transfers-test.png`](nguyen/B4-19-api-throttling-transfers-test.png) – Kiểm thử giới hạn tải (Route Throttling) trên endpoint `/transfers` bằng vòng lặp 40 requests cURL.

---

### 📁 Thư mục [`duc/`](duc/README.md) – Vũ Minh Đức (19 ảnh minh chứng)

Đã hoàn thành kiểm thử tích hợp 5 endpoints, phân quyền JWT, giao dịch nguyên tử và idempotency, concurrency, đối soát DynamoDB, cấu hình Secrets Manager/IAM, CloudWatch, SQS DLQ và thử tải hai routes API:

- **`A4-01`:** [`A4-01-aws-environment-and-resources.png`](duc/A4-01-aws-environment-and-resources.png) – Xác thực Account `487906062447`, Region `us-east-1`, Lambda, DynamoDB và HTTP API.
- **`A4-02`:** [`A4-02-api-gateway-five-routes.png`](duc/A4-02-api-gateway-five-routes.png) – Xác nhận đủ 5 API routes và cấu hình authorizer.
- **`A4-03`:** [`A4-03-api-auth-token-success.png`](duc/A4-03-api-auth-token-success.png) – Cấp JWT thành công qua `POST /auth/token`.
- **`A4-04`:** [`A4-04-api-wallet-query-owner-success.png`](duc/A4-04-api-wallet-query-owner-success.png) – Tra cứu ví `W001` chính chủ thành công.
- **`A4-05`:** [`A4-05-api-wallet-query-forbidden.png`](duc/A4-05-api-wallet-query-forbidden.png) – Chặn truy cập ví `W002` của người khác với HTTP 403.
- **`A4-06`:** [`A4-06-api-transfer-success.png`](duc/A4-06-api-transfer-success.png) – Chuyển tiền thành công, HTTP 201 và `replayed: false`.
- **`A4-07`:** [`A4-07-api-transaction-query-detail.png`](duc/A4-07-api-transaction-query-detail.png) – Tra cứu chi tiết giao dịch theo ID.
- **`A4-08`:** [`A4-08-api-wallet-transactions-history.png`](duc/A4-08-api-wallet-transactions-history.png) – Gọi API lịch sử ví; ảnh ghi nhận response rỗng tại thời điểm kiểm thử.
- **`A4-09`:** [`A4-09-dynamodb-wallets-balance-reconciliation.png`](duc/A4-09-dynamodb-wallets-balance-reconciliation.png) – Đối soát số dư ví trên DynamoDB.
- **`A4-10`:** [`A4-10-api-idempotency-replay-success.png`](duc/A4-10-api-idempotency-replay-success.png) – Xác nhận idempotent replay với `replayed: true`.
- **`A4-11`:** [`A4-11-api-idempotency-conflict.png`](duc/A4-11-api-idempotency-conflict.png) – Xác nhận HTTP 409 khi tái sử dụng key với payload khác.
- **`A4-12`:** [`A4-12-test-concurrency-parallel-requests.png`](duc/A4-12-test-concurrency-parallel-requests.png) – 5 request đồng thời cùng một key chỉ tạo một transaction.
- **`A4-13`:** [`A4-13-secrets-manager-and-iam-labrole.png`](duc/A4-13-secrets-manager-and-iam-labrole.png) – Kiểm tra Secrets Manager, Python 3.12 và IAM `LabRole`.
- **`A4-14`:** [`A4-14-cloudwatch-log-groups-retention.png`](duc/A4-14-cloudwatch-log-groups-retention.png) – Xác nhận 5 Log Groups có retention 7 ngày.
- **`A4-15`:** [`A4-15-cloudwatch-dashboard-metrics.png`](duc/A4-15-cloudwatch-dashboard-metrics.png) – Kiểm tra dashboard và các metrics vận hành.
- **`A4-16`:** [`A4-16-cloudwatch-alarm-lambda-errors.png`](duc/A4-16-cloudwatch-alarm-lambda-errors.png) – Xác nhận alarm lỗi Lambda ở trạng thái `OK`.
- **`A4-17`:** [`A4-17-sqs-dead-letter-queue-test.png`](duc/A4-17-sqs-dead-letter-queue-test.png) – Gửi message kiểm thử vào SQS DLQ thành công.
- **`A4-18`:** [`A4-18-api-auth-token-burst-test.png`](duc/A4-18-api-auth-token-burst-test.png) – Gửi đồng thời 30 request có thông tin xác thực không hợp lệ, xác nhận `/auth/token` trả HTTP 401 nhất quán dưới tải burst.
- **`A4-19`:** [`A4-19-api-transfers-idempotency-burst-test.png`](duc/A4-19-api-transfers-idempotency-burst-test.png) – Gửi đồng thời 40 request cùng key, ghi nhận 1 HTTP 201, 39 HTTP 200 và một transaction ID duy nhất.

---

## 3. Tiêu chuẩn tính xác thực & Liêm chính học thuật
- Toàn bộ ảnh minh chứng được chụp trực tiếp từ các phiên AWS Academy Learner Lab của **Nguyễn Nguyên** và **Vũ Minh Đức** trong đợt thực hành Tuần 4.
- Giữ nguyên giao diện và số liệu gốc, bao gồm Account ID `930162821234` (Nguyễn Nguyên), `487906062447` (Vũ Minh Đức) và Region `us-east-1`; thao tác chuẩn hóa chỉ đổi tên tệp và đồng bộ danh mục Markdown.
- Ảnh A4-03 đã được che riêng giá trị demo code và JWT trước khi công khai; các trường kết quả kiểm thử vẫn được giữ nguyên.

