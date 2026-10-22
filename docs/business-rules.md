# QUY TẮC NGHIỆP VỤ & BẤT BIẾN TÀI CHÍNH (BUSINESS RULES & INVARIANTS)

> **Học phần:** Cloud Computing – Đợt 1, Năm học 2026–2027  
> **Dự án:** Cổng thanh toán giả lập không máy chủ (`serverless-payment`)  
> **Người phụ trách:** Vũ Minh Đức  
> **Phối hợp & Rà soát:** Nguyễn Nguyên  
> **AWS Region:** `us-east-1` · **Phiên bản:** 2.0 (Kiến trúc 3 bảng DynamoDB & 5 Endpoints)  

---

## 1. Phạm vi nghiệp vụ

Hệ thống giả lập chuyển tiền VND giữa các tài khoản ví số dư do hệ thống quản trị trên nền tảng AWS Serverless. Hệ thống tuân thủ chặt chẽ nguyên tắc bảo toàn số dư (zero balance discrepancy), chống lặp giao dịch (Idempotency vĩnh viễn) và phân quyền chặt chẽ theo chủ sở hữu (Least Privilege).

- **Trong phạm vi:**
  1. Cấp token demo có chữ ký số qua `POST /auth/token`.
  2. Chuyển tiền nguyên tử qua `POST /transfers` (4 actions trong `TransactWriteItems`).
  3. Tra cứu số dư ví chính chủ qua `GET /wallets/{walletId}`.
  4. Tra cứu chi tiết giao dịch theo ID qua `GET /transactions/{transactionId}` (chỉ các bên tham gia).
  5. Tra cứu lịch sử biến động số dư theo ví có phân trang con trỏ qua `GET /wallets/{walletId}/transactions`.
  6. Kiểm soát lưu lượng tại tầng biên (Route Throttling: HTTP 429) và điều hướng lỗi ngoại lệ sang SQS DLQ.

- **Ngoài phạm vi:** Không liên kết với ngân hàng thương mại ngoài đời thực; không nạp/rút tiền mặt; không phát sinh số thập phân (tiền VND là số nguyên dương).

---

## 2. Các thực thể và Bối cảnh hoạt động

- **Người dùng (`userId`):** Được định danh tin cậy qua claim `sub` trích xuất từ JWT hợp lệ do Lambda Authorizer cung cấp. Backend không bao giờ tin cậy `userId` do client tự gửi trong request body.
- **Ví điện tử (`walletId`):** Chứa `walletId`, `ownerId`, `balance` (số nguyên VND), `currency` (`VND`), `status` (`ACTIVE` hoặc `SUSPENDED`).
- **Giao dịch (`transactionId`):** Chứa `transactionId`, `fromWalletId`, `toWalletId`, `amount`, `currency`, `timeKey` (`<createdAt>#<txId>`), `status: "SUCCESS"`, `createdAt`.
- **Bản ghi chống lặp (`userId`, `idempotencyKey`):** Chứa `requestHash` (băm SHA-256 nội dung chuẩn hóa của request) và `transactionId` tương ứng.

**Dữ liệu mẫu khởi tạo:**
- Ví `W001` (`user-a`, số dư 100.000 VND, `ACTIVE`).
- Ví `W002` (`user-b`, số dư 50.000 VND, `ACTIVE`).
- Ví `W003` (`user-b`, số dư 20.000 VND, `SUSPENDED`).
- Ví `W004` (`user-a`, số dư 10.000 USD, `ACTIVE`).

*Ví dụ:* Khi `user-a` chuyển 30.000 VND từ `W001` sang `W002`: `W001` còn 70.000 VND, `W002` tăng lên 80.000 VND. Tổng số dư hai ví luôn bảo toàn tuyệt đối bằng 150.000 VND.

---

## 3. Danh mục quy tắc nghiệp vụ (Business Rules)

| Mã | Quy tắc nghiệp vụ | Hành vi / Mã lỗi khi vi phạm |
|---|---|---|
| **BR-01** | `amount` phải là số nguyên dương (> 0); không chấp nhận số âm, `0`, số thực dấu phẩy động (`float`), chuỗi hoặc `boolean`. | `400 INVALID_AMOUNT` |
| **BR-02** | `fromWalletId` và `toWalletId` là bắt buộc, không được để trống và phải khác nhau (`fromWalletId != toWalletId`). | `400 INVALID_WALLET` |
| **BR-03** | Cả hai ví tham gia giao dịch phải tồn tại trong CSDL và có trạng thái hoạt động `status=ACTIVE`. | `404 WALLET_NOT_FOUND` hoặc `409 WALLET_INACTIVE` |
| **BR-04** | Người thực hiện (`sub` trong JWT) bắt buộc phải là chủ sở hữu của ví nguồn (`sub == fromWallet.ownerId`). | `403 WALLET_FORBIDDEN` |
| **BR-05** | Số dư ví nguồn tại thời điểm thực thi phải lớn hơn hoặc bằng số tiền chuyển (`balance >= amount`). | `409 INSUFFICIENT_FUNDS` |
| **BR-06** | Cả hai ví tham gia giao dịch phải cùng đơn vị tiền tệ Việt Nam Đồng (`currency=VND`). | `400 UNSUPPORTED_CURRENCY` |
| **BR-07** | Thao tác trừ tiền nguồn, cộng tiền đích, ghi nhận giao dịch và lưu vết idempotency phải thực hiện đồng thời trong **một lệnh `TransactWriteItems` duy nhất (4 actions)**. | Đảm bảo tính nguyên tử: không bao giờ trừ tiền một phía |
| **BR-08** | Yêu cầu vào các route bảo vệ bắt buộc có header `Authorization: Bearer <token>`. Nếu thiếu, sai chữ ký hoặc hết hạn thì từ chối ngay. | `401 Unauthorized` (Gateway) hoặc `403 Forbidden` (Authorizer) |
| **BR-09** | Yêu cầu `POST /transfers` bắt buộc phải có header `Idempotency-Key` (chuỗi định dạng UUID). | `400 MISSING_IDEMPOTENCY_KEY` |
| **BR-10** | Cùng cặp khóa `(userId, idempotencyKey)` và cùng `requestHash`: hệ thống không chuyển tiền lần hai mà trả về kết quả cũ kèm `replayed: true`. | `200 OK`, `replayed=true` |
| **BR-11** | Cùng cặp khóa `(userId, idempotencyKey)` nhưng `requestHash` khác (thay đổi amount, ví nguồn/đích): từ chối xử lý. | `409 IDEMPOTENCY_KEY_CONFLICT` |
| **BR-12** | Mọi điều kiện số dư và trạng thái ví phải được kiểm tra nguyên tử trong biểu thức `ConditionExpression` của DynamoDB transaction, không chỉ dựa vào bước đọc trước (pre-read). | Ngăn chặn race condition khi có giao dịch song song |
| **BR-13** | Tuyệt đối không để lộ signing key, demo code hay thông tin nội bộ nhạy cảm trong response hoặc log CloudWatch. | Tiêu chuẩn an toàn thông tin |
| **BR-14** | Khóa chống trùng `idempotencyKey` được phân tách theo `userId`. Hai người dùng khác nhau sử dụng trùng một chuỗi UUID không bị coi là xung đột. | Tách biệt không gian khóa chống trùng |
| **BR-15** | Tra cứu thông tin ví (`GET /wallets/{walletId}`): chỉ người dùng sở hữu ví (`ownerId == sub`) mới được phép xem số dư và thông tin ví. | `403 WALLET_FORBIDDEN` nếu không phải chủ sở hữu |
| **BR-16** | Tra cứu chi tiết giao dịch (`GET /transactions/{transactionId}`): chỉ người dùng sở hữu ví nguồn hoặc ví đích tham gia giao dịch mới được phép truy xuất. | `403 TRANSACTION_FORBIDDEN` đối với bên thứ ba |
| **BR-17** | Phân trang danh sách giao dịch ví (`GET /wallets/{walletId}/transactions`): yêu cầu quyền sở hữu ví; hỗ trợ tham số `limit` (1..50, mặc định 20) và con trỏ `nextToken` (Base64 JSON của `ExclusiveStartKey`); sắp xếp giảm dần theo `timeKey`. | `400 INVALID_QUERY_PARAMETER` nếu limit sai dải |

---

## 4. Luồng nghiệp vụ chuyển tiền thành công

1. **Client xác thực:** Gửi yêu cầu tới `POST /auth/token` với `userId` và `demoCode` hợp lệ $\rightarrow$ Nhận Bearer JWT (hạn dùng 15 phút).
2. **Client gửi lệnh chuyển tiền:** `POST /transfers` kèm header `Authorization: Bearer <JWT>`, `Idempotency-Key: <UUID>` và payload chuyển tiền.
3. **Ủy quyền:** API Gateway gọi Lambda Authorizer kiểm tra tính toàn vẹn của token; Authorizer trả về ngữ cảnh `userId` (`sub`).
4. **Kiểm tra dữ liệu đầu vào:** Transfer Lambda kiểm tra cú pháp, lượng tiền VND nguyên dương, `fromWalletId != toWalletId`.
5. **Tính toán `requestHash`:** Băm SHA-256 payload chuẩn hóa (`userId`, `fromWalletId`, `toWalletId`, `amount`, `currency`).
6. **Kiểm tra chống trùng:** Truy vấn bảng `serverless-payment-idempotency` với `ConsistentRead=True`:
   - Nếu tồn tại và `requestHash` khớp $\rightarrow$ Trả kết quả cũ (`200 OK`, `replayed: true`).
   - Nếu tồn tại và `requestHash` khác $\rightarrow$ Báo lỗi `409 IDEMPOTENCY_KEY_CONFLICT`.
7. **Thực thi giao dịch 4 actions:** Khi là giao dịch mới, thực thi một lệnh `TransactWriteItems`:
   - **Put** bản ghi vào `serverless-payment-idempotency` (chưa tồn tại).
   - **Put** bản ghi vào `serverless-payment-transactions` (chưa tồn tại, kèm `timeKey`).
   - **Update** trừ tiền ví nguồn trong `serverless-payment-wallets` (đủ số dư, đúng chủ sở hữu, đang hoạt động).
   - **Update** cộng tiền ví đích trong `serverless-payment-wallets` (đang hoạt động, cùng loại tiền VND).
8. **Kết quả:** Trả về `201 Created` kèm `transactionId`, `replayed: false`, thời gian giao dịch `createdAt`.

---

## 5. Quy tắc xử lý lỗi và Tính nguyên tử (ACID)

- **Nguyên tắc "Tất cả hoặc Không gì cả" (All-or-Nothing):** Nếu bất kỳ điều kiện nào trong 4 thao tác của `TransactWriteItems` bị vi phạm (ví dụ số dư ví nguồn bị một luồng khác trừ đi trước dẫn đến `balance < amount`, hoặc ví đích bất ngờ bị khóa), toàn bộ lệnh `TransactWriteItems` bị hủy bỏ lập tức. Số dư hai ví không đổi và không có bản ghi giao dịch hay bản ghi idempotency rác nào được lưu lại.
- **Chính sách chiếm khóa Idempotency:** Chỉ các giao dịch thực sự thành công (`SUCCESS`) mới ghi nhận và giữ khóa idempotency. Nếu yêu cầu thất bại do lỗi nghiệp vụ (thiếu tiền, ví đích bị khóa, dữ liệu sai định dạng...), client hoàn toàn có quyền gửi lại request với cùng `Idempotency-Key` sau khi đã khắc phục nguyên nhân lỗi (ví dụ nạp thêm tiền vào ví nguồn).
- **Phân tách bảng dữ liệu độc lập:** Hệ thống phân tách rõ ràng thành 3 bảng chuyên biệt (`wallets`, `transactions`, `idempotency`) giúp cô lập rủi ro tranh chấp dữ liệu, đảm bảo hiệu năng đọc ghi cao nhất và tránh hiện tượng hot-partition trong DynamoDB.
