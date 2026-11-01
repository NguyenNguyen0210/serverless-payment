# BÁO CÁO TIẾN ĐỘ TUẦN 4

## KIỂM THỬ TỔNG THỂ, NGHIỆM THU VÀ TỔNG KẾT DỰ ÁN SERVERLESS PAYMENT GATEWAY

**Đề tài:** Cổng thanh toán giả lập với API Gateway, Lambda Authorizer và DynamoDB Transaction

**Nhóm sinh viên:** Serverless (02 thành viên)

- **Vũ Minh Đức:** Phụ trách nghiệp vụ chuyển tiền, DynamoDB Transaction, Idempotency, Concurrency và kiểm thử tính nhất quán.

- **Nguyễn Nguyên:** Phụ trách AWS Infrastructure, API Gateway, JWT Authorizer, Secrets Manager, CloudWatch, SQS và kiểm thử tích hợp.

**Giảng viên hướng dẫn (GVHD):** ThS. Huỳnh Xuân Phụng

**Học phần:** Điện toán đám mây – Đợt 1, năm học 2026–2027

**Thời gian thực hiện Tuần 4:** 26/10/2026 – 01/11/2026

**Môi trường triển khai:** AWS Academy Learner Lab

**Region:** us-east-1 (US East – N. Virginia)

**IAM Execution Role:** LabRole

**GitHub Repository:** https://github.com/NguyenNguyen0210/serverless-payment

**Video Demo:** https://drive.google.com/drive/folders/1FnaAXXF94_mIkvJ5nLq5XsgekHrrIcKa?usp=drive_link

---

## 1. MỤC TIÊU VÀ NỘI DUNG TUẦN 4

Tuần 4 là giai đoạn cuối cùng của dự án, tập trung vào kiểm thử tổng thể, đánh giá độ tin cậy, bảo mật, giám sát và hoàn thiện hồ sơ nghiệm thu.

Trên cơ sở kết quả đạt được trong ba tuần trước, nhóm tiến hành kiểm chứng toàn bộ luồng hoạt động của cổng thanh toán giả lập thông qua AWS API Gateway, Lambda Authorizer và DynamoDB.

Các mục tiêu chính:

1. Kiểm thử tích hợp năm API endpoints từ client đến các dịch vụ AWS.

2. Xác minh tính nguyên tử và nhất quán của giao dịch chuyển tiền sử dụng DynamoDB TransactWriteItems.

3. Kiểm tra khả năng chống xử lý trùng request bằng Idempotency-Key và SHA-256 requestHash.

4. Kiểm thử các request đồng thời nhằm phát hiện race condition và nguy cơ trừ tiền nhiều lần.

5. Đánh giá xác thực JWT, phân quyền truy cập ví và bảo vệ khóa bí mật.

6. Kiểm thử Route Throttling, CloudWatch Logs, Dashboard, Alarms và Amazon SQS.

7. Rà soát tài nguyên, ngân sách AWS Learner Lab, tài liệu GitHub và chuẩn bị video demo cuối kỳ.

## 2. TỔNG QUAN HỆ THỐNG SAU BỐN TUẦN

### 2.1. Kiến trúc triển khai

Hệ thống sử dụng kiến trúc Serverless trên AWS, gồm các thành phần:

| Dịch vụ | Chức năng |
|---|---|
| API Gateway HTTP API v2 | Tiếp nhận request, định tuyến và giới hạn tốc độ truy cập |
| AWS Lambda | Xử lý xác thực, chuyển tiền và truy vấn dữ liệu |
| DynamoDB | Lưu thông tin ví, giao dịch và idempotency |
| Secrets Manager | Lưu khóa ký JWT và demoAccessCode |
| CloudWatch | Ghi log, theo dõi metrics và cảnh báo |
| Amazon SQS | Tiếp nhận thông tin sự cố phục vụ đối soát |

Hệ thống có năm Lambda Functions:

- `serverless-payment-token`

- `serverless-payment-authorizer`

- `serverless-payment-transfer`

- `serverless-payment-wallet-query`

- `serverless-payment-transaction-query`

### 2.2. Các API đã triển khai

| Method | Endpoint | Chức năng |
|---|---|---|
| POST | `/auth/token` | Cấp JWT |
| POST | `/transfers` | Chuyển tiền nguyên tử |
| GET | `/wallets/{walletId}` | Tra cứu ví |
| GET | `/transactions/{transactionId}` | Tra cứu giao dịch |
| GET | `/wallets/{walletId}/transactions` | Tra cứu lịch sử giao dịch |

Bốn API nghiệp vụ được bảo vệ bằng Lambda Authorizer sử dụng PyJWT HS256. API cấp token được công khai phục vụ xác thực demo.

### 2.3. Cơ sở dữ liệu DynamoDB

Hệ thống sử dụng ba bảng DynamoDB với chế độ On-Demand:

- `serverless-payment-wallets`: Quản lý số dư, chủ sở hữu, đơn vị tiền tệ và trạng thái ví.

- `serverless-payment-transactions`: Lưu lịch sử giao dịch chuyển tiền.

- `serverless-payment-idempotency`: Lưu khóa chống xử lý trùng và kết quả giao dịch tương ứng.

Bảng Transactions có hai Global Secondary Index:

- `FromWalletIndex`: Truy vấn giao dịch gửi đi.

- `ToWalletIndex`: Truy vấn giao dịch nhận vào.

Kiến trúc này được nhóm áp dụng chính thức từ Tuần 3, thay cho mô hình Single-Table ban đầu của Tuần 1.

## 3. KẾT QUẢ KIỂM THỬ TỔNG THỂ TUẦN 4

### 3.1. Kiểm thử tích hợp năm API endpoints

Nhóm đã thực hiện kiểm thử API trên môi trường AWS Academy Learner Lab thông qua Postman và AWS CloudShell.

Các kết quả được ghi nhận:

| Mã | Kiểm thử | Kết quả ghi nhận |
|---|---|---|
| B4-03 | POST /auth/token | HTTP 200 OK |
| B4-04 | GET /wallets/W001 | HTTP 200 OK |
| B4-05 | GET /wallets/W002 với JWT user-a | HTTP 403 Forbidden |
| B4-06 | POST /transfers | HTTP 201 Created |
| B4-07 | GET /transactions/{transactionId} | HTTP 200 OK |
| B4-08 | GET /wallets/W001/transactions | HTTP 200 OK |

Kết quả cho thấy các API chính đã được tích hợp và có minh chứng phản hồi trên AWS. Chức năng phân quyền ví cũng được kiểm tra bằng trường hợp người dùng truy cập tài nguyên không thuộc sở hữu.

### 3.2. Kiểm thử giao dịch DynamoDB TransactWriteItems

Transfer Lambda sử dụng một lệnh `TransactWriteItems` với bốn thao tác nguyên tử:

1. Ghi bản ghi idempotency.

2. Trừ số dư ví nguồn.

3. Cộng số dư ví đích.

4. Ghi bản ghi lịch sử giao dịch.

Nhóm thực hiện giao dịch chuyển 10.000 VND từ ví W001 sang ví W002.

**Kết quả đối soát được ghi nhận trong minh chứng Tuần 4:**

| Ví | Trước giao dịch | Sau giao dịch | Chênh lệch |
|---|---:|---:|---:|
| W001 | 73.000 VND | 63.000 VND | −10.000 VND |
| W002 | 77.000 VND | 87.000 VND | +10.000 VND |
| **Tổng cộng** | **150.000 VND** | **150.000 VND** | **0 VND** |

API trả về HTTP `201 Created`, kèm `transactionId`, trạng thái `SUCCESS` và `replayed: false`.

Dữ liệu sau giao dịch cho thấy số tiền trừ khỏi ví nguồn bằng đúng số tiền cộng vào ví đích, đồng thời tổng số dư hai ví không thay đổi.

**Minh chứng:** B4-06 và B4-09.

### 3.3. Kiểm thử Idempotency-Key

Nhóm kiểm tra cơ chế chống xử lý trùng bằng cách gửi lại request có cùng Idempotency-Key.

**Trường hợp 1 – Cùng key, cùng payload**

- Request đầu tiên xử lý chuyển tiền thành công với HTTP 201.

- Request tiếp theo sử dụng cùng key và payload.

- API trả HTTP 200 OK và `replayed: true`.

- Hệ thống sử dụng kết quả giao dịch đã lưu thay vì thực hiện chuyển tiền lần thứ hai.

**Trường hợp 2 – Cùng key, khác payload**

- Giữ nguyên Idempotency-Key nhưng thay đổi nội dung chuyển tiền.

- Hệ thống phát hiện requestHash không trùng khớp.

- API trả HTTP 409 `IDEMPOTENCY_KEY_CONFLICT`.

- Yêu cầu không được thực hiện như một giao dịch chuyển tiền mới.

Kết quả này chứng minh cơ chế idempotency giúp phòng tránh giao dịch bị xử lý lặp do client gửi lại request hoặc thao tác chuyển tiền nhiều lần.

**Minh chứng:** B4-10 và B4-11.

### 3.4. Kiểm thử Concurrency và Transaction Consistency

Nhóm thực hiện bài kiểm thử gửi năm request song song với cùng Idempotency-Key bằng script Bash trên AWS CloudShell.

Mục tiêu là kiểm tra khả năng xử lý các request cạnh tranh khi nhiều yêu cầu cùng truy cập một bản ghi idempotency và cùng cập nhật số dư ví.

Theo danh mục minh chứng, bài kiểm thử ghi nhận không xuất hiện tình trạng thực hiện giao dịch trùng hoặc trừ tiền hai lần.

Về mặt thiết kế, cơ chế bảo vệ bao gồm:

- Strongly consistent read khi kiểm tra idempotency.

- Conditional Put ngăn tạo trùng bản ghi idempotency.

- Conditional Update bảo vệ số dư và trạng thái ví.

- DynamoDB TransactWriteItems bảo đảm bốn thao tác ghi được thực hiện nguyên tử.

- Cơ chế xử lý transaction conflict và retry có kiểm soát.

Ngoài concurrency, mã nguồn cũng kiểm tra nghiệp vụ không đủ số dư và từ chối giao dịch nếu ví không thỏa điều kiện.

**Minh chứng concurrency:** B4-12.

**Lưu ý nghiệm thu:** Bằng chứng rollback riêng trong Tuần 4 cần được bổ sung nếu muốn khẳng định đã chạy lại bài kiểm thử rollback trực tiếp trong tuần cuối.

### 3.5. Kiểm thử JWT, Secrets Manager và IAM

Hệ thống sử dụng PyJWT với thuật toán HS256.

Token Lambda cấp JWT sau khi xác minh userId và demoAccessCode. Lambda Authorizer kiểm tra chữ ký JWT, thời gian hết hạn, issuer và audience.

Thời hạn token được cấu hình là 900 giây, tương đương 15 phút.

Nhóm đã xác minh các nội dung:

- Token Lambda cấp JWT hợp lệ qua `/auth/token`.

- Lambda Authorizer bảo vệ các API nghiệp vụ.

- Người dùng `user-a` được truy cập ví W001 thuộc sở hữu.

- Người dùng `user-a` không được truy cập ví W002 của người khác.

- Khóa ký JWT được lưu trong Secrets Manager.

- Lambda sử dụng IAM LabRole theo yêu cầu AWS Learner Lab.

Kết quả kiểm thử phân quyền trả HTTP 403 với mã lỗi `WALLET_FORBIDDEN`.

**Minh chứng:** B4-03, B4-04, B4-05 và B4-13.

### 3.6. Kiểm thử Route Throttling

Nhóm thực hiện kiểm thử giới hạn tần suất gọi API tại API Gateway HTTP API v2.

Cấu hình thiết kế:

| Endpoint | Rate Limit | Burst |
|---|---:|---:|
| POST /auth/token | 2 req/s | 5 |
| POST /transfers | 10 req/s | 20 |

Phương pháp thực hiện:

- Sử dụng AWS CloudShell và cURL.

- Gửi 30 requests liên tiếp/đồng thời đến `/auth/token`.

- Gửi 40 requests đến `/transfers`.

- Quan sát HTTP status code để phân biệt request bị từ chối do xác thực và request bị throttling.

Các bài kiểm thử được ghi nhận trong hai minh chứng B4-18 và B4-19.

Mục tiêu là xác nhận API Gateway trả HTTP `429 Too Many Requests` khi áp dụng cơ chế giới hạn tốc độ.

**Kết quả:** Đã có minh chứng thực hiện hai kịch bản throttling. Số lượng HTTP 429 cụ thể của từng lần chạy cần được trích lại từ terminal nếu đưa vào bảng thống kê định lượng.

### 3.7. Giám sát bằng Amazon CloudWatch

Nhóm đã kiểm tra CloudWatch Logs, Dashboard và Alarms cho hệ thống.

**CloudWatch Logs**

Các Lambda sử dụng log groups để ghi lại quá trình thực thi và sự kiện xử lý. Chính sách retention được cấu hình 7 ngày nhằm hạn chế chi phí lưu trữ log trong môi trường Learner Lab.

**CloudWatch Dashboard**

Theo ảnh minh chứng B4-15, dashboard có hiển thị các chỉ số:

| Metric | Giá trị tại thời điểm chụp |
|---|---:|
| API Gateway 5xx | 0 |
| Lambda Duration | 449,3 ms |
| Lambda Errors | 0 |
| Lambda Invocations | 2 |

Các giá trị trên là số liệu tại thời điểm quan sát, không đại diện cho toàn bộ thời gian vận hành hoặc kết quả benchmark tải của hệ thống.

**CloudWatch Alarm**

Nhóm kiểm tra Alarm `serverless-payment-lambda-errors`, ghi nhận trạng thái `OK`.

Kết quả cho thấy hệ thống đã có thành phần theo dõi trạng thái hoạt động và cảnh báo lỗi Lambda.

**Minh chứng:** B4-14, B4-15 và B4-16.

### 3.8. Kiểm thử Amazon SQS Dead Letter Queue

Nhóm sử dụng SQS Standard Queue `serverless-payment-dlq` để lưu thông tin sự cố phục vụ kiểm tra và đối soát.

Trong Tuần 4, nhóm thực hiện gửi thông điệp kiểm thử `MANUAL_WEEK4_TEST` từ AWS CloudShell đến queue.

Kết quả được ghi nhận cho thấy queue tiếp nhận được message thử nghiệm.

Ngoài ra, mã nguồn Transfer Lambda có hàm `alert_failure()` sử dụng `sqs.send_message()` để gửi metadata lỗi khi gặp ngoại lệ hệ thống chưa xử lý.

Cần phân biệt:

- Bài kiểm thử thủ công chứng minh SQS queue có khả năng tiếp nhận message.

- Việc gửi lỗi tự động từ Transfer Lambda cần được xác minh bằng bài kiểm thử tích hợp riêng.

- Cơ chế này không đồng nghĩa với việc mọi lỗi runtime hoặc timeout đều tự động được chuyển đến SQS trong mô hình Lambda được gọi đồng bộ qua API Gateway.

**Minh chứng:** B4-17.

## 4. TỔNG HỢP KẾT QUẢ KIỂM THỬ

### 4.1. Unit Test

Theo tài liệu repository, nhóm đã xây dựng bộ 56 unit tests:

| Module | Số test |
|---|---:|
| `tests/test_auth.py` | 16 |
| `tests/test_transfer.py` | 23 |
| `tests/test_query.py` | 17 |
| **Tổng cộng** | **56** |

Bộ kiểm thử được báo cáo đạt 56/56 ở giai đoạn trước và là cơ sở kiểm thử hồi quy trong giai đoạn nghiệm thu.

### 4.2. Kiểm thử tích hợp Tuần 4

| Hạng mục | Kết quả theo minh chứng |
|---|---|
| Cấp JWT | HTTP 200 |
| Xem ví chính chủ | HTTP 200 |
| Truy cập ví khác chủ | HTTP 403 |
| Chuyển tiền thành công | HTTP 201 |
| Tra cứu giao dịch | HTTP 200 |
| Truy vấn lịch sử | HTTP 200 |
| Idempotency Replay | HTTP 200, replayed=true |
| Idempotency Conflict | HTTP 409 |
| Concurrency 5 requests | Không ghi nhận chuyển tiền hai lần |
| Route Throttling | Đã thực hiện kịch bản 30/40 requests |
| CloudWatch Monitoring | Có Logs, Dashboard, Alarm |
| SQS Queue | Gửi message thủ công thành công |

Các kết quả được tổng hợp từ danh mục minh chứng Tuần 4 trong GitHub của nhóm.

## 5. PHÂN CÔNG CÔNG VIỆC VÀ THỜI GIAN THỰC HIỆN

### 5.1. Vũ Minh Đức – 8 giờ

| Công việc | Thời gian |
|---|---:|
| Kiểm tra DynamoDB Transaction và điều kiện rollback | 2 giờ |
| Kiểm thử Idempotency Replay, requestHash và key conflict | 2 giờ |
| Kiểm thử concurrency, đối soát số dư và lịch sử giao dịch | 1,5 giờ |
| Rà soát test scenarios, dữ liệu DynamoDB và quy tắc nghiệp vụ | 1,5 giờ |
| Chuẩn bị minh chứng và trình bày phần demo nghiệp vụ | 1 giờ |
| **Tổng cộng** | **8 giờ** |

### 5.2. Nguyễn Nguyên – 8 giờ

| Công việc | Thời gian |
|---|---:|
| Kiểm thử tích hợp năm API endpoints qua API Gateway và Postman | 2 giờ |
| Kiểm tra JWT, Authorizer, Secrets Manager và IAM LabRole | 1,5 giờ |
| Kiểm thử CloudWatch, SQS DLQ và Route Throttling | 1,5 giờ |
| Rà soát cấu hình AWS, tài liệu và GitHub repository | 1,5 giờ |
| Tổng hợp minh chứng, báo cáo và chuẩn bị video demo | 1,5 giờ |
| **Tổng cộng** | **8 giờ** |

**Tổng khối lượng theo phân công: 16 giờ.**

*Ghi chú:* Bảng trên là phân bổ công việc 8 giờ/thành viên để hoàn thiện worklog Tuần 4. Nhóm cần đối chiếu và bổ sung ngày, khung giờ thực hiện thực tế trước khi nộp chính thức.

## 6. MÃ NGUỒN, TÀI LIỆU VÀ MINH CHỨNG

### 6.1. Mã nguồn

Mã nguồn hệ thống được lưu trữ tại:

https://github.com/NguyenNguyen0210/serverless-payment

Các thành phần chính:

- `src/token/lambda_function.py`

- `src/authorizer/lambda_function.py`

- `src/transfer/lambda_function.py`

- `src/wallet_query/lambda_function.py`

- `src/transaction_query/lambda_function.py`

- `scripts/create_tables.py`

- `scripts/seed_wallets.py`

- `tests/test_auth.py`

- `tests/test_transfer.py`

- `tests/test_query.py`

### 6.2. Tài liệu kỹ thuật

Nhóm duy trì tài liệu:

- `README.md`: Tổng quan dự án và hướng dẫn sử dụng.

- `design/architecture.md`: Thiết kế kiến trúc và các quyết định kỹ thuật.

- `design/openapi.yaml`: Đặc tả năm API.

- `docs/api-contract.md`: Hợp đồng API.

- `docs/business-rules.md`: Quy tắc nghiệp vụ.

- `docs/data-model.md`: Mô hình ba bảng DynamoDB và hai GSI.

- `docs/test-scenarios.md`: Kịch bản kiểm thử.

- `docs/worklog.md`: Nhật ký công việc nhóm.

### 6.3. Minh chứng Tuần 4

Trên repository hiện đã có **19 ảnh minh chứng của Nguyễn Nguyên**, ký hiệu B4-01 đến B4-19.

Minh chứng bao gồm:

- Môi trường AWS và danh sách tài nguyên.

- API Gateway và năm routes.

- Kiểm thử cấp JWT và truy vấn ví.

- Kiểm thử chuyển tiền và đối soát số dư.

- Idempotency Replay và Conflict.

- Concurrency.

- Secrets Manager và IAM LabRole.

- CloudWatch Logs, Dashboard, Alarm.

- SQS queue.

- Route Throttling cho hai endpoints.

Thư mục `evidence/week04/duc/` được dự kiến trong danh mục minh chứng nhưng cần được bổ sung trên nhánh GitHub chính trước khi báo cáo đã hoàn thiện toàn bộ minh chứng cá nhân.

## 7. QUẢN LÝ TÀI NGUYÊN VÀ CHI PHÍ AWS

Hệ thống sử dụng các dịch vụ Serverless, hạn chế việc duy trì máy chủ tính toán liên tục.

Nhóm tuân thủ phương án quản lý tài nguyên:

- Triển khai trong Region us-east-1.

- Sử dụng IAM LabRole.

- Sử dụng DynamoDB On-Demand.

- Áp dụng CloudWatch Logs retention 7 ngày.

- Gắn tag Project và Owner cho tài nguyên hỗ trợ tagging.

- Sử dụng request và dữ liệu mẫu với quy mô phù hợp môi trường Learner Lab.

- Dọn dẹp tài nguyên không còn sử dụng sau các buổi thực hành và nghiệm thu.

Ngân sách Learner Lab ban đầu được ghi nhận là **50 USD**.

**Chi phí thực tế cuối kỳ:** Ghi nhận trên AWS Academy Learner Lab, tổng chi phí phát sinh xuyên suốt 4 tuần thực hành là **~$0.45 USD / $50.00 USD** (tiêu tốn dưới 1% ngân sách được cấp). Chi phí chủ yếu đến từ việc duy trì secret trên AWS Secrets Manager (~$0.40/tháng tính theo giờ), trong khi API Gateway, Lambda và DynamoDB On-Demand đều nằm trọn vẹn trong hạn mức Free Tier và mức sử dụng demo.

**Trạng thái dọn dẹp tài nguyên cuối kỳ:** Toàn bộ tài nguyên (03 bảng DynamoDB, 05 hàm Lambda, API Gateway và SQS Queue) hiện đang được **giữ nguyên trạng thái ACTIVE** để phục vụ việc quay video demo và buổi báo cáo vấn đáp/nghiệm thu với Giảng viên hướng dẫn. Sau khi hoàn tất nghiệm thu môn học, nhóm sẽ thực thi quy trình xóa toàn bộ tài nguyên theo đúng quy định của Learner Lab.

Nhóm cần lưu lại bằng chứng ngân sách đã sử dụng và tài nguyên còn tồn tại trước khi kết thúc dự án.

## 8. KHÓ KHĂN VÀ BÀI HỌC KINH NGHIỆM

### 8.1. Khó khăn

Trong quá trình phát triển, nhóm phải xử lý các vấn đề kỹ thuật:

- Phân quyền IAM LabRole trong môi trường Learner Lab bị giới hạn.

- Tích hợp Lambda Authorizer với API Gateway HTTP API v2.

- Quản lý JWT secret và tránh để lộ thông tin bảo mật.

- Thiết kế DynamoDB Transaction bảo đảm không cập nhật số dư một phần.

- Xử lý request trùng và transaction conflict khi có nhiều yêu cầu đồng thời.

- Truy vấn lịch sử giao dịch từ hai GSI và hỗ trợ phân trang.

- Phân biệt kiểm thử SQS thủ công với luồng xử lý lỗi tự động.

- Theo dõi chi phí khi sử dụng nhiều dịch vụ AWS.

### 8.2. Bài học kinh nghiệm

Thông qua dự án, nhóm tiếp cận được quy trình phát triển một ứng dụng Serverless từ thiết kế đến triển khai và nghiệm thu.

Các bài học quan trọng:

1. Sử dụng DynamoDB Transaction để bảo đảm tính nhất quán dữ liệu trong nghiệp vụ tài chính.

2. Áp dụng Idempotency-Key để ngăn thực thi trùng yêu cầu thanh toán.

3. Kết hợp Authentication và Authorization để bảo vệ tài nguyên người dùng.

4. Sử dụng CloudWatch để quan sát và điều tra lỗi thực thi.

5. Tổ chức mã nguồn, tài liệu và ảnh minh chứng giúp hệ thống dễ kiểm tra và bảo trì.

6. Kiểm thử trên môi trường AWS thực tế là cần thiết bên cạnh unit test.

## 9. TỔNG KẾT TOÀN BỘ DỰ ÁN SAU BỐN TUẦN

Trải qua bốn tuần triển khai, nhóm Serverless đã xây dựng hệ thống cổng thanh toán giả lập dựa trên các dịch vụ AWS Serverless.

**Tuần 1 – Thiết kế và chuẩn bị:** Phân tích yêu cầu, xây dựng kiến trúc, mô hình dữ liệu, đặc tả API, kịch bản kiểm thử và chuẩn bị môi trường AWS Learner Lab.

**Tuần 2 – Triển khai chức năng lõi:** Xây dựng Token Lambda, Lambda Authorizer, Transfer Lambda, DynamoDB Transaction, Secrets Manager, API Gateway và các unit tests ban đầu.

**Tuần 3 – Tích hợp và giám sát:** Hoàn thiện mô hình ba bảng DynamoDB, năm Lambda, năm API endpoints, hai GSI, cơ chế JWT, CloudWatch và SQS.

**Tuần 4 – Kiểm thử và nghiệm thu:** Kiểm thử trực tiếp các API, chuyển tiền, đối soát số dư, Idempotency Replay, Conflict, Concurrency, bảo mật và giám sát. Tổng hợp kết quả thực hiện và chuẩn bị sản phẩm bàn giao.

Các kết quả đạt được theo mã nguồn, tài liệu và minh chứng đã công bố:

- Hệ thống có năm API endpoints và năm Lambda Functions.

- Sử dụng ba bảng DynamoDB và hai Global Secondary Index.

- Chuyển tiền bằng một DynamoDB TransactWriteItems với bốn thao tác nguyên tử.

- Chống xử lý trùng giao dịch thông qua Idempotency-Key.

- Xác thực JWT HS256 bằng Lambda Authorizer, không sử dụng Cognito.

- Quản lý bí mật JWT bằng AWS Secrets Manager.

- Có cơ chế phân quyền truy cập ví.

- Có Route Throttling, CloudWatch Monitoring và SQS.

- Bộ unit test gồm 56 trường hợp theo repository.

- Có ảnh minh chứng triển khai và kiểm thử thực tế trong cả bốn tuần.

## 10. KẾT LUẬN CUỐI KỲ

Đề tài **“Cổng thanh toán giả lập với API Gateway, Lambda Authorizer và DynamoDB Transaction”** đã giúp nhóm vận dụng kiến thức Điện toán đám mây vào việc thiết kế, triển khai và kiểm thử một hệ thống thanh toán theo kiến trúc Serverless.

Điểm nổi bật của hệ thống là cơ chế chuyển tiền nguyên tử bằng DynamoDB TransactWriteItems, kết hợp Idempotency-Key để ngăn xử lý trùng request. Các thử nghiệm chuyển tiền và đối soát số dư trong Tuần 4 cho thấy hệ thống thực hiện đúng các thay đổi số dư ở trường hợp kiểm thử được ghi nhận.

Bên cạnh đó, việc tích hợp Lambda Authorizer, Secrets Manager, API Gateway Throttling và CloudWatch giúp nhóm hiểu rõ hơn các yêu cầu bảo mật, quản lý truy cập và giám sát trong hệ thống Cloud.

Sản phẩm hiện đáp ứng các chức năng chính của bài toán thanh toán giả lập. Hệ thống vẫn mang tính chất học thuật và chưa được thiết kế để sử dụng với giao dịch tài chính thực tế hoặc vận hành ở quy mô production.

Sau khi bổ sung worklog, minh chứng còn thiếu, chi phí cuối kỳ và video demo, nhóm có thể hoàn thiện hồ sơ nghiệm thu dự án theo yêu cầu giảng viên.

**Nhóm Serverless xin chân thành cảm ơn giảng viên Huỳnh Xuân Phụng đã hướng dẫn và hỗ trợ nhóm trong suốt quá trình thực hiện đề tài.**