# QUY TẮC NGHIỆP VỤ & BẤT BIẾN TÀI CHÍNH (BUSINESS RULES & INVARIANTS)

> **Học phần:** Cloud Computing – Đợt 1, Năm học 2026–2027  
> **Dự án:** Cổng thanh toán giả lập không máy chủ (`serverless-payment`)  
> **Người phụ trách:** Vũ Minh Đức  
> **Phối hợp & Rà soát:** Nguyễn Nguyên  
> **AWS Region:** `us-east-1` · **Phiên bản:** 1.0 (Giai đoạn Thiết kế – Tuần 1)  

## 1. Phạm vi

Hệ thống giả lập chuyển tiền VND giữa hai ví do hệ thống quản lý. Không tích hợp ngân hàng, thanh toán thực hoặc nạp/rút tiền thật. Người dùng demo phải nhận JWT hợp lệ trước khi truy cập API chuyển tiền.

**Trong phạm vi chính:** cấp token demo; chuyển tiền; xác thực JWT; kiểm tra chủ sở hữu ví; cập nhật số dư nguyên tử; ngăn lặp request nhờ idempotency key; lưu lịch sử; ghi log không chứa bí mật.

**Ngoài phạm vi Tuần 1:** tạo tài nguyên AWS, triển khai Lambda, chạy các test thật. `GET /transactions/{id}` là chức năng mở rộng, chỉ triển khai khi nhóm thống nhất thiết kế chỉ mục tra cứu.

## 2. Bối cảnh và các đối tượng

- Người gửi (userId): được xác định từ claim `sub` của JWT, không tin `userId` tự gửi trong request.
- Ví nguồn: chứa `walletId`, `ownerId`, `balance`, `status`, `currency`.
- Ví đích: phải tồn tại, đang hoạt động và cùng loại tiền `VND`.
- Giao dịch: có `transactionId`, `idempotencyKey`, `requestHash`, `status`, thông tin 2 ví, số tiền, thời gian.

Dữ liệu minh họa: Ví `W001` của `user-a` có 100.000 VND; `W002` của `user-b` có 50.000 VND. Chuyển 30.000 VND: ví nguồn còn 70.000, ví đích thành 80.000, tổng luôn 150.000.

## 3. Quy tắc nghiệp vụ

| ID | Quy tắc | Kết quả khi vi phạm |
|---|---|---|
| BR-01 | `amount` phải là số nguyên dương; không chấp nhận `float`, chuỗi hoặc `boolean`. | `400 INVALID_AMOUNT` |
| BR-02 | `fromWalletId`, `toWalletId` bắt buộc và khác nhau. | `400 INVALID_WALLET` |
| BR-03 | Cả hai ví phải tồn tại và có `status=ACTIVE`. | `404 WALLET_NOT_FOUND` hoặc `409 WALLET_INACTIVE` |
| BR-04 | `sub` trong JWT phải trùng `ownerId` của ví nguồn. | `403 WALLET_FORBIDDEN` |
| BR-05 | Ví nguồn có `balance >= amount` tại thời điểm cập nhật. | `409 INSUFFICIENT_FUNDS` |
| BR-06 | Hai ví sử dụng `currency=VND`. | `400 UNSUPPORTED_CURRENCY` |
| BR-07 | Trừ nguồn, cộng đích, ghi lịch sử `SUCCESS` thực hiện nguyên tử trong **một** `TransactWriteItems`. | Không cập nhật một phần |
| BR-08 | Thiếu / sai / hết hạn JWT: từ chối từ API Gateway/Lambda Authorizer. | `401` khi thiếu header; `403` nếu Authorizer trả `isAuthorized=false` |
| BR-09 | Bắt buộc có `Idempotency-Key` hợp lệ. | `400 MISSING_IDEMPOTENCY_KEY` |
| BR-10 | Cùng `(userId, idempotencyKey)`, cùng `requestHash`: không chuyển lần hai; trả lại bản ghi cũ. | `200`, `replayed=true` nếu bản ghi cũ `SUCCESS` |
| BR-11 | Cùng `(userId, idempotencyKey)` nhưng `requestHash` khác: từ chối. | `409 IDEMPOTENCY_KEY_CONFLICT` |
| BR-12 | Giao dịch cạnh tranh trên ví phải kiểm tra điều kiện *trong* transaction, không chỉ pre-read. | Không chi vượt số dư |
| BR-13 | Không được tiết lộ signing key, demo code, thông tin nhạy cảm trong log/response. | Xử lý như lỗi bảo mật |
| BR-14 | Một `idempotencyKey` của hai `userId` khác nhau không tự động bị coi là trùng. | Hai không gian khóa tách biệt |

## 4. Luồng nghiệp vụ thành công

1. Client lấy JWT từ `POST /token` bằng mã truy cập demo hợp lệ.
2. Client gửi `POST /transfers` với `Authorization: Bearer <JWT>` và `Idempotency-Key`.
3. API Gateway gọi Lambda Authorizer; Authorizer xác minh chữ ký / thời hạn / issuer / audience, trả ngữ cảnh `sub`.
4. Transfer Lambda kiểm tra body, lượng tiền, khóa chống trùng, quyền đối với ví nguồn và ví đích.
5. Tính `requestHash` từ nội dung chuẩn hóa; kiểm tra bản ghi `(userId, idempotencyKey)` nếu có.
6. Gọi **một** `TransactWriteItems` gồm: `Put` giao dịch có điều kiện chưa tồn tại; `Update` ví nguồn có điều kiện; `Update` ví đích có điều kiện.
7. Giao dịch thành công: trả `201` và lưu `transactionId`, `status=SUCCESS`.

## 5. Quy tắc xử lý lỗi và tính nguyên tử

- Nếu 1 trong 3 thao tác của `TransactWriteItems` lỗi: **cả 3 cùng không có hiệu lực**.
- Kiểm tra ví nguồn bằng `ConditionExpression`: `attribute_exists(walletId) AND ownerId = :actor AND #status = :active AND balance >= :amount AND currency = :vnd`.
- Kiểm tra ví đích bằng `ConditionExpression`: `attribute_exists(walletId) AND #status = :active AND currency = :vnd`.
- Không thể tác động lên cùng một item hai lần trong một `TransactWriteItems`; vì vậy loại `fromWalletId == toWalletId` trước khi gọi DynamoDB.
- Khi transaction bị hủy do xung đột đồng thời, đọc nhất quán bản ghi idempotency và thử lại có giới hạn nếu phù hợp. Không tự động báo thất bại thiếu tiền khi nguyên nhân thực tế là xung đột kỹ thuật.
- **Quyết định thiết kế MVP (đã chuẩn hóa giữa 5 tài liệu):** Bảng `Transactions` chỉ ghi `SUCCESS` sau khi tiền thực sự được chuyển trong cùng transaction. Yêu cầu bị từ chối (thiếu tiền, ví không tồn tại, thiếu quyền, payload sai...) không tạo bản ghi giao dịch thành công và không chiếm vĩnh viễn idempotency key. Do đó, cùng key của một lần thử **thất bại** có thể được gửi lại sau khi điều kiện nghiệp vụ đã thay đổi. Đây là phạm vi idempotency được công bố trong API contract; không hứa replay chính xác mã lỗi cũ trong MVP.
- Không cài TTL tự động cho bản ghi idempotency trong giai đoạn demo 4 tuần để tránh dùng lại khóa sau khi record bị xóa.

## 6. Các trạng thái và phạm vi

- `SUCCESS`: giao dịch đã hoàn thành, tồn tại trong transaction thành công.
- `FAILED`: **không lưu vào Transactions trong MVP**. Lỗi nghiệp vụ được trả về ngay và ghi log không nhạy cảm; mở rộng trạng thái FAILED nếu có thiết kế thêm sau.
- Không dùng `PENDING` nếu hệ thống chỉ chạy transaction đồng bộ và chưa xây state machine/tác vụ bất đồng bộ.
