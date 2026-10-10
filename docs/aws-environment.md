# AWS Learner Lab – Environment & CLI Access Verification

**Dự án:** Cổng thanh toán giả lập với API Gateway, Lambda Authorizer và DynamoDB Transaction  
**Tuần:** 1 · **Thành viên phụ trách:** B · **Nhiệm vụ:** B1, B2  
**Ngày ghi nhận:** 10/10/2026 (giờ Việt Nam, UTC+7; theo ảnh màn hình)  
**Thời gian thực tế đã làm:** CHƯA GHI NHẬN – bổ sung trong `docs/worklog.md`  
**Nguồn:** AWS Learner Lab README (hướng dẫn cập nhật 24/06/2025), ảnh chụp AWS Console/CloudShell, log CLI do thành viên B thực hiện.

> Phạm vi: kiểm tra **quyền đọc/khả năng truy cập** và môi trường. Bài kiểm tra chưa xác minh quyền tạo/sửa/xóa tài nguyên, quyền `dynamodb:TransactWriteItems` hay quyền `iam:PassRole`. Không được diễn giải PASS bên dưới là tất cả quyền đã được cấp.

## 1. B1 – Thông tin môi trường

| Hạng mục | Giá trị quan sát | Kết luận |
|---|---|---|
| Nền tảng | AWS Academy Learner Lab trên Vocareum | Hoạt động, chỉ báo AWS màu xanh trên ảnh |
| AWS Account ID | `9301••••1234` (che trong tài liệu; đầy đủ ở ảnh minh chứng nội bộ) | Có Account ID khớp giữa Console và AWS STS |
| AWS Console Region | **US East (N. Virginia), `us-east-1`** | PASS |
| CloudShell Region | `us-east-1` | PASS |
| AWS CLI | `aws-cli/2.37.6` | PASS |
| Python CloudShell (trong chuỗi phiên bản CLI) | `Python/3.14.6` | Chỉ là phiên bản Python dùng bởi CLI, không chứng minh runtime Lambda |
| Xác thực AWS CLI | `aws sts get-caller-identity` trả về `UserId`, `Account`, `Arn` | PASS |
| Tài khoản thực thi lệnh CLI | STS cho thấy **assumed role `voclabs`** | Phân biệt với **`LabRole`** gắn cho Lambda |
| IAM LabRole | `aws iam get-role --role-name LabRole` trả `Name=LabRole`, `Arn=...:role/LabRole` | PASS – role có tồn tại và đọc được |
| Ngân sách Learner Lab | **Used $0 of $50** (hiển thị tại thời điểm chụp) | Đã ghi nhận; không phải số liệu chi phí thời gian thực |
| Phiên Lab | Đang hoạt động khi chụp; đồng hồ hiển thị khoảng `03:32`–`03:56` ở các ảnh | PASS – có ảnh phiên, không suy ra thời lượng công việc |

Lệnh cấu hình terminal đã dùng:

```bash
export AWS_REGION=us-east-1
export AWS_DEFAULT_REGION=us-east-1
export AWS_PAGER=""
aws configure list
aws sts get-caller-identity
```

**Giải thích:** Trước khi đặt biến môi trường, `aws configure get region` không in giá trị. Sau khi đặt, `aws configure list` xác nhận Region từ `env`. Không cần chỉnh tệp AWS credentials. Biến môi trường cần đặt lại nếu mở terminal mới và không được duy trì.

## 2. B1 – Khả năng truy cập các dịch vụ

| Dịch vụ | Lệnh đọc | Quan sát thực tế | Đánh giá |
|---|---|---|---|
| API Gateway REST | `aws apigateway get-rest-apis --region us-east-1` | `items: []` | PASS – truy cập lệnh liệt kê; 0 REST API lúc kiểm tra |
| API Gateway HTTP | `aws apigatewayv2 get-apis --region us-east-1` | `Items: []` | PASS – truy cập lệnh liệt kê; 0 HTTP API lúc kiểm tra |
| Lambda | `aws lambda list-functions --region us-east-1` | Ban đầu trả ít mục hơn; ảnh B2 sau đó cho thấy **5 Lambda** | PASS – liệt kê được |
| DynamoDB | `aws dynamodb list-tables --region us-east-1` | `TableNames: []` | PASS – 0 bảng lúc kiểm tra |
| Secrets Manager | `aws secretsmanager list-secrets --region us-east-1` | `SecretList: []` | PASS – 0 secret lúc kiểm tra |
| CloudWatch Logs | `aws logs describe-log-groups --region us-east-1` | 3 log groups được trả về | PASS – liệt kê được |
| CloudWatch Alarms | `aws cloudwatch describe-alarms --region us-east-1 --no-cli-pager` | `MetricAlarms: []`, `CompositeAlarms: []`, `LogAlarms: []` | PASS – 0 alarm được trả về |

**Không sửa/xóa các tài nguyên tồn tại sẵn.** Ảnh `B2-02-lambda-roles.png` liệt kê 5 Lambda: `RedshiftOverwatch`, `MainMonitoringFunction`, `ModLabRole`, `RoleCreationFunction`, `RedshiftEventSubscription`. Danh sách Lambda ở những thời điểm khác nhau có thể khác nhau vì tài nguyên lab/hệ thống thay đổi; số liệu 5 ở đây là ảnh sau cùng.

CloudWatch Logs đã liệt kê 3 nhóm: `/aws/lambda/RedshiftEventSubscription`, `/aws/lambda/RedshiftOverwatch`, `/aws/lambda/RoleCreationFunction`. Chưa có bằng chứng đây là tài nguyên do nhóm tạo.

## 3. B2 – CLI và role

| Kiểm tra | Kết quả | Bằng chứng |
|---|---|---|
| `aws --version` | `aws-cli/2.37.6` | `B1-03-cli-config.png` |
| `aws configure list` | AWS CLI dùng credentials dạng `container-role`; Region `us-east-1` từ `env` | `B1-03-cli-config.png` |
| `aws sts get-caller-identity` | PASS; STS trả danh tính phiên `voclabs` | Log CLI B1 và ảnh Console có Account ID |
| `aws iam get-role --role-name LabRole` | PASS; role có tên `LabRole` và ARN hợp lệ | `B2-01-labrole.png` |
| `aws lambda list-functions --query ...Role...` | PASS; `MainMonitoringFunction` sử dụng `LabRole` | `B2-02-lambda-roles.png` |
| `aws cloudwatch describe-alarms` | PASS; không có alarm được liệt kê | `B2-03-cloudwatch-alarms.png` |

**Điểm giới hạn:** `get-role` chỉ xác nhận đọc được metadata IAM. Lambda dùng `LabRole` trong ảnh không đồng nghĩa người thực hiện được quyền `iam:PassRole`. Quyền triển khai sẽ được kiểm tra khi tạo đúng tài nguyên của đồ án ở Tuần 2, có ghi log lỗi nếu thất bại.

### Quyền ghi vẫn CHƯA kiểm chứng

- `apigateway:POST` / `apigatewayv2:CreateApi`
- `lambda:CreateFunction`, `lambda:UpdateFunctionCode`, `iam:PassRole`
- `dynamodb:CreateTable`, `dynamodb:TransactWriteItems`
- `secretsmanager:CreateSecret`, `secretsmanager:GetSecretValue`
- `logs:CreateLogGroup` / cấu hình giám sát

Không chạy lệnh tạo/xóa ngoài phạm vi dự án chỉ nhằm thử quyền.

## 4. Ràng buộc và quyết định kỹ thuật

- Region thống nhất: `us-east-1`; README chỉ cho phép `us-east-1`/`us-west-2` (trừ ngoại lệ dịch vụ).
- Dùng `LabRole` có sẵn làm execution role cho Lambda; không tạo IAM user/role mới.
- Theo README, tối đa 10 Lambda execution environments thực thi đồng thời trong Lab.
- Không cần EC2, NAT Gateway hoặc VPC mới cho thiết kế serverless cơ bản.
- Gắn tag `Project=serverless-payment`, `Owner=<mã SV/nhóm>` cho tài nguyên mới hỗ trợ tag.
- Không nhấn `Reset` trừ khi chấp nhận xóa toàn bộ dữ liệu/tài nguyên; kết thúc session **không tự động xóa** mọi tài nguyên.
- Ngân sách `Used $0 of $50` là giá trị quan sát, AWS Budgets có thể cập nhật trễ 8–12 giờ.

## 5. Danh sách evidence

| Ảnh | Nội dung / thời điểm hiển thị |
|---|---|
| `evidence/week01/B1-01-lab-started.png` | Vocareum Learner Lab, trạng thái AWS, đồng hồ và ngân sách |
| `evidence/week01/B1-02-region.png` | Region N. Virginia / us-east-1 và Account ID |
| `evidence/week01/B1-03-cli-config.png` | Phiên bản AWS CLI và cấu hình Region |
| `evidence/week01/B1-04-services-console.png` | 5 dịch vụ trong Recently visited |
| `evidence/week01/B1-05-budget.png` | `Used $0 of $50` trên Learner Lab |
| `evidence/week01/B2-01-labrole.png` | `get-role LabRole` trả thành công |
| `evidence/week01/B2-02-lambda-roles.png` | Danh sách 5 Lambda và role tương ứng |
| `evidence/week01/B2-03-cloudwatch-alarms.png` | CloudWatch Alarms trả mảng rỗng |
| `evidence/week01/B1-06-cloudshell.png` | CloudShell hoạt động, terminal sẵn sàng |

**Quản lý dữ liệu:** Evidence hiển thị Account ID, tên phiên đăng nhập và thông tin trên trình duyệt. Chỉ commit vào **private repo** nếu nhóm được phép. Nếu repo public, lưu evidence ngoài repo hoặc biên tập che bớt thông tin cá nhân trước khi công khai. Không có khóa bí mật nào được đưa vào các tệp markdown này.

## 6. Checklist nghiệm thu

- [x] AWS Learner Lab đã khởi động và truy cập Console.
- [x] Console/CloudShell Region `us-east-1`.
- [x] AWS CLI và STS hoạt động.
- [x] Đã kiểm tra quyền đọc 5 dịch vụ cần thiết.
- [x] Đã xác minh `LabRole` bằng IAM read-only API.
- [x] Đã kiểm tra CloudWatch Alarms.
- [x] Có ảnh ngân sách và môi trường.
- [x] Đã lưu ảnh minh chứng trong gói bàn giao.\

