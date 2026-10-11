# KIẾN TRÚC HỆ THỐNG & QUYẾT ĐỊNH THIẾT KẾ (SYSTEM ARCHITECTURE & ADR)

> **Dự án:** Cổng thanh toán giả lập không máy chủ (`serverless-payment`)  
> **Học phần:** Cloud Computing – Đợt 1, Năm học 2026–2027  
> **GVHD:** ThS. Huỳnh Xuân Phụng  
> **Nhóm thực hiện:** Serverless (Vũ Minh Đức & Nguyễn Nguyên)  
> **Môi trường:** AWS Academy Learner Lab (`us-east-1`)  
> **Trạng thái:** Bản thiết kế hoàn chỉnh – Tuần 1  

---

## 1. Sơ đồ kiến trúc tổng thể (System Architecture)

Toàn bộ hệ thống được thiết kế theo mô hình **Pure Serverless (Hoàn toàn không máy chủ)**, tối ưu cho khả năng mở rộng tự động, độ trễ thấp và tiết kiệm tối đa chi phí hoạt động trên môi trường học tập AWS Learner Lab:

```mermaid
flowchart TB
    Client["Client / Postman / Automated Test"]

    subgraph APIGW["Amazon API Gateway (HTTP API v2 - us-east-1)"]
        Ingress["Ingress & Throttling Engine\n(Default: 10 RPS, Burst: 20)"]
        TokenRoute["POST /token\n(Rate: 2 RPS, Burst: 5)"]
        TransferRoute["POST /transfers\n(Rate: 10 RPS, Burst: 20)"]
    end

    subgraph Security["Xác thực & Bảo mật (Security Layer)"]
        AuthLambda["Lambda Authorizer (REQUEST mode)"]
        TokenLambda["Token Lambda (Issue JWT)"]
        SecretsMgr[("AWS Secrets Manager\n(serverless-payment/jwt-secret)")]
    end

    subgraph Business["Xử lý nghiệp vụ lõi (Business Layer)"]
        TransferLambda["Transfer Lambda (Core Engine)"]
    end

    subgraph Database["Lưu trữ dữ liệu (Amazon DynamoDB)"]
        WalletsTable[("Table: Wallets\nPK: walletId (S)")]
        TxTable[("Table: Transactions\nPK: userId (S)\nSK: idempotencyKey (S)")]
    end

    subgraph Resilience["Khả năng phục hồi & Chịu lỗi (Resilience Layer)"]
        DLQ[("Amazon SQS: Dead Letter Queue\n(serverless-payment-dlq)")]
    end

    subgraph Monitoring["Giám sát & Nhật ký (Observability)"]
        CloudWatch[("Amazon CloudWatch Logs & Metrics")]
    end

    Client -->|"Gọi API"| Ingress
    Ingress -.->|"Vượt hạn mức RPS"| Client429["HTTP 429 Too Many Requests\n(Header: Retry-After)"]
    Ingress -->|"1. Cấp token demo"| TokenRoute
    TokenRoute --> TokenLambda
    TokenLambda -->|"Kiểm tra demoCode"| SecretsMgr
    TokenLambda -->|"Ký JWT bằng PyJWT"| TokenLambda
    TokenLambda -.->|"Ghi log"| CloudWatch

    Ingress -->|"2. Chuyển tiền (Bearer JWT + Idempotency-Key)"| TransferRoute
    TransferRoute -->|"3. Gửi header xác thực"| AuthLambda
    AuthLambda -->|"Đọc khóa bí mật"| SecretsMgr
    AuthLambda -->|"Xác thực chữ ký & hạn dùng"| AuthLambda
    AuthLambda -->|"4. Trả isAuthorized: true + Context (sub)"| TransferRoute
    AuthLambda -.->|"Ghi log"| CloudWatch

    TransferRoute -->|"5. Chuyển tiếp request hợp lệ"| TransferLambda
    TransferLambda -->|"6. Kiểm tra quy tắc nghiệp vụ & Băm requestHash"| TransferLambda
    TransferLambda -->|"7. Kiểm tra trùng lặp (userId, idempotencyKey)"| TxTable
    TransferLambda ==>|"8. Thực thi TransactWriteItems:\n- Update Ví nguồn (balance >= amount)\n- Update Ví đích (status == ACTIVE)\n- Put Transactions (not exists)"| WalletsTable
    TransferLambda ==>|"Ghi nhận giao dịch SUCCESS"| TxTable
    TransferLambda -.->|"Unhandled exception / Timeout"| DLQ
    TransferLambda -.->|"Ghi log"| CloudWatch
```

---

## 2. Luồng xử lý chi tiết (Interaction Flows)

### 2.1. Luồng cấp token demo (`POST /token`)
1. Client gửi yêu cầu kèm `userId` và `demoCode`.
2. `Token Lambda` đọc mã bí mật từ AWS Secrets Manager và đối chiếu với danh sách allowlist nội bộ.
3. Nếu hợp lệ, Lambda sử dụng thư viện **PyJWT** (thuật toán HS256) ký token có thời hạn 15 phút (`expiresIn: 900`).
4. Trả về `accessToken` dạng Bearer token cho client.

### 2.2. Luồng xác thực với Lambda Authorizer
1. Client gọi `POST /transfers` kèm header `Authorization: Bearer <token>`.
2. API Gateway HTTP API kích hoạt **Lambda Authorizer (REQUEST mode)**, Payload format 2.0.
3. Authorizer giải mã token, kiểm tra: chữ ký HMAC-SHA256, thời hạn hết hạn (`exp`), issuer và audience.
4. Nếu hợp lệ, Authorizer trả về:
   ```json
   {
     "isAuthorized": true,
     "context": {
       "userId": "user-a"
     }
   }
   ```
5. API Gateway gắn `context.userId` vào request chuyển tiếp sang Transfer Lambda, đảm bảo nghiệp vụ chỉ thao tác với người dùng đã được định danh an toàn.

### 2.3. Luồng chuyển tiền nguyên tử & Chống lặp (Core Transfer & Idempotency)
1. **Kiểm tra đầu vào:** Kiểm tra số tiền `amount` (số nguyên dương VND), kiểm tra mã ví nguồn khác ví đích.
2. **Định danh chủ sở hữu:** Đối chiếu quyền sở hữu ví nguồn với `userId` được cấp từ context của Authorizer.
3. **Tính toán `requestHash`:** Băm SHA-256 nội dung chuẩn hóa (`userId`, `fromWalletId`, `toWalletId`, `amount`, `currency`).
4. **Kiểm tra lịch sử Idempotency:**
   - Thực hiện `GetItem` (Strongly Consistent Read) trên bảng `Transactions` với cặp khóa `(userId, idempotencyKey)`.
   - **Trường hợp 1 (Đã thành công trước đó):** Nếu đã tồn tại và `requestHash` khớp $\rightarrow$ Trả về kết quả cũ kèm `replayed: true` (HTTP 200), không trừ thêm tiền.
   - **Trường hợp 2 (Xung đột key):** Nếu đã tồn tại nhưng `requestHash` khác $\rightarrow$ Trả về lỗi `409 IDEMPOTENCY_KEY_CONFLICT`.
   - **Trường hợp 3 (Giao dịch mới):** Tiếp tục bước thực thi nguyên tử.
5. **Thực thi `TransactWriteItems`:**
   - **Put Transactions:** Ghi bản ghi trạng thái `SUCCESS`, điều kiện `attribute_not_exists(userId)`.
   - **Update Ví nguồn:** Trừ tiền, điều kiện `attribute_exists(walletId) AND ownerId = :userId AND #status = :active AND balance >= :amount`.
   - **Update Ví đích:** Cộng tiền, điều kiện `attribute_exists(walletId) AND #status = :active AND currency = :vnd`.
6. **Kết quả:** Nếu tất cả điều kiện thỏa mãn, giao dịch commit đồng thời (HTTP 201 Created). Nếu có bất kỳ điều kiện nào vi phạm, toàn bộ giao dịch rollback về trạng thái ban đầu.

### 2.4. Luồng kiểm soát lưu lượng (Rate Limiting & Throttling)
1. **Mục đích:** Chống tấn công brute-force vào endpoint cấp token và bảo vệ backend DynamoDB/Lambda khỏi tình trạng cạn kiệt tài nguyên (DoS) khi có đột biến lưu lượng.
2. **Cấu hình trên API Gateway HTTP API v2:**
   - **Stage Default Throttling:** Rate Limit = 10 requests/giây (RPS), Burst Limit = 20 requests.
   - **Route Throttling riêng biệt:**
     - Route `POST /token`: Rate = 2 RPS, Burst = 5 (giới hạn chặt chẽ vì đây là endpoint cấp quyền thử nghiệm).
     - Route `POST /transfers`: Rate = 10 RPS, Burst = 20.
3. **Phản hồi khi vi phạm:** Khi client gửi request vượt quá hạn mức, API Gateway từ chối ngay tại tầng ingress với mã phản hồi **`429 Too Many Requests`** kèm header `Retry-After`. Thao tác này không kích hoạt Lambda backend, giúp tiết kiệm 100% chi phí xử lý và bảo vệ hạn ngạch tính toán của Learner Lab.

### 2.5. Luồng xử lý sự cố bất thường & Hàng đợi chết (Dead Letter Queue - DLQ)
1. **Mục đích:** Trong hệ thống tài chính, các lỗi hệ thống nghiêm trọng (unhandled exceptions, timeout hoặc sự cố phân vùng mạng giữa Lambda và DynamoDB) không được phép làm mất dấu vết giao dịch của người dùng.
2. **Kiến trúc DLQ qua Amazon SQS:**
   - Sử dụng một hàng đợi Standard Queue: `serverless-payment-dlq`.
   - Cấu hình Dead Letter Queue trên hàm `Transfer Lambda`.
3. **Cơ chế kích hoạt:**
   - Khi Lambda gặp biệt lệ chưa bắt được (Unhandled Error) hoặc timeout trong quá trình xử lý giao dịch, bản tin sự kiện gốc (event payload) tự động được chuyển tiếp vào SQS DLQ.
   - Hàng đợi DLQ giữ lại thông điệp lỗi (Message Retention Period: 14 ngày), cho phép đội ngũ kỹ sư kiểm tra đối soát thủ công (manual audit), tái hiện sự cố và hoàn trả trạng thái ví nếu cần thiết mà không lo mất dữ liệu.
   - Thiết lập CloudWatch Alarm theo dõi chỉ số `ApproximateNumberOfMessagesVisible` trên SQS DLQ để phát hiện tức thì khi có lỗi hệ thống phát sinh.

---

## 3. Nhật ký quyết định kiến trúc (Architecture Decision Records - ADR)

Các quyết định thiết kế then chốt được nhóm thống nhất nhằm tối ưu kỹ thuật và tuân thủ giới hạn của môi trường AWS Academy Learner Lab:

| Mã ADR | Hạng mục | Quyết định kỹ thuật | Cơ sở & Lợi ích |
|:---:|---|---|---|
| **ADR-01** | **AWS Region** | Sử dụng duy nhất **`us-east-1`** (US East - N. Virginia). | Tuân thủ chính sách của Learner Lab; tương thích đầy đủ tính năng của API Gateway HTTP API v2 và Secrets Manager. |
| **ADR-02** | **API Gateway Type** | Chọn **HTTP API (API Gateway v2)** thay cho REST API. | Giảm 70% chi phí, độ trễ thấp hơn (nhẹ hơn), hỗ trợ cơ chế Simple Response cho Lambda Authorizer (`isAuthorized: true/false`). |
| **ADR-03** | **Cơ sở dữ liệu** | Sử dụng **Amazon DynamoDB** (chế độ On-Demand Capacity). | Thuần serverless, không phát sinh chi phí duy trì cố định theo giờ; hỗ trợ giao dịch nguyên tử nhiều bảng qua `TransactWriteItems`. |
| **ADR-04** | **Kiểu dữ liệu tiền tệ** | Sử dụng **Số nguyên dương (Integer VND)**, loại bỏ hoàn toàn `float`. | Tránh lỗi làm tròn dấu phẩy động (floating-point error) thường gặp trong hệ thống tài chính; phù hợp với tiền tệ Việt Nam Đồng (không có xu). |
| **ADR-05** | **Tính nguyên tử (ACID)** | Gom 2 Update ví và 1 Put giao dịch vào **một lệnh `TransactWriteItems`**. | Bảo đảm tính bất biến tài chính: không bao giờ xảy ra lỗi trừ tiền một phía (zero balance discrepancy). |
| **ADR-06** | **Cơ chế Idempotency** | Sử dụng cặp khóa `(userId, idempotencyKey)` kết hợp `requestHash` (SHA-256) trong DynamoDB. | Khắc phục giới hạn 10 phút của `ClientRequestToken` trên DynamoDB; lưu vết chống gửi lặp vĩnh viễn trong cơ sở dữ liệu. |
| **ADR-07** | **Phạm vi lưu giao dịch** | Trong MVP, **chỉ ghi nhận giao dịch `SUCCESS`**. | Yêu cầu bị lỗi (thiếu số dư, sai ví) sẽ bị rollback và không chiếm key; cho phép client thử lại cùng key sau khi đã nạp đủ tiền hoặc sửa lỗi. |
| **ADR-08** | **Cơ chế Xác thực** | Tự sinh và kiểm tra JWT bằng thư viện **PyJWT (HS256)**, khóa bí mật lưu tại Secrets Manager. | Đúng yêu cầu đề bài (không dùng AWS Cognito); kiểm soát hoàn toàn vòng đời và claims của token. |
| **ADR-09** | **Quản lý hạ tầng & VPC** | **Không sử dụng VPC riêng, NAT Gateway hay EC2** cho các hàm Lambda. | Tránh phí duy trì NAT Gateway ($0.045/giờ); Lambda có thể gọi trực tiếp DynamoDB và Secrets Manager qua AWS internal network an toàn và miễn phí. |
| **ADR-10** | **Phân quyền IAM** | Tận dụng IAM Role có sẵn **`LabRole`** của Learner Lab. | Tuân thủ quy định môi trường học tập (không có quyền tạo IAM User hay IAM Role mới). |
| **ADR-11** | **Kiểm soát lưu lượng** | Cấu hình **Stage & Route Throttling** trên API Gateway HTTP API (Token: 2 RPS / Burst 5; Transfers: 10 RPS / Burst 20). | Chống tấn công DoS, ngăn brute-force mã token demo; từ chối sớm với HTTP 429 tại tầng gateway giúp tiết kiệm 100% chi phí tính toán Lambda backend. |
| **ADR-12** | **Xử lý sự cố ngoại lệ** | Tích hợp **Amazon SQS Dead Letter Queue (`serverless-payment-dlq`)** gắn với Transfer Lambda. | Bảo đảm tính kiên cường (Resilience): lưu giữ toàn bộ thông điệp lỗi khi xảy ra sự cố hạ tầng không lường trước phục vụ đối soát và khôi phục, nằm trọn trong gói Free Tier của SQS. |

---

## 4. Quy ước định danh tài nguyên (Resource Naming Conventions)

Chuẩn hóa tên gọi tài nguyên phục vụ việc triển khai tự động ở Tuần 2:

| Thành phần AWS | Quy ước đặt tên | Ghi chú |
|---|---|---|
| **API Gateway HTTP API** | `serverless-payment-api` | Endpoint HTTPS tại `us-east-1` (tích hợp Route Throttling) |
| **Lambda Token** | `serverless-payment-token` | Xử lý `POST /token` |
| **Lambda Authorizer** | `serverless-payment-authorizer` | Lambda REQUEST Authorizer (Python 3.12, PyJWT) |
| **Lambda Transfer** | `serverless-payment-transfer` | Xử lý `POST /transfers` (gắn DLQ SQS) |
| **DynamoDB Wallets** | `Wallets` | PK: `walletId` (String) |
| **DynamoDB Transactions** | `Transactions` | PK: `userId` (String), SK: `idempotencyKey` (String) |
| **Amazon SQS DLQ** | `serverless-payment-dlq` | Dead Letter Queue lưu vết giao dịch lỗi hệ thống |
| **AWS Secrets Manager** | `serverless-payment/jwt-secret` | Lưu chuỗi bí mật HMAC ký JWT |
| **CloudWatch Log Groups** | `/aws/lambda/serverless-payment-*` | Thiết lập retention 7 ngày để tiết kiệm chi phí |

---

## 5. Quy chuẩn gắn thẻ (Tagging Policy)

Mọi tài nguyên được tạo ra trên AWS bắt buộc phải được gắn thẻ đầy đủ:
- `Project`: `serverless-payment`
- `Owner`: `Serverless-Team` (hoặc `VuMinhDuc` / `NguyenNguyen`)
- `Environment`: `Lab`
