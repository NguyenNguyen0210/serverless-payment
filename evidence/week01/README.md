# DANH MỤC MINH CHỨNG KỸ THUẬT TUẦN 1 (EVIDENCE CATALOG - WEEK 1)

> **Học phần:** Cloud Computing – Đợt 1, Năm học 2026–2027  
> **Dự án:** Cổng thanh toán giả lập không máy chủ (`serverless-payment`)  
> **Người thực hiện:** Nguyễn Nguyên  
> **Nền tảng:** AWS Academy Learner Lab (Vocareum) · **Region:** `us-east-1`  
> **Thời điểm ghi nhận:** Ngày 10/10/2026  

---

## 1. Danh sách ảnh chụp màn hình kiểm chứng (Console & CLI)

Toàn bộ ảnh minh chứng được thực hiện trực tiếp trên giao diện AWS Console và terminal AWS CloudShell/CLI, bảo đảm tính xác thực với Account ID `930162821234` và dấu mốc thời gian rõ ràng:

| Mã | Tên tệp ảnh | Nội dung kiểm tra & Xác nhận kỹ thuật |
|:---:|---|---|
| **B1-01** | [`B1-01-lab-started.png`](B1-01-lab-started.png) | Trạng thái phiên AWS Learner Lab đang chạy (chấm xanh); thời gian phiên còn lại và ngân sách khởi đầu $0/$50. |
| **B1-02** | [`B1-02-region.png`](B1-02-region.png) | Menu vùng trên AWS Console xác nhận Region hoạt động là `us-east-1` (US East - N. Virginia). |
| **B1-03** | [`B1-03-cli-config.png`](B1-03-cli-config.png) | Lệnh `aws --version` (`aws-cli/2.37.6`) và `aws configure list` xác nhận Region nhận từ biến môi trường terminal. |
| **B1-04** | [`B1-04-services-console.png`](B1-04-services-console.png) | Giao diện AWS Console hiển thị 5 dịch vụ cốt lõi đã truy cập: API Gateway, Lambda, DynamoDB, Secrets Manager, CloudWatch. |
| **B1-05** | [`B1-05-budget.png`](B1-05-budget.png) | Màn hình chi phí của Learner Lab xác nhận mức tiêu thụ ban đầu `Used $0 of $50`. |
| **B1-06** | [`B1-06-cloudshell.png`](B1-06-cloudshell.png) | Môi trường AWS CloudShell tại Region `us-east-1` sẵn sàng thực thi các câu lệnh CLI quản trị. |
| **B2-01** | [`B2-01-labrole.png`](B2-01-labrole.png) | Lệnh `aws iam get-role --role-name LabRole` xác nhận quyền đọc metadata của execution role có sẵn. |
| **B2-02** | [`B2-02-lambda-roles.png`](B2-02-lambda-roles.png) | Truy vấn danh sách Lambda hiện hữu trong Lab và kiểm tra các IAM Role gắn kèm. |
| **B2-03** | [`B2-03-cloudwatch-alarms.png`](B2-03-cloudwatch-alarms.png) | Lệnh `aws cloudwatch describe-alarms` xác nhận hệ thống chưa phát sinh alarm nào. |

---

## 2. Tiêu chuẩn bảo mật thông tin & Liêm chính học thuật

- **Bảo mật danh tính:** Ảnh minh chứng phục vụ đối chiếu nội bộ môn học với giảng viên hướng dẫn. Tuyệt đối không để lộ Access Key, Session Token hay JWT secret.
- **Liêm chính học thuật:** Toàn bộ ảnh được chụp từ tài khoản thực tế của sinh viên trên hệ thống Vocareum, không can thiệp chỉnh sửa dữ liệu số hoặc thời gian.
