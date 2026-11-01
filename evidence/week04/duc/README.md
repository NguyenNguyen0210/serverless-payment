# DANH MỤC MINH CHỨNG THỰC HÀNH TUẦN 4 – VŨ MINH ĐỨC

> **Học phần:** Cloud Computing (Điện toán đám mây) – Đợt 1, Năm học 2026–2027
> **Dự án:** Cổng thanh toán giả lập không máy chủ (`serverless-payment`)
> **Người thực hiện:** Vũ Minh Đức
> **Phạm vi trách nhiệm:** Kiểm thử tích hợp 5 API endpoints, phân quyền JWT, giao dịch nguyên tử và idempotency, kiểm thử concurrency, đối soát DynamoDB, kiểm tra Secrets Manager/IAM, CloudWatch, SQS DLQ và thử tải các route API.
> **Nền tảng:** AWS Academy Learner Lab · **Region:** `us-east-1` · **Account ID:** `487906062447`
> **Thời điểm ghi nhận:** Ngày 01/11/2026

---

## Danh mục ảnh chụp màn hình kiểm chứng

Toàn bộ 19 ảnh minh chứng được chụp trực tiếp từ AWS Management Console, AWS CloudShell và Postman. Nội dung dưới đây mô tả đúng kết quả đang hiển thị trong từng ảnh.

| Mã | Tên tệp ảnh | Nội dung kiểm tra & xác nhận kỹ thuật |
|:---:|---|---|
| **A4-01** | [`A4-01-aws-environment-and-resources.png`](A4-01-aws-environment-and-resources.png) | Xác thực AWS Learner Lab qua STS, Region `us-east-1`, các Lambda functions, 3 bảng DynamoDB và HTTP API `serverless-payment-api` trên Account `487906062447`. |
| **A4-02** | [`A4-02-api-gateway-five-routes.png`](A4-02-api-gateway-five-routes.png) | Lấy API ID động theo tên và xác nhận đủ 5 routes; `/auth/token` dùng `NONE`, 4 routes nghiệp vụ dùng `CUSTOM` authorizer. |
| **A4-03** | [`A4-03-api-auth-token-success.png`](A4-03-api-auth-token-success.png) | Kiểm thử Postman `POST /auth/token`, nhận HTTP 200, Bearer JWT và `expiresIn: 900`. |
| **A4-04** | [`A4-04-api-wallet-query-owner-success.png`](A4-04-api-wallet-query-owner-success.png) | Kiểm thử `GET /wallets/W001` bằng JWT của `user-a`, nhận HTTP 200 và thông tin ví chính chủ. |
| **A4-05** | [`A4-05-api-wallet-query-forbidden.png`](A4-05-api-wallet-query-forbidden.png) | Kiểm thử `user-a` truy cập ví `W002` của người khác, hệ thống trả HTTP 403 `WALLET_FORBIDDEN`. |
| **A4-06** | [`A4-06-api-transfer-success.png`](A4-06-api-transfer-success.png) | Kiểm thử `POST /transfers` với Bearer JWT và Idempotency Key, nhận HTTP 201, trạng thái `SUCCESS`, `replayed: false`. |
| **A4-07** | [`A4-07-api-transaction-query-detail.png`](A4-07-api-transaction-query-detail.png) | Tra cứu chi tiết giao dịch theo `transactionId`, nhận HTTP 200 và dữ liệu giao dịch thành công. |
| **A4-08** | [`A4-08-api-wallet-transactions-history.png`](A4-08-api-wallet-transactions-history.png) | Gọi `GET /wallets/W001/transactions`, nhận HTTP 200; response tại thời điểm chụp có `items: []` và `nextToken: null`. |
| **A4-09** | [`A4-09-dynamodb-wallets-balance-reconciliation.png`](A4-09-dynamodb-wallets-balance-reconciliation.png) | Đối soát 4 ví trong bảng `serverless-payment-wallets`; ảnh ghi nhận `W001 = 89.000 VND`, `W002 = 61.000 VND`. |
| **A4-10** | [`A4-10-api-idempotency-replay-success.png`](A4-10-api-idempotency-replay-success.png) | Gửi lại cùng request và Idempotency Key, nhận kết quả cũ với `replayed: true`, không tạo giao dịch mới. |
| **A4-11** | [`A4-11-api-idempotency-conflict.png`](A4-11-api-idempotency-conflict.png) | Dùng lại Idempotency Key với payload khác, hệ thống trả HTTP 409 `IDEMPOTENCY_KEY_CONFLICT`. |
| **A4-12** | [`A4-12-test-concurrency-parallel-requests.png`](A4-12-test-concurrency-parallel-requests.png) | Gửi 5 request song song cùng key; kết quả có 1 request HTTP 201, 4 request HTTP 200, cùng một `transactionId`, đúng 1 response `replayed: false`. |
| **A4-13** | [`A4-13-secrets-manager-and-iam-labrole.png`](A4-13-secrets-manager-and-iam-labrole.png) | Xác nhận secret `serverless-payment/jwt-secret` và Lambda Authorizer dùng Python 3.12, IAM `LabRole`, timeout 15 giây. |
| **A4-14** | [`A4-14-cloudwatch-log-groups-retention.png`](A4-14-cloudwatch-log-groups-retention.png) | Xác nhận đủ 5 CloudWatch Log Groups của hệ thống đều có retention 7 ngày. |
| **A4-15** | [`A4-15-cloudwatch-dashboard-metrics.png`](A4-15-cloudwatch-dashboard-metrics.png) | Kiểm tra dashboard `serverless-payment` với các chỉ số API Gateway, Duration, Errors và Invocations. |
| **A4-16** | [`A4-16-cloudwatch-alarm-lambda-errors.png`](A4-16-cloudwatch-alarm-lambda-errors.png) | Xác nhận alarm `serverless-payment-lambda-errors` ở trạng thái `OK`. |
| **A4-17** | [`A4-17-sqs-dead-letter-queue-test.png`](A4-17-sqs-dead-letter-queue-test.png) | Kiểm tra SQS DLQ thuộc Account `487906062447` và gửi message `MANUAL_WEEK4_TEST`, nhận `MessageId` thành công. |
| **A4-18** | [`A4-18-api-auth-token-burst-test.png`](A4-18-api-auth-token-burst-test.png) | Gửi đồng thời 30 request dùng demo code không hợp lệ vào `/auth/token`, xác nhận endpoint từ chối nhất quán với HTTP 401 dưới tải burst. |
| **A4-19** | [`A4-19-api-transfers-idempotency-burst-test.png`](A4-19-api-transfers-idempotency-burst-test.png) | Gửi đồng thời 40 request cùng Idempotency Key vào `/transfers`; ghi nhận 1 HTTP 201, 39 HTTP 200 và một `transactionId` duy nhất, xác nhận idempotency dưới tải burst. |

---

## Tệp lệnh CloudShell

Các lệnh dùng cho những ảnh CloudShell được tổng hợp tại [`CLOUDSHELL-COMMANDS.md`](CLOUDSHELL-COMMANDS.md).

## Tiêu chuẩn liêm chính học thuật

- Toàn bộ 19 ảnh được giữ nguyên nội dung và số liệu tại thời điểm chụp; thao tác chuẩn hóa chỉ đổi tên tệp và bổ sung danh mục Markdown.
- Riêng A4-03 đã che hai giá trị credential (`demoCode` và JWT) trước khi đưa lên repository public; URL, HTTP 200, `tokenType` và `expiresIn` vẫn được giữ để kiểm chứng kết quả.
- Ảnh Postman có thể chứa JWT hoặc demo code đã dùng trong phiên kiểm thử; không tái sử dụng các giá trị này cho môi trường khác.
