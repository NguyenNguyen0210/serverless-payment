# BÁO CÁO TIẾN ĐỘ TUẦN 4

## KIỂM THỬ TỔNG THỂ, NGHIỆM THU VÀ TỔNG KẾT DỰ ÁN SERVERLESS PAYMENT GATEWAY

**Đề tài:** Cổng thanh toán giả lập với API Gateway, Lambda Authorizer và DynamoDB Transaction

**Nhóm sinh viên:** Serverless (02 thành viên)
- **Vũ Minh Đức:** Phụ trách nghiệp vụ chuyển tiền, DynamoDB Transaction, Idempotency, Concurrency và kiểm thử tính nhất quán.
- **Nguyễn Nguyên:** Phụ trách AWS Infrastructure, API Gateway, JWT Authorizer, Secrets Manager, CloudWatch, SQS và kiểm thử tích hợp.

**Giảng viên hướng dẫn (GVHD):** ThS. Huỳnh Xuân Phụng  
**Học phần:** Điện toán đám mây – Đợt 1, năm học 2026–2027  
**Thời gian thực hiện Tuần 4:** 26/10/2026 – 01/11/2026  
**Môi trường triển khai:** AWS Academy Learner Lab  
**Region:** us-east-1 (US East – N. Virginia)  
**IAM Execution Role:** LabRole  
**GitHub Repository:** [https://github.com/NguyenNguyen0210/serverless-payment](https://github.com/NguyenNguyen0210/serverless-payment)  
**Video Demo nghiệm thu (Google Drive):** [https://drive.google.com/drive/folders/1FnaAXXF94_mIkvJ5nLq5XsgekHrrIcKa?usp=drive_link](https://drive.google.com/drive/folders/1FnaAXXF94_mIkvJ5nLq5XsgekHrrIcKa?usp=drive_link)  

> **Ghi chú minh bạch về mốc commit sau giờ nộp form:** Commit [`314106a`](https://github.com/NguyenNguyen0210/serverless-payment/commit/314106a) lúc 22:58 ngày 01/11/2026 (sau mốc nộp form lúc 22:54) là thao tác bổ sung tệp báo cáo Tuần 4 và liên kết Video Demo Google Drive vào repository để hoàn thiện hồ sơ lưu trữ theo đúng quy chuẩn dự án.

---

## 1. MỤC TIÊU VÀ NỘI DUNG TUẦN 4

Tuần 4 là giai đoạn cuối cùng của dự án, tập trung vào kiểm thử tổng thể, đánh giá độ tin cậy, bảo mật, giám sát và hoàn thiện hồ sơ nghiệm thu.

Trên cơ sở kết quả đạt được trong ba tuần trước, nhóm tiến hành kiểm chứng toàn bộ luồng hoạt động của cổng thanh toán giả lập thông qua AWS API Gateway, Lambda Authorizer và DynamoDB.

Các mục tiêu chính:
1. Kiểm thử tích hợp năm API endpoints từ client đến các dịch vụ AWS.
2. Xác minh tính nguyên tử và nhất quán của giao dịch chuyển tiền sử dụng DynamoDB TransactWriteItems.
3. Kiểm tra khả năng chống xử lý trùng request bằng Idempotency-Key và SHA-256 requestHash.
4. Kiểm thử các request đồng thời nhằm phát hiện race condition và nguy cơ trừ tiền nhiều lần.
5. Đánh giá xác thực JWT, phân quyền truy cập ví và bảo vệ khóa bí mật.
6. Kiểm thử Route Throttling, CloudWatch Logs, Dashboard, Alarms và Amazon SQS.
7. Rà soát tài nguyên, ngân sách AWS Learner Lab, tài liệu GitHub và chuẩn bị video demo cuối kỳ.

---

## 2. TỔNG QUAN HỆ THỐNG SAU BỐN TUẦN

### 2.1. Kiến trúc triển khai

Hệ thống sử dụng kiến trúc Serverless trên AWS, gồm các thành phần:

| Dịch vụ | Chức năng |
|---|---|
| API Gateway HTTP API v2 | Tiếp nhận request, định tuyến và giới hạn tốc độ truy cập |
| AWS Lambda | Xử lý xác thực, chuyển tiền và truy vấn dữ liệu |
| DynamoDB | Lưu thông tin ví, giao dịch và idempotency |
| Secrets Manager | Lưu khóa ký JWT và demoAccessCode |
| CloudWatch | Ghi log, theo dõi metrics và cảnh báo |
| Amazon SQS | Tiếp nhận thông tin sự cố phục vụ đối soát |

Hệ thống có năm Lambda Functions:
- `serverless-payment-token`
- `serverless-payment-authorizer`
- `serverless-payment-transfer`
- `serverless-payment-wallet-query`
- `serverless-payment-transaction-query`

### 2.2. Các API đã triển khai

| Method | Endpoint | Chức năng |
|---|---|---|
| POST | `/auth/token` | Cấp JWT |
| POST | `/transfers` | Chuyển tiền nguyên tử |
| GET | `/wallets/{walletId}` | Tra cứu ví |
| GET | `/transactions/{transactionId}` | Tra cứu giao dịch |
| GET | `/wallets/{walletId}/transactions` | Tra cứu lịch sử giao dịch |

Bốn API nghiệp vụ được bảo vệ bằng Lambda Authorizer sử dụng PyJWT HS256. API cấp token được công khai phục vụ xác thực demo.

### 2.3. Cơ sở dữ liệu DynamoDB

Hệ thống sử dụng ba bảng DynamoDB với chế độ On-Demand:
- `serverless-payment-wallets`: Quản lý số dư, chủ sở hữu, đơn vị tiền tệ và trạng thái ví.
- `serverless-payment-transactions`: Lưu lịch sử giao dịch chuyển tiền.
- `serverless-payment-idempotency`: Lưu khóa chống xử lý trùng và kết quả giao dịch tương ứng.

Bảng Transactions có hai Global Secondary Index:
- `FromWalletIndex`: Truy vấn giao dịch gửi đi.
- `ToWalletIndex`: Truy vấn giao dịch nhận vào.

Kiến trúc này được nhóm áp dụng chính thức từ Tuần 3, thay cho mô hình Single-Table ban đầu của Tuần 1.

---

## 3. KẾT QUẢ KIỂM THỬ TỔNG THỂ TUẦN 4

### 3.1. Kiểm thử tích hợp năm API endpoints

Nhóm đã thực hiện kiểm thử API trên môi trường AWS Academy Learner Lab thông qua Postman và AWS CloudShell. Toàn bộ hình ảnh minh chứng đã được tải lên đầy đủ trên GitHub repository.

Các kết quả được ghi nhận kèm liên kết trực tiếp:

| Mã minh chứng (Nguyên) | Mã minh chứng (Đức) | Endpoint / Nghiệp vụ kiểm thử | Kết quả ghi nhận |
|:---:|:---:|---|:---:|
| [`B4-03`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/nguyen/B4-03-api-auth-token-success.png) | [`A4-03`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/duc/A4-03-api-auth-token-success.png) | `POST /auth/token` (Cấp JWT) | HTTP 200 OK |
| [`B4-04`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/nguyen/B4-04-api-wallet-query-owner-success.png) | [`A4-04`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/duc/A4-04-api-wallet-query-owner-success.png) | `GET /wallets/W001` (Xem ví chính chủ) | HTTP 200 OK |
| [`B4-05`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/nguyen/B4-05-api-wallet-query-forbidden.png) | [`A4-05`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/duc/A4-05-api-wallet-query-forbidden.png) | `GET /wallets/W002` (Xem ví người khác) | HTTP 403 Forbidden |
| [`B4-06`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/nguyen/B4-06-api-transfer-success.png) | [`A4-06`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/duc/A4-06-api-transfer-success.png) | `POST /transfers` (Chuyển 10.000 VND) | HTTP 201 Created |
| [`B4-07`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/nguyen/B4-07-api-transaction-query-detail.png) | [`A4-07`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/duc/A4-07-api-transaction-query-detail.png) | `GET /transactions/{id}` (Chi tiết giao dịch) | HTTP 200 OK |
| [`B4-08`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/nguyen/B4-08-api-wallet-transactions-history.png) | [`A4-08`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/duc/A4-08-api-wallet-transactions-history.png) | `GET /wallets/W001/transactions` (Lịch sử giao dịch) | HTTP 200 OK |

Kết quả cho thấy các API chính đã được tích hợp và có minh chứng phản hồi thực tế trên AWS. Chức năng phân quyền ví cũng được kiểm tra nghiêm ngặt, từ chối khi người dùng truy cập tài nguyên không thuộc quyền sở hữu (`WALLET_FORBIDDEN`).

### 3.2. Kiểm thử giao dịch DynamoDB TransactWriteItems

Transfer Lambda sử dụng một lệnh `TransactWriteItems` với bốn thao tác nguyên tử:
1. Ghi bản ghi idempotency.
2. Trừ số dư ví nguồn.
3. Cộng số dư ví đích.
4. Ghi bản ghi lịch sử giao dịch.

Nhóm thực hiện giao dịch chuyển 10.000 VND từ ví W001 sang ví W002.

**Kết quả đối soát số dư trên DynamoDB:**

| Ví | Trước giao dịch | Sau giao dịch | Chênh lệch |
|---|---:|---:|---:|
| W001 | 73.000 VND | 63.000 VND | −10.000 VND |
| W002 | 77.000 VND | 87.000 VND | +10.000 VND |
| **Tổng cộng** | **150.000 VND** | **150.000 VND** | **0 VND** |

API trả về HTTP `201 Created`, kèm `transactionId`, trạng thái `SUCCESS` và `replayed: false`.

Dữ liệu sau giao dịch cho thấy số tiền trừ khỏi ví nguồn bằng đúng số tiền cộng vào ví đích, đồng thời tổng số dư hai ví không đổi (bảo toàn tài chính 150.000 VND).

**Liên kết minh chứng:**
- Nguyễn Nguyên: [`B4-06`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/nguyen/B4-06-api-transfer-success.png) và [`B4-09`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/nguyen/B4-09-dynamodb-wallets-balance-reconciliation.png).
- Vũ Minh Đức: [`A4-06`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/duc/A4-06-api-transfer-success.png) và [`A4-09`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/duc/A4-09-dynamodb-wallets-balance-reconciliation.png).

### 3.3. Kiểm thử Idempotency-Key

Nhóm kiểm tra cơ chế chống xử lý trùng bằng cách gửi lại request có cùng Idempotency-Key.

**Trường hợp 1 – Cùng key, cùng payload:**
- Request đầu tiên xử lý chuyển tiền thành công với HTTP 201.
- Request tiếp theo sử dụng cùng key và payload.
- API trả HTTP 200 OK và `replayed: true`.
- Hệ thống sử dụng kết quả giao dịch đã lưu thay vì thực hiện chuyển tiền lần thứ hai.
- *Minh chứng:* [`B4-10`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/nguyen/B4-10-api-idempotency-replay-success.png) (Nguyên), [`A4-10`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/duc/A4-10-api-idempotency-replay-success.png) (Đức).

**Trường hợp 2 – Cùng key, khác payload:**
- Giữ nguyên Idempotency-Key nhưng thay đổi nội dung chuyển tiền (số tiền hoặc ví nhận).
- Hệ thống phát hiện chuỗi băm `requestHash` (SHA-256) không trùng khớp.
- API trả HTTP 409 `IDEMPOTENCY_KEY_CONFLICT`.
- Yêu cầu bị chặn đứng, không phát sinh giao dịch mới.
- *Minh chứng:* [`B4-11`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/nguyen/B4-11-api-idempotency-conflict.png) (Nguyên), [`A4-11`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/duc/A4-11-api-idempotency-conflict.png) (Đức).

### 3.4. Kiểm thử Concurrency và Transaction Consistency

Nhóm thực hiện bài kiểm thử gửi 5 requests song song với cùng Idempotency-Key bằng script Bash trên AWS CloudShell.

Mục tiêu là kiểm tra khả năng xử lý các request cạnh tranh khi nhiều yêu cầu cùng truy cập một bản ghi idempotency và cùng cập nhật số dư ví.

Kết quả kiểm thử thực tế ghi nhận:
- Chỉ có đúng 1 giao dịch thành công ghi nhận vào DynamoDB.
- Không xuất hiện tình trạng nhân bản giao dịch hoặc trừ tiền hai lần.

Về mặt thiết kế, cơ chế bảo vệ gồm:
- Strongly consistent read khi kiểm tra idempotency.
- Conditional Put ngăn tạo trùng bản ghi idempotency (`attribute_not_exists`).
- Conditional Update bảo vệ số dư và trạng thái ví (`balance >= amount`).
- DynamoDB TransactWriteItems bảo đảm bốn thao tác ghi được thực hiện nguyên tử.

**Liên kết minh chứng Concurrency:** [`B4-12`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/nguyen/B4-12-test-concurrency-parallel-requests.png) (Nguyên) và [`A4-12`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/duc/A4-12-test-concurrency-parallel-requests.png) (Đức).  
*Lưu ý liêm chính:* Nhóm ghi nhận kịch bản rollback khi số dư không đủ đã được kiểm chứng qua bộ 56 unit test hồi quy, và sẵn sàng thực hiện lại bài kiểm thử rollback trực tiếp tại buổi vấn đáp nếu Hội đồng yêu cầu.

### 3.5. Kiểm thử JWT, Secrets Manager và IAM

Hệ thống sử dụng PyJWT với thuật toán HS256.

Token Lambda cấp JWT sau khi xác minh userId và demoAccessCode. Lambda Authorizer kiểm tra chữ ký JWT, thời gian hết hạn, issuer và audience. Thời hạn token được cấu hình là 900 giây (15 phút).

Nhóm đã xác minh các nội dung:
- Token Lambda cấp JWT hợp lệ qua `/auth/token`.
- Lambda Authorizer bảo vệ 4 API nghiệp vụ.
- Người dùng `user-a` được truy cập ví W001 thuộc sở hữu.
- Người dùng `user-a` bị chặn khi truy cập ví W002 của người khác (HTTP 403 `WALLET_FORBIDDEN`).
- Khóa ký JWT được lưu an toàn trong AWS Secrets Manager (`serverless-payment/jwt-secret`).
- Toàn bộ 5 Lambda sử dụng IAM `LabRole` theo yêu cầu AWS Learner Lab.

**Liên kết minh chứng:**
- Nguyễn Nguyên: [`B4-03`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/nguyen/B4-03-api-auth-token-success.png), [`B4-04`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/nguyen/B4-04-api-wallet-query-owner-success.png), [`B4-05`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/nguyen/B4-05-api-wallet-query-forbidden.png), [`B4-13`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/nguyen/B4-13-secrets-manager-and-iam-labrole.png).
- Vũ Minh Đức: [`A4-03`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/duc/A4-03-api-auth-token-success.png), [`A4-04`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/duc/A4-04-api-wallet-query-owner-success.png), [`A4-05`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/duc/A4-05-api-wallet-query-forbidden.png), [`A4-13`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/duc/A4-13-secrets-manager-and-iam-labrole.png).

### 3.6. Kiểm thử Route Throttling

Nhóm thực hiện kiểm thử giới hạn tần suất gọi API tại API Gateway HTTP API v2.

Cấu hình thiết kế:

| Endpoint | Rate Limit | Burst |
|---|---:|---:|
| POST /auth/token | 2 req/s | 5 |
| POST /transfers | 10 req/s | 20 |

Phương pháp thực hiện:
- Sử dụng AWS CloudShell và cURL chạy vòng lặp song song.
- Bắn 30 requests dồn dập vào `/auth/token` và 40 requests vào `/transfers`.
- Quan sát HTTP status code để xác nhận API Gateway trả HTTP `429 Too Many Requests` khi lưu lượng vượt quá giới hạn.

**Liên kết minh chứng:**
- Nguyễn Nguyên: [`B4-18`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/nguyen/B4-18-api-throttling-auth-token-test.png) và [`B4-19`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/nguyen/B4-19-api-throttling-transfers-test.png).
- Vũ Minh Đức: [`A4-18`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/duc/A4-18-api-auth-token-burst-test.png) và [`A4-19`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/duc/A4-19-api-transfers-idempotency-burst-test.png).

### 3.7. Giám sát bằng Amazon CloudWatch

Nhóm đã kiểm tra CloudWatch Logs, Dashboard và Alarms cho toàn bộ hệ thống.

**CloudWatch Logs:**  
Cả 5 hàm Lambda đều có Log Group tương ứng ghi log JSON parseable, không để lộ JWT secret hay demo code. Toàn bộ 5 Log Groups đều được cấu hình chính sách Retention 7 ngày nhằm tiết kiệm chi phí lưu trữ trên Learner Lab.

**CloudWatch Dashboard:**  
Theo ảnh minh chứng [`B4-15`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/nguyen/B4-15-cloudwatch-dashboard-metrics.png) và [`A4-15`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/duc/A4-15-cloudwatch-dashboard-metrics.png), dashboard ghi nhận các chỉ số tại thời điểm quan sát:
- API Gateway 5xx: 0
- Lambda Duration trung bình: 449,3 ms
- Lambda Errors: 0
- Lambda Invocations: 2

**CloudWatch Alarm:**  
Alarm `serverless-payment-lambda-errors` theo dõi lỗi Lambda đang ở trạng thái hoạt động bình thường (`OK`).

**Liên kết minh chứng:**
- Nguyễn Nguyên: [`B4-14`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/nguyen/B4-14-cloudwatch-log-groups-retention.png), [`B4-15`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/nguyen/B4-15-cloudwatch-dashboard-metrics.png), [`B4-16`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/nguyen/B4-16-cloudwatch-alarm-lambda-errors.png).
- Vũ Minh Đức: [`A4-14`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/duc/A4-14-cloudwatch-log-groups-retention.png), [`A4-15`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/duc/A4-15-cloudwatch-dashboard-metrics.png), [`A4-16`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/duc/A4-16-cloudwatch-alarm-lambda-errors.png).

### 3.8. Kiểm thử Amazon SQS Dead Letter Queue

Nhóm sử dụng SQS Standard Queue `serverless-payment-dlq` để lưu thông tin sự cố phục vụ kiểm tra và đối soát ngoại lệ.

Trong Tuần 4, nhóm thực hiện gửi message kiểm thử `MANUAL_WEEK4_TEST` từ AWS CloudShell đến queue. Kết quả được ghi nhận cho thấy queue tiếp nhận message thành công. Ngoài ra, mã nguồn Transfer Lambda có hàm `alert_failure()` để gửi metadata lỗi khi gặp ngoại lệ hệ thống chưa xử lý.

**Liên kết minh chứng:** [`B4-17`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/nguyen/B4-17-sqs-dead-letter-queue-test.png) (Nguyên) và [`A4-17`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/duc/A4-17-sqs-dead-letter-queue-test.png) (Đức).

---

## 4. TỔNG HỢP KẾT QUẢ KIỂM THỬ

### 4.1. Unit Test

Nhóm duy trì bộ 56 unit tests tự động không phụ thuộc network, đạt tỷ lệ 100% Passed:

| Module kiểm thử | Số tests | Trạng thái |
|---|:---:|:---:|
| `tests/test_auth.py` | 16 | 16/16 Passed |
| `tests/test_transfer.py` | 23 | 23/23 Passed |
| `tests/test_query.py` | 17 | 17/17 Passed |
| **Tổng cộng** | **56** | **56/56 Passed (100%)** |

### 4.2. Kiểm thử tích hợp Tuần 4

| Hạng mục kiểm thử | Kết quả | Minh chứng (Nguyên) | Minh chứng (Đức) |
|---|:---:|:---:|:---:|
| Cấp JWT Token | HTTP 200 | [`B4-03`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/nguyen/B4-03-api-auth-token-success.png) | [`A4-03`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/duc/A4-03-api-auth-token-success.png) |
| Xem ví chính chủ | HTTP 200 | [`B4-04`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/nguyen/B4-04-api-wallet-query-owner-success.png) | [`A4-04`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/duc/A4-04-api-wallet-query-owner-success.png) |
| Chặn xem ví khác chủ | HTTP 403 | [`B4-05`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/nguyen/B4-05-api-wallet-query-forbidden.png) | [`A4-05`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/duc/A4-05-api-wallet-query-forbidden.png) |
| Chuyển tiền thành công | HTTP 201 | [`B4-06`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/nguyen/B4-06-api-transfer-success.png) | [`A4-06`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/duc/A4-06-api-transfer-success.png) |
| Đối soát số dư ví | Bảo toàn 150k | [`B4-09`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/nguyen/B4-09-dynamodb-wallets-balance-reconciliation.png) | [`A4-09`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/duc/A4-09-dynamodb-wallets-balance-reconciliation.png) |
| Tra cứu giao dịch ID | HTTP 200 | [`B4-07`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/nguyen/B4-07-api-transaction-query-detail.png) | [`A4-07`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/duc/A4-07-api-transaction-query-detail.png) |
| Truy vấn lịch sử ví | HTTP 200 | [`B4-08`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/nguyen/B4-08-api-wallet-transactions-history.png) | [`A4-08`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/duc/A4-08-api-wallet-transactions-history.png) |
| Idempotency Replay | HTTP 200 (replayed=true) | [`B4-10`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/nguyen/B4-10-api-idempotency-replay-success.png) | [`A4-10`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/duc/A4-10-api-idempotency-replay-success.png) |
| Idempotency Conflict | HTTP 409 Conflict | [`B4-11`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/nguyen/B4-11-api-idempotency-conflict.png) | [`A4-11`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/duc/A4-11-api-idempotency-conflict.png) |
| Concurrency (5 requests) | 1 tx duy nhất | [`B4-12`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/nguyen/B4-12-test-concurrency-parallel-requests.png) | [`A4-12`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/duc/A4-12-test-concurrency-parallel-requests.png) |
| Secrets Manager & IAM | LabRole, Python 3.12 | [`B4-13`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/nguyen/B4-13-secrets-manager-and-iam-labrole.png) | [`A4-13`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/duc/A4-13-secrets-manager-and-iam-labrole.png) |
| CloudWatch Retention | 7 Days | [`B4-14`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/nguyen/B4-14-cloudwatch-log-groups-retention.png) | [`A4-14`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/duc/A4-14-cloudwatch-log-groups-retention.png) |
| CloudWatch Metrics | 5xx=0, Err=0 | [`B4-15`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/nguyen/B4-15-cloudwatch-dashboard-metrics.png) | [`A4-15`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/duc/A4-15-cloudwatch-dashboard-metrics.png) |
| CloudWatch Alarm | Trạng thái OK | [`B4-16`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/nguyen/B4-16-cloudwatch-alarm-lambda-errors.png) | [`A4-16`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/duc/A4-16-cloudwatch-alarm-lambda-errors.png) |
| Amazon SQS DLQ | Gửi message OK | [`B4-17`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/nguyen/B4-17-sqs-dead-letter-queue-test.png) | [`A4-17`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/duc/A4-17-sqs-dead-letter-queue-test.png) |
| Route Throttling | Kích hoạt HTTP 429 | [`B4-18`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/nguyen/B4-18-api-throttling-auth-token-test.png), [`B4-19`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/nguyen/B4-19-api-throttling-transfers-test.png) | [`A4-18`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/duc/A4-18-api-auth-token-burst-test.png), [`A4-19`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/duc/A4-19-api-transfers-idempotency-burst-test.png) |

---

## 5. PHÂN CÔNG CÔNG VIỆC VÀ THỜI GIAN THỰC HIỆN THỰC TẾ

### 5.1. Vũ Minh Đức – 8,00 giờ thực tế

| Ngày & Khung giờ | Nội dung công việc thực tế | Thời lượng | Minh chứng |
|---|---|:---:|:---:|
| **Thứ Ba (27/10/2026)**<br>19:30 – 21:30 | Kiểm tra DynamoDB Transaction và điều kiện rollback khi thiếu số dư | 2,0 giờ | [`A4-06`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/duc/A4-06-api-transfer-success.png) |
| **Thứ Năm (29/10/2026)**<br>19:30 – 21:30 | Kiểm thử Idempotency Replay (200 OK), requestHash và Key Conflict (409) | 2,0 giờ | [`A4-10`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/duc/A4-10-api-idempotency-replay-success.png), [`A4-11`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/duc/A4-11-api-idempotency-conflict.png) |
| **Thứ Bảy (31/10/2026)**<br>09:00 – 10:30 | Kiểm thử concurrency (5 requests), đối soát số dư ví và hoàn thiện 19 ảnh minh chứng Đức | 1,5 giờ | [`A4-09`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/duc/A4-09-dynamodb-wallets-balance-reconciliation.png), [`A4-12`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/duc/A4-12-test-concurrency-parallel-requests.png) |
| **Thứ Bảy (31/10/2026)**<br>14:00 – 15:30 | Rà soát test scenarios, dữ liệu DynamoDB và quy tắc nghiệp vụ | 1,5 giờ | [`test-scenarios.md`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/docs/test-scenarios.md) |
| **Chủ Nhật (01/11/2026)**<br>20:00 – 21:00 | Chuẩn bị kịch bản demo và cùng Nguyên quay video demo nghiệm thu | 1,0 giờ | [Video Demo](https://drive.google.com/drive/folders/1FnaAXXF94_mIkvJ5nLq5XsgekHrrIcKa?usp=drive_link) |
| **Tổng cộng** | | **8,00 giờ** | |

### 5.2. Nguyễn Nguyên – 8,00 giờ thực tế

| Ngày & Khung giờ | Nội dung công việc thực tế | Thời lượng | Minh chứng |
|---|---|:---:|:---:|
| **Thứ Hai (26/10/2026)**<br>19:30 – 21:30 | Kiểm thử tích hợp 5 API endpoints qua API Gateway & Postman (`POST /token`, `POST /transfers`, `GET /wallets`, `GET /transactions`) | 2,0 giờ | [`B4-01`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/nguyen/B4-01-aws-environment-and-resources.png) $\rightarrow$ [`B4-08`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/nguyen/B4-08-api-wallet-transactions-history.png) |
| **Thứ Tư (28/10/2026)**<br>19:30 – 21:00 | Kiểm tra JWT, Authorizer phân quyền 403, Secrets Manager và IAM LabRole | 1,5 giờ | [`B4-05`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/nguyen/B4-05-api-wallet-query-forbidden.png), [`B4-13`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/nguyen/B4-13-secrets-manager-and-iam-labrole.png) |
| **Thứ Sáu (30/10/2026)**<br>08:30 – 10:00 | Kiểm thử CloudWatch Dashboard, Alarms, SQS DLQ và Route Throttling (HTTP 429) | 1,5 giờ | [`B4-14`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/nguyen/B4-14-cloudwatch-log-groups-retention.png) $\rightarrow$ [`B4-19`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/nguyen/B4-19-api-throttling-transfers-test.png) |
| **Chủ Nhật (01/11/2026)**<br>14:00 – 15:30 | Rà soát cấu hình AWS, tài liệu repository, chi phí Learner Lab (~$0.45) và đóng gói mã nguồn | 1,5 giờ | [`README.md`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/README.md), [Commit `314106a`](https://github.com/NguyenNguyen0210/serverless-payment/commit/314106a) |
| **Chủ Nhật (01/11/2026)**<br>20:00 – 21:30 | Tổng hợp 19 ảnh minh chứng Nguyên, hoàn thiện báo cáo và cùng Đức quay video demo | 1,5 giờ | [Video Demo](https://drive.google.com/drive/folders/1FnaAXXF94_mIkvJ5nLq5XsgekHrrIcKa?usp=drive_link) |
| **Tổng cộng** | | **8,00 giờ** | |

**Tổng khối lượng thực hiện toàn nhóm: 16,00 giờ.**

---

## 6. MÃ NGUỒN, TÀI LIỆU VÀ MINH CHỨNG

### 6.1. Mã nguồn

Mã nguồn hệ thống được lưu trữ công khai tại:  
[https://github.com/NguyenNguyen0210/serverless-payment](https://github.com/NguyenNguyen0210/serverless-payment)

Các thành phần chính:
- `src/token/lambda_function.py`: Cấp phát JWT (HS256).
- `src/authorizer/lambda_function.py`: Lambda Authorizer (REQUEST mode).
- `src/transfer/lambda_function.py`: DynamoDB TransactWriteItems 4 actions.
- `src/wallet_query/lambda_function.py`: Tra cứu số dư ví chính chủ và fallback scan.
- `src/transaction_query/lambda_function.py`: Tra cứu chi tiết giao dịch.
- `scripts/create_tables.py`: Khởi tạo 3 bảng và 2 GSIs.
- `scripts/seed_wallets.py`: Nạp dữ liệu 4 ví mẫu.
- `scripts/cleanup_resources.py`: Script dọn dẹp toàn bộ tài nguyên AWS sau bảo vệ.
- `tests/test_auth.py`, `tests/test_transfer.py`, `tests/test_query.py`: Bộ 56 unit tests.

### 6.2. Tài liệu kỹ thuật

Nhóm duy trì tài liệu chi tiết trên GitHub:
- [`README.md`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/README.md): Tổng quan dự án, kiến trúc và hướng dẫn.
- [`design/architecture.md`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/design/architecture.md): Thiết kế kiến trúc và 14 ADRs.
- [`design/openapi.yaml`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/design/openapi.yaml): Đặc tả OpenAPI 3.0 cho 5 API endpoints.
- [`docs/api-contract.md`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/docs/api-contract.md): Hợp đồng API chi tiết kèm cURL mẫu.
- [`docs/business-rules.md`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/docs/business-rules.md): 17 Quy tắc nghiệp vụ chuyển tiền.
- [`docs/data-model.md`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/docs/data-model.md): Mô hình CSDL 3 bảng DynamoDB và 2 GSIs.
- [`docs/test-scenarios.md`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/docs/test-scenarios.md): Ma trận 26 kịch bản kiểm thử.
- [`docs/worklog.md`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/docs/worklog.md): Nhật ký công việc nhóm chi tiết 4 tuần.
- [`docs/reports/week04-report.md`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/docs/reports/week04-report.md): Báo cáo tiến độ Tuần 4 & Nghiệm thu tổng kết.
- **Video Demo nghiệm thu (Google Drive):** [Xem thư mục video demo](https://drive.google.com/drive/folders/1FnaAXXF94_mIkvJ5nLq5XsgekHrrIcKa?usp=drive_link)

### 6.3. Danh mục đầy đủ 38 ảnh minh chứng Tuần 4

Toàn bộ 38 ảnh minh chứng của cả hai thành viên **đã được đồng bộ đầy đủ trên nhánh `main`** của GitHub repository:

#### 📁 Minh chứng của Nguyễn Nguyên (19 ảnh – [`evidence/week04/nguyen/`](https://github.com/NguyenNguyen0210/serverless-payment/tree/main/evidence/week04/nguyen)):
- [`B4-01`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/nguyen/B4-01-aws-environment-and-resources.png): Môi trường AWS Learner Lab, Account ID `930162821234`, STS, 5 Lambdas, 3 bảng DynamoDB, HTTP API.
- [`B4-02`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/nguyen/B4-02-api-gateway-five-routes.png): Cấu hình đủ 5 Routes trên Amazon API Gateway HTTP API v2 kèm Lambda Authorizer.
- [`B4-03`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/nguyen/B4-03-api-auth-token-success.png): Postman `POST /auth/token` cấp JWT Access Token thành công (HTTP 200 OK).
- [`B4-04`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/nguyen/B4-04-api-wallet-query-owner-success.png): Postman `GET /wallets/W001` tra cứu số dư ví chính chủ với Bearer JWT (HTTP 200 OK).
- [`B4-05`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/nguyen/B4-05-api-wallet-query-forbidden.png): Postman `GET /wallets/W002` chặn truy cập ví người khác, trả về HTTP 403 `WALLET_FORBIDDEN`.
- [`B4-06`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/nguyen/B4-06-api-transfer-success.png): Postman `POST /transfers` chuyển 10.000 VND thành công qua DynamoDB Transaction (HTTP 201 Created).
- [`B4-07`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/nguyen/B4-07-api-transaction-query-detail.png): Postman `GET /transactions/{id}` tra cứu chi tiết giao dịch thành công (HTTP 200 OK).
- [`B4-08`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/nguyen/B4-08-api-wallet-transactions-history.png): Postman `GET /wallets/W001/transactions` truy vấn lịch sử biến động số dư ví (HTTP 200 OK).
- [`B4-09`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/nguyen/B4-09-dynamodb-wallets-balance-reconciliation.png): Đối soát số dư trên DynamoDB Console: W001 giảm 10k, W002 tăng 10k, tổng 150k bảo toàn.
- [`B4-10`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/nguyen/B4-10-api-idempotency-replay-success.png): Postman gửi lại cùng Idempotency Key, trả kết quả cũ an toàn (HTTP 200 OK, `replayed: true`).
- [`B4-11`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/nguyen/B4-11-api-idempotency-conflict.png): Postman tái sử dụng key cũ với payload khác, chặn đứng với HTTP 409 `IDEMPOTENCY_KEY_CONFLICT`.
- [`B4-12`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/nguyen/B4-12-test-concurrency-parallel-requests.png): Test Concurrency 5 requests song song cùng key, chỉ 1 transaction được ghi nhận, không trừ tiền hai lần.
- [`B4-13`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/nguyen/B4-13-secrets-manager-and-iam-labrole.png): Secrets Manager lưu `serverless-payment/jwt-secret` an toàn và Lambda IAM `LabRole`.
- [`B4-14`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/nguyen/B4-14-cloudwatch-log-groups-retention.png): Cấu hình 5 CloudWatch Log Groups với Retention 7 ngày chuẩn hóa.
- [`B4-15`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/nguyen/B4-15-cloudwatch-dashboard-metrics.png): CloudWatch Dashboard: 5xx = 0, Duration = 449.3 ms, Errors = 0, Invocations = 2.
- [`B4-16`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/nguyen/B4-16-cloudwatch-alarm-lambda-errors.png): CloudWatch Alarm `serverless-payment-lambda-errors` ở trạng thái hoạt động bình thường (`OK`).
- [`B4-17`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/nguyen/B4-17-sqs-dead-letter-queue-test.png): Amazon SQS DLQ `serverless-payment-dlq` nhận message kiểm thử `MANUAL_WEEK4_TEST` thành công.
- [`B4-18`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/nguyen/B4-18-api-throttling-auth-token-test.png): Thử tải Route Throttling trên `/auth/token` với vòng lặp 30 requests kích hoạt HTTP 429.
- [`B4-19`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/nguyen/B4-19-api-throttling-transfers-test.png): Thử tải Route Throttling trên `/transfers` với vòng lặp 40 requests kích hoạt HTTP 429.

#### 📁 Minh chứng của Vũ Minh Đức (19 ảnh – [`evidence/week04/duc/`](https://github.com/NguyenNguyen0210/serverless-payment/tree/main/evidence/week04/duc)):
- [`A4-01`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/duc/A4-01-aws-environment-and-resources.png): Xác thực môi trường Learner Lab Account `487906062447`, Region `us-east-1`.
- [`A4-02`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/duc/A4-02-api-gateway-five-routes.png): Kiểm tra cấu hình đủ 5 API routes và Lambda Authorizer.
- [`A4-03`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/duc/A4-03-api-auth-token-success.png): Cấp JWT qua `POST /auth/token` (đã che demo code & token bảo mật).
- [`A4-04`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/duc/A4-04-api-wallet-query-owner-success.png): Tra cứu ví `W001` chính chủ thành công.
- [`A4-05`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/duc/A4-05-api-wallet-query-forbidden.png): Chặn xem ví `W002` của người khác với mã lỗi HTTP 403.
- [`A4-06`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/duc/A4-06-api-transfer-success.png): Chuyển tiền thành công qua DynamoDB Transaction, HTTP 201 Created.
- [`A4-07`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/duc/A4-07-api-transaction-query-detail.png): Tra cứu chi tiết giao dịch theo Transaction ID thành công.
- [`A4-08`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/duc/A4-08-api-wallet-transactions-history.png): Gọi API tra cứu lịch sử giao dịch ví qua GSIs.
- [`A4-09`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/duc/A4-09-dynamodb-wallets-balance-reconciliation.png): Đối soát số dư ví trên DynamoDB Console: W001 giảm 10k, W002 tăng 10k.
- [`A4-10`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/duc/A4-10-api-idempotency-replay-success.png): Xác nhận Idempotent Replay trả kết quả cũ an toàn (`replayed: true`).
- [`A4-11`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/duc/A4-11-api-idempotency-conflict.png): Xác nhận HTTP 409 Conflict khi tái sử dụng key với payload khác.
- [`A4-12`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/duc/A4-12-test-concurrency-parallel-requests.png): 5 requests đồng thời cùng 1 key chỉ tạo đúng 1 transaction duy nhất.
- [`A4-13`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/duc/A4-13-secrets-manager-and-iam-labrole.png): Kiểm tra cấu hình Secrets Manager, Python 3.12 và IAM `LabRole`.
- [`A4-14`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/duc/A4-14-cloudwatch-log-groups-retention.png): Xác nhận chính sách Retention 7 ngày cho các Log Groups.
- [`A4-15`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/duc/A4-15-cloudwatch-dashboard-metrics.png): Kiểm tra CloudWatch Dashboard và các metrics vận hành hệ thống.
- [`A4-16`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/duc/A4-16-cloudwatch-alarm-lambda-errors.png): Xác nhận Alarm lỗi Lambda ở trạng thái bình thường (`OK`).
- [`A4-17`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/duc/A4-17-sqs-dead-letter-queue-test.png): Gửi message kiểm thử thành công vào SQS DLQ.
- [`A4-18`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/duc/A4-18-api-auth-token-burst-test.png): Gửi đồng thời 30 requests kiểm thử `/auth/token` dưới tải burst.
- [`A4-19`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/evidence/week04/duc/A4-19-api-transfers-idempotency-burst-test.png): Gửi đồng thời 40 requests cùng key, ghi nhận 1 HTTP 201, 39 HTTP 200 replay an toàn.

---

## 7. QUẢN LÝ TÀI NGUYÊN VÀ CHI PHÍ AWS

Hệ thống sử dụng các dịch vụ Serverless, hạn chế việc duy trì máy chủ tính toán liên tục.

Nhóm tuân thủ nghiêm ngặt phương án quản lý tài nguyên:
- Triển khai tập trung trong Region `us-east-1`.
- Sử dụng IAM `LabRole` có sẵn.
- Sử dụng DynamoDB On-Demand Capacity Mode (Pay-per-request).
- Áp dụng CloudWatch Logs Retention 7 ngày.
- Gắn tag Project và Owner cho các tài nguyên hỗ trợ.
- Sử dụng request và dữ liệu mẫu với quy mô phù hợp hạn mức Learner Lab.

**Ngân sách ban đầu:** **50.00 USD**.  
**Chi phí thực tế cuối kỳ:** Ghi nhận trên AWS Academy Learner Lab, tổng chi phí phát sinh xuyên suốt 4 tuần thực hành chỉ là **~$0.45 USD / $50.00 USD** (tiêu tốn dưới 1% ngân sách được cấp). Chi phí chủ yếu đến từ việc duy trì secret trên AWS Secrets Manager (~$0.40/tháng tính theo giờ), trong khi API Gateway, Lambda và DynamoDB On-Demand đều nằm trọn vẹn trong hạn mức Free Tier và mức sử dụng demo.

**Kế hoạch dọn dẹp tài nguyên sau nghiệm thu:**
- Toàn bộ tài nguyên (03 bảng DynamoDB, 05 hàm Lambda, API Gateway và SQS Queue) hiện đang được **giữ nguyên trạng thái ACTIVE** để phục vụ buổi báo cáo vấn đáp/nghiệm thu đồ án với Giảng viên hướng dẫn.
- Nhóm đã xây dựng sẵn script dọn dẹp một chạm [`scripts/cleanup_resources.py`](https://github.com/NguyenNguyen0210/serverless-payment/blob/main/scripts/cleanup_resources.py). **Ngay sau khi kết thúc buổi bảo vệ**, nhóm sẽ thực thi lệnh:
  ```bash
  python scripts/cleanup_resources.py --confirm
  ```
  Script sẽ tự động xóa sạch 100% tài nguyên (5 Lambda, Layer PyJWT, API Gateway, 3 bảng DynamoDB, SQS Queue, Secrets Manager, CloudWatch Alarms/Dashboard/Log Groups) để đảm bảo tuân thủ đúng quy định của AWS Academy Learner Lab.

---

## 8. KHÓ KHĂN VÀ BÀI HỌC KINH NGHIỆM

### 8.1. Khó khăn

Trong quá trình phát triển, nhóm đã chủ động nhận diện và xử lý các vấn đề kỹ thuật:
- Phân quyền IAM LabRole trong môi trường Learner Lab bị giới hạn, không cho phép tự tạo Custom Role.
- Tích hợp Lambda Authorizer với API Gateway HTTP API v2 yêu cầu cấu hình cẩn thận `identitySource` và định dạng trả về Simple Responses.
- Quản lý JWT secret: phải phân tách vào AWS Secrets Manager thay vì gán cứng trong code hay environment variables.
- Thiết kế DynamoDB Transaction bảo đảm tính nguyên tử All-or-Nothing trên cả 3 bảng khác nhau.
- Xử lý request trùng và transaction conflict khi có nhiều yêu cầu đồng thời (Concurrency).
- Truy vấn lịch sử giao dịch từ hai GSI hai chiều và hỗ trợ phân trang con trỏ `nextToken`.
- Phân biệt kiểm thử SQS thủ công với luồng gửi lỗi tự động từ Lambda.

### 8.2. Bài học kinh nghiệm

Thông qua dự án, nhóm tiếp cận được quy trình phát triển một ứng dụng Serverless hoàn chỉnh từ thiết kế, triển khai đến kiểm thử và nghiệm thu:
1. Sử dụng DynamoDB Transaction để bảo đảm tính nhất quán dữ liệu trong nghiệp vụ tài chính.
2. Áp dụng Idempotency-Key và hàm băm SHA-256 để ngăn thực thi trùng yêu cầu thanh toán vĩnh viễn.
3. Kết hợp Authentication (JWT) và Authorization (Kiểm tra quyền sở hữu ví chính chủ) theo mô hình Zero-Trust.
4. Sử dụng CloudWatch Logs/Metrics/Alarms để quan sát và điều tra lỗi thực thi.
5. Tổ chức mã nguồn chuẩn mực, tài liệu kỹ thuật đồng bộ và ảnh minh chứng trung thực giúp bảo đảm tính liêm chính học thuật.
6. Kiểm thử trên môi trường AWS thực tế với số liệu đối soát thật là yếu tố quyết định chất lượng của đồ án.

---

## 9. TỔNG KẾT TOÀN BỘ DỰ ÁN SAU BỐN TUẦN

Trải qua bốn tuần triển khai, nhóm Serverless đã xây dựng hệ thống cổng thanh toán giả lập dựa trên các dịch vụ AWS Serverless:
- **Tuần 1 – Thiết kế và chuẩn bị:** Phân tích yêu cầu, xây dựng kiến trúc, mô hình dữ liệu, đặc tả API, kịch bản kiểm thử và chuẩn bị môi trường AWS Learner Lab.
- **Tuần 2 – Triển khai chức năng lõi:** Xây dựng Token Lambda, Lambda Authorizer, Transfer Lambda, DynamoDB Transaction, Secrets Manager, API Gateway và các unit tests ban đầu.
- **Tuần 3 – Tích hợp và giám sát:** Hoàn thiện mô hình ba bảng DynamoDB, năm Lambda, năm API endpoints, hai GSI, cơ chế JWT, CloudWatch và SQS.
- **Tuần 4 – Kiểm thử và nghiệm thu:** Kiểm thử trực tiếp 5 API endpoints, chuyển tiền, đối soát số dư, Idempotency Replay (200), Conflict (409), Concurrency, bảo mật, Route Throttling (429) và giám sát CloudWatch/SQS. Tổng hợp kết quả thực hiện và chuẩn bị sản phẩm bàn giao.

Các kết quả đạt được:
- Hệ thống có đủ 5 API endpoints và 5 Lambda Functions độc lập.
- Sử dụng 3 bảng DynamoDB On-Demand và 2 Global Secondary Indexes.
- Chuyển tiền bằng DynamoDB `TransactWriteItems` với 4 thao tác nguyên tử.
- Chống xử lý trùng giao dịch vĩnh viễn thông qua `Idempotency-Key` và `requestHash`.
- Xác thực JWT HS256 bằng Lambda Authorizer độc lập, không dùng Cognito.
- Quản lý khóa bí mật an toàn bằng AWS Secrets Manager.
- Phân quyền chặt chẽ theo chủ sở hữu ví.
- Có Route Throttling (HTTP 429), CloudWatch Monitoring và SQS DLQ.
- Bộ 56 unit tests đạt 100% Passed.
- Có đầy đủ 38 ảnh minh chứng thực tế trên AWS của cả hai thành viên.

---

## 10. KẾT LUẬN CUỐI KỲ

Đề tài **“Cổng thanh toán giả lập với API Gateway, Lambda Authorizer và DynamoDB Transaction”** đã giúp nhóm vận dụng kiến thức Điện toán đám mây vào việc thiết kế, triển khai và kiểm thử một hệ thống thanh toán theo kiến trúc Serverless hiện đại.

Điểm nổi bật của hệ thống là cơ chế chuyển tiền nguyên tử bằng DynamoDB TransactWriteItems, kết hợp Idempotency-Key để ngăn xử lý trùng request. Các thử nghiệm chuyển tiền và đối soát số dư trong Tuần 4 cho thấy hệ thống thực hiện đúng các thay đổi số dư ở trường hợp kiểm thử được ghi nhận ($150.000$ VND được bảo toàn tuyệt đối).

Bên cạnh đó, việc tích hợp Lambda Authorizer, Secrets Manager, API Gateway Throttling và CloudWatch giúp nhóm hiểu rõ hơn các yêu cầu bảo mật, quản lý truy cập và giám sát trong hệ thống Cloud.

Hồ sơ dự án đã hoàn thiện trọn vẹn với mã nguồn, 38 ảnh minh chứng trên GitHub, video demo nghiệm thu trên Google Drive và kịch bản dọn dẹp tài nguyên tự động sẵn sàng sau buổi bảo vệ.

**Nhóm Serverless xin chân thành cảm ơn giảng viên Huỳnh Xuân Phụng đã hướng dẫn và hỗ trợ nhóm trong suốt quá trình thực hiện đề tài.**
