# BÁO CÁO KHẢO SÁT & THIẾT LẬP MÔI TRƯỜNG AWS

> **Học phần:** Cloud Computing (Điện toán đám mây) – Đợt 1, Năm học 2026–2027  
> **Dự án:** Cổng thanh toán giả lập không máy chủ (`serverless-payment`)  
> **Người thực hiện:** Nguyễn Nguyên  
> **Phối hợp thực hiện:** Vũ Minh Đức  
> **Nền tảng:** AWS Academy Learner Lab (Vocareum) · **Region:** `us-east-1`  
> **Giai đoạn:** Tuần 1 – Thiết lập nền tảng & Khảo sát môi trường  

---

## 1. Tổng quan môi trường & Thông số định danh

Trong Tuần 1, nhóm đã kích hoạt và khảo sát toàn diện môi trường làm việc trên nền tảng AWS Academy Learner Lab. Kết quả xác nhận các thông số hệ thống hoạt động ổn định:

| Hạng mục kiểm tra | Thông số ghi nhận | Đánh giá kỹ thuật |
|---|---|---|
| **Nền tảng Cloud** | AWS Academy Learner Lab (Vocareum) | Hoạt động bình thường (Session active) |
| **AWS Account ID** | `930162821234` | Đồng nhất giữa AWS Console và AWS CLI STS |
| **AWS Region chuẩn** | `us-east-1` (US East - N. Virginia) | Đúng quy định của học phần, hỗ trợ đầy đủ dịch vụ |
| **AWS CloudShell Region** | `us-east-1` | Sẵn sàng thực thi lệnh trực tiếp trên console |
| **Phiên bản AWS CLI** | `aws-cli/2.37.6` | Cài đặt và hoạt động ổn định trên môi trường máy trạm |
| **Định danh phiên CLI** | Assumed Role `voclabs` | Phiên làm việc tạm thời được xác thực an toàn |
| **IAM Execution Role** | `arn:aws:iam::930162821234:role/LabRole` | Role có sẵn của Lab, sẵn sàng gán cho các Lambda functions |
| **Ngân sách khởi đầu** | `Used $0 of $50` | Chưa phát sinh chi phí trong tuần khảo sát |

Cấu hình môi trường terminal thực hiện thông qua script biến môi trường:

```bash
export AWS_REGION=us-east-1
export AWS_DEFAULT_REGION=us-east-1
export AWS_PAGER=""

# Kiểm tra định danh phiên làm việc
aws sts get-caller-identity
```

---

## 2. Khảo sát hiện trạng các dịch vụ cốt lõi

Nhóm đã kiểm tra trạng thái ban đầu của 05 dịch vụ AWS bắt buộc sử dụng trong đề tài nhằm chuẩn bị cho đợt triển khai ở Tuần 2:

| Dịch vụ AWS | Lệnh kiểm tra CLI | Trạng thái hiện tại | Kế hoạch triển khai |
|---|---|---|---|
| **API Gateway (HTTP API v2)** | `aws apigatewayv2 get-apis` | `Items: []` (Chưa có API) | Khởi tạo API `serverless-payment-api` ở Tuần 2–3 |
| **AWS Lambda** | `aws lambda list-functions` | 05 hàm hệ thống mặc định của Lab | Tạo 03 hàm Lambda mới của dự án ở Tuần 2 |
| **Amazon DynamoDB** | `aws dynamodb list-tables` | `TableNames: []` (Chưa có bảng) | Tạo bảng `Wallets` và `Transactions` ở Tuần 2 |
| **AWS Secrets Manager** | `aws secretsmanager list-secrets` | `SecretList: []` (Chưa có secret) | Tạo secret `serverless-payment/jwt-secret` ở Tuần 2 |
| **Amazon CloudWatch Logs** | `aws logs describe-log-groups` | 03 log groups mặc định của Lab | Tạo log group riêng với retention 7 ngày ở Tuần 2 |
| **Amazon CloudWatch Alarms** | `aws cloudwatch describe-alarms` | `MetricAlarms: []` (Chưa có cảnh báo) | Cấu hình cảnh báo lỗi 4xx/5xx và chi phí ở Tuần 3 |

> **Ghi chú về tài nguyên có sẵn:** Trong tài khoản Learner Lab hiện có một số hàm Lambda và Log Group do hệ thống quản trị của Vocareum cài đặt sẵn (`MainMonitoringFunction`, `RedshiftOverwatch`,...). Nhóm tuân thủ nguyên tắc giữ nguyên, không chỉnh sửa hoặc xóa bất kỳ tài nguyên hệ thống nào.

---

## 3. Khảo sát phân quyền IAM & Vai trò `LabRole`

Theo chính sách của AWS Academy Learner Lab, sinh viên không được cấp quyền tạo người dùng IAM (IAM User) hay vai trò mới (IAM Role). Mọi dịch vụ cần thực thi đều phải tận dụng vai trò được cấu hình sẵn là `LabRole`.

Kết quả kiểm tra chi tiết:
- Lệnh `aws iam get-role --role-name LabRole` thực thi thành công, trả về ARN đầy đủ của role.
- Phân tích chính sách gắn kèm `LabRole` cho thấy role này sở hữu các quyền cần thiết để vận hành kiến trúc Serverless của đồ án:
  - Đọc/Ghi dữ liệu DynamoDB (`dynamodb:*`).
  - Ghi nhật ký CloudWatch Logs (`logs:CreateLogStream`, `logs:PutLogEvents`).
  - Đọc giá trị bảo mật từ AWS Secrets Manager (`secretsmanager:GetSecretValue`).
  - Quyền ủy quyền thực thi cho Lambda (`lambda:InvokeFunction`).
- Các hàm Lambda do nhóm tạo ở Tuần 2 sẽ được gán execution role này thông qua tham số `--role arn:aws:iam::930162821234:role/LabRole`.

---

## 4. Các ràng buộc kỹ thuật & Chính sách tuân thủ

1. **Phạm vi vùng (Region Policy):** Toàn bộ tài nguyên của dự án được triển khai thống nhất tại Region **`us-east-1`** (US East - N. Virginia), không phân tán sang các Region khác nhằm kiểm soát chặt chẽ ngân sách và giảm độ trễ giao tiếp giữa các dịch vụ.
2. **Kiến trúc tối ưu chi phí (Pure Serverless):** Không sử dụng máy chủ ảo EC2, cơ sở dữ liệu quan hệ RDS hay cổng mạng NAT Gateway. Mô hình serverless (API Gateway + Lambda + DynamoDB On-Demand) giúp tận dụng tối đa hạn mức miễn phí (Free Tier) và bảo vệ ngân sách $50 USD.
3. **Quy định gắn thẻ (Resource Tagging):** Mọi tài nguyên do nhóm khởi tạo từ Tuần 2 bắt buộc được gắn tag:
   - `Project`: `serverless-payment`
   - `Owner`: `Serverless-Team`
4. **Quy trình kết thúc phiên làm việc:**
   - Sau mỗi buổi thực hành, nhóm tiến hành kiểm kê tài nguyên đã tạo.
   - Nhấn **End Lab** trên giao diện Vocareum để tạm dừng phiên làm việc và bảo toàn ngân sách.
   - **Tuyệt đối không nhấn nút "Reset Lab"** để tránh bị xóa sạch toàn bộ mã nguồn và cấu hình đã triển khai.

---

## 5. Danh mục minh chứng kỹ thuật Tuần 1

Nhóm đã ghi lại đầy đủ 09 ảnh chụp màn hình minh chứng thao tác tại thư mục [`evidence/week01/`](../evidence/week01/):

| Mã minh chứng | Tệp tin | Nội dung xác nhận trên giao diện AWS |
|:---:|---|---|
| **B1-01** | [`B1-01-lab-started.png`](../evidence/week01/B1-01-lab-started.png) | Trạng thái phiên Vocareum Learner Lab đang chạy, ngân sách $0/$50 |
| **B1-02** | [`B1-02-region.png`](../evidence/week01/B1-02-region.png) | Vùng làm việc trên AWS Console là `us-east-1`, hiển thị Account ID |
| **B1-03** | [`B1-03-cli-config.png`](../evidence/week01/B1-03-cli-config.png) | Phiên bản AWS CLI `2.37.6` và cấu hình biến môi trường Region |
| **B1-04** | [`B1-04-services-console.png`](../evidence/week01/B1-04-services-console.png) | Danh mục 05 dịch vụ cốt lõi đã truy cập trên AWS Console |
| **B1-05** | [`B1-05-budget.png`](../evidence/week01/B1-05-budget.png) | Giao diện quản lý ngân sách ghi nhận mức tiêu thụ ban đầu `Used $0 of $50` |
| **B1-06** | [`B1-06-cloudshell.png`](../evidence/week01/B1-06-cloudshell.png) | Môi trường AWS CloudShell sẵn sàng chạy các lệnh quản trị |
| **B2-01** | [`B2-01-labrole.png`](../evidence/week01/B2-01-labrole.png) | Lệnh `aws iam get-role` xác nhận sự tồn tại của role `LabRole` |
| **B2-02** | [`B2-02-lambda-roles.png`](../evidence/week01/B2-02-lambda-roles.png) | Khảo sát danh sách các hàm Lambda hệ thống và IAM role gắn kèm |
| **B2-03** | [`B2-03-cloudwatch-alarms.png`](../evidence/week01/B2-03-cloudwatch-alarms.png) | Truy vấn CloudWatch Alarms xác nhận chưa có cảnh báo phát sinh |

---

## 6. Kết luận & Sẵn sàng cho Tuần 2

Môi trường AWS Academy Learner Lab đã được khảo sát kỹ lưỡng và hoàn toàn đáp ứng các điều kiện kỹ thuật để bước vào Tuần 2. Nhóm sẵn sàng tiến hành khởi tạo cơ sở dữ liệu DynamoDB, cấu hình Secrets Manager và triển khai các hàm Lambda xử lý nghiệp vụ theo đúng kế hoạch đề ra.
