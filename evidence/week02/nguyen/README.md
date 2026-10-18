# DANH MỤC MINH CHỨNG THỰC HÀNH TUẦN 2 – NGUYỄN NGUYÊN

> **Học phần:** Cloud Computing (Điện toán đám mây) – Đợt 1, Năm học 2026–2027  
> **Dự án:** Cổng thanh toán giả lập không máy chủ (`serverless-payment`)  
> **Người thực hiện:** Nguyễn Nguyên  
> **Phạm vi trách nhiệm:** Hạ tầng AWS, CSDL DynamoDB, Secrets Manager, PyJWT Layer, Lambda Functions, API Gateway & SQS DLQ.  
> **Nền tảng:** AWS Academy Learner Lab · **Region:** `us-east-1` · **Account ID:** `930162821234`  
> **Thời điểm ghi nhận:** Ngày 18/10/2026  

---

## Danh mục ảnh chụp màn hình kiểm chứng (AWS Console & CLI)

Toàn bộ ảnh chụp màn hình được thực hiện trực tiếp trên giao diện AWS Management Console và terminal CloudShell/CLI, bảo đảm hiển thị đầy đủ **Account ID `930162821234`**, **Region `us-east-1`**, và **dấu mốc thời gian**:

| Mã | Tên tệp ảnh | Nội dung kiểm tra & Xác nhận kỹ thuật |
|:---:|---|---|
| **B2-01** | [`B2-01-secrets-manager.png`](B2-01-secrets-manager.png) | Khởi tạo thành công secret `serverless-payment/jwt-secret` trên AWS Secrets Manager lưu `jwtSigningKey` và `demoAccessCode`. |
| **B2-02** | [`B2-02-pyjwt-layer.png`](B2-02-pyjwt-layer.png) | Đóng gói và tạo thành công Lambda Layer `pyjwt-layer` (Python 3.12, PyJWT 2.10.1). |
| **B2-03** | [`B2-03-token-lambda.png`](B2-03-token-lambda.png) | Cấu hình hàm `serverless-payment-token` (Python 3.12, IAM `LabRole`, Memory 128 MB, gắn layer PyJWT). |
| **B2-04** | [`B2-04-token-test-success.png`](B2-04-token-test-success.png) | Test event `POST /token` hợp lệ trên Lambda Console, trả về HTTP 200 kèm `accessToken` (JWT HS256). |
| **B2-05** | [`B2-05-token-test-invalid.png`](B2-05-token-test-invalid.png) | Test event `POST /token` với mã `demoCode` không hợp lệ, hệ thống từ chối với HTTP 401 Unauthorized. |
| **B2-06** | [`B2-06-dynamodb-table.png`](B2-06-dynamodb-table.png) | Bảng DynamoDB `serverless-payment` được khởi tạo thành công ở chế độ On-Demand với Partition Key `PK` và Sort Key `SK`. |
| **B2-07** | [`B2-07-wallet-seed.png`](B2-07-wallet-seed.png) | Thực thi script `scripts/seed_wallets.py` trong AWS CloudShell nạp 4 ví mẫu (`W001` đến `W004`) vào DynamoDB. |
| **B2-08** | [`B2-08-authorizer-success.png`](B2-08-authorizer-success.png) | Test hàm `serverless-payment-authorizer` với JWT hợp lệ, trả về `isAuthorized: true` kèm `context.userId`. |
| **B2-09** | [`B2-09-authorizer-denied.png`](B2-09-authorizer-denied.png) | Test hàm `serverless-payment-authorizer` với JWT sai chữ ký / thiếu header, trả về `isAuthorized: false`. |
| **B2-10** | [`B2-10-transfer-lambda.png`](B2-10-transfer-lambda.png) | Cấu hình hàm `serverless-payment-transfer` với biến môi trường `TABLE_NAME=serverless-payment` và timeout phù hợp. |
| **B2-11** | [`B2-11-transfer-success.png`](B2-11-transfer-success.png) | Test chuyển tiền thành công 30.000 VND giữa 2 ví, DynamoDB thực thi 4 actions nguyên tử và trả về HTTP 201. |
| **B2-12** | [`B2-12-transfer-insufficient-funds.png`](B2-12-transfer-insufficient-funds.png) | Test chuyển tiền thất bại do số dư ví nguồn không đủ, hệ thống rollback an toàn và trả về HTTP 409 Conflict. |
| **B2-13** | [`B2-13-api-routes.png`](B2-13-api-routes.png) | Cấu hình các route trên Amazon API Gateway HTTP API v2: `POST /token` và `POST /transfers`. |
| **B2-14** | [`B2-14-api-authorizer.png`](B2-14-api-authorizer.png) | Tích hợp Lambda Authorizer (REQUEST mode, simple response) kiểm soát bảo mật cho route `POST /transfers`. |
| **B2-15** | [`B2-15-route-throttling.png`](B2-15-route-throttling.png) | Cấu hình Rate Limiting (Route Throttling: 2 RPS cho `/token`, 10 RPS cho `/transfers`) chống tấn công DoS. |
| **B2-16** | [`B2-16-sqs-dlq.png`](B2-16-sqs-dlq.png) | Khởi tạo thành công hàng đợi Amazon SQS Dead Letter Queue `serverless-payment-dlq` trong hạn mức Free Tier. |

---

## Tiêu chuẩn liêm chính học thuật
- Toàn bộ 16 ảnh minh chứng được chụp trực tiếp từ môi trường AWS Academy Learner Lab của sinh viên **Nguyễn Nguyên** trong ngày 18/10/2026.
- Không can thiệp chỉnh sửa dữ liệu số, dấu mốc thời gian hoặc cắt xén định danh tài khoản.
