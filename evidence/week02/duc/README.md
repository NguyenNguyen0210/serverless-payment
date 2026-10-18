# DANH MỤC MINH CHỨNG THỰC HÀNH TUẦN 2 – VŨ MINH ĐỨC

> **Học phần:** Cloud Computing (Điện toán đám mây) – Đợt 1, Năm học 2026–2027
> **Dự án:** Cổng thanh toán giả lập không máy chủ (`serverless-payment`)
> **Người thực hiện:** Vũ Minh Đức
> **Phạm vi:** Lambda, Secrets Manager, DynamoDB, API Gateway, SQS, giao dịch nguyên tử, idempotency và kiểm thử API.
> **Nền tảng:** AWS Academy Learner Lab · **Region:** `us-east-1` · **Account ID:** `892973274103`
> **Thời điểm ghi nhận:** Ngày 18/10/2026

---

## Danh mục ảnh minh chứng

| Mã | Tệp ảnh | Nội dung xác nhận |
|:---:|---|---|
| **A2-01** | [`A2-01-lab-environment.png`](A2-01-lab-environment.png) | Xác nhận danh tính phiên AWS Academy Learner Lab, Account ID và Region `us-east-1` bằng AWS CLI. |
| **A2-02** | [`A2-02-secrets-manager.png`](A2-02-secrets-manager.png) | Secret `serverless-payment/jwt-secret` được lưu thành công trong AWS Secrets Manager. |
| **A2-03** | [`A2-03-pyjwt-layer.png`](A2-03-pyjwt-layer.png) | Lambda Layer `serverless-payment-pyjwt` phiên bản 1, tương thích Python 3.12 và kiến trúc x86_64. |
| **A2-04** | [`A2-04-token-lambda-runtime-layer.png`](A2-04-token-lambda-runtime-layer.png) | Token Lambda sử dụng runtime Python 3.12 và gắn PyJWT Layer. |
| **A2-05** | [`A2-05-token-lambda-execution-role.png`](A2-05-token-lambda-execution-role.png) | Token Lambda sử dụng IAM execution role `LabRole`. |
| **A2-06** | [`A2-06-token-test-success.png`](A2-06-token-test-success.png) | Token Lambda cấp JWT thành công, phản hồi HTTP `200`. |
| **A2-07** | [`A2-07-token-test-invalid-credentials.png`](A2-07-token-test-invalid-credentials.png) | Token Lambda từ chối demo credential không hợp lệ, phản hồi HTTP `401`. |
| **A2-08** | [`A2-08-authorizer-test-success.png`](A2-08-authorizer-test-success.png) | Lambda Authorizer chấp nhận JWT hợp lệ và trả `isAuthorized: true` cùng `userId`. |
| **A2-09** | [`A2-09-authorizer-test-denied.png`](A2-09-authorizer-test-denied.png) | Lambda Authorizer từ chối JWT không hợp lệ và trả `isAuthorized: false`. |
| **A2-10** | [`A2-10-dynamodb-table.png`](A2-10-dynamodb-table.png) | Bảng DynamoDB `serverless-payment` hoạt động ở chế độ On-Demand với khóa `PK` và `SK`. |
| **A2-11** | [`A2-11-wallet-seed-data.png`](A2-11-wallet-seed-data.png) | Bốn ví mẫu `W001`–`W004` đã được nạp đúng số dư, chủ sở hữu, tiền tệ và trạng thái. |
| **A2-12** | [`A2-12-transfer-test-insufficient-funds.png`](A2-12-transfer-test-insufficient-funds.png) | Transfer Lambda từ chối giao dịch thiếu số dư với HTTP `409 INSUFFICIENT_FUNDS`. |
| **A2-13** | [`A2-13-transfer-test-success.png`](A2-13-transfer-test-success.png) | Transfer Lambda xử lý giao dịch thành công với HTTP `201` và `replayed: false`. |
| **A2-14** | [`A2-14-transfer-test-idempotent-replay.png`](A2-14-transfer-test-idempotent-replay.png) | Gửi lại cùng payload và key trả HTTP `200`, `replayed: true`, không trừ tiền lần hai. |
| **A2-15** | [`A2-15-transfer-test-idempotency-conflict.png`](A2-15-transfer-test-idempotency-conflict.png) | Tái sử dụng key với payload khác bị từ chối bằng HTTP `409 IDEMPOTENCY_KEY_CONFLICT`. |
| **A2-16** | [`A2-16-transfer-test-wallet-forbidden.png`](A2-16-transfer-test-wallet-forbidden.png) | Người gọi không sở hữu ví nguồn bị từ chối bằng HTTP `403 WALLET_FORBIDDEN`. |
| **A2-17** | [`A2-17-api-token-success.png`](A2-17-api-token-success.png) | Kiểm thử end-to-end `POST /token` bằng Postman trả HTTP `200` cùng access token. |
| **A2-18** | [`A2-18-api-transfer-success.png`](A2-18-api-transfer-success.png) | Kiểm thử end-to-end `POST /transfers` bằng Postman trả HTTP `201` cùng dữ liệu giao dịch. |
| **A2-19** | [`A2-19-api-gateway-routes.png`](A2-19-api-gateway-routes.png) | API Gateway HTTP API có hai route `POST /token` và `POST /transfers`; route transfer đã gắn integration và authorizer. |
| **A2-20** | [`A2-20-api-gateway-lambda-authorizer.png`](A2-20-api-gateway-lambda-authorizer.png) | Lambda Authorizer được gắn vào `POST /transfers`, sử dụng payload 2.0, simple response và header `Authorization`. |
| **A2-21** | [`A2-21-api-gateway-route-throttling.png`](A2-21-api-gateway-route-throttling.png) | Xác nhận route throttling: `/token` 2 RPS, burst 5; `/transfers` 10 RPS, burst 20. |
| **A2-22** | [`A2-22-sqs-dead-letter-queue.png`](A2-22-sqs-dead-letter-queue.png) | Hàng đợi SQS Standard `serverless-payment-dlq` đã được tạo tại `us-east-1` và bật mã hóa SSE-SQS. |

---

## Quy ước đặt tên

- Tiền tố `A2` xác định phần việc của Vũ Minh Đức trong Tuần 2.
- Hai chữ số tiếp theo thể hiện thứ tự minh chứng theo luồng triển khai và kiểm thử.
- Phần mô tả dùng chữ thường, phân tách bằng dấu gạch ngang và phản ánh trực tiếp nội dung ảnh.

## Tính xác thực

- Ảnh được chụp trực tiếp từ AWS Academy Learner Lab và Postman trong quá trình triển khai, kiểm thử.
- Ảnh gốc chỉ được đổi tên để chuẩn hóa danh mục; nội dung hình ảnh không bị chỉnh sửa.
