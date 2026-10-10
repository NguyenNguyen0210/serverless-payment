# NHẬT KÝ CÔNG VIỆC TUẦN 1 (WORKLOG WEEK 1)

> **Học phần:** Cloud Computing (Điện toán đám mây) – Đợt 1, Năm học 2026–2027  
> **Đề tài:** Cổng thanh toán giả lập với API Gateway, Lambda Authorizer và DynamoDB Transaction  
> **Giảng viên hướng dẫn (GVHD):** ThS. Huỳnh Xuân Phụng  
> **Nhóm thực hiện:** Serverless  
> - **Vũ Minh Đức** – Phân tích nghiệp vụ, Kiến trúc & Thiết kế kỹ thuật  
> - **Nguyễn Nguyên** – Môi trường AWS, IAM, Quản trị tài nguyên & Git  
> **Tuần báo cáo:** Tuần 1 (05/10/2026 – 11/10/2026)  
> **Thời lượng cam kết:** 08 giờ / thành viên / tuần (Tổng cộng 16 giờ / nhóm / tuần)  

---

## 1. Thông số môi trường AWS đã xác minh

Dữ liệu được khảo sát và ghi nhận trực tiếp trên nền tảng AWS Academy Learner Lab:

| Hạng mục kiểm tra | Giá trị ghi nhận | Trạng thái kỹ thuật |
|---|---|---|
| **Nền tảng** | AWS Academy Learner Lab (Vocareum) | Hoạt động bình thường |
| **AWS Account ID** | `930162821234` | Khớp giữa Console và AWS STS |
| **AWS Region** | `us-east-1` (US East - N. Virginia) | Đạt chuẩn theo quy định |
| **AWS CLI Version** | `aws-cli/2.37.6` | Sẵn sàng thực thi lệnh |
| **STS Caller Identity** | Assumed Role `voclabs` | Đã xác thực phiên đăng nhập |
| **IAM Execution Role** | `arn:aws:iam::930162821234:role/LabRole` | Đã kiểm tra tồn tại qua `iam get-role` |
| **Ngân sách ban đầu** | `Used $0 of $50` | Chưa phát sinh chi phí |
| **API Gateway** | `GetApis` trả về `Items: []` | Sẵn sàng khởi tạo ở Tuần 2 |
| **DynamoDB** | `ListTables` trả về `TableNames: []` | Sẵn sàng tạo bảng ở Tuần 2 |
| **Secrets Manager** | `ListSecrets` trả về `SecretList: []` | Sẵn sàng tạo secret ở Tuần 2 |
| **CloudWatch** | Logs trả về 03 log groups có sẵn của Lab | Sẵn sàng tạo log group dự án |

---

## 2. Nhật ký công việc – Nguyễn Nguyên

**Trách nhiệm:** Khảo sát nền tảng AWS Learner Lab, kiểm tra quyền truy cập IAM `LabRole`, thiết lập môi trường Git repository và xây dựng chính sách quản trị tài nguyên.

| Ngày | Khung giờ | Mã | Nội dung công việc thực hiện | Giờ | Kết quả đầu ra / Minh chứng |
|:---:|:---:|:---:|---|:---:|---|
| 10/10/2026 | 21:30 – 23:30 | **B1** | Truy cập AWS Learner Lab; cấu hình terminal Region `us-east-1`, xác minh định danh STS; khảo sát các dịch vụ API Gateway, Lambda, DynamoDB, Secrets Manager, CloudWatch; chụp ảnh ngân sách ban đầu. | 2,00 | Báo cáo môi trường: [`docs/aws-environment.md`](aws-environment.md)<br>Minh chứng: `B1-01` đến `B1-06` trong [`evidence/week01/`](../evidence/week01/) |
| 10–11/10/2026 | 23:30 – 01:30 | **B2** | Kiểm tra chi tiết phiên bản AWS CLI, cấu hình biến môi trường, truy vấn IAM `LabRole`, rà soát các hàm Lambda có sẵn trong Lab và chính sách CloudWatch Alarms; tổng hợp hạn chế quyền của Lab. | 2,00 | Báo cáo phân quyền: [`docs/aws-environment.md`](aws-environment.md)<br>Minh chứng: `B2-01` đến `B2-03` trong [`evidence/week01/`](../evidence/week01/) |
| 11/10/2026 | 08:30 – 10:30 | **B3** | Khởi tạo repository Git local, chuẩn hóa cấu trúc thư mục (`design/`, `docs/`, `src/`, `infra/`, `tests/`, `evidence/`); cấu hình `.gitignore` bảo vệ thông tin bí mật; thiết lập file `README.md` chính. | 2,00 | Cấu trúc repository hoàn chỉnh, file cấu hình [`.gitignore`](../.gitignore), [`README.md`](../README.md) |
| 11/10/2026 | 14:00 – 16:00 | **B4** | Chuẩn hóa danh mục minh chứng, thiết lập quy định gắn thẻ tài nguyên (`Project=serverless-payment`), kế hoạch kiểm soát ngân sách $50 và quy trình dọn dẹp tài nguyên sau mỗi phiên làm việc. | 2,00 | Tài liệu quản trị chi phí: [`docs/resource-management.md`](resource-management.md)<br>Chỉ mục bằng chứng: [`evidence/week01/README.md`](../evidence/week01/README.md) |
| **Tổng kết** | **4 phiên** | **B1–B4** | **Hoàn thành toàn bộ nhiệm vụ nền tảng môi trường và quản trị** | **8,00** | **Đầy đủ báo cáo môi trường, chính sách và 09 ảnh minh chứng** |

---

## 3. Nhật ký công việc – Vũ Minh Đức

**Trách nhiệm:** Phân tích nghiệp vụ thanh toán, thiết kế kiến trúc hệ thống, xây dựng hợp đồng API, mô hình dữ liệu DynamoDB và thiết kế cơ chế bảo mật JWT.

| Ngày | Khung giờ | Mã | Nội dung công việc thực hiện | Giờ | Kết quả đầu ra / Minh chứng |
|:---:|:---:|:---:|---|:---:|---|
| 10/10/2026 | 08:30 – 10:30 | **A1** | Phân tích nghiệp vụ chuyển tiền giả lập; xác định các thực thể ví, giao dịch; thiết lập 14 quy tắc nghiệp vụ (BR-01 đến BR-14) và nguyên tắc bất biến số dư tài chính (zero double-spending). | 2,00 | Tài liệu quy tắc nghiệp vụ: [`docs/business-rules.md`](business-rules.md) |
| 10/10/2026 | 14:00 – 16:00 | **A2** | Thiết kế hợp đồng API cho `POST /token` và `POST /transfers`; chuẩn hóa request body, response schema, mã lỗi HTTP và viết đặc tả máy đọc được OpenAPI 3.0. | 2,00 | Hợp đồng API: [`docs/api-contract.md`](api-contract.md)<br>Đặc tả OpenAPI: [`design/openapi.yaml`](../design/openapi.yaml) |
| 11/10/2026 | 08:30 – 10:30 | **A3** | Thiết kế mô hình dữ liệu DynamoDB bảng `Wallets` và `Transactions`; xây dựng cấu trúc lệnh nguyên tử `TransactWriteItems` (3 actions); thiết kế cơ chế băm `requestHash` và chống lặp Idempotency. | 2,00 | Tài liệu thiết kế CSDL: [`docs/data-model.md`](data-model.md) |
| 11/10/2026 | 13:30 – 15:30 | **A4** | Thiết kế luồng xác thực token JWT (HS256) qua PyJWT và Lambda Authorizer; xây dựng sơ đồ kiến trúc tổng thể, 10 quyết định thiết kế (ADR) và bộ 16+ kịch bản kiểm thử (Test Scenarios). | 2,00 | Thiết kế xác thực: [`docs/auth-flow.md`](auth-flow.md)<br>Kiến trúc & ADRs: [`design/architecture.md`](../design/architecture.md)<br>Kế hoạch test: [`docs/test-scenarios.md`](test-scenarios.md) |
| **Tổng kết** | **4 phiên** | **A1–A4** | **Hoàn thành toàn bộ hồ sơ phân tích, kiến trúc và thiết kế hệ thống** | **8,00** | **Đầy đủ 06 tài liệu kỹ thuật, sơ đồ kiến trúc và đặc tả OpenAPI** |

---

## 4. Tổng hợp khối lượng công việc Tuần 1

| Chỉ tiêu đánh giá | Vũ Minh Đức | Nguyễn Nguyên | Toàn nhóm |
|---|:---:|:---:|:---:|
| **Số nhiệm vụ hoàn thành** | 4 (A1, A2, A3, A4) | 4 (B1, B2, B3, B4) | 8 nhiệm vụ |
| **Thời lượng thực hiện** | **8,00 giờ** | **8,00 giờ** | **16,00 giờ** |
| **Sản phẩm bàn giao** | 06 tài liệu thiết kế kỹ thuật (`docs/`), sơ đồ kiến trúc & đặc tả OpenAPI (`design/`) | Báo cáo môi trường AWS, quy chế quản trị tài nguyên, cấu trúc repo Git và 09 ảnh minh chứng (`evidence/`) | Toàn bộ hồ sơ nền tảng Tuần 1 |
| **Đánh giá mức độ hoàn thành** | **Đạt 100% yêu cầu Tuần 1** | **Đạt 100% yêu cầu Tuần 1** | **Sẵn sàng triển khai Tuần 2** |

---

## 5. Danh mục minh chứng kỹ thuật (Evidence Catalog)

| Mã | Tệp minh chứng | Nội dung xác nhận trên AWS Console / CLI |
|:---:|---|---|
| **B1-01** | [`B1-01-lab-started.png`](../evidence/week01/B1-01-lab-started.png) | Phiên AWS Academy Learner Lab đang hoạt động; hiển thị ngân sách $0/$50. |
| **B1-02** | [`B1-02-region.png`](../evidence/week01/B1-02-region.png) | AWS Console xác nhận Region đang chọn là `us-east-1` (US East - N. Virginia). |
| **B1-03** | [`B1-03-cli-config.png`](../evidence/week01/B1-03-cli-config.png) | Phiên bản AWS CLI `2.37.6` và Region `us-east-1` cấu hình từ biến môi trường. |
| **B1-04** | [`B1-04-services-console.png`](../evidence/week01/B1-04-services-console.png) | Danh mục 5 dịch vụ cốt lõi đã truy cập trên AWS Console. |
| **B1-05** | [`B1-05-budget.png`](../evidence/week01/B1-05-budget.png) | Giao diện quản lý ngân sách Learner Lab ghi nhận chi phí `Used $0 of $50`. |
| **B1-06** | [`B1-06-cloudshell.png`](../evidence/week01/B1-06-cloudshell.png) | Môi trường AWS CloudShell sẵn sàng chạy các lệnh quản trị và kiểm tra. |
| **B2-01** | [`B2-01-labrole.png`](../evidence/week01/B2-01-labrole.png) | Lệnh `aws iam get-role --role-name LabRole` xác nhận tồn tại role `LabRole`. |
| **B2-02** | [`B2-02-lambda-roles.png`](../evidence/week01/B2-02-lambda-roles.png) | Danh sách các Lambda functions có sẵn trong Lab và role liên kết. |
| **B2-03** | [`B2-03-cloudwatch-alarms.png`](../evidence/week01/B2-03-cloudwatch-alarms.png) | Truy vấn CloudWatch Alarms trả về danh sách rỗng (chưa phát sinh cảnh báo). |

---

## 6. Kế hoạch và Điều kiện chuyển giao Tuần 2

1. **Điều kiện chuyển giao:** Hai thành viên đã rà soát chéo và phê duyệt toàn bộ sơ đồ kiến trúc, mô hình dữ liệu DynamoDB và hợp đồng API.
2. **Kế hoạch Tuần 2:**
   - Tạo hai bảng DynamoDB `Wallets` và `Transactions` qua script AWS CLI.
   - Tạo khóa bí mật JWT trong AWS Secrets Manager (`serverless-payment/jwt-secret`).
   - Lập trình và triển khai các hàm Lambda: `Token Lambda`, `Lambda Authorizer`, `Transfer Lambda`.
   - Kiểm thử đơn lẻ (Unit Test) từng thành phần trước khi tích hợp vào API Gateway.

---

## 7. Tuyên bố sử dụng công cụ hỗ trợ AI (AI Usage Transparency)

Tuân thủ quy định của học phần về việc sử dụng AI/LLM:
- **Công cụ hỗ trợ:** ChatGPT, Claude, Gemini.
- **Phạm vi ứng dụng:** Hỗ trợ tra cứu tài liệu đặc tả AWS, gợi ý cấu trúc tài liệu kỹ thuật, chuẩn hóa cú pháp Mermaid và sinh dữ liệu kiểm thử mẫu.
- **Trách nhiệm của sinh viên:** Toàn bộ khảo sát môi trường AWS, phân tích luồng logic, quyết định kiến trúc và nội dung tài liệu do hai sinh viên trực tiếp thực hiện, kiểm chứng và chịu trách nhiệm giải trình trước giảng viên hướng dẫn.

