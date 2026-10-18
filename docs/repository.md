# THÔNG TIN KHO LƯU TRỮ DỰ ÁN (GIT REPOSITORY)

> **Học phần:** Cloud Computing (Điện toán đám mây) – Đợt 1, Năm học 2026–2027  
> **Dự án:** Cổng thanh toán giả lập không máy chủ (`serverless-payment`)  
> **Giảng viên hướng dẫn (GVHD):** ThS. Huỳnh Xuân Phụng  
> **Nhóm thực hiện:** Serverless (Vũ Minh Đức & Nguyễn Nguyên)  

---

## 🔗 Liên kết kho lưu trữ GitHub chính thức

- **Đường dẫn Repository (Công khai):** [https://github.com/NguyenNguyen0210/serverless-payment](https://github.com/NguyenNguyen0210/serverless-payment)
- **Git Clone URL (HTTPS):**
  ```bash
  git clone https://github.com/NguyenNguyen0210/serverless-payment.git
  ```
- **Nhánh chính (Default Branch):** `main`
- **Nhánh triển khai Tuần 2:** `feat/week02-auth-gateway`

---

## 📌 Đối chiếu nội dung mã nguồn & Báo cáo đồ án theo tuần

Kho lưu trữ GitHub chứa đầy đủ toàn bộ tài liệu thiết kế, phân tích nghiệp vụ, hợp đồng API, mô hình CSDL, mã nguồn Lambda và ảnh minh chứng thực tế trên AWS:

| Thư mục / Tệp tin | Tiến độ | Nội dung kỹ thuật tương ứng |
|---|:---:|---|
| `README.md` | Tuần 1 & 2 | Tổng quan kiến trúc, bài toán kỹ thuật, tiến độ tuần 1 & 2 chi tiết từng thành viên, sơ đồ Mermaid và danh mục tài liệu. |
| `design/architecture.md` | Tuần 1 | Sơ đồ tương tác toàn diện, luồng Rate Limiting, Dead Letter Queue (DLQ), 12 quyết định thiết kế kiến trúc (ADR-01 -> ADR-12). |
| `design/openapi.yaml` | Tuần 1 | Đặc tả máy đọc được OpenAPI 3.0 với các mã lỗi HTTP 400, 401, 403, 404, 409, 429 (Too Many Requests), 500, 503. |
| `docs/api-contract.md` | Tuần 1 | Hợp đồng API chi tiết, cơ chế Route Throttling / Rate Limit và điều hướng lỗi nghiêm trọng sang DLQ. |
| `docs/business-rules.md` | Tuần 1 | 14 quy tắc nghiệp vụ chuyển tiền và nguyên tắc bảo toàn số dư tài chính. |
| `docs/data-model.md` | Tuần 1 | Thiết kế CSDL DynamoDB, cấu trúc `TransactWriteItems` và thuật toán băm chuẩn hóa `requestHash`. |
| `docs/auth-flow.md` | Tuần 1 | Luồng xác thực JWT qua Lambda Authorizer (REQUEST mode) và bảo vệ khóa trong AWS Secrets Manager. |
| `docs/test-scenarios.md` | Tuần 1 | Ma trận 21 kịch bản kiểm thử (TC-01 -> TC-21) bao gồm kiểm thử gửi trùng request, tranh chấp đồng thời và Rate Limiting. |
| `docs/aws-environment.md` | Tuần 1 | Báo cáo xác minh môi trường AWS Academy Learner Lab (`us-east-1`, IAM `LabRole`, AWS CLI). |
| `docs/resource-management.md` | Tuần 1 | Chính sách quản trị tài nguyên, ngân sách $50 và cấu hình Amazon SQS DLQ trong hạn mức Free Tier. |
| `docs/worklog.md` | Tuần 1 & 2 | Nhật ký công việc nhóm chi tiết theo tuần (đạt tối thiểu 8 giờ/thành viên/tuần). |
| `evidence/week01/` | Tuần 1 | Toàn bộ 09 ảnh chụp màn hình minh chứng thao tác trực tiếp trên AWS Console/CLI (`B1-01` -> `B2-03`). |
| `evidence/week02/` | Tuần 2 | Danh mục tổng hợp minh chứng Tuần 2 phân chia riêng theo 2 thành viên. |
| `evidence/week02/nguyen/` | Tuần 2 | **16 ảnh minh chứng thực tế trên AWS của Nguyễn Nguyên** (`B2-01` -> `B2-16`): Secrets Manager, Layer, Token, DynamoDB, Authorizer, Transfer, API Gateway, Throttling, SQS DLQ. |
| `evidence/week02/duc/` | Tuần 2 | Minh chứng kiểm thử, idempotency replay, concurrency lock và CloudWatch logs của Vũ Minh Đức (`A2-01` -> `A2-07`). |
| `src/token/` | Tuần 2 | Mã nguồn hàm `serverless-payment-token` xử lý cấp phát JWT (HS256) từ Secrets Manager. |
| `src/authorizer/` | Tuần 2 | Mã nguồn hàm `serverless-payment-authorizer` giải mã và xác thực chữ ký JWT bằng `PyJWT`. |
| `src/transfer/` | Tuần 2 | Mã nguồn hàm `serverless-payment-transfer` xử lý DynamoDB `TransactWriteItems` và chống lặp `Idempotency-Key`. |
| `scripts/seed_wallets.py` | Tuần 2 | Script khởi tạo số dư ví mẫu (`W001` - `W004`) trên DynamoDB qua AWS CloudShell. |
| `tests/` | Tuần 2 | Bộ 15/15 unit test cases tự động (`test_auth.py`, `test_transfer.py`) và các test event payload 2.0 (`tests/events/`). |
| `requirements-layer.txt` | Tuần 2 | Khai báo dependency `PyJWT==2.10.1` phục vụ đóng gói Lambda Layer. |
| `requirements-test.txt` | Tuần 2 | Khai báo dependency phục vụ unit testing trên môi trường Python 3.12. |
| `.gitignore` | Tuần 1 & 2 | Cấu hình bảo vệ thông tin bí mật, khóa truy cập và loại trừ build artifacts (`build/`, `*.zip`). |
