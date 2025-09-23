import os
import json
import boto3
import requests

s3 = boto3.client("s3")

OPENAI_KEY = os.environ.get("OPENAI_API_KEY")
PINECONE_KEY = os.environ.get("PINECONE_API_KEY")
PINECONE_INDEX = os.environ.get("PINECONE_INDEX")
PINECONE_PROJECT = os.environ.get("PINECONE_PROJECT")  # e.g. b3u2wwf
PINECONE_ENV = os.environ.get("PINECONE_ENV", "us-east-1-aws")

# Build Pinecone URL correctly: <index>-<project>.svc.<env>.pinecone.io
PINECONE_HOST = os.environ.get("PINECONE_HOST")  # set this in Lambda env vars


PINECONE_URL = f"{PINECONE_HOST}/vectors/upsert"

def chunk_text(text, max_chunk_size=1000):
    """Split text into smaller chunks."""
    return [text[i : i + max_chunk_size] for i in range(0, len(text), max_chunk_size)]


def embed_chunks(chunks):
    """Call OpenAI embeddings API for each chunk."""
    headers = {"Authorization": f"Bearer {OPENAI_KEY}", "Content-Type": "application/json"}
    url = "https://api.openai.com/v1/embeddings"

    vectors = []
    for i, chunk in enumerate(chunks):
        try:
            body = {"model": "text-embedding-3-small", "input": chunk}
            resp = requests.post(url, headers=headers, json=body)
            if resp.status_code == 200:
                vec = resp.json()["data"][0]["embedding"]
                vectors.append({"id": f"chunk-{i}", "values": vec, "metadata": {"text": chunk}})
                print(f"✅ EMBEDDING OK: chunk-{i}, dim={len(vec)}")
            else:
                print(f"❌ EMBEDDING FAIL: chunk-{i}, status={resp.status_code}, body={resp.text}")
        except Exception as e:
            print(f"❌ EMBEDDING EXCEPTION: {e}")
    return vectors


def upsert_vectors(vectors):
    """Send vectors to Pinecone index."""
    headers = {"Api-Key": PINECONE_KEY, "Content-Type": "application/json"}
    body = {"vectors": vectors, "namespace": "default"}  # Add namespace for safety
    try:
        print("UPSERT URL:", PINECONE_URL)
        print("UPSERT HEADERS:", {k: v[:6] + "..." for k, v in headers.items()})  # mask secrets
        print("UPSERT BODY SAMPLE:", json.dumps(body)[:300])  # first 300 chars only

        resp = requests.post(PINECONE_URL, headers=headers, data=json.dumps(body))
        if resp.status_code == 200:
            print(f"✅ UPSERT OK: {len(vectors)} vectors")
        else:
            print(f"❌ UPSERT FAIL: status={resp.status_code}, body={resp.text}")
    except Exception as e:
        print(f"❌ UPSERT EXCEPTION: {e}")


def lambda_handler(event, context):
    print(f"EVENT: {json.dumps(event)}")

    for record in event.get("Records", []):
        bucket = record["s3"]["bucket"]["name"]
        key = record["s3"]["object"]["key"]
        print(f"Downloading s3://{bucket}/{key}")

        # Fetch file from S3
        obj = s3.get_object(Bucket=bucket, Key=key)
        text = obj["Body"].read().decode("utf-8")
        print(f"READ {bucket}/{key}: {len(text)} bytes")

        # Chunk it
        chunks = chunk_text(text)
        print(f"Chunked into {len(chunks)} pieces")

        # Embeddings
        print("START embeddings...")
        vectors = embed_chunks(chunks)
        print(f"Total vectors embedded: {len(vectors)}")

        # Pinecone upsert
        if vectors and PINECONE_KEY and PINECONE_INDEX and PINECONE_PROJECT:
            print("START Pinecone upsert...")
            upsert_vectors(vectors)
        else:
            print("❌ Missing Pinecone config or no vectors to upsert")

    return {"statusCode": 200, "body": "OK"}
