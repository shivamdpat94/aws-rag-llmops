print("BOOT OK: app.py loaded")

import json
import os
import boto3

s3 = boto3.client("s3")

def lambda_handler(event, context):
    # Log the event we received
    print("EVENT:", json.dumps(event))

    # Handle S3 put events (ObjectCreated)
    recs = event.get("Records", [])
    if not recs:
        return {"ok": True, "note": "no records"}

    bucket = recs[0]["s3"]["bucket"]["name"]
    key    = recs[0]["s3"]["object"]["key"]

    # Read the object to confirm permissions/plumbing
    obj = s3.get_object(Bucket=bucket, Key=key)
    body = obj["Body"].read().decode("utf-8", errors="ignore")
    print(f"READ {bucket}/{key}: {len(body)} bytes")

    # Return something small
    return {"ok": True, "bucket": bucket, "key": key, "bytes": len(body)}
