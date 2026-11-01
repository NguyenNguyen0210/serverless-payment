# Các lệnh CloudShell trong ảnh minh chứng Week 04

Các lệnh dưới đây được chép lại từ đầy đủ 8 ảnh CloudShell: `B4-01`, `B4-02`, `B4-12`, `B4-13`, `B4-14`, `B4-17`, `B4-18` và `B4-19`. Câu lệnh được chuẩn hóa để có thể sao chép/chạy lại; các lần gõ sai hoặc lệnh bị lặp trong ảnh đã được bỏ qua.

> Lưu ý: JWT xuất hiện trong ảnh `B4-12` không được chép nguyên văn. Hãy thay `<JWT_TOKEN>` bằng token còn hiệu lực. File `transfer.json` phải tồn tại trước khi chạy bài test concurrency.

## B4-01 — Kiểm tra môi trường và tài nguyên AWS

```bash
aws sts get-caller-identity

aws configure get region

aws lambda list-functions \
  --region us-east-1 \
  --query 'Functions[].FunctionName' \
  --output table

aws dynamodb list-tables \
  --region us-east-1 \
  --output table

aws apigatewayv2 get-apis \
  --region us-east-1 \
  --query 'Items[].{Name:Name,ApiId:ApiId,Endpoint:ApiEndpoint}' \
  --output table
```

## B4-02 — Liệt kê 5 route của API Gateway

```bash
export AWS_REGION=us-east-1
export API_ID=i7t9xqlrx7

aws apigatewayv2 get-routes \
  --api-id "$API_ID" \
  --region "$AWS_REGION" \
  --query 'Items[].{Route:RouteKey,Auth:AuthorizationType}' \
  --output table
```

## B4-12 — Gửi 5 request đồng thời với cùng Idempotency Key

```bash
export API_URL="https://i7t9xqlrx7.execute-api.us-east-1.amazonaws.com"
export TOKEN="<JWT_TOKEN>"
export CONCURRENT_KEY=$(python3 -c 'import uuid; print(uuid.uuid4())')

for i in $(seq 1 5); do
  (
    curl -sS -o "response-$i.json" \
      -w "Request $i: %{http_code}\n" \
      -X POST "$API_URL/transfers" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Idempotency-Key: $CONCURRENT_KEY" \
      -H "Content-Type: application/json" \
      --data-binary @transfer.json
  ) &
done

wait
```

## B4-13 — Kiểm tra Secrets Manager và cấu hình Lambda Authorizer

```bash
aws secretsmanager describe-secret \
  --secret-id serverless-payment/jwt-secret \
  --region us-east-1 \
  --query '{Name:Name,ARN:ARN,LastChangedDate:LastChangedDate}'

aws lambda get-function-configuration \
  --function-name serverless-payment-authorizer \
  --region us-east-1 \
  --query '{Runtime:Runtime,Role:Role,Timeout:Timeout}'
```

## B4-14 — Kiểm tra retention của CloudWatch Log Groups

```bash
aws logs describe-log-groups \
  --log-group-name-prefix /aws/lambda/serverless-payment \
  --region us-east-1 \
  --query 'logGroups[].{Name:logGroupName,Retention:retentionInDays}' \
  --output table
```

## B4-17 — Kiểm tra và gửi message vào SQS DLQ

```bash
aws sqs get-queue-url \
  --queue-name serverless-payment-dlq \
  --region us-east-1

export QUEUE_URL=$(aws sqs get-queue-url \
  --queue-name serverless-payment-dlq \
  --region us-east-1 \
  --query QueueUrl \
  --output text)

aws sqs get-queue-attributes \
  --queue-url "$QUEUE_URL" \
  --attribute-names ApproximateNumberOfMessages \
  --region us-east-1

aws sqs send-message \
  --queue-url "$QUEUE_URL" \
  --message-body '{"event":"MANUAL_WEEK4_TEST","source":"cloudshell"}' \
  --region us-east-1
```

## B4-18 — Bắn 30 request vào `/auth/token`

Phần đầu vòng lặp đã bị cuộn khỏi khung ảnh. Khối dưới đây được phục dựng từ các câu lệnh job còn hiển thị và phần tổng kết trong ảnh.

```bash
mkdir -p throttling-results

for i in $(seq 1 30); do
  (
    status=$(curl -sS --max-time 10 \
      -o "throttling-results/response-$i.json" \
      -w "%{http_code}" \
      -X POST "$API_URL/auth/token" \
      -H "Content-Type: application/json" \
      -d '{"userId":"user-a","demoCode":"invalid-test-code"}')

    echo "$status" > "throttling-results/status-$i.txt"
    echo "Request $i: HTTP $status"
  ) &
done

wait

echo "===== TỔNG KẾT ====="
for code in 200 400 401 403 429 500 502 503 000; do
  count=$(grep -lFx "$code" throttling-results/status-*.txt 2>/dev/null | wc -l)
  echo "HTTP $code: $count"
done
```

## B4-19 — Bắn 40 request vào `/transfers`

Phần đầu vòng lặp đã bị cuộn khỏi khung ảnh. Khối dưới đây được phục dựng từ các câu lệnh job còn hiển thị và phần tổng kết trong ảnh.

```bash
mkdir -p transfer-throttle-results

for i in $(seq 1 40); do
  (
    status=$(curl -sS --max-time 10 \
      -o "transfer-throttle-results/response-$i.json" \
      -w "%{http_code}" \
      -X POST "$API_URL/transfers" \
      -H "Content-Type: application/json" \
      -d '{}')

    echo "$status" > "transfer-throttle-results/status-$i.txt"
    echo "Request $i: HTTP $status"
  ) &
done

wait

echo "===== TỔNG KẾT /transfers ====="
sort transfer-throttle-results/status-*.txt | uniq -c
```

