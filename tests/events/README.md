# DANH MỤC MẪU JSON EVENTS KIỂM THỬ (TEST EVENT PAYLOADS)

> Thư mục này chứa các payload mẫu chuẩn HTTP API v2.0 để dán vào tab **Test** trên AWS Lambda Console hoặc truyền vào lệnh `aws lambda invoke`.

---

## 📌 Bảng tra cứu tệp JSON theo từng Lambda Function

| Lambda Function | Tệp JSON Event | Mô tả kịch bản kiểm thử | Kết quả kỳ vọng |
|---|---|---|:---:|
| **`serverless-payment-token`** | [`token_request_success.json`](token_request_success.json) | Gửi `userId: user-a` và `demoCode` đúng | HTTP 200 (Trả về `accessToken`) |
| | [`token_request_invalid_code.json`](token_request_invalid_code.json) | Gửi `demoCode` sai | HTTP 401 (`INVALID_CREDENTIALS`) |
| **`serverless-payment-authorizer`** | [`authorizer_request_valid.json`](authorizer_request_valid.json) | Header Bearer JWT hợp lệ | `{"isAuthorized": true, "context": {"userId": "user-a"}}` |
| | [`authorizer_request_missing_header.json`](authorizer_request_missing_header.json) | Thiếu header `Authorization` | `{"isAuthorized": false}` |
| **`serverless-payment-transfer`** | [`transfer_success.json`](transfer_success.json) | Chuyển 1.000 VND từ `W001` sang `W002` lần đầu | HTTP 201 (`SUCCESS`, `replayed: false`) |
| | [`transfer_replay.json`](transfer_replay.json) | Gửi lại cùng `idempotency-key` và nội dung trên | HTTP 200 (`SUCCESS`, `replayed: true`) |
| | [`transfer_insufficient.json`](transfer_insufficient.json) | Chuyển 200.000 VND (vượt số dư ví 100k) | HTTP 409 (`INSUFFICIENT_FUNDS`) |
| | [`transfer_wrong_owner.json`](transfer_wrong_owner.json) | `user-b` cố chuyển tiền từ ví `W001` của `user-a` | HTTP 403 (`WALLET_FORBIDDEN`) |
| **`serverless-payment-wallet-query`** | [`wallet_get_success.json`](wallet_get_success.json) | `user-a` tra cứu số dư ví chính chủ `W001` | HTTP 200 (Trả về thông tin ví) |
| | [`wallet_get_forbidden.json`](wallet_get_forbidden.json) | `user-a` cố tra cứu ví `W002` của `user-b` | HTTP 403 (`WALLET_FORBIDDEN`) |
| | [`wallet_history_page.json`](wallet_history_page.json) | `user-a` xem lịch sử giao dịch ví `W001` (`limit=10`) | HTTP 200 (Danh sách `items` + `nextToken`) |
| **`serverless-payment-transaction-query`** | [`transaction_get_success.json`](transaction_get_success.json) | `user-a` xem chi tiết giao dịch đã tham gia | HTTP 200 (Chi tiết giao dịch) |
| | [`transaction_get_forbidden.json`](transaction_get_forbidden.json) | `user-c` (bên ngoài) xem giao dịch người khác | HTTP 403 (`TRANSACTION_FORBIDDEN`) |

---

## 🚀 Hướng dẫn sử dụng

### Cách 1: Kiểm thử trên AWS Lambda Console
1. Mở AWS Console $\rightarrow$ Chọn dịch vụ **Lambda** $\rightarrow$ Chọn hàm cần test (ví dụ `serverless-payment-token`).
2. Chuyển sang tab **Test**.
3. Chọn **Create new event**, đặt tên (Event name: `TokenSuccess`).
4. Sao chép nội dung tệp JSON tương ứng (ví dụ [`token_request_success.json`](token_request_success.json)) dán vào ô **Event JSON**.
5. Bấm nút **Test** màu cam và xem kết quả thực thi Execution result.

### Cách 2: Kiểm thử qua AWS CLI
```bash
# Ví dụ gọi Transfer Lambda với payload thành công:
aws lambda invoke \
  --function-name serverless-payment-transfer \
  --payload file://tests/events/transfer_success.json \
  --cli-binary-format raw-in-base64-out \
  response.json

# Xem phản hồi:
cat response.json
```

