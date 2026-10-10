# Quy định quản lý tài nguyên & ngân sách – Tuần 1

**Dự án:** `serverless-payment`  
**Phụ trách:** Nguyễn Nguyên
**Region mặc định:** `us-east-1`  
**Nguồn:** README AWS Learner Lab và ảnh màn hình/CLI ngày 10/10/2026.

## 1. Ngân sách quan sát

| Thời điểm / nguồn | Used | Tổng ngân sách | Ghi chú |
|---|---:|---:|---|
| 10/10/2026, ảnh Learner Lab | $0 | $50 | Giá trị hiển thị, có thể trễ 8–12 giờ |
| Buổi tiếp theo | _Cần cập nhật_ | $50 (nếu ngân sách không đổi) | Chụp ảnh mới |
| Cuối Tuần 1 | _Cần cập nhật_ | _Cần cập nhật_ | Dùng số hiển thị thực tế |

Không khẳng định dự án 'miễn phí' từ `Used $0`: một số chi phí xuất hiện trễ; các tài nguyên còn tồn tại có thể tiếp tục tính phí.

## 2. Quy tắc tài nguyên mới

- Region: **`us-east-1`**.
- Execution role AWS Lambda: **`LabRole`** có sẵn; không tạo IAM user/role.
- Tags khi dịch vụ hỗ trợ: `Project=serverless-payment`; `Owner=<mã thành viên/nhóm được thống nhất>`.
- Tiền tố tên dự án gợi ý: `spg-` (chỉ áp dụng sau khi nhóm thống nhất tên chính thức).
- Chỉ tạo những tài nguyên đã được thống nhất với Thành viên A; Tuần 1 hiện mới kiểm tra read-only.
- Không tạo NAT Gateway, EC2, RDS hoặc cấu hình VPC Lambda nếu không có nhu cầu đã được phê duyệt.
- Không lưu key, token, JWT secret trên GitHub; sử dụng AWS Secrets Manager khi triển khai.

## 3. Kiểm kê tài nguyên

| Loại | Tên/ID | Trạng thái | Nhóm tạo? | Quy tắc xử lý |
|---|---|---|---|---|
| Lambda | `RedshiftOverwatch` | Có sẵn trong Lab | Không xác minh | KHÔNG sửa/xóa |
| Lambda | `MainMonitoringFunction` | Có sẵn trong Lab | Không xác minh | KHÔNG sửa/xóa |
| Lambda | `ModLabRole` | Có trong ảnh kiểm tra | Không xác minh | KHÔNG sửa/xóa |
| Lambda | `RoleCreationFunction` | Có trong ảnh kiểm tra | Không xác minh | KHÔNG sửa/xóa |
| Lambda | `RedshiftEventSubscription` | Có trong ảnh kiểm tra | Không xác minh | KHÔNG sửa/xóa |
| DynamoDB | Chưa có bảng khi kiểm tra | 0 | Chưa tạo | Tuần 2 tạo theo schema của A |
| API Gateway | Chưa có REST/HTTP API khi kiểm tra | 0 | Chưa tạo | Tuần 2 tạo theo contract của A |
| Secrets Manager | Chưa có secret khi kiểm tra | 0 | Chưa tạo | Tuần 2 theo thiết kế bảo mật |
| CloudWatch Alarms | Chưa có alarm khi kiểm tra | 0 | Chưa tạo | Thiết kế giám sát ở Tuần 3 |
| **Tài nguyên dự án mới** | **Chưa có bằng chứng đã tạo trong Tuần 1** | **Chưa xác định** | — | Khi tạo phải bổ sung vào bảng |

**CloudWatch Logs đã có 3 log group:** `/aws/lambda/RedshiftEventSubscription`, `/aws/lambda/RedshiftOverwatch`, `/aws/lambda/RoleCreationFunction`; xem là tài nguyên hiện hữu chưa rõ nguồn gốc, **không xóa**.

## 4. Quy trình kết thúc buổi làm việc

1. Lưu mã nguồn/tài liệu/evidence và ghi worklog.
2. Kiểm kê tài nguyên **do nhóm tạo** trong `us-east-1` (kiểm tra cả `us-west-2` nếu đã dùng), gắn tag và ghi ARN/tên.
3. Dừng/xóa tài nguyên không còn cần thiết; đối với tài nguyên serverless không có nút `Stop` chung, chỉ xóa đúng tài nguyên nhóm sở hữu khi được phép.
4. Chụp màn hình ngân sách và đánh dấu khoản chưa phản ánh do cập nhật chậm.
5. Có thể kết thúc phiên Lab bằng `End Lab`; **không nhấn `Reset`** vì có thể xóa vĩnh viễn mọi tài nguyên/data. Kết thúc session không xóa mặc định mọi tài nguyên đã tạo.

## 5. Kế hoạch chi phí và dọn dẹp Cuối kỳ

- Ghi tài nguyên và ngày tạo/ngày xóa, số lượng request, lượng lưu trữ và chi phí quan sát.
- CloudWatch Logs có thể phát sinh phí lưu trữ/ingest; cần thiết lập retention phù hợp khi triển khai.
- Secrets Manager có thể có chi phí riêng ngay cả khi ít gọi API; xóa secret thử nghiệm không cần thiết theo quy trình an toàn.
- Cuối kỳ kiểm tra bảng DynamoDB, secret, API Gateway, Lambda, log groups, CloudWatch alarms và đối chiếu chi phí.
- Không xóa tài nguyên hệ thống Learner Lab hoặc tài nguyên do nhóm khác tạo.

## 6. Quyền ghi – Chưa kết luận

Các lệnh kiểm tra tuần 1 là `get`, `list`, `describe`, nên không xác minh quyền ghi. Quyền `lambda:CreateFunction`, `iam:PassRole`, `dynamodb:TransactWriteItems`, `secretsmanager:CreateSecret` và thao tác tương tự sẽ được kiểm tra trong tuần 2 qua tài nguyên đúng phạm vi thiết kế.
