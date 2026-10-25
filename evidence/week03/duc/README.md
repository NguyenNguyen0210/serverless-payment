# DANH MỤC MINH CHỨNG THỰC HÀNH TUẦN 3 – VŨ MINH ĐỨC

> **Học phần:** Cloud Computing (Điện toán đám mây) – Đợt 1, Năm học 2026–2027  
> **Dự án:** Cổng thanh toán giả lập không máy chủ (`serverless-payment`)  
> **Người thực hiện:** Vũ Minh Đức  
> **Phạm vi trách nhiệm:** Rà soát và tái cấu trúc dữ liệu DynamoDB, cấu hình Transfer Lambda, thiết lập CloudWatch Logs/Metrics/Dashboard/Alarms, kiểm tra SQS DLQ, API Gateway và các kịch bản tích hợp chuyển tiền.  
> **Nền tảng:** AWS Academy Learner Lab · **Region:** `us-east-1` · **Account ID:** `892973274103`  
> **Thời điểm ghi nhận:** Ngày 21/10/2026 – 22/10/2026  

---

## Danh mục ảnh chụp màn hình kiểm chứng (AWS Console, CLI & Postman)

Toàn bộ 20 ảnh minh chứng được chụp trực tiếp từ AWS Management Console, AWS CloudShell và Postman, bảo đảm hiển thị thông tin môi trường thực hành tương ứng:

| Mã | Tên tệp ảnh | Nội dung kiểm tra & Xác nhận kỹ thuật |
|:---:|---|---|
| **A3-01** | [`A3-01-aws-environment.png`](A3-01-aws-environment.png) | Xác thực phiên AWS Academy Learner Lab bằng `aws sts get-caller-identity`, kiểm tra cấu hình AWS CLI, Account ID `892973274103`, Region `us-east-1` và thời gian UTC. |
| **A3-02** | [`A3-02-dynamodb-existing-single-table.png`](A3-02-dynamodb-existing-single-table.png) | Rà soát bảng DynamoDB `serverless-payment` hiện hữu ở chế độ On-Demand với khóa `PK` và `SK` trước khi tách dữ liệu. |
| **A3-03** | [`A3-03-dynamodb-wallets-table.png`](A3-03-dynamodb-wallets-table.png) | Xác nhận bảng `serverless-payment-wallets` hoạt động với Partition Key `walletId` và trạng thái `ACTIVE`. |
| **A3-04** | [`A3-04-dynamodb-transactions-table.png`](A3-04-dynamodb-transactions-table.png) | Xác nhận bảng `serverless-payment-transactions` hoạt động với Partition Key `transactionId` và trạng thái `ACTIVE`. |
| **A3-05** | [`A3-05-dynamodb-idempotency-table.png`](A3-05-dynamodb-idempotency-table.png) | Xác nhận bảng `serverless-payment-idempotency` hoạt động với Partition Key `userId` và Sort Key `idempotencyKey`. |
| **A3-06** | [`A3-06-dynamodb-wallet-seed-data.png`](A3-06-dynamodb-wallet-seed-data.png) | Kiểm tra dữ liệu 4 ví mẫu `W001`–`W004` trong bảng `serverless-payment-wallets`. |
| **A3-07** | [`A3-07-lambda-transfer-environment-variables.png`](A3-07-lambda-transfer-environment-variables.png) | Kiểm tra các biến môi trường của Transfer Lambda cho bảng Wallets, Transactions, Idempotency và SQS DLQ. |
| **A3-08** | [`A3-08-lambda-transfer-success.png`](A3-08-lambda-transfer-success.png) | Kiểm thử Transfer Lambda thành công trên Lambda Console, trả HTTP 201 Created và `replayed: false`. |
| **A3-09** | [`A3-09-cloudwatch-log-groups.png`](A3-09-cloudwatch-log-groups.png) | Cấu hình CloudWatch Log Groups cho Token, Authorizer và Transfer Lambda với thời gian lưu trữ 1 tuần. |
| **A3-10** | [`A3-10-cloudwatch-metrics.png`](A3-10-cloudwatch-metrics.png) | Theo dõi các CloudWatch Metrics của hệ thống gồm Invocations, Duration và Errors. |
| **A3-11** | [`A3-11-cloudwatch-dashboard.png`](A3-11-cloudwatch-dashboard.png) | Kiểm tra CloudWatch Dashboard `serverless-payment` hiển thị các chỉ số vận hành chính. |
| **A3-12** | [`A3-12-cloudwatch-alarms.png`](A3-12-cloudwatch-alarms.png) | Xác nhận CloudWatch Alarm `serverless-payment-lambda-errors` ở trạng thái `OK`. |
| **A3-13** | [`A3-13-sqs-dead-letter-queue.png`](A3-13-sqs-dead-letter-queue.png) | Kiểm tra cấu hình SQS Standard Queue `serverless-payment-dlq` và mã hóa SSE-SQS. |
| **A3-14** | [`A3-14-sqs-manual-test.png`](A3-14-sqs-manual-test.png) | Gửi thông điệp kiểm thử vào SQS DLQ bằng AWS CLI và nhận `MessageId` thành công. |
| **A3-15** | [`A3-15-api-gateway-five-routes.png`](A3-15-api-gateway-five-routes.png) | Xác nhận API Gateway có đủ 5 routes; route cấp token không yêu cầu authorizer và các route nghiệp vụ dùng CUSTOM Authorizer. |
| **A3-16** | [`A3-16-api-transfer-success-request.png`](A3-16-api-transfer-success-request.png) | Kiểm thử request `POST /transfers` qua Postman với Bearer JWT và `Idempotency-Key`, nhận HTTP 201 Created. |
| **A3-17** | [`A3-17-api-transfer-success-response.png`](A3-17-api-transfer-success-response.png) | Xác nhận response giao dịch thành công gồm `transactionId`, thông tin hai ví, số tiền, trạng thái `SUCCESS` và `replayed: false`. |
| **A3-18** | [`A3-18-api-idempotency-replay.png`](A3-18-api-idempotency-replay.png) | Gửi lại cùng request và `Idempotency-Key`, hệ thống trả HTTP 200 OK với `replayed: true`. |
| **A3-19** | [`A3-19-api-authorizer-denied-invalid-jwt.png`](A3-19-api-authorizer-denied-invalid-jwt.png) | Kiểm thử request có Bearer token không hợp lệ, Lambda Authorizer từ chối với HTTP 403 Forbidden. |
| **A3-20** | [`A3-20-api-route-throttling-429.png`](A3-20-api-route-throttling-429.png) | Gửi liên tiếp 30 request bằng cURL và ghi nhận HTTP 429 Too Many Requests khi vượt ngưỡng throttling. |

---

## Tiêu chuẩn liêm chính học thuật

- Toàn bộ 20 ảnh minh chứng được chụp trực tiếp từ môi trường AWS Academy Learner Lab của sinh viên **Vũ Minh Đức** trong ngày 21/10/2026 – 22/10/2026.
- Hình ảnh giữ nguyên dữ liệu và giao diện gốc; thao tác trong nhiệm vụ này chỉ đổi tên tệp và đồng bộ danh mục Markdown.
