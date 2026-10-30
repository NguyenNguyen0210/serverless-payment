# DANH MỤC MINH CHỨNG THỰC HÀNH TUẦN 4 – NGUYỄN NGUYÊN

> **Học phần:** Cloud Computing (Điện toán đám mây) – Đợt 1, Năm học 2026–2027  
> **Dự án:** Cổng thanh toán giả lập không máy chủ (`serverless-payment`)  
> **Người thực hiện:** Nguyễn Nguyên  
> **Phạm vi trách nhiệm:** Kiểm thử tích hợp toàn diện 5 API endpoints, kiểm tra phân quyền JWT/IAM/Secrets Manager, kiểm thử chống lặp giao dịch (Idempotency Replay/Conflict/Concurrency), kiểm thử giám sát CloudWatch (Logs retention 7 ngày, Metrics, Dashboard, Alarms), kiểm thử hàng đợi Amazon SQS DLQ, và kiểm thử giới hạn tốc độ Route Throttling (HTTP 429).  
> **Nền tảng:** AWS Academy Learner Lab · **Region:** `us-east-1` · **Account ID:** `930162821234`  
> **Thời điểm ghi nhận:** Ngày 26/10/2026 – 30/10/2026  

---

## Danh mục ảnh chụp màn hình kiểm chứng (AWS Console, CLI & Postman)

Toàn bộ 19 ảnh minh chứng được chụp trực tiếp từ giao diện AWS Management Console, Postman và terminal CloudShell, bảo đảm hiển thị đầy đủ **Account ID `930162821234`**, **Region `us-east-1`**, và **dấu mốc thời gian thực tế**:

| Mã | Tên tệp ảnh | Nội dung kiểm tra & Xác nhận kỹ thuật |
|:---:|---|---|
| **B4-01** | [`B4-01-aws-environment-and-resources.png`](B4-01-aws-environment-and-resources.png) | Xác thực môi trường thực hành AWS Learner Lab qua CloudShell: STS Caller Identity (`930162821234`), 5 Lambda functions, 3 bảng DynamoDB On-Demand và HTTP API. |
| **B4-02** | [`B4-02-api-gateway-five-routes.png`](B4-02-api-gateway-five-routes.png) | Xác nhận cấu hình 5 Routes trên Amazon API Gateway HTTP API v2 (`i7t9xqlrx7`) kèm cơ chế Lambda Authorizer bảo vệ. |
| **B4-03** | [`B4-03-api-auth-token-success.png`](B4-03-api-auth-token-success.png) | Kiểm thử Postman: Endpoint `POST /auth/token` xác thực `demoCode` và cấp JWT Access Token thành công (HTTP 200 OK, `expiresIn: 900`). |
| **B4-04** | [`B4-04-api-wallet-query-owner-success.png`](B4-04-api-wallet-query-owner-success.png) | Kiểm thử Postman: Endpoint `GET /wallets/W001` tra cứu thông tin và số dư ví chính chủ thành công với Bearer JWT (HTTP 200 OK, `balance: 73000`). |
| **B4-05** | [`B4-05-api-wallet-query-forbidden.png`](B4-05-api-wallet-query-forbidden.png) | Kiểm thử bảo mật Postman: Endpoint `GET /wallets/W002` từ chối khi `user-a` cố tình xem ví của người khác, trả về HTTP 403 `WALLET_FORBIDDEN`. |
| **B4-06** | [`B4-06-api-transfer-success.png`](B4-06-api-transfer-success.png) | Kiểm thử Postman: Endpoint `POST /transfers` chuyển tiền thành công 10.000 VND từ `W001` sang `W002` qua DynamoDB Transaction (HTTP 201 Created, `replayed: false`). |
| **B4-07** | [`B4-07-api-transaction-query-detail.png`](B4-07-api-transaction-query-detail.png) | Kiểm thử Postman: Endpoint `GET /transactions/{id}` tra cứu chi tiết giao dịch vừa thực hiện thành công theo `transactionId` (HTTP 200 OK). |
| **B4-08** | [`B4-08-api-wallet-transactions-history.png`](B4-08-api-wallet-transactions-history.png) | Kiểm thử Postman: Endpoint `GET /wallets/W001/transactions` truy vấn lịch sử giao dịch của ví qua GSIs (HTTP 200 OK). |
| **B4-09** | [`B4-09-dynamodb-wallets-balance-reconciliation.png`](B4-09-dynamodb-wallets-balance-reconciliation.png) | Đối soát số dư trên DynamoDB Console: ví nguồn `W001` bị trừ đúng 10.000 VND (còn 63.000 VND) và ví đích `W002` nhận đủ 10.000 VND (lên 87.000 VND). |
| **B4-10** | [`B4-10-api-idempotency-replay-success.png`](B4-10-api-idempotency-replay-success.png) | Kiểm thử chống lặp giao dịch (Idempotent Replay): gửi lại request cùng Idempotency Key, hệ thống nhận diện và trả kết quả cũ an toàn (HTTP 200 OK, `replayed: true`). |
| **B4-11** | [`B4-11-api-idempotency-conflict.png`](B4-11-api-idempotency-conflict.png) | Kiểm thử xung đột key: tái sử dụng Idempotency Key cũ với payload khác, hệ thống chặn đứng với HTTP 409 `IDEMPOTENCY_KEY_CONFLICT`. |
| **B4-12** | [`B4-12-test-concurrency-parallel-requests.png`](B4-12-test-concurrency-parallel-requests.png) | Kiểm thử đồng thời (Concurrency): dùng bash background loop bắn 5 requests song song cùng `CONCURRENT_KEY`, chứng minh hệ thống không nhân bản giao dịch hay trừ tiền 2 lần. |
| **B4-13** | [`B4-13-secrets-manager-and-iam-labrole.png`](B4-13-secrets-manager-and-iam-labrole.png) | Xác thực cấu hình Secrets Manager `serverless-payment/jwt-secret` an toàn và Lambda Authorizer sử dụng IAM `LabRole` (Python 3.12). |
| **B4-14** | [`B4-14-cloudwatch-log-groups-retention.png`](B4-14-cloudwatch-log-groups-retention.png) | Kiểm tra CloudWatch Log Groups qua CloudShell: xác nhận chính sách lưu trữ (Retention) 7 ngày chuẩn hóa giúp tối ưu chi phí ngân sách Lab. |
| **B4-15** | [`B4-15-cloudwatch-dashboard-metrics.png`](B4-15-cloudwatch-dashboard-metrics.png) | Giám sát toàn diện trên CloudWatch Dashboard `serverless-payment`: Count, 5xx (0), Duration (449.3 ms), Errors (0) và Invocations (2). |
| **B4-16** | [`B4-16-cloudwatch-alarm-lambda-errors.png`](B4-16-cloudwatch-alarm-lambda-errors.png) | Xác nhận CloudWatch Alarm `serverless-payment-lambda-errors` theo dõi lỗi thực thi Lambda hoạt động ổn định ở trạng thái bình thường (`OK`). |
| **B4-17** | [`B4-17-sqs-dead-letter-queue-test.png`](B4-17-sqs-dead-letter-queue-test.png) | Kiểm tra hàng đợi Amazon SQS Dead Letter Queue `serverless-payment-dlq` và gửi thành công message kiểm thử `MANUAL_WEEK4_TEST` qua CloudShell CLI. |
| **B4-18** | [`B4-18-api-throttling-auth-token-test.png`](B4-18-api-throttling-auth-token-test.png) | Kiểm thử giới hạn tốc độ (Route Throttling) trên endpoint `/auth/token` bằng vòng lặp 30 requests cURL liên tục. |
| **B4-19** | [`B4-19-api-throttling-transfers-test.png`](B4-19-api-throttling-transfers-test.png) | Kiểm thử giới hạn tốc độ (Route Throttling) trên endpoint `/transfers` bằng vòng lặp 40 requests cURL liên tục. |

---

## Tiêu chuẩn liêm chính học thuật
- Toàn bộ 19 ảnh minh chứng được chụp trực tiếp từ môi trường AWS Academy Learner Lab của sinh viên **Nguyễn Nguyên** trong đợt thực hành Tuần 4 (26/10/2026 – 30/10/2026).
- Hình ảnh giữ nguyên toàn bộ giao diện trình duyệt bao gồm Account ID `930162821234`, Region `us-east-1` và dấu mốc thời gian thực tế, không qua chỉnh sửa can thiệp số liệu.

