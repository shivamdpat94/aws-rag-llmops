import json
import boto3  # comes from your layer (src/lambdas/python/)

def lambda_handler(event, context):
    s3 = boto3.client("s3")
    return {"statusCode": 200, "body": json.dumps({"ok": True})}
