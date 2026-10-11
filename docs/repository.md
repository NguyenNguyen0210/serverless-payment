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

---

## 📌 Đối chiếu nội dung mã nguồn & Báo cáo đồ án

Kho lưu trữ GitHub chứa đầy đủ toàn bộ tài liệu thiết kế, phân tích nghiệp vụ, hợp đồng API, mô hình CSDL và mã nguồn các dịch vụ theo đúng tiến độ báo cáo Tuần 1:

| Thư mục / Tệp tin | Nội dung kỹ thuật tương ứng |
|---|---|
| `README.md` | Tổng quan kiến trúc hệ thống, 5 thách thức kỹ thuật cốt lõi (bao gồm Rate Limiting & DLQ), sơ đồ Mermaid và danh mục tài liệu. |
| `design/architecture.md` | Sơ đồ tương tác toàn diện, luồng Rate Limiting, Dead Letter Queue (DLQ), 12 quyết định thiết kế kiến trúc (ADR-01 -> ADR-12). |
| `design/openapi.yaml` | Đặc tả máy đọc được OpenAPI 3.0 với các mã lỗi HTTP 400, 401, 403, 404, 409, 429 (Too Many Requests), 500, 503. |
| `docs/api-contract.md` | Hợp đồng API chi tiết, cơ chế Route Throttling / Rate Limit và điều hướng lỗi nghiêm trọng sang DLQ. |
| `docs/business-rules.md` | 14 quy tắc nghiệp vụ chuyển tiền và nguyên tắc bảo toàn số dư tài chính. |
| `docs/data-model.md` | Thiết kế CSDL DynamoDB (`Wallets`, `Transactions`), cấu trúc `TransactWriteItems` và thuật toán băm chuẩn hóa `requestHash`. |
| `docs/auth-flow.md` | Luồng xác thực JWT qua Lambda Authorizer (REQUEST mode) và bảo vệ khóa trong AWS Secrets Manager. |
| `docs/test-scenarios.md` | Ma trận 21 kịch bản kiểm thử (TC-01 -> TC-21) bao gồm kiểm thử gửi trùng request, tranh chấp đồng thời và Rate Limiting. |
| `docs/aws-environment.md` | Báo cáo xác minh môi trường AWS Academy Learner Lab (`us-east-1`, IAM `LabRole`, AWS CLI). |
| `docs/resource-management.md` | Chính sách quản trị tài nguyên, ngân sách $50 và cấu hình Amazon SQS DLQ trong hạn mức Free Tier. |
| `docs/worklog.md` | Nhật ký công việc nhóm Tuần 1 (16 giờ công chi tiết, 09 ảnh minh chứng). |
| `evidence/week01/` | Toàn bộ 09 ảnh chụp màn hình minh chứng thao tác trực tiếp trên AWS Console/CLI. |
| `examples/api-examples.md` | Bộ lệnh cURL mẫu thực thi gọi API, kiểm tra replay và kiểm thử ngưỡng Rate Limit. |
