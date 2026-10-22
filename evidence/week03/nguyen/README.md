# DANH MỤC MINH CHỨNG THỰC HÀNH TUẦN 3 – NGUYỄN NGUYÊN

> **Học phần:** Cloud Computing (Điện toán đám mây) – Đợt 1, Năm học 2026–2027  
> **Dự án:** Cổng thanh toán giả lập không máy chủ (`serverless-payment`)  
> **Người thực hiện:** Nguyễn Nguyên  
> **Phạm vi trách nhiệm:** Tái cấu trúc CSDL 3 bảng DynamoDB On-Demand, phát triển & kiểm thử độc lập 5 hàm Lambda, cấu hình API Gateway 5 routes kèm Lambda Authorizer, thiết lập CloudWatch Logs/Metrics/Dashboard/Alarms và Amazon SQS DLQ.  
> **Nền tảng:** AWS Academy Learner Lab · **Region:** `us-east-1` · **Account ID:** `930162821234`  
> **Thời điểm ghi nhận:** Ngày 21/10/2026 – 22/10/2026  

---

## Danh mục ảnh chụp màn hình kiểm chứng (AWS Console & CLI)

Toàn bộ 22 ảnh minh chứng được chụp trực tiếp từ giao diện AWS Management Console, Postman và terminal CloudShell, bảo đảm hiển thị đầy đủ **Account ID `930162821234`**, **Region `us-east-1`**, và **dấu mốc thời gian thực tế**:

| Mã | Tên tệp ảnh | Nội dung kiểm tra & Xác nhận kỹ thuật |
|:---:|---|---|
| **B3-01** | [`B3-01-aws-environment.png`](B3-01-aws-environment.png) | Xác thực môi trường thực hành AWS Academy Learner Lab qua CloudShell (`aws sts get-caller-identity`, Account ID `930162821234`, Region `us-east-1`). |
| **B3-02** | [`B3-02-existing-resources.png`](B3-02-existing-resources.png) | Rà soát kiểm tra toàn bộ tài nguyên hiện hữu trước khi nâng cấp Tuần 3 (DynamoDB tables, Lambda functions, API Gateway, SQS queues). |
| **B3-03** | [`B3-03-dynamodb-wallets-table.png`](B3-03-dynamodb-wallets-table.png) | Khởi tạo thành công bảng DynamoDB `serverless-payment-wallets` ở chế độ On-Demand (Partition Key `walletId`, trạng thái `ACTIVE`). |
| **B3-04** | [`B3-04-dynamodb-transactions-table.png`](B3-04-dynamodb-transactions-table.png) | Khởi tạo thành công bảng DynamoDB `serverless-payment-transactions` ở chế độ On-Demand (Partition Key `transactionId`, trạng thái `ACTIVE`). |
| **B3-05** | [`B3-05-dynamodb-idempotency-table.png`](B3-05-dynamodb-idempotency-table.png) | Khởi tạo thành công bảng DynamoDB `serverless-payment-idempotency` ở chế độ On-Demand (Partition Key `userId`, Sort Key `idempotencyKey`). |
| **B3-06** | [`B3-06-dynamodb-wallet-seed-data.png`](B3-06-dynamodb-wallet-seed-data.png) | Nạp thành công dữ liệu khởi tạo 4 ví mẫu (`W001` đến `W004`) bằng script `seed_wallets.py` qua DynamoDB Explore Items. |
| **B3-07** | [`B3-07-lambda-transfer-success.png`](B3-07-lambda-transfer-success.png) | Kiểm thử hàm `serverless-payment-transfer` trên Lambda Console: chuyển tiền thành công 1.000 VND, giao dịch nguyên tử đạt HTTP 201 Created (`replayed: false`). |
| **B3-08** | [`B3-08-lambda-transfer-idempotent-replay.png`](B3-08-lambda-transfer-idempotent-replay.png) | Kiểm thử chống lặp giao dịch trên Lambda Console: gửi lại cùng Idempotency Key, hệ thống nhận diện replay an toàn HTTP 200 OK (`replayed: true`). |
| **B3-09** | [`B3-09-lambda-wallet-query-success.png`](B3-09-lambda-wallet-query-success.png) | Kiểm thử hàm `serverless-payment-wallet-query` trên Lambda Console: tra cứu số dư và trạng thái ví `W001` thành công (HTTP 200 OK). |
| **B3-10** | [`B3-10-lambda-transaction-query-success.png`](B3-10-lambda-transaction-query-success.png) | Kiểm thử hàm `serverless-payment-transaction-query` trên Lambda Console: tra cứu chi tiết giao dịch theo `transactionId` thành công (HTTP 200 OK). |
| **B3-11** | [`B3-11-cloudwatch-log-groups.png`](B3-11-cloudwatch-log-groups.png) | Cấu hình CloudWatch Log Groups cho các Lambda với chính sách lưu trữ (Retention) 1 tuần (`1 week`) giúp tối ưu chi phí Learner Lab. |
| **B3-12** | [`B3-12-cloudwatch-metrics.png`](B3-12-cloudwatch-metrics.png) | Theo dõi CloudWatch Metrics chi tiết của `serverless-payment-transfer` (Invocations, Duration, ConcurrentExecutions, Throttles, Errors). |
| **B3-13** | [`B3-13-cloudwatch-dashboard.png`](B3-13-cloudwatch-dashboard.png) | Thiết lập CloudWatch Dashboard `serverless-payment` trực quan hóa các số liệu vận hành hệ thống (độ trễ trung bình 173.7 ms, tỉ lệ lỗi, số lượng gọi). |
| **B3-14** | [`B3-14-cloudwatch-alarms.png`](B3-14-cloudwatch-alarms.png) | Thiết lập CloudWatch Alarms giám sát ngưỡng lỗi của các Lambda, xác nhận trạng thái hệ thống hoạt động ổn định (`OK 1`). |
| **B3-15** | [`B3-15-sqs-dead-letter-queue.png`](B3-15-sqs-dead-letter-queue.png) | Cấu hình hàng đợi Amazon SQS Standard Dead Letter Queue `serverless-payment-dlq` với mã hóa SSE-SQS. |
| **B3-16** | [`B3-16-sqs-manual-test.png`](B3-16-sqs-manual-test.png) | Kiểm thử gửi thông điệp kiểm tra vào hàng đợi SQS DLQ qua AWS CloudShell CLI thành công, nhận diện `MessageId` hợp lệ. |
| **B3-17** | [`B3-17-api-gateway-five-routes.png`](B3-17-api-gateway-five-routes.png) | Cấu hình đầy đủ 5 Routes trên Amazon API Gateway HTTP API v2: `POST /auth/token` (NONE) và 4 routes bảo vệ bằng Lambda Authorizer (CUSTOM). |
| **B3-18** | [`B3-18-api-token-success.png`](B3-18-api-token-success.png) | Kiểm thử tích hợp End-to-End qua Postman: Endpoint `POST /auth/token` cấp JWT Access Token thành công (HTTP 200 OK, `expiresIn: 900`). |
| **B3-19** | [`B3-19-api-transfer-success.png`](B3-19-api-transfer-success.png) | Kiểm thử tích hợp End-to-End qua Postman: Endpoint `POST /transfers` chuyển tiền 10.000 VND thành công qua API Gateway (HTTP 201 Created). |
| **B3-20** | [`B3-20-api-idempotency-replay.png`](B3-20-api-idempotency-replay.png) | Kiểm thử tích hợp qua Postman: Gửi lại cùng Idempotency Key, API Gateway và Lambda trả về kết quả cũ với HTTP 200 OK (`replayed: true`). |
| **B3-21** | [`B3-21-api-authorizer-denied-invalid-jwt.png`](B3-21-api-authorizer-denied-invalid-jwt.png) | Kiểm thử bảo mật qua Postman: Lambda Authorizer chặn đứng request không hợp lệ / thiếu token, trả về HTTP 403 Forbidden. |
| **B3-22** | [`B3-22-api-route-throttling-429.png`](B3-22-api-route-throttling-429.png) | Kiểm thử giới hạn tốc độ (Route Throttling) bằng vòng lặp cURL trên CloudShell: hệ thống kích hoạt trả về HTTP 429 Too Many Requests. |

---

## Tiêu chuẩn liêm chính học thuật
- Toàn bộ 22 ảnh minh chứng được chụp trực tiếp từ môi trường AWS Academy Learner Lab của sinh viên **Nguyễn Nguyên** trong ngày 21/10/2026 – 22/10/2026.
- Hình ảnh giữ nguyên toàn bộ giao diện trình duyệt bao gồm Account ID `930162821234`, Region `us-east-1` và dấu mốc thời gian thực tế, không qua chỉnh sửa can thiệp số liệu.

