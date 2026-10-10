# THIẾT KẾ CƠ SỞ DỮ LIỆU DYNAMODB & GIAO DỊCH ACID (DATA MODEL & TRANSACTIONS)

> **Học phần:** Cloud Computing – Đợt 1, Năm học 2026–2027  
> **Dự án:** Cổng thanh toán giả lập không máy chủ (`serverless-payment`)  
> **Người phụ trách:** Vũ Minh Đức  
> **Phối hợp & Rà soát:** Nguyễn Nguyên  
> **AWS Region:** `us-east-1` · **Phiên bản:** 1.0 (Design)  

## 1. Bảng Wallets

| Thuộc tính | Kiểu DynamoDB | Vai trò |
|---|---|---|
| walletId | S | Partition key (PK) |
| ownerId | S | userId sở hữu ví |
| balance | N | Số nguyên VND, không âm |
| currency | S | VND |
| status | S | ACTIVE/SUSPENDED |
| createdAt | S | UTC ISO 8601 |
| updatedAt | S | UTC ISO 8601 |

Ví dụ: `W001/user-a/100000/VND/ACTIVE`; `W002/user-b/50000/VND/ACTIVE`.

## 2. Bảng Transactions

| Thuộc tính | Kiểu | Vai trò |
|---|---|---|
| userId | S | Partition key (PK), lấy từ JWT |
| idempotencyKey | S | Sort key (SK), lấy từ header |
| transactionId | S | ID giao dịch do server tạo |
| requestHash | S | SHA256 của request chuẩn hóa |
| fromWalletId | S | Ví nguồn |
| toWalletId | S | Ví đích |
| amount | N | VND nguyên |
| currency | S | VND |
| status | S | `SUCCESS` cho bản ghi đã commit trong MVP |
| createdAt | S | UTC ISO 8601 |
| errorCode | S (mở rộng) | Chưa sử dụng trong MVP |

Khóa `(userId, idempotencyKey)` là duy nhất; `GetItem` với `ConsistentRead=True` giúp nhận diện lại request đã xử lý. Chưa cần GSI cho API chuyển tiền.

## 3. Canonical request và requestHash

Chuẩn hóa các trường cố định: `userId`, `fromWalletId`, `toWalletId`, `amount`, `currency`. Sort keys và encode JSON ổn định rồi lấy `SHA256`. Không trộn các trường thay đổi như thời điểm gửi hoặc transactionId vào hash.

- Key cũ, hash bằng nhau: trả lại giao dịch đã lưu, không debit tiếp.
- Key cũ, hash khác: 409 IDEMPOTENCY_KEY_CONFLICT.
- Không dùng TTL xóa bản ghi chống trùng trong giai đoạn demo.

## 4. TransactWriteItems: 3 hành động trong một lần gọi

**Put vào Transactions:** item `SUCCESS` với khóa `(userId,idempotencyKey)`, điều kiện `attribute_not_exists(userId)` để không tạo đè record cũ.

**Update ví nguồn:**

```text
SET balance = balance - :amount, updatedAt = :now
ConditionExpression:
  attribute_exists(walletId)
  AND ownerId = :userId
  AND #status = :active
  AND currency = :vnd
  AND balance >= :amount
```

**Update ví đích:**

```text
SET balance = balance + :amount, updatedAt = :now
ConditionExpression:
  attribute_exists(walletId)
  AND #status = :active
  AND currency = :vnd
```

`#status` là alias dùng với `ExpressionAttributeNames`. Các biến `:amount`, `:userId`, `:active`, `:vnd`, `:now` là expression attribute values.

Nếu bất cứ tác vụ nào không đáp ứng điều kiện, **toàn bộ transaction bị hủy**, không cập nhật một phần. Loại `fromWalletId == toWalletId` trước khi gọi (DynamoDB không cho hai thao tác trong một transaction lên cùng một item).

## 5. Xử lý cạnh tranh và retry

1. Nhận JWT và validate input trước khi gọi DynamoDB.
2. Đọc mạnh bản ghi Transactions theo `(userId,idempotencyKey)`; nếu có thì so hash và trả replay/conflict.
3. Nếu chưa có thì thử `TransactWriteItems`.
4. Nếu bị TransactionCanceledException: đọc lại nhất quán bản ghi, xem nguyên nhân hủy transaction, thử lại có giới hạn chỉ khi phù hợp.
5. Tuyệt đối không thay thế bằng 2 lệnh update ví chạy độc lập; tránh làm mất tính nguyên tử.
6. Với lỗi `INSUFFICIENT_FUNDS` trong MVP, **không ghi** `FAILED` vào Transactions; trả 409 và không cập nhật hai ví. Key của lần chưa commit không bị chiếm. Sau khi số dư thay đổi, client có thể thử lại cùng key. Cam kết idempotency bền vững chỉ áp dụng cho giao dịch `SUCCESS` đã commit.

## 6. Điểm dễ sai cần giải thích khi vấn đáp

- ClientRequestToken của `TransactWriteItems` chỉ bảo đảm idempotency trong **10 phút**, nên không dùng riêng thay cho bảng Transactions.
- Điều kiện `balance >= amount` **nằm trong transaction**; chỉ đọc trước rồi ghi sau không an toàn khi có hai yêu cầu đồng thời.
- `Transactions` được Put cùng 2 Update trong một transaction, không ghi history sau khi chuyển xong bằng lệnh rời.
- Nếu muốn `GET /transactions/{id}`, cần GSI trên `transactionId` hoặc cách tra cứu khác; GSI không hỗ trợ strongly consistent reads.

## 7. Checklist A3

- [ ] Khóa PK/SK của hai bảng thống nhất với API.
- [ ] Đã nêu đủ 3 thao tác transaction và điều kiện cập nhật.
- [ ] Đã mô tả cách xử lý retry, trùng key và đồng thời.
- [ ] Đồng bộ với A1/A2: MVP chỉ lưu `SUCCESS`; các yêu cầu lỗi không chiếm key.
- [ ] Vũ Minh Đức và Nguyễn Nguyên phê duyệt schema trước Tuần 2.

**Tham khảo chính thức:**
- https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_TransactWriteItems.html
- https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Expressions.UpdateExpressions.html

## 8. Đặc tả dữ liệu mẫu và quy trình đọc/ghi

Ví dụ hai item **minh họa, không phải dữ liệu AWS đã tạo**:

```json
{"walletId":"W001","ownerId":"user-a","balance":100000,"currency":"VND","status":"ACTIVE","createdAt":"2026-10-11T00:00:00Z","updatedAt":"2026-10-11T00:00:00Z"}
```

```json
{"walletId":"W002","ownerId":"user-b","balance":50000,"currency":"VND","status":"ACTIVE","createdAt":"2026-10-11T00:00:00Z","updatedAt":"2026-10-11T00:00:00Z"}
```

- Kiểu `N` trong DynamoDB lưu số nguyên VND, chuyển dữ liệu JSON bằng Python `int` (không sử dụng `float` để tính tiền).
- `requestHash` = SHA256 của canonical JSON có `userId`, `fromWalletId`, `toWalletId`, `amount`, `currency`, sắp xếp key, không có timestamp/key.
- Bảng `Transactions` tạo với PK `userId` và SK `idempotencyKey`. Nếu muốn tra giao dịch bằng ID riêng, cần thêm GSI hoặc chỉ mục phụ được thiết kế riêng; truy vấn GSI là eventual consistency.
- Khởi tạo `on-demand` để tránh quản lý provisioned capacity khi bắt đầu, đánh giá chi phí trong Learner Lab.
- Nên tách quyền IAM của Lambda theo nguyên tắc tối thiểu nhưng giới hạn Learner Lab yêu cầu dùng role có sẵn `LabRole`. Ghi nhận đây là hạn chế demo.
- Tag đề xuất: `Project=serverless-payment`, `Owner=VuMinhDuc` / `Owner=NguyenNguyen` (hoặc `Owner=Serverless-Team`).

### Mẫu ba hành động nguyên tử ở mức thiết kế (pseudocode)

```python
transact_write_items(
    TransactItems=[
        {"Put": {"TableName": "Transactions", "Item": transaction_success,
                 "ConditionExpression": "attribute_not_exists(userId)"}},
        {"Update": {"TableName": "Wallets", "Key": {"walletId": from_id},
                    "UpdateExpression": "SET balance = balance - :amount, updatedAt = :now",
                    "ConditionExpression": "attribute_exists(walletId) AND ownerId = :actor AND #status = :active AND currency = :vnd AND balance >= :amount"}},
        {"Update": {"TableName": "Wallets", "Key": {"walletId": to_id},
                    "UpdateExpression": "SET balance = balance + :amount, updatedAt = :now",
                    "ConditionExpression": "attribute_exists(walletId) AND #status = :active AND currency = :vnd"}}
    ]
)
```

> Đây chỉ là **pseudocode để mô tả cấu trúc**, chưa đủ kiểu AttributeValue `S/N`, `ExpressionAttributeNames` và `ExpressionAttributeValues` theo boto3 client; không chạy trực tiếp.
