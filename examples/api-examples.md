# Ví dụ gọi API (chỉ dùng sau khi deploy Tuần 2)

> Thay `API_URL`, `YOUR_JWT` và demo code bằng giá trị thực lấy qua kênh an toàn; ví dụ trong tài liệu **không có token hoặc secret thật**. Tuyệt đối không commit JWT thật.

## 1. Lấy token

```bash
curl -X POST "$API_URL/token" \
  -H 'Content-Type: application/json' \
  -d '{"userId":"user-a","demoCode":"REPLACE_FROM_SECURE_SOURCE"}'
```

## 2. Chuyển tiền

```bash
curl -X POST "$API_URL/transfers" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H 'Content-Type: application/json' \
  -H 'Idempotency-Key: 4c7d3e65-1f10-47c7-b6f3-e99c91ba00d1' \
  -d '{"fromWalletId":"W001","toWalletId":"W002","amount":30000}'
```

- Lần đầu thành công: `201`, `replayed=false`.
- Lặp nguyên request cùng key: `200`, `replayed=true`, cùng `transactionId`.
- Giữ key nhưng thay `amount`: `409 IDEMPOTENCY_KEY_CONFLICT`.

## 3. Kiểm chứng sau lệnh

Đối chiếu hai item `Wallets` và một item `Transactions` trong DynamoDB Console/CLI, ghi hình trước–sau và thời gian kiểm thử. Dữ liệu seed của ví demo cần được thiết lập nhất quán.

**Không thực hiện lệnh này ở Tuần 1:** Mục đích file là mẫu để dùng ở Tuần 2 khi API đã chạy thật.
