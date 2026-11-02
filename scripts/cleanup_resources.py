#!/usr/bin/env python3
"""
Script dọn dẹp toàn bộ tài nguyên AWS sau buổi bảo vệ đồ án cuối kỳ.
Hệ thống: Serverless Payment Gateway
Học phần: Điện toán đám mây - Đợt 1, 2026-2027
GVHD: ThS. Huỳnh Xuân Phụng

LƯU Ý QUAN TRỌNG:
Chỉ chạy script này SAU KHI ĐÃ BẢO VỆ ĐỒ ÁN XONG!
Script yêu cầu truyền cờ --confirm hoặc xác nhận từ bàn phím.
"""

import sys
import argparse

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')
try:
    import boto3
    from botocore.exceptions import ClientError
except ImportError:
    boto3 = None
    ClientError = Exception

REGION = 'us-east-1'

LAMBDA_FUNCTIONS = [
    'serverless-payment-token',
    'serverless-payment-authorizer',
    'serverless-payment-transfer',
    'serverless-payment-wallet-query',
    'serverless-payment-transaction-query',
]

LAMBDA_LAYERS = [
    'serverless-payment-pyjwt',
]

DYNAMODB_TABLES = [
    'serverless-payment-wallets',
    'serverless-payment-transactions',
    'serverless-payment-idempotency',
]

SQS_QUEUE_NAME = 'serverless-payment-dlq'
API_GATEWAY_NAME = 'serverless-payment-api'
SECRET_NAME = 'serverless-payment/jwt-secret'
CLOUDWATCH_ALARM_NAME = 'serverless-payment-lambda-errors'
CLOUDWATCH_DASHBOARDS = ['serverless-payment', 'serverless-payment-dashboard']

def delete_lambdas(client):
    print("\n=== [1/8] XÓA CÁC HÀM LAMBDA ===")
    for fn in LAMBDA_FUNCTIONS:
        try:
            client.delete_function(FunctionName=fn)
            print(f"  [V] Đã xóa Lambda: {fn}")
        except ClientError as e:
            code = e.response['Error']['Code']
            if code == 'ResourceNotFoundException':
                print(f"  [-] Không tìm thấy Lambda: {fn} (đã xóa trước đó)")
            else:
                print(f"  [!] Lỗi khi xóa Lambda {fn}: {e}")

def delete_layers(client):
    print("\n=== [2/8] XÓA LAMBDA LAYERS ===")
    for layer in LAMBDA_LAYERS:
        try:
            versions = client.list_layer_versions(LayerName=layer).get('LayerVersions', [])
            for v in versions:
                v_num = v['Version']
                client.delete_layer_version(LayerName=layer, VersionNumber=v_num)
                print(f"  [V] Đã xóa Layer {layer} version {v_num}")
            if not versions:
                print(f"  [-] Không tìm thấy version nào của Layer: {layer}")
        except ClientError as e:
            print(f"  [-] Layer {layer}: {e.response['Error']['Message']}")

def delete_apigateway(client):
    print("\n=== [3/8] XÓA API GATEWAY HTTP API V2 ===")
    try:
        apis = client.get_apis().get('Items', [])
        found = False
        for api in apis:
            if api.get('Name') == API_GATEWAY_NAME:
                api_id = api['ApiId']
                client.delete_api(ApiId=api_id)
                print(f"  [V] Đã xóa API Gateway: {API_GATEWAY_NAME} (ID: {api_id})")
                found = True
        if not found:
            print(f"  [-] Không tìm thấy API Gateway: {API_GATEWAY_NAME}")
    except ClientError as e:
        print(f"  [!] Lỗi khi xóa API Gateway: {e}")

def delete_dynamodb(client):
    print("\n=== [4/8] XÓA CÁC BẢNG DYNAMODB ===")
    for tbl in DYNAMODB_TABLES:
        try:
            client.delete_table(TableName=tbl)
            print(f"  [V] Đã yêu cầu xóa DynamoDB Table: {tbl}")
        except ClientError as e:
            code = e.response['Error']['Code']
            if code == 'ResourceNotFoundException':
                print(f"  [-] Không tìm thấy bảng: {tbl}")
            else:
                print(f"  [!] Lỗi khi xóa bảng {tbl}: {e}")

def delete_sqs(client):
    print("\n=== [5/8] XÓA AMAZON SQS DLQ ===")
    try:
        url_resp = client.get_queue_url(QueueName=SQS_QUEUE_NAME)
        q_url = url_resp.get('QueueUrl')
        if q_url:
            client.delete_queue(QueueUrl=q_url)
            print(f"  [V] Đã xóa SQS Queue: {SQS_QUEUE_NAME}")
    except ClientError as e:
        code = e.response['Error']['Code']
        if code in ('QueueDoesNotExist', 'AWS.SimpleQueueService.NonExistentQueue'):
            print(f"  [-] Không tìm thấy queue: {SQS_QUEUE_NAME}")
        else:
            print(f"  [!] Lỗi khi xóa queue {SQS_QUEUE_NAME}: {e}")

def delete_secrets(client):
    print("\n=== [6/8] XÓA SECRETS MANAGER (DỪNG TÍNH PHÍ NGAY) ===")
    try:
        client.delete_secret(SecretId=SECRET_NAME, ForceDeleteWithoutRecovery=True)
        print(f"  [V] Đã xóa vĩnh viễn Secret: {SECRET_NAME} (ForceDeleteWithoutRecovery)")
    except ClientError as e:
        code = e.response['Error']['Code']
        if code == 'ResourceNotFoundException':
            print(f"  [-] Không tìm thấy Secret: {SECRET_NAME}")
        else:
            print(f"  [!] Lỗi khi xóa secret: {e}")

def delete_cloudwatch(cw_client, logs_client):
    print("\n=== [7/8] XÓA CLOUDWATCH ALARMS & DASHBOARDS ===")
    try:
        cw_client.delete_alarms(AlarmNames=[CLOUDWATCH_ALARM_NAME])
        print(f"  [V] Đã xóa Alarm: {CLOUDWATCH_ALARM_NAME}")
    except ClientError as e:
        print(f"  [-] Alarm: {e}")

    for db in CLOUDWATCH_DASHBOARDS:
        try:
            cw_client.delete_dashboards(DashboardNames=[db])
            print(f"  [V] Đã xóa Dashboard: {db}")
        except ClientError as e:
            print(f"  [-] Dashboard {db}: {e}")

    print("\n=== [8/8] XÓA CLOUDWATCH LOG GROUPS ===")
    for fn in LAMBDA_FUNCTIONS:
        log_group = f"/aws/lambda/{fn}"
        try:
            logs_client.delete_log_group(logGroupName=log_group)
            print(f"  [V] Đã xóa Log Group: {log_group}")
        except ClientError as e:
            code = e.response['Error']['Code']
            if code == 'ResourceNotFoundException':
                print(f"  [-] Không tìm thấy Log Group: {log_group}")
            else:
                print(f"  [-] Log Group {log_group}: {e}")

def main():
    parser = argparse.ArgumentParser(description='Dọn dẹp tài nguyên AWS sau nghiệm thu/bảo vệ đồ án')
    parser.add_argument('--confirm', action='store_true', help='Bỏ qua bước xác nhận qua bàn phím')
    args = parser.parse_args()

    print("="*65)
    print("CẢNH BÁO: BẠN ĐANG CHUẨN BỊ XÓA TOÀN BỘ TÀI NGUYÊN HỆ THỐNG PAYMENT!")
    print("Hạ tầng sẽ bị xóa vĩnh viễn trên AWS Region us-east-1:")
    print(" - 5 hàm Lambda + Layer PyJWT")
    print(" - API Gateway HTTP API v2")
    print(" - 3 bảng DynamoDB (wallets, transactions, idempotency)")
    print(" - SQS DLQ + Secrets Manager secret")
    print(" - CloudWatch Alarms, Dashboards, Log Groups")
    print("="*65)

    if not args.confirm:
        confirm_text = input("\nHãy nhập 'CONFIRM_DELETE' để tiến hành xóa toàn bộ: ")
        if confirm_text.strip() != 'CONFIRM_DELETE':
            print("Đã hủy thao tác. Không có tài nguyên nào bị xóa!")
            sys.exit(0)

    if boto3 is None:
        print("[!] Lỗi: Chưa cài đặt thư viện 'boto3'. Hãy chạy: pip install boto3 (hoặc chạy trong AWS CloudShell nơi đã có sẵn boto3).")
        sys.exit(1)

    print("\nBắt đầu quá trình dọn dẹp tài nguyên...")
    session = boto3.Session(region_name=REGION)
    lambda_cli = session.client('lambda')
    apigw_cli = session.client('apigatewayv2')
    dynamodb_cli = session.client('dynamodb')
    sqs_cli = session.client('sqs')
    secrets_cli = session.client('secretsmanager')
    cw_cli = session.client('cloudwatch')
    logs_cli = session.client('logs')

    delete_lambdas(lambda_cli)
    delete_layers(lambda_cli)
    delete_apigateway(apigw_cli)
    delete_dynamodb(dynamodb_cli)
    delete_sqs(sqs_cli)
    delete_secrets(secrets_cli)
    delete_cloudwatch(cw_cli, logs_cli)

    print("\n" + "="*65)
    print("HOÀN TẤT DỌN DẸP 100% TÀI NGUYÊN TRÊN AWS ACADEMY LEARNER LAB!")
    print("Môi trường đã sạch sẽ và tuân thủ đúng quy định của môn học.")
    print("="*65)

if __name__ == '__main__':
    main()
