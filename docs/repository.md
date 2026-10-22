# THÔNG TIN KHO LƯU TRỮ DỰ ÁN (GIT REPOSITORY)

> **Học phần:** Cloud Computing (Điện toán đám mây) – Đợt 1, Năm học 2026–2027  
> **Dự án:** Cổng thanh toán giả lập không máy chủ (`serverless-payment`)  
> **Giảng viên hướng dẫn (GVHD):** ThS. Huỳnh Xuân Phụng  
> **Nhóm thực hiện:** Serverless (Vũ Minh Đức & Nguyễn Nguyên)  
> **Phiên bản:** 2.0 (Hệ thống 3 bảng DynamoDB & 5 Standalone Lambdas)  

---

## 🔗 Liên kết kho lưu trữ GitHub chính thức

- **Đường dẫn Repository (Công khai):** [https://github.com/NguyenNguyen0210/serverless-payment](https://github.com/NguyenNguyen0210/serverless-payment)
- **Git Clone URL (HTTPS):**
  ```bash
  git clone https://github.com/NguyenNguyen0210/serverless-payment.git
  ```
- **Nhánh chính (Default Branch):** `main`

---

## 📌 Đối chiếu nội dung mã nguồn & Báo cáo đồ án

Toàn bộ tài liệu kỹ thuật, mô hình CSDL 3 bảng, 5 API endpoints, bộ mã nguồn 5 hàm Lambda độc lập (standalone - không cần module phụ thuộc `shared.py`), 2 scripts khởi tạo CSDL và ảnh minh chứng thực tế trên AWS:

| Thư mục / Tệp tin | Tiến độ | Nội dung kỹ thuật tương ứng |
|---|:---:|---|
| `README.md` | Tuần 1 & 2 | Tổng quan kiến trúc, bài toán kỹ thuật, tiến độ tuần 1 & 2 chi tiết từng thành viên, sơ đồ Mermaid, danh mục tài liệu và hướng dẫn chạy khởi tạo CSDL. |
| `design/architecture.md` | Tuần 1 & 2 | Sơ đồ tương tác toàn diện, kiến trúc xác thực JWT qua Lambda Authorizer (REQUEST mode), Secrets Manager, Rate Limiting, Dead Letter Queue (DLQ), 14 quyết định thiết kế kiến trúc (ADR-01 -> ADR-14). |
| `design/openapi.yaml` | Tuần 1 & 2 | Đặc tả máy đọc được OpenAPI 3.0 cho toàn bộ 5 endpoints (`POST /auth/token`, `POST /transfers`, `GET /wallets/{id}`, `GET /transactions/{id}`, `GET /wallets/{id}/transactions`) với đầy đủ mã lỗi HTTP. |
| `docs/api-contract.md` | Tuần 1 & 2 | Hợp đồng API chi tiết cho 5 routes, tích hợp đầy đủ lệnh cURL kiểm thử, cơ chế Route Throttling và điều hướng sự cố sang SQS DLQ. |
| `docs/business-rules.md` | Tuần 1 & 2 | 17 quy tắc nghiệp vụ chuyển tiền, kiểm soát quyền sở hữu ví/giao dịch và bất biến số dư tài chính. |
| `docs/data-model.md` | Tuần 1 & 2 | Thiết kế CSDL 3 bảng DynamoDB (`wallets`, `transactions` với 2 GSIs, `idempotency`), cấu trúc 4 actions trong `TransactWriteItems` và thuật toán băm chuẩn hóa `requestHash`. |
| `docs/test-scenarios.md` | Tuần 1 & 2 | Ma trận 26 kịch bản kiểm thử (TC-01 -> TC-26) bao gồm kiểm thử chuyển tiền, replay chống trùng, tranh chấp đồng thời, Rate Limiting, SQS DLQ và các API tra cứu mở rộng. |
| `docs/worklog.md` | Tuần 1 & 2 | Nhật ký công việc nhóm chi tiết theo tuần (đạt tối thiểu 8 giờ/thành viên/tuần). |
| `evidence/week01/` | Tuần 1 | Toàn bộ 09 ảnh chụp màn hình minh chứng thao tác trực tiếp trên AWS Console/CLI (`B1-01` -> `B2-03`). |
| `evidence/week02/nguyen/` | Tuần 2 | **16 ảnh minh chứng thực tế trên AWS của Nguyễn Nguyên** (`B2-01` -> `B2-16`): Secrets Manager, Layer, Token, DynamoDB, Authorizer, Transfer, API Gateway, Throttling, SQS DLQ. |
| `evidence/week02/duc/` | Tuần 2 | **22 ảnh minh chứng triển khai và kiểm thử của Vũ Minh Đức** (`A2-01` -> `A2-22`): Learner Lab, Secrets Manager, Lambda, DynamoDB, API Gateway, SQS, xác thực và idempotency. |
| `src/token/` | Tuần 2 | Mã nguồn hàm `serverless-payment-token` xử lý cấp phát JWT (HS256) từ Secrets Manager (Standalone). |
| `src/authorizer/` | Tuần 2 | Mã nguồn hàm `serverless-payment-authorizer` giải mã và xác thực chữ ký JWT bằng `PyJWT` (Standalone). |
| `src/transfer/` | Tuần 2 | Mã nguồn hàm `serverless-payment-transfer` xử lý DynamoDB `TransactWriteItems` 4 actions và chống lặp `Idempotency-Key` (Standalone). |
| `src/wallet_query/` | Tuần 2 | Mã nguồn hàm `serverless-payment-wallet-query` xử lý tra cứu số dư ví chính chủ và lịch sử phân trang `nextToken` (Standalone). |
| `src/transaction_query/` | Tuần 2 | Mã nguồn hàm `serverless-payment-transaction-query` xử lý tra cứu chi tiết giao dịch theo ID cho các bên tham gia (Standalone). |
| `scripts/create_tables.py` | Tuần 2 | Script khởi tạo hạ tầng 3 bảng DynamoDB On-Demand và 2 GSIs một cách an toàn và idempotent. |
| `scripts/seed_wallets.py` | Tuần 2 | Script nạp dữ liệu số dư 4 ví mẫu (`W001` - `W004`) có kiểm tra điều kiện chống ghi đè số dư. |
| `tests/` | Tuần 2 | Bộ 56 unit test cases tự động (`test_auth.py`, `test_transfer.py`, `test_query.py`) đạt 100% Passed không phụ thuộc network/AWS. |
| `requirements-layer.txt` | Tuần 2 | Khai báo dependency `PyJWT==2.10.1` phục vụ đóng gói Lambda Layer. |
| `requirements-test.txt` | Tuần 2 | Khai báo dependency phục vụ unit testing trên môi trường Python 3.12. |
| `.gitignore` | Tuần 1 & 2 | Cấu hình bảo vệ thông tin bí mật, khóa truy cập và loại trừ build artifacts (`dist/`, `*.zip`). |
