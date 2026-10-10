# KẾ HOẠCH & KỊCH BẢN KIỂM THỬ (TEST PLAN & SCENARIOS)

> **Học phần:** Cloud Computing – Đợt 1, Năm học 2026–2027  
> **Dự án:** Cổng thanh toán giả lập không máy chủ (`serverless-payment`)  
> **Người phụ trách:** Vũ Minh Đức  
> **Phối hợp thực hiện:** Nguyễn Nguyên  
> **Trạng thái:** Kế hoạch kiểm thử hoàn chỉnh cho các tuần 2–4  

**Dữ liệu khởi tạo mẫu:** `user-a` sở hữu `W001` = 100.000 VND; `user-b` sở hữu `W002` = 50.000 VND; status cả hai ACTIVE.

| ID | Kiểm thử | Kết quả kỳ vọng |
|---|---|---|
| TC-01 | Token hợp lệ; W001 → W002, 30.000 với K1 | 201 SUCCESS; W001=70.000; W002=80.000 |
| TC-02 | Gửi lại đúng payload và K1 | 200 replayed=true; số dư không đổi; transactionId cũ |
| TC-03 | K1 nhưng amount=40.000 | 409 IDEMPOTENCY_KEY_CONFLICT; số dư không đổi |
| TC-04 | Thiếu Authorization | 401; không chuyển tiền |
| TC-05 | Token hết hạn/chữ ký sai | 403 (simple authorizer deny); không chuyển tiền |
| TC-06 | user-b cố chuyển từ W001 | 403; không chuyển tiền |
| TC-07 | Gửi 200.000 từ W001 còn 100.000 | 409 INSUFFICIENT_FUNDS; không trừ |
| TC-08 | Chuyển từ W001 đến chính W001 | 400 INVALID_WALLET |
| TC-09 | Chuyển đến W999 không tồn tại | 404; ví nguồn không bị trừ |
| TC-10 | amount=0,-1,1.5,"10",true | 400 INVALID_AMOUNT |
| TC-11 | Hai request khác key đồng thời, mỗi request 80.000 từ ví có 100.000 | Tối đa 1 thành công; không âm số dư |
| TC-12 | Gửi song song 10 request cùng key | Chỉ 1 SUCCESS và 1 lần debit/credit |
| TC-13 | Gửi lại K1 sau hơn 10 phút | Không trừ thêm; replay nhờ record còn tồn tại |
| TC-14 | Thiếu Idempotency-Key | 400; không cập nhật ví |
| TC-15 | JWT sai audience/issuer | 403 (simple authorizer deny) |
| TC-16 | DynamoDB transaction có 1 thao tác thất bại | Toàn bộ rollback; không cập nhật từng phần |

## Phương pháp chạy kiểm thử trong Tuần 2–4

1. Thiết lập dữ liệu ví mẫu và bảo đảm biết **số dư ban đầu** trước mỗi test.
2. Dùng Postman hoặc script requests/curl với JWT và Idempotency-Key.
3. Ghi status HTTP, `transactionId`, response body.
4. Đọc lại `Wallets` và `Transactions` sau mỗi test, ghi đối chiếu số dư và số lượng giao dịch.
5. Kiểm tra CloudWatch log (không lộ JWT/signing key).
6. Lưu ảnh minh chứng và thời gian thực hiện. Nếu test cần concurrency, dùng script gửi song song, không chỉ click Postman thủ công.

## Lịch kiểm thử đề xuất

- Tuần 2: TC-01, TC-04...TC-10, TC-14, TC-15 (chức năng lõi + auth).
- Tuần 3: TC-02, TC-03, TC-11...TC-13, TC-16 (concurrency/idempotency).
- Tuần 4: chạy lại toàn bộ và quay demo.

## Bảng ghi kết quả thực tế (sau khi code chạy thật)

| Test | Trạng thái hiện tại | HTTP thực tế | Evidence |
|---|---|---|---|
| TC-01 | NOT RUN | Chưa có | Chưa có |
| TC-02 | NOT RUN | Chưa có | Chưa có |

**Tuyệt đối không đổi `NOT RUN` thành PASS nếu chưa thực hiện test thật trên AWS Learner Lab.**

## Quy tắc nghiệm thu tự động

- TC-01: `balance(W001) + balance(W002) == 150000` và chỉ **một** bản ghi Transactions có key K1.
- TC-02/12/13: `transactionId` trả về bằng TC-01, không có khoản debit/credit tiếp theo.
- TC-03: không thay đổi dữ liệu dù request amount khác.
- TC-11: hai key khác nhau tranh chấp, nếu mỗi request 80.000 thì **không quá một** request được commit với nguồn 100.000.
- TC-16: mô phỏng điều kiện cập nhật ví đích không thỏa mãn, không có item SUCCESS và không có số dư cập nhật.
- Thêm TC-17: thử lại cùng key của **request chưa commit** sau khi reset/chuẩn bị lại số dư và trạng thái ví: được phép thực hiện vì chưa có record SUCCESS (theo MVP).
- Thêm TC-18: nếu role không có quyền TransactWriteItems, việc list table thành công không có nghĩa có quyền ghi; cần ghi nhận AccessDenied trong kiểm thử thực tế.

## Mẫu bảng kết quả để điền sau khi có AWS chạy thật

| TC | Expected HTTP | Actual HTTP | Wallets before / after | Transactions count | Evidence | Result |
|---|---|---|---|---|---|---|
| TC-01 | 201 | NOT RUN | NOT RUN | NOT RUN | NOT RUN | NOT RUN |
| TC-02 | 200 | NOT RUN | NOT RUN | NOT RUN | NOT RUN | NOT RUN |
| TC-11 | 201 / lỗi phù hợp | NOT RUN | NOT RUN | NOT RUN | NOT RUN | NOT RUN |

> Khi chạy thật, thực hiện các test độc lập với seed/reset có kiểm soát để không làm test trước ảnh hưởng test sau.
