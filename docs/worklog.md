# WORKLOG TUẦN 1 – SERVERLESS PAYMENT GATEWAY

**Học phần:** Cloud Computing – Đợt 1, năm học 2026–2027  
**Đề tài:** Cổng thanh toán giả lập với API Gateway, Lambda Authorizer và DynamoDB Transaction  
**Giảng viên hướng dẫn:** Huỳnh Xuân Phụng  
**Nhóm:** Nguyễn Nguyên,Vũ Minh Đức
**Tuần báo cáo minh họa:** 05/10/2026 – 11/10/2026 
**Thời lượng trong kế hoạch:** 08 giờ/thành viên/tuần;  

## 1. Thông tin môi trường 

| Trường | Giá trị |
|---|---|
| AWS Platform | AWS Academy Learner Lab (Vocareum) |
| AWS Account ID | `930162821234` (trong ảnh kiểm tra của nhóm) |
| AWS Region | `us-east-1` — US East (N. Virginia) |
| AWS CLI | `aws-cli/2.37.6` |
| AWS CLI identity | STS `get-caller-identity` trả về assumed role `voclabs` |
| IAM execution role dự kiến | `arn:aws:iam::930162821234:role/LabRole` — đã đọc thành công bằng `iam get-role` |
| Chi phí Learner Lab trên ảnh | `Used $0 of $50` — giá trị hiển thị, có thể cập nhật trễ |
| API Gateway | Liệt kê thành công; chưa có REST/HTTP API được trả về |
| DynamoDB | Liệt kê thành công; `TableNames: []` |
| Secrets Manager | Liệt kê thành công; `SecretList: []` |
| Lambda | Liệt kê thành công; ảnh kiểm tra sau cùng hiển thị 05 Lambda có sẵn |
| CloudWatch | Logs liệt kê được 03 log groups; Alarms trả danh sách rỗng |

## 2. Nhật ký công việc Thành viên B

**Vai trò:** Chuẩn bị Learner Lab, kiểm tra AWS CLI/quyền đọc, khởi tạo repository và chuẩn hóa hồ sơ.    
**Thời gian :** 

| Ngày | Bắt đầu  | Kết thúc | Mã | Nội dung công việc | Giờ mẫu | Trạng thái có thể xác minh | Tệp đầu ra / minh chứng |
|---|---|---|---|---|---:|---|---|
| 10/10/2026 | 21:30 | 23:30 | B1 | Truy cập Learner Lab; xác nhận `us-east-1`, CloudShell, AWS CLI/STS; liệt kê API Gateway, Lambda, DynamoDB, Secrets Manager, CloudWatch; chụp ngân sách | 2,00 | **Đã có ảnh và log kết quả**; giờ mẫu chưa xác minh | `docs/aws-environment.md`; `evidence/week01/B1-01-lab-started.png` đến `B1-06-cloudshell.png` |
| 10–11/10/2026 | 23:30 | 01:30 (+1 ngày) | B2 | Kiểm tra phiên bản AWS CLI, Region từ môi trường, `iam get-role` với `LabRole`, danh sách Lambda và role gắn kèm, CloudWatch Alarms; tổng hợp giới hạn quyền | 2,00 | **Đã có ảnh và log kết quả**; giờ mẫu chưa xác minh | `docs/aws-environment.md`; `evidence/week01/B2-01-labrole.png`, `B2-02-lambda-roles.png`, `B2-03-cloudwatch-alarms.png` |
| 11/10/2026 | 09:00 | 11:00 | B3 | Chuẩn hóa Git repository local, cấu trúc `docs/`, `src/`, `tests/`, `infra/`, `evidence/`; rà soát README, `.gitignore`; kiểm tra remote/nhánh trước khi commit và push | 2,00 | **Lập lịch mẫu**; chỉ xác nhận từ lời người dùng rằng Git và thư mục local đã được tạo, chưa có minh chứng push | `README.md`, `.gitignore`, cấu trúc repository local; đường dẫn commit chưa có vì chưa xác minh |
| 11/10/2026 | 14:00 | 16:00 | B4 | Sắp xếp evidence, lập quy định tag `Project/Owner`, ghi nhận ngân sách, rà soát tài nguyên đã có, tổng hợp worklog và kế hoạch dọn tài nguyên | 2,00 | **Lập lịch mẫu**; bộ file đã được AI hỗ trợ soạn, chưa xác nhận thành viên thực hiện và lưu trên GitHub | `docs/worklog.md`, `docs/resource-management.md`, `evidence/week01/` |

## 3. Nhật ký công việc Thành viên A

**Vai trò:** Phân tích nghiệp vụ và thiết kế kỹ thuật.  
**Trạng thái:** **Toàn bộ bảng A là kế hoạch mô phỏng**; chưa có tài liệu hoặc dữ liệu giờ công do Thành viên A cung cấp trong cuộc trao đổi này.

| Ngày (UTC+7) | Bắt đầu (mẫu) | Kết thúc (mẫu) | Mã | Nội dung công việc dự kiến | Giờ mẫu | Trạng thái | Đầu ra dự kiến |
|---|---|---|---|---|---:|---|---|
| 12/10/2026 | 08:00 | 10:00 | A1 | Xác định luồng chuyển tiền, kiểm tra số dư, ví nguồn/đích, giao dịch hợp lệ và lỗi nghiệp vụ | 2,00 | Dự kiến; chưa xác minh | `docs/business-rules.md` |
| 12/10/2026 | 13:00 | 15:00 | A2 | Xác định contract cho `POST /token`, `POST /transfers`, `GET /transactions/{id}`; request/response, mã lỗi và `Idempotency-Key` | 2,00 | Dự kiến; chưa xác minh | `docs/api-contract.md` |
| 13/10/2026 | 08:00 | 10:00 | A3 | Thiết kế `Wallets`, `Transactions`; điều kiện số dư, `TransactWriteItems`, chống trùng và chống cạnh tranh | 2,00 | Dự kiến; chưa xác minh | `docs/data-model.md` |
| 13/10/2026 | 13:00 | 15:00 | A4 | Thiết kế JWT/PyJWT, Lambda Authorizer, Secrets Manager, các trường hợp kiểm thử | 2,00 | Dự kiến; chưa xác minh | `docs/auth-flow.md`, `docs/test-scenarios.md` |
| **Tổng A (kế hoạch/mô phỏng)** | **4 phiên** | **2 ngày** | **A1–A4** | **Mỗi nhiệm vụ 2 giờ theo phân công** | **8,00** | **Không đồng nghĩa đã làm đủ 8 giờ thực tế** | **Chờ xác nhận và bàn giao của A** |

## 4. Tổng hợp khối lượng theo kế hoạch

| Chỉ tiêu | Thành viên A | Thành viên B | Toàn nhóm |
|---|---:|---:|---:|
| Số nhiệm vụ theo phân công | 4 | 4 | 8 |
| Giờ dự kiến / mô phỏng | 8,00 | 8,00 | 16,00 |
| Giờ thực tế được chứng thực bằng bảng chấm giờ | Chưa có dữ liệu | Chưa có dữ liệu | Chưa có dữ liệu |
| Kết quả có thể xác nhận độc lập | Chưa cung cấp | B1–B2: log và ảnh CLI | Phần môi trường AWS |

**Quy tắc nghiệm thu:** Giờ công thực tế phải lấy từ thời gian làm việc của từng sinh viên, không suy ra từ thời gian phiên Lab hoặc ảnh chụp; ảnh có timestamp chỉ chứng minh thao tác tại thời điểm chụp. Theo đề bài, mỗi người cần tối thiểu 8 giờ làm việc thực tế/tuần.

## 5. Danh mục evidence hiện có

| Mã | Đường dẫn | Nội dung xác nhận |
|---|---|---|
| B1-01 | `evidence/week01/B1-01-lab-started.png` | Phiên AWS Learner Lab hoạt động |
| B1-02 | `evidence/week01/B1-02-region.png` | Console Region `us-east-1` |
| B1-03 | `evidence/week01/B1-03-cli-config.png` | AWS CLI version và configure list |
| B1-04 | `evidence/week01/B1-04-services-console.png` | 5 dịch vụ trong Recently visited |
| B1-05 | `evidence/week01/B1-05-budget.png` | Giao diện ngân sách Used $0 of $50 |
| B1-06 | `evidence/week01/B1-06-cloudshell.png` | Môi trường CloudShell |
| B2-01 | `evidence/week01/B2-01-labrole.png` | IAM get-role trả metadata LabRole |
| B2-02 | `evidence/week01/B2-02-lambda-roles.png` | Danh sách Lambda và role |
| B2-03 | `evidence/week01/B2-03-cloudwatch-alarms.png` | CloudWatch Alarms trả danh sách rỗng |

**Bảo vệ thông tin:** Ảnh minh chứng chứa Account ID và định danh phiên đăng nhập. Chỉ lưu trong repo riêng tư hoặc nơi được phép; tuyệt đối không commit AWS credentials, session tokens hoặc JWT secret.

## 6. Tài nguyên, ngân sách và nguyên tắc phối hợp

- **Region triển khai:** `us-east-1`; chỉ sử dụng `us-east-1`/`us-west-2` theo README Lab.
- **IAM:** Sử dụng `LabRole` có sẵn; không tạo IAM user/role mới.
- **Quy tắc gắn thẻ tài nguyên mới:** `Project=serverless-payment` và `Owner=Serverless-Team-B` (Owner là **quy ước đề xuất**, chưa có tài nguyên nhóm nào được chứng minh đã gắn thẻ).
- **Tài nguyên nhóm đã tạo trên AWS trong các bước kiểm tra:** không có thao tác tạo được báo cáo; chỉ chạy các lệnh đọc. Tài nguyên Lambda/log hiện hữu không được tự ý xóa.
- **Ngân sách tham chiếu:** `Used $0 of $50` từ ảnh Learner Lab ngày 10/10/2026, có độ trễ cập nhật; chưa có số liệu chi phí cuối kỳ.
- **B3 Git:** thư mục local do người dùng cho biết đã khởi tạo; chưa có bằng chứng về `origin`, nhánh, commit và push.
- **Điều kiện bắt đầu Tuần 2:** A và B xác nhận thống nhất Region, endpoint, tên bảng, schema, secret name; kiểm tra quyền ghi khi triển khai chính thức.
