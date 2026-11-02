# NHẬT KÝ CÔNG VIỆC DỰ ÁN (PROJECT WORKLOG WEEKS 1 – 4)

> **Học phần:** Cloud Computing (Điện toán đám mây) – Đợt 1, Năm học 2026–2027  
> **Đề tài:** Cổng thanh toán giả lập với API Gateway, Lambda Authorizer và DynamoDB Transaction  
> **Giảng viên hướng dẫn (GVHD):** ThS. Huỳnh Xuân Phụng  
> **Nhóm thực hiện:** Serverless  
> - **Vũ Minh Đức** – Phân tích nghiệp vụ, CSDL DynamoDB, Idempotency & Concurrency  
> - **Nguyễn Nguyên** – Môi trường AWS, IAM, Secrets Manager, CloudWatch, API Gateway & Tests  
> **GitHub Repository:** [https://github.com/NguyenNguyen0210/serverless-payment](https://github.com/NguyenNguyen0210/serverless-payment)  
> **Thời lượng cam kết:** 08 giờ / thành viên / tuần (Tổng cộng 64,0 giờ / 4 tuần)  

---

## BẢNG TỔNG HỢP KHỐI LƯỢNG 4 TUẦN

| Tuần | Thời gian | Vũ Minh Đức | Nguyễn Nguyên | Tổng nhóm | Trạng thái kỹ thuật |
|:---:|:---:|:---:|:---:|:---:|:---:|
| **Tuần 1** | 05/10 – 11/10/2026 | 8,00 giờ | 8,00 giờ | 16,00 giờ | **Đạt 100%** (Khảo sát môi trường, thiết kế kiến trúc, OpenAPI) |
| **Tuần 2** | 12/10 – 18/10/2026 | 8,00 giờ | 8,00 giờ | 16,00 giờ | **Đạt 100%** (Triển khai 5 Lambdas, Secrets Manager, 3 bảng, API Gateway) |
| **Tuần 3** | 19/10 – 25/10/2026 | 8,00 giờ | 8,00 giờ | 16,00 giờ | **Đạt 100%** (Tái cấu trúc 3 bảng, 2 GSIs, CloudWatch, 56 Unit Tests) |
| **Tuần 4** | 26/10 – 01/11/2026 | 8,00 giờ | 8,00 giờ | 16,00 giờ | **Đạt 100%** (Kiểm thử 5 endpoints, Concurrency, Throttling, Nghiệm thu) |
| **TỔNG CỘNG** | **4 Tuần** | **32,00 giờ** | **32,00 giờ** | **64,00 giờ** | **Hoàn thành 100% yêu cầu đồ án** |

---

## 1. NHẬT KÝ CHI TIẾT TUẦN 1 (05/10/2026 – 11/10/2026)

### 1.1. Nguyễn Nguyên (8,00 giờ)
- **B1 (2,0h):** Khảo sát nền tảng AWS Learner Lab, xác thực định danh STS (`930162821234`), cấu hình terminal Region `us-east-1`, chụp ảnh ngân sách ban đầu ($0/$50). *(Minh chứng: `B1-01` -> `B1-06`)*.
- **B2 (2,0h):** Kiểm tra phiên bản AWS CLI, cấu hình biến môi trường, rà soát IAM `LabRole`, kiểm tra CloudWatch Alarms và tổng hợp giới hạn quyền Lab. *(Minh chứng: `B2-01` -> `B2-03`)*.
- **B3 (2,0h):** Khởi tạo Git repository, cấu hình `.gitignore`, chuẩn hóa cấu trúc thư mục dự án và đẩy lên GitHub công khai.
- **B4 (2,0h):** Xây dựng quy chế quản trị tài nguyên, kế hoạch kiểm soát ngân sách, chính sách SQS DLQ (`serverless-payment-dlq`) và tài liệu [`README.md`](../README.md).

### 1.2. Vũ Minh Đức (8,00 giờ)
- **A1 (2,0h):** Phân tích nghiệp vụ chuyển tiền, thiết lập 14 quy tắc nghiệp vụ ban đầu (BR-01 -> BR-14) và nguyên tắc bất biến số dư tài chính.
- **A2 (2,0h):** Thiết kế hợp đồng API cho `POST /token` và `POST /transfers`, viết đặc tả OpenAPI 3.0 và cơ chế Route Throttling.
- **A3 (2,0h):** Thiết kế mô hình CSDL DynamoDB ban đầu, cấu trúc lệnh nguyên tử `TransactWriteItems`, cơ chế băm `requestHash` và chống lặp Idempotency.
- **A4 (2,0h):** Thiết kế luồng xác thực JWT (HS256) qua PyJWT và Lambda Authorizer, xây dựng 12 ADRs và ma trận kịch bản kiểm thử.

---

## 2. NHẬT KÝ CHI TIẾT TUẦN 2 (12/10/2026 – 18/10/2026)

### 2.1. Nguyễn Nguyên (8,00 giờ)
- **B2-1 (2,0h):** Khởi tạo secret `serverless-payment/jwt-secret` trên Secrets Manager, đóng gói Lambda Layer `pyjwt-layer` (Python 3.12, PyJWT 2.10.1). *(Minh chứng: `B2-01`, `B2-02`)*.
- **B2-2 (2,0h):** Triển khai hàm `serverless-payment-token` và `serverless-payment-authorizer`, kiểm thử cấp JWT và xác thực phân quyền qua Lambda Console. *(Minh chứng: `B2-03` -> `B2-05`, `B2-08`, `B2-09`)*.
- **B2-3 (2,0h):** Cấu hình Amazon API Gateway HTTP API v2 (`serverless-payment-api`), tích hợp Lambda Authorizer (REQUEST mode) bảo vệ các route. *(Minh chứng: `B2-13`, `B2-14`)*.
- **B2-4 (2,0h):** Cấu hình Route Throttling (2 RPS cho Token, 10 RPS cho Transfer), khởi tạo hàng đợi Amazon SQS DLQ `serverless-payment-dlq`, tổng hợp 16 ảnh minh chứng [`evidence/week02/nguyen/`](../evidence/week02/nguyen/). *(Minh chứng: `B2-15`, `B2-16`)*.

### 2.2. Vũ Minh Đức (8,00 giờ)
- **A2-1 (2,0h):** Lập trình hàm `serverless-payment-transfer` xử lý giao dịch nguyên tử qua `TransactWriteItems`, kiểm tra điều kiện ví và số dư.
- **A2-2 (2,0h):** Cài đặt thuật toán băm chuẩn hóa `requestHash` (SHA-256) và cơ chế Idempotent Replay trả kết quả cũ an toàn (`replayed: true`).
- **A2-3 (2,0h):** Viết script nạp dữ liệu ví `scripts/seed_wallets.py` và triển khai kiểm thử đơn vị độc lập.
- **A2-4 (2,0h):** Thực hiện kiểm thử toàn diện trên AWS Console: chuyển tiền thành công, thiếu số dư, sai chủ ví, tổng hợp 22 ảnh minh chứng [`evidence/week02/duc/`](../evidence/week02/duc/). *(Minh chứng: `A2-01` -> `A2-22`)*.

---

## 3. NHẬT KÝ CHI TIẾT TUẦN 3 (19/10/2026 – 25/10/2026)

### 3.1. Nguyễn Nguyên (8,00 giờ)
- **B3-1 (2,0h):** Cấu hình và triển khai 3 bảng DynamoDB On-Demand trên AWS qua script `create_tables.py --apply`. *(Minh chứng: `B3-01` -> `B3-06`)*.
- **B3-2 (2,0h):** Phát triển 2 hàm Lambda truy vấn độc lập: `serverless-payment-wallet-query` (tra cứu số dư ví) và `serverless-payment-transaction-query` (chi tiết giao dịch). *(Minh chứng: `B3-09`, `B3-10`)*.
- **B3-3 (2,0h):** Thiết lập hệ thống giám sát CloudWatch: cấu hình Log Groups retention 7 ngày, xây dựng CloudWatch Dashboard và Alarms theo dõi lỗi Lambda. *(Minh chứng: `B3-11` -> `B3-14`)*.
- **B3-4 (2,0h):** Kiểm thử tích hợp 5 routes API Gateway, gửi message thử nghiệm vào SQS DLQ, chuẩn hóa 22 ảnh minh chứng [`evidence/week03/nguyen/`](../evidence/week03/nguyen/). *(Minh chứng: `B3-15` -> `B3-22`)*.

### 3.2. Vũ Minh Đức (8,00 giờ)
- **A3-1 (2,0h):** Thiết kế lại CSDL 3 bảng DynamoDB On-Demand chuyên biệt và 2 Global Secondary Indexes (`FromWalletIndex`, `ToWalletIndex`).
- **A3-2 (2,0h):** Refactor `TransferLambda` thực thi 4 actions nguyên tử trên 3 bảng trong cùng 1 lệnh `TransactWriteItems`.
- **A3-3 (2,0h):** Chuẩn hóa khóa sắp xếp `timeKey` (`<createdAt>#<txId>`) phục vụ truy vấn lịch sử hai chiều có phân trang con trỏ `nextToken`.
- **A3-4 (2,0h):** Xây dựng bộ 56 unit test cases tự động (`test_auth.py`, `test_transfer.py`, `test_query.py`) đạt 100% Passed, tổng hợp 20 ảnh minh chứng [`evidence/week03/duc/`](../evidence/week03/duc/). *(Minh chứng: `A3-01` -> `A3-20`)*.

---

## 4. NHẬT KÝ CHI TIẾT TUẦN 4 (26/10/2026 – 01/11/2026)

> **Ghi chú minh bạch về mốc commit sau giờ nộp form:** Commit [`314106a`](https://github.com/NguyenNguyen0210/serverless-payment/commit/314106a) lúc 22:58 ngày 01/11/2026 (sau mốc nộp form lúc 22:54) là thao tác bổ sung tệp báo cáo Tuần 4 ([`docs/reports/week04-report.md`](reports/week04-report.md)) và liên kết Video Demo Google Drive vào repository để hoàn thiện hồ sơ lưu trữ theo đúng quy chuẩn dự án.

### 4.1. Nguyễn Nguyên (8,00 giờ thực tế)
- **B4-1 (2,0h) – Thứ Hai 26/10/2026 (19:30 – 21:30):** Kiểm thử tích hợp toàn bộ 5 API endpoints qua Postman và CloudShell: cấp token, xem ví chính chủ, chặn xem ví người khác (403), chuyển tiền (201), xem chi tiết và lịch sử giao dịch. *(Minh chứng: [`B4-01`](../evidence/week04/nguyen/B4-01-aws-environment-and-resources.png) $\rightarrow$ [`B4-08`](../evidence/week04/nguyen/B4-08-api-wallet-transactions-history.png))*.
- **B4-2 (2,0h) – Thứ Tư 28/10/2026 (19:30 – 21:30):** Kiểm tra bảo mật JWT, IAM `LabRole`, Secrets Manager, kiểm thử chống lặp Idempotent Replay (200 OK) và xung đột payload (409 Conflict). *(Minh chứng: [`B4-10`](../evidence/week04/nguyen/B4-10-api-idempotency-replay-success.png), [`B4-11`](../evidence/week04/nguyen/B4-11-api-idempotency-conflict.png), [`B4-13`](../evidence/week04/nguyen/B4-13-secrets-manager-and-iam-labrole.png))*.
- **B4-3 (2,0h) – Thứ Sáu 30/10/2026 (08:30 – 10:30):** Kiểm thử giới hạn tốc độ Route Throttling (HTTP 429) trên route token (30 reqs) và transfers (40 reqs); kiểm tra CloudWatch Dashboard/Alarms và gửi message kiểm thử vào SQS DLQ. *(Minh chứng: [`B4-14`](../evidence/week04/nguyen/B4-14-cloudwatch-log-groups-retention.png) $\rightarrow$ [`B4-19`](../evidence/week04/nguyen/B4-19-api-throttling-transfers-test.png))*.
- **B4-4 (2,0h) – Chủ Nhật 01/11/2026 (14:00 – 16:00):** Nâng cấp hàm `wallet_query` với cơ chế Fallback Scan dự phòng, rà soát chi phí Learner Lab (~$0.45), tổng hợp đủ 19 ảnh minh chứng [`evidence/week04/nguyen/`](../evidence/week04/nguyen/), hoàn thiện hồ sơ báo cáo nghiệm thu cuối kỳ và cùng Đức quay video demo.

### 4.2. Vũ Minh Đức (8,00 giờ thực tế)
- **A4-1 (2,0h) – Thứ Ba 27/10/2026 (19:30 – 21:30):** Kiểm tra tính nguyên tử và điều kiện rollback của DynamoDB TransactWriteItems khi số dư ví nguồn không đủ, bảo đảm không xảy ra tình trạng trừ tiền một phía. *(Minh chứng: [`A4-06`](../evidence/week04/duc/A4-06-api-transfer-success.png))*.
- **A4-2 (2,0h) – Thứ Năm 29/10/2026 (19:30 – 21:30):** Kiểm thử tải tranh chấp đồng thời (Concurrency): bắn song song 5 requests cùng `CONCURRENT_KEY`, chứng minh hệ thống không nhân bản giao dịch hay trừ tiền 2 lần; kiểm thử Replay/Conflict. *(Minh chứng: [`A4-10`](../evidence/week04/duc/A4-10-api-idempotency-replay-success.png) $\rightarrow$ [`A4-12`](../evidence/week04/duc/A4-12-test-concurrency-parallel-requests.png))*.
- **A4-3 (2,0h) – Thứ Bảy 31/10/2026 (09:00 – 11:00):** Đối soát số dư trên DynamoDB Console: ví `W001` (73k $\rightarrow$ 63k VND) và `W002` (77k $\rightarrow$ 87k VND), bảo toàn tuyệt đối tổng 150k VND; hoàn thiện 19 ảnh minh chứng Đức đưa lên nhánh `main`. *(Minh chứng: [`A4-01`](../evidence/week04/duc/A4-01-aws-environment-and-resources.png) $\rightarrow$ [`A4-19`](../evidence/week04/duc/A4-19-api-transfers-idempotency-burst-test.png))*.
- **A4-4 (2,0h) – Chủ Nhật 01/11/2026 (19:30 – 21:30):** Rà soát toàn bộ tài liệu kỹ thuật, hợp đồng API, ma trận kiểm thử và cùng Nguyên quay video demo nghiệm thu đồ án lưu tại Google Drive.

---

## 5. CÔNG CỤ HỖ TRỢ & LIÊM CHÍNH HỌC THUẬT

Tuân thủ nghiêm ngặt quy định về liêm chính học thuật và sử dụng công nghệ hỗ trợ:
1. **Tài liệu tham khảo chính thống:** AWS Documentation (API Gateway HTTP APIs, DynamoDB TransactWriteItems, CloudWatch, SQS DLQ, Secrets Manager), RFC 7519 (JWT), PyJWT Documentation.
2. **Công cụ phát triển & Kiểm thử:** AWS CLI v2, AWS CloudShell, Visual Studio Code, Postman, Git/GitHub, cURL, Python 3.12 unittest.
3. **Công cụ AI hỗ trợ:** Nhóm có tham khảo ChatGPT / Google Antigravity trong việc tra cứu nhanh cú pháp SDK Boto3, gợi ý định dạng sơ đồ Mermaid và soát lỗi văn phong kỹ thuật.
4. **Cam kết:** Toàn bộ kiến trúc hệ thống, mã nguồn 5 hàm Lambda, cấu hình dịch vụ AWS và 100% dữ liệu/ảnh minh chứng đều được thực thi trực tiếp trên tài khoản AWS Academy Learner Lab của nhóm sinh viên, sẵn sàng giải trình và bảo vệ trước Hội đồng chấm thi.
