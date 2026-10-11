# CHÍNH SÁCH QUẢN TRỊ TÀI NGUYÊN & KIỂM SOÁT NGÂN SÁCH

> **Học phần:** Cloud Computing (Điện toán đám mây) – Đợt 1, Năm học 2026–2027  
> **Dự án:** Cổng thanh toán giả lập không máy chủ (`serverless-payment`)  
> **Người thực hiện:** Nguyễn Nguyên  
> **Phối hợp thực hiện:** Vũ Minh Đức  
> **Nền tảng:** AWS Academy Learner Lab · **Ngân sách cấp:** $50,00 USD  
> **AWS Region:** `us-east-1` (US East - N. Virginia)  

---

## 1. Mục tiêu và Nguyên tắc quản trị

Môi trường thực hành AWS Academy Learner Lab cung cấp hạn mức ngân sách cố định **$50,00 USD** cho mỗi sinh viên trong suốt kỳ học. Nhóm thiết lập chính sách quản trị tài nguyên nhằm bảo đảm:
1. **Kiểm soát chi phí nghiêm ngặt:** Không để xảy ra tình trạng cạn kiệt ngân sách trước khi hoàn thành đồ án và bảo vệ trước giảng viên.
2. **Minh bạch và trách nhiệm:** Mọi tài nguyên khởi tạo đều có mục đích rõ ràng, được gắn thẻ (tag) nhận diện và theo dõi thường xuyên.
3. **An toàn hệ thống:** Không tác động vào các tài nguyên mặc định của phòng lab Vocareum, tránh rủi ro lỗi tài khoản.

---

## 2. Theo dõi & Kiểm soát ngân sách $50 USD

- **Trạng thái khởi đầu (Tuần 1):** `Used $0 of $50` (xác nhận qua ảnh minh chứng `B1-05-budget.png`).
- **Độ trễ cập nhật của AWS Billing:** Hệ thống ghi nhận chi phí của AWS thường có độ trễ từ 8–12 giờ so với thời điểm tài nguyên thực tế hoạt động. Do đó, nhóm theo dõi ngân sách định kỳ sau mỗi phiên làm việc và không dựa hoàn toàn vào số liệu tức thời.
- **Biện pháp tối ưu hóa chi phí:**
  - **Kiến trúc Pure Serverless:** Chỉ sử dụng API Gateway HTTP API, Lambda và DynamoDB On-Demand. Đây là các dịch vụ tính tiền theo lượng request thực tế, gần như miễn phí trong quy mô kiểm thử đồ án.
  - **Kiểm soát lưu lượng từ Ingress (Rate Limiting):** API Gateway Throttling từ chối sớm các request vượt ngưỡng (HTTP 429), ngăn chặn tình trạng vòng lặp gọi API vô tận hoặc tấn công DoS làm cạn kiệt ngân sách tính toán của Lambda.
  - **Hàng đợi Dead Letter Queue (Amazon SQS):** Sử dụng Standard Queue (`serverless-payment-dlq`) nằm hoàn toàn trong hạn mức AWS Free Tier (1.000.000 request/tháng miễn phí), không phát sinh phí duy trì theo giờ.
  - **Tuyệt đối không dùng tài nguyên tính phí theo giờ cao:** Không tạo NAT Gateway ($0,045/giờ $\approx$ $1,08/ngày), EC2 Instances hay Amazon RDS.
  - **Giới hạn lưu trữ CloudWatch Logs:** Thiết lập thời hạn lưu log (Log Retention) là 7 ngày để tránh phát sinh chi phí lưu trữ không cần thiết.

---

## 3. Quy chuẩn định danh & Gắn thẻ tài nguyên (Tagging Standards)

Mọi tài nguyên được nhóm tạo ra trên AWS bắt buộc phải tuân thủ chuẩn đặt tên và gắn thẻ định danh:

### 3.1. Tiêu chuẩn gắn thẻ (Tags)
- `Project`: `serverless-payment`
- `Owner`: `Serverless-Team`
- `Environment`: `Lab`

### 3.2. Tiêu chuẩn đặt tên (Naming Convention)
- **API Gateway:** `serverless-payment-api` (kèm Route Throttling)
- **Lambda Functions:** `serverless-payment-token`, `serverless-payment-authorizer`, `serverless-payment-transfer`
- **DynamoDB Tables:** `Wallets`, `Transactions`
- **Amazon SQS DLQ:** `serverless-payment-dlq`
- **Secrets Manager:** `serverless-payment/jwt-secret`
- **CloudWatch Log Groups:** `/aws/lambda/serverless-payment-*`

---

## 4. Bảng kiểm kê tài nguyên hệ thống (Resource Inventory)

| Phân nhóm | Tên tài nguyên | Vai trò trong hệ thống | Kế hoạch quản lý |
|---|---|---|---|
| **Tài nguyên Lab có sẵn** | `MainMonitoringFunction`, `RedshiftOverwatch`,... | Quản trị nền tảng của Vocareum | **Giữ nguyên, tuyệt đối không chỉnh sửa hoặc xóa** |
| **IAM Role có sẵn** | `arn:aws:iam::<ACCOUNT_ID>:role/LabRole` | Cung cấp quyền thực thi cho Lambda | Dùng làm Execution Role cho toàn bộ Lambda dự án |
| **Dự án: Cơ sở dữ liệu** | Bảng `Wallets` và `Transactions` | Lưu trữ thông tin ví và lịch sử giao dịch | Khởi tạo ở Tuần 2 theo thiết kế CSDL DynamoDB |
| **Dự án: API Gateway** | `serverless-payment-api` (HTTP API v2) | Tiếp nhận HTTPS request, Rate Limiting & định tuyến | Khởi tạo ở Tuần 2–3 theo hợp đồng API |
| **Dự án: Lambda Functions** | Token, Authorizer, Transfer functions | Xử lý logic nghiệp vụ và xác thực JWT | Triển khai mã nguồn Python ở Tuần 2 |
| **Dự án: Hàng đợi lỗi (DLQ)** | `serverless-payment-dlq` (Amazon SQS) | Lưu vết sự cố hệ thống nghiêm trọng phục vụ đối soát | Khởi tạo ở Tuần 2–3 theo thiết kế kiên cường |
| **Dự án: Quản lý khóa** | `serverless-payment/jwt-secret` | Lưu trữ an toàn khóa ký JWT | Khởi tạo ở Tuần 2 trên AWS Secrets Manager |
| **Dự án: Giám sát** | Log Groups, Metric Alarms | Theo dõi vận hành và phát hiện lỗi | Cấu hình log retention 7 ngày ở Tuần 3 |

---

## 5. Quy trình làm việc sau mỗi buổi thực hành

Để đảm bảo an toàn cho dữ liệu và ngân sách tài khoản, nhóm thực hiện quy trình chuẩn sau mỗi phiên làm việc:
1. **Kiểm tra và commit mã nguồn:** Đẩy toàn bộ mã nguồn, tài liệu và ảnh minh chứng lên Git repository.
2. **Kiểm kê tài nguyên đang chạy:** Xác nhận không có tài nguyên tính phí theo giờ nào bị bỏ quên.
3. **Kiểm tra mức tiêu thụ ngân sách:** Đối soát lại số dư tài khoản trên màn hình Vocareum.
4. **Kết thúc phiên làm việc:**
   - Nhấn **End Lab** trên giao diện điều khiển của Learner Lab để dừng phiên và ngắt đồng hồ đếm giờ.
   - **Cảnh báo quan trọng:** Tuyệt đối không bao giờ nhấn nút **"Reset Lab"** vì thao tác này sẽ xóa sạch toàn bộ tài khoản và các tài nguyên đã dày công cấu hình.

---

## 6. Kế hoạch dọn dẹp & Báo cáo chi phí cuối kỳ (Tuần 4)

Vào Tuần 4, sau khi hoàn thành toàn bộ kịch bản kiểm thử và quay video demo đồ án, nhóm sẽ thực hiện:
1. Chạy kịch bản tự động dọn dẹp (cleanup script) để xóa các bảng DynamoDB, hàm Lambda, API Gateway và secret đã tạo nhằm đưa tài khoản về trạng thái ban đầu.
2. Xuất bảng đối soát chi phí chi tiết từ AWS Billing / Learner Lab, tổng hợp mức chi phí thực tế phát sinh (kỳ vọng $\le$ $5 USD).
3. Đính kèm báo cáo chi phí vào tài liệu nộp cuối kỳ cho giảng viên hướng dẫn.
