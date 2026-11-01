# Các lệnh CloudShell trong ảnh minh chứng Week 04 – Vũ Minh Đức

Tệp này tổng hợp lệnh từ 8 ảnh CloudShell: `A4-01`, `A4-02`, `A4-12`, `A4-13`, `A4-14`, `A4-17`, `A4-18` và `A4-19`. Các lần gõ sai trong terminal đã được bỏ qua; token và secret không được ghi lại.

## Biến môi trường dùng chung

```bash
export AWS_REGION=us-east-1

export API_ID=$(aws apigatewayv2 get-apis \
  --region "$AWS_REGION" \
  --query "Items[?Name=='serverless-payment-api'].ApiId | [0]" \
  --output text)

export API_URL=$(aws apigatewayv2 get-api \
  --api-id "$API_ID" \
  --region "$AWS_REGION" \
  --query ApiEndpoint \
  --output text)
```

## A4-01 — Kiểm tra môi trường và tài nguyên AWS

```bash
aws sts get-caller-identity
aws configure get region

aws lambda list-functions \
  --region "$AWS_REGION" \
  --query 'Functions[].FunctionName' \
  --output table

aws dynamodb list-tables \
  --region "$AWS_REGION" \
  --output table

aws apigatewayv2 get-apis \
  --region "$AWS_REGION" \
  --query 'Items[].{Name:Name,ApiId:ApiId,Endpoint:ApiEndpoint}' \
  --output table
```

## A4-02 — Liệt kê 5 API routes

```bash
aws apigatewayv2 get-routes \
  --api-id "$API_ID" \
  --region "$AWS_REGION" \
  --query 'Items[].{Route:RouteKey,Auth:AuthorizationType}' \
  --output table
```

## A4-12 — Kiểm thử 5 request đồng thời

Trước khi chạy, biến `TOKEN` phải chứa JWT còn hiệu lực và `transfer.json` phải có payload hợp lệ.

```bash
export CONCURRENT_KEY=$(python3 -c 'import uuid; print(uuid.uuid4())')
rm -f response-{1..5}.json

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

for file in response-*.json; do
  printf "%s: " "$file"
  jq -r '"transactionId=\(.transactionId) | status=\(.status) | replayed=\(.replayed)"' "$file"
done
```

## A4-13 — Kiểm tra Secrets Manager và IAM Lambda

```bash
aws secretsmanager describe-secret \
  --secret-id serverless-payment/jwt-secret \
  --region "$AWS_REGION" \
  --query '{Name:Name,ARN:ARN,LastChangedDate:LastChangedDate}'

aws lambda get-function-configuration \
  --function-name serverless-payment-authorizer \
  --region "$AWS_REGION" \
  --query '{Runtime:Runtime,Role:Role,Timeout:Timeout}'
```

## A4-14 — Kiểm tra CloudWatch Logs retention

```bash
aws logs describe-log-groups \
  --log-group-name-prefix /aws/lambda/serverless-payment \
  --region "$AWS_REGION" \
  --query 'logGroups[].{Name:logGroupName,Retention:retentionInDays}' \
  --output table
```

## A4-17 — Kiểm tra và gửi message vào SQS DLQ

```bash
export QUEUE_URL=$(aws sqs get-queue-url \
  --queue-name serverless-payment-dlq \
  --region "$AWS_REGION" \
  --query QueueUrl \
  --output text)

echo "QUEUE_URL=$QUEUE_URL"

aws sqs get-queue-attributes \
  --queue-url "$QUEUE_URL" \
  --attribute-names QueueArn ApproximateNumberOfMessages \
  --region "$AWS_REGION"

aws sqs send-message \
  --queue-url "$QUEUE_URL" \
  --message-body '{"event":"MANUAL_WEEK4_TEST","source":"cloudshell"}' \
  --region "$AWS_REGION"

aws sqs get-queue-attributes \
  --queue-url "$QUEUE_URL" \
  --attribute-names QueueArn ApproximateNumberOfMessages \
  --region "$AWS_REGION"
```

## A4-18 — Kiểm thử burst 30 request vào `/auth/token`

```bash
mkdir -p throttling-results
rm -f throttling-results/response-*.json throttling-results/status-*.txt throttling-results/headers-*.txt

for i in $(seq 1 30); do
  (
    status=$(curl -sS --max-time 10 \
      -D "throttling-results/headers-$i.txt" \
      -o "throttling-results/response-$i.json" \
      -w "%{http_code}" \
      -X POST "$API_URL/auth/token" \
      -H "Content-Type: application/json" \
      -d '{"userId":"user-a","demoCode":"invalid-test-code"}')

    echo "$status" > "throttling-results/status-$i.txt"
  ) &
done

wait

for code in 200 400 401 403 429 500 502 503 000; do
  count=$(grep -lFx "$code" throttling-results/status-*.txt 2>/dev/null | wc -l)
  echo "HTTP $code: $count"
done
```

Kết quả trong ảnh A4-18: 30 request đều được từ chối với `HTTP 401` do dùng demo code không hợp lệ.

## A4-19 — Kiểm thử idempotency dưới tải burst trên `/transfers`

Trước khi chạy, `TOKEN` phải còn hiệu lực và `transfer-throttle.json` phải chứa payload hợp lệ. Cùng một `TRANSFER_THROTTLE_KEY` được dùng để không trừ tiền nhiều lần.

```bash
mkdir -p transfer-throttle-results
rm -f transfer-throttle-results/response-*.json transfer-throttle-results/status-*.txt transfer-throttle-results/headers-*.txt

export TRANSFER_THROTTLE_KEY=$(python3 -c 'import uuid; print(uuid.uuid4())')

for i in $(seq 1 40); do
  (
    status=$(curl -sS --max-time 10 \
      -D "transfer-throttle-results/headers-$i.txt" \
      -o "transfer-throttle-results/response-$i.json" \
      -w "%{http_code}" \
      -X POST "$API_URL/transfers" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Idempotency-Key: $TRANSFER_THROTTLE_KEY" \
      -H "Content-Type: application/json" \
      --data-binary @transfer-throttle.json)

    echo "$status" > "transfer-throttle-results/status-$i.txt"
  ) &
done

wait

for code in 200 201 400 401 403 409 429 500 502 503 000; do
  count=$(grep -lFx "$code" transfer-throttle-results/status-*.txt 2>/dev/null | wc -l)
  echo "HTTP $code: $count"
done

jq -r 'select(.transactionId != null) | .transactionId' \
  transfer-throttle-results/response-*.json \
  | sort | uniq -c
```

Kết quả trong ảnh A4-19: `HTTP 201: 1`, `HTTP 200: 39` và chỉ có một `transactionId`.
