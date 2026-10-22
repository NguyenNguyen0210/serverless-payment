# KẾ HOẠCH & BỘ KỊCH BẢN KIỂM THỬ (TEST PLAN & TEST SCENARIOS)

> **Học phần:** Cloud Computing – Đợt 1, Năm học 2026–2027  
> **Dự án:** Cổng thanh toán giả lập không máy chủ (`serverless-payment`)  
> **Người phụ trách:** Vũ Minh Đức  
> **Phối hợp thực hiện:** Nguyễn Nguyên  
> **Môi trường thực thi:** AWS Academy Learner Lab (`us-east-1`)  
> **Phiên bản:** 2.0 (Kiến trúc 3 bảng DynamoDB & 5 Endpoints)  

---

## 1. Mục tiêu và Phạm vi kiểm thử

Tài liệu này xác định kế hoạch và các kịch bản kiểm thử toàn diện cho hệ thống cổng thanh toán giả lập không máy chủ, nhằm bảo đảm:
1. **Tính nguyên tử tài chính (ACID):** Số tiền chuyển giữa hai ví được thực hiện đồng thời trong một lệnh `TransactWriteItems` gồm 4 hành động, không xảy ra tình trạng trừ tiền một phía hay số dư âm khi gặp lỗi hoặc hủy giao dịch.
2. **Cơ chế chống lặp (Idempotency Control):** Xử lý an toàn khi client gửi lại request (do retry mạng hoặc thao tác bấm nhiều lần), bảo đảm không trừ tiền hai lần và phản hồi đúng kết quả giao dịch ban đầu (`200 OK, replayed: true`).
3. **Bảo mật và kiểm soát truy cập (Zero-Trust Security):** Xác thực token JWT qua Lambda Authorizer (PyJWT), kiểm tra chặt chẽ quyền sở hữu ví của người gửi (`sub == ownerId`), kiểm tra quyền truy cập lịch sử và chi tiết giao dịch.
4. **Xử lý tranh chấp đồng thời (Concurrency):** Đảm bảo tính nhất quán dữ liệu khi có nhiều yêu cầu chuyển tiền từ cùng một ví xảy ra trong cùng một thời điểm.
5. **Khả năng chịu tải và chống lỗi hệ thống:** Xác thực cơ chế Route Throttling (HTTP 429) và điều hướng lỗi unhandled exception vào Amazon SQS Dead Letter Queue (DLQ).
6. **Kiểm thử các API tra cứu mở rộng:** Đảm bảo các route tra cứu số dư, chi tiết giao dịch và lịch sử phân trang hoạt động chính xác, bảo mật và hiệu năng cao.

---

## 2. Dữ liệu khởi tạo mẫu (Test Fixtures & Seed Data)

Trước khi thực hiện các chu kỳ kiểm thử, dữ liệu khởi tạo trên bảng DynamoDB `serverless-payment-wallets` được thiết lập bằng script [`scripts/seed_wallets.py`](../scripts/seed_wallets.py):

| Mã ví (`walletId`) | Chủ sở hữu (`ownerId`) | Số dư (`balance`) | Loại tiền (`currency`) | Trạng thái (`status`) | Mục đích thử nghiệm |
|---|---|---:|:---:|:---:|---|
| `W001` | `user-a` | 100.000 | `VND` | `ACTIVE` | Ví nguồn chính của User A |
| `W002` | `user-b` | 50.000 | `VND` | `ACTIVE` | Ví đích nhận tiền của User B |
| `W003` | `user-b` | 20.000 | `VND` | `SUSPENDED` | Ví đích bị khóa (kiểm tra điều kiện) |
| `W004` | `user-a` | 10.000 | `USD` | `ACTIVE` | Ví ngoại tệ (kiểm tra sai loại tiền) |

---

## 3. Ma trận kịch bản kiểm thử chi tiết (Test Scenarios Matrix)

### Nhóm 1: Kiểm thử chức năng cốt lõi (Happy Path)

| Mã | Mô tả kịch bản | Dữ liệu đầu vào | Kết quả kỳ vọng | Kiểm tra cơ sở dữ liệu DynamoDB |
|:---:|---|---|:---:|---|
| **TC-01** | Chuyển tiền thành công giữa 2 ví hợp lệ | JWT `user-a`, `W001` $\rightarrow$ `W002`, 30.000 VND, `Idempotency-Key: K1` | `201 Created`<br>`status: SUCCESS`<br>`replayed: false` | `W001.balance` = 70.000<br>`W002.balance` = 80.000<br>Bảng `idempotency` có `K1`, bảng `transactions` có 1 record |
| **TC-02** | Gửi lại cùng request và key đã thành công (Idempotent Replay) | Giữ nguyên toàn bộ payload, header và `Idempotency-Key: K1` như TC-01 | `200 OK`<br>`status: SUCCESS`<br>`replayed: true` | Số dư `W001` vẫn là 70.000<br>Số dư `W002` vẫn là 80.000<br>Không sinh bản ghi mới, không trừ thêm tiền |

### Nhóm 2: Kiểm thử cơ chế Chống lặp (Idempotency Control)

| Mã | Mô tả kịch bản | Dữ liệu đầu vào | Kết quả kỳ vọng | Kiểm tra cơ sở dữ liệu DynamoDB |
|:---:|---|---|:---:|---|
| **TC-03** | Tái sử dụng key cũ nhưng thay đổi nội dung (Payload Conflict) | JWT `user-a`, cùng `Idempotency-Key: K1`, đổi `amount: 40000` | `409 Conflict`<br>`code: IDEMPOTENCY_KEY_CONFLICT` | Dữ liệu ví và giao dịch không thay đổi |
| **TC-12** | Gửi song song 10 request cùng key (Burst Replay) | 10 luồng đồng thời gửi cùng payload và `Idempotency-Key: K2` | Đúng 1 request nhận `201 Created`, 9 request còn lại nhận `200 OK` (replayed) | Chỉ thực hiện trừ tiền 1 lần duy nhất; bảng `transactions` có đúng 1 record `K2` |
| **TC-13** | Gửi lại key cũ sau khoảng thời gian dài (> 10 phút) | Gửi lại `Idempotency-Key: K1` sau 15 phút | `200 OK`<br>`replayed: true` | Không bị trừ tiền thêm; chứng minh không phụ thuộc giới hạn 10 phút của DynamoDB ClientRequestToken |
| **TC-17** | Thử lại cùng key của request từng thất bại trước đó | Gửi request lỗi (ví dụ thiếu tiền) với `K3`, sau đó nạp tiền ví và gửi lại đúng `K3` | Lần 1: `409 INSUFFICIENT_FUNDS`<br>Lần 2: `201 Created` | Request thất bại không chiếm key; cho phép client hoàn tất giao dịch sau khi thỏa điều kiện |

### Nhóm 3: Kiểm thử Xác thực & Phân quyền (Authentication & Authorization)

| Mã | Mô tả kịch bản | Dữ liệu đầu vào | Kết quả kỳ vọng | Ghi chú kỹ thuật |
|:---:|---|---|:---:|---|
| **TC-04** | Yêu cầu không có header `Authorization` | Không gửi header `Authorization` | `401 Unauthorized` | API Gateway chặn trực tiếp tại tầng ingress |
| **TC-05** | Token JWT hết hạn hoặc chữ ký HMAC bị sửa đổi | Gửi JWT hết hạn (`exp` quá khứ) hoặc chữ ký không khớp | `403 Forbidden` | Lambda Authorizer trả về `isAuthorized: false` |
| **TC-06** | Người dùng cố chuyển tiền từ ví của người khác | JWT `user-b`, yêu cầu chuyển tiền từ `W001` (chủ sở hữu là `user-a`) | `403 Forbidden` | Transfer Lambda kiểm tra `sub != ownerId` và từ chối |
| **TC-14** | Yêu cầu thiếu header `Idempotency-Key` | Header hợp lệ nhưng không có `Idempotency-Key` | `400 Bad Request`<br>`code: MISSING_IDEMPOTENCY_KEY` | Dữ liệu ví không thay đổi |
| **TC-15** | Token JWT sai trường `iss` (Issuer) hoặc `aud` (Audience) | JWT ký hợp lệ nhưng `iss: untrusted-issuer` | `403 Forbidden` | Lambda Authorizer kiểm tra claims và từ chối |

### Nhóm 4: Kiểm thử Quy tắc nghiệp vụ (Business Rules Validation)

| Mã | Mô tả kịch bản | Dữ liệu đầu vào | Kết quả kỳ vọng | Ghi chú kỹ thuật |
|:---:|---|---|:---:|---|
| **TC-07** | Số dư ví nguồn không đủ thực hiện giao dịch | `W001` có 100.000 VND, yêu cầu chuyển 200.000 VND | `409 Conflict`<br>`code: INSUFFICIENT_FUNDS` | Điều kiện `balance >= amount` bị vi phạm |
| **TC-08** | Ví nguồn và ví đích trùng nhau | `fromWalletId: W001`, `toWalletId: W001` | `400 Bad Request`<br>`code: INVALID_WALLET` | Chặn từ tầng kiểm tra dữ liệu đầu vào |
| **TC-09** | Chuyển tiền tới ví đích không tồn tại | `toWalletId: W999` (không có trong CSDL) | `404 Not Found`<br>`code: WALLET_NOT_FOUND` | Ví nguồn không bị trừ tiền |
| **TC-10** | Số tiền giao dịch không hợp lệ | `amount` nhận giá trị: `0`, `-50000`, `15.5`, `"30000"`, `true` | `400 Bad Request`<br>`code: INVALID_AMOUNT` | Bắt buộc số nguyên dương VND |
| **TC-19** | Chuyển tiền tới ví đích đang bị khóa (`SUSPENDED`) | `toWalletId: W003` (`status: SUSPENDED`) | `409 Conflict`<br>`code: WALLET_INACTIVE` | Điều kiện `status == ACTIVE` bị vi phạm |

### Nhóm 5: Kiểm thử Tính nguyên tử & Tranh chấp đồng thời (Atomicity & Concurrency)

| Mã | Mô tả kịch bản | Dữ liệu đầu vào | Kết quả kỳ vọng | Kiểm tra bảo đảm tính nhất quán |
|:---:|---|---|:---:|---|
| **TC-11** | Hai yêu cầu khác key rút tiền đồng thời vượt quá số dư | `W001` có 100.000 VND. Gửi đồng thời Request 1 (80.000) và Request 2 (80.000) với 2 key khác nhau | Chính xác 1 request thành công (`201`), 1 request thất bại (`409 INSUFFICIENT_FUNDS`) | Số dư ví còn 20.000 VND; tuyệt đối không xảy ra số dư âm (-60.000 VND) |
| **TC-16** | Mô phỏng lỗi một nhánh trong `TransactWriteItems` | Ví nguồn đủ tiền nhưng ví đích vi phạm điều kiện | Toàn bộ transaction bị rollback, trả về mã lỗi thích hợp | Ví nguồn không bị trừ tiền; không xảy ra lỗi cập nhật một phần |
| **TC-18** | Đọc nhất quán sau khi hoàn tất giao dịch | Đọc trạng thái ví ngay sau khi nhận phản hồi `201` | Dữ liệu số dư phản ánh chính xác giá trị mới | Đảm bảo tính nhất quán tức thì (Strong Consistency) |

### Nhóm 6: Kiểm thử Kiểm soát lưu lượng & Khả năng chịu lỗi (Rate Limiting & DLQ)

| Mã | Mô tả kịch bản | Dữ liệu đầu vào | Kết quả kỳ vọng | Cơ chế kiểm tra hạ tầng AWS |
|:---:|---|---|:---:|---|
| **TC-20** | Gửi request dồn dập vượt ngưỡng Rate Limit (Throttling) | Gửi burst 30 requests/giây liên tục vào route `/auth/token` hoặc `/transfers` | Các request vượt ngưỡng nhận `429 Too Many Requests` kèm header `Retry-After` | Chặn trực tiếp tại API Gateway Ingress; không kích hoạt Lambda và không tính chi phí backend |
| **TC-21** | Mô phỏng sự cố hệ thống nghiêm trọng kích hoạt DLQ | Giả lập lỗi ngoại lệ chưa xử lý (unhandled error/timeout) trong Transfer Lambda | Trả về `500 Internal Server Error`, payload gốc tự động chuyển vào SQS DLQ | Truy vấn hàng đợi `serverless-payment-dlq` xác nhận message được lưu vết an toàn |

### Nhóm 7: Kiểm thử API tra cứu mở rộng (Query Endpoints Validation)

| Mã | Mô tả kịch bản | Dữ liệu đầu vào | Kết quả kỳ vọng | Ghi chú kỹ thuật |
|:---:|---|---|:---:|---|
| **TC-22** | Tra cứu thông tin ví chính chủ | JWT `user-a`, `GET /wallets/W001` | `200 OK`<br>Trả về `balance`, `currency`, `status` | Kiểm tra `ownerId == sub`, cho phép truy cập |
| **TC-23** | Tra cứu ví của người khác | JWT `user-a`, `GET /wallets/W002` (ví của `user-b`) | `403 Forbidden` | Chặn truy cập trái phép, bảo vệ tính riêng tư |
| **TC-24** | Tra cứu chi tiết giao dịch hợp lệ | JWT `user-a` (người gửi), `GET /transactions/{id}` | `200 OK`<br>Trả về chi tiết giao dịch | Kiểm tra `sub` là một trong hai bên tham gia |
| **TC-25** | Tra cứu giao dịch của bên thứ ba | JWT `user-c` (không tham gia), `GET /transactions/{id}` | `403 Forbidden` | Chặn bên thứ ba đọc thông tin giao dịch |
| **TC-26** | Tra cứu lịch sử giao dịch ví có phân trang | JWT `user-a`, `GET /wallets/W001/transactions?limit=10` | `200 OK`<br>Trả về danh sách `items` và `nextToken` | Truy vấn đồng thời 2 GSIs, sắp xếp giảm dần theo `timeKey` |

---

## 4. Phương pháp thực thi kiểm thử

Hệ thống hỗ trợ kiểm thử linh hoạt qua hai phương pháp:

### Phương pháp 1: Kiểm thử API trực tiếp bằng cURL / Postman
Mỗi endpoint trong số 5 API endpoints đều được chuẩn hóa cú pháp cURL mẫu chi tiết tại [`docs/api-contract.md`](api-contract.md). Người thực hiện có thể sao chép trực tiếp lệnh cURL chạy trên Command Prompt, PowerShell hoặc nhập vào Postman.

### Phương pháp 2: Kiểm thử Unit Tests tự động
Bộ 15 unit tests tự động (`tests/test_auth.py`, `tests/test_transfer.py`) kiểm tra trọn vẹn logic chữ ký JWT, kiểm tra quyền sở hữu ví và tính nguyên tử của giao dịch.

```bash
# Thực thi toàn bộ bộ Unit Tests
python -m unittest discover -s tests -v
```

---

## 5. Biểu mẫu ghi nhận kết quả kiểm thử (Test Execution Log)

| Mã TC | Tên kịch bản | HTTP kỳ vọng | HTTP thực tế | Trạng thái số dư ví / Hạ tầng | Kết quả | Tệp minh chứng |
|:---:|---|:---:|:---:|---|:---:|---|
| **TC-01** | Chuyển tiền thành công | `201` | `201` | `W001 -30k`, `W002 +30k` | **Đạt** | [`A2-13`](../evidence/week02/duc/A2-13-transfer-test-success.png), [`A2-18`](../evidence/week02/duc/A2-18-api-transfer-success.png) |
| **TC-02** | Gửi lại cùng key (Replay) | `200` | `200` | Không đổi số dư, `replayed: true` | **Đạt** | [`A2-14`](../evidence/week02/duc/A2-14-transfer-test-idempotent-replay.png) |
| **TC-03** | Trùng key khác nội dung | `409` | `409` | Không đổi số dư | **Đạt** | [`A2-15`](../evidence/week02/duc/A2-15-transfer-test-idempotency-conflict.png) |
| **TC-04** | Thiếu Authorization | `401` | `401` | Chặn tại Gateway Ingress | **Đạt** | cURL & Unit test |
| **TC-05** | Token JWT hết hạn | `403` | `403` | Lambda Authorizer từ chối | **Đạt** | Unit test `test_auth.py` |
| **TC-06** | Chuyển tiền ví người khác | `403` | `403` | Không tác động CSDL | **Đạt** | [`A2-16`](../evidence/week02/duc/A2-16-transfer-test-wallet-forbidden.png) |
| **TC-07** | Không đủ số dư | `409` | `409` | Không đổi số dư | **Đạt** | [`A2-12`](../evidence/week02/duc/A2-12-transfer-test-insufficient-funds.png) |
| **TC-08** | Chuyển cho chính mình | `400` | `400` | Không tác động | **Đạt** | Unit test `test_transfer.py` |
| **TC-09** | Ví đích không tồn tại | `404` | `404` | Không tác động | **Đạt** | Unit test `test_transfer.py` |
| **TC-10** | Số tiền không hợp lệ | `400` | `400` | Không tác động | **Đạt** | Unit test `test_transfer.py` |
| **TC-11** | Hai giao dịch tranh chấp | `201 & 409` | `201 & 409` | Chỉ trừ 1 lần, không âm ví | **Đạt** | Unit test & Concurrency test |
| **TC-12** | 10 request song song cùng key | `1x 201, 9x 200` | `1x 201, 9x 200` | Chỉ trừ 1 lần duy nhất | **Đạt** | Idempotency test |
| **TC-20** | Vượt ngưỡng Rate Limit | `429` | `429` | Chặn tại Gateway, header Retry-After | **Đạt** | Throttling test |
| **TC-21** | Ngoại lệ hệ thống chuyển DLQ | `500` | `500` | Message chuyển vào SQS DLQ | **Đạt** | Resilience test |
| **TC-22** | Tra cứu ví chính chủ | `200` | `200` | Trả về số dư chính xác | **Đạt** | cURL `GET /wallets/{id}` |
| **TC-23** | Tra cứu ví người khác | `403` | `403` | Bị từ chối bảo vệ quyền riêng tư | **Đạt** | cURL `GET /wallets/{id}` |
| **TC-24** | Tra cứu chi tiết giao dịch | `200` | `200` | Trả về đúng `amount` và `transactionId` | **Đạt** | cURL `GET /transactions/{id}` |
| **TC-25** | Tra cứu giao dịch bên thứ ba | `403` | `403` | Bị từ chối truy xuất | **Đạt** | cURL `GET /transactions/{id}` |
| **TC-26** | Phân trang lịch sử giao dịch | `200` | `200` | Trả về `items` và `nextToken` | **Đạt** | cURL `GET /wallets/{id}/transactions` |
