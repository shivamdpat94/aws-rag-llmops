# src/lambdas/app.py
import json, os, urllib.parse, boto3
from pypdf import PdfReader
from openai import OpenAI
from pinecone import Pinecone

DOCS_BUCKET      = os.environ["DOCS_BUCKET"]
OPENAI_API_KEY   = os.environ["OPENAI_API_KEY"]
PINECONE_API_KEY = os.environ["PINECONE_API_KEY"]
PINECONE_INDEX   = os.environ["PINECONE_INDEX"]

s3 = boto3.client("s3")

def _read_pdf(bucket, key):
    obj = s3.get_object(Bucket=bucket, Key=key)
    reader = PdfReader(obj["Body"])
    return "\n".join((p.extract_text() or "") for p in reader.pages).strip()

def _read_text(bucket, key):
    obj = s3.get_object(Bucket=bucket, Key=key)
    return obj["Body"].read().decode("utf-8", errors="ignore")

def _chunk(text: str, chunk_size=900, overlap=150):
    if not text:
        return []
    chunks = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + chunk_size, n)
        chunks.append(text[start:end])
        if end == n:
            break
        start = max(end - overlap, 0)
    return [c.strip() for c in chunks if c.strip()]

def _embed(texts):
    client = OpenAI(api_key=OPENAI_API_KEY)
    resp = client.embeddings.create(model="text-embedding-3-small", input=texts)
    return [d.embedding for d in resp.data]  # 1536-dim

def _upsert_pinecone(vectors):
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index(PINECONE_INDEX)
    index.upsert(vectors=vectors)

def lambda_handler(event, context):
    # Optional: quick diagnostics if needed
    # import sys, os
    # print("SYS.PATH:", sys.path)
    # print("LAYER EXISTS:", os.path.isdir("/opt/python"))

    records = event.get("Records", [])
    total = 0
    for r in records:
        bucket = r["s3"]["bucket"]["name"]
        key = urllib.parse.unquote_plus(r["s3"]["object"]["key"])
        text = _read_pdf(bucket, key) if key.lower().endswith(".pdf") else _read_text(bucket, key)
        chunks = _chunk(text)
        if not chunks:
            continue
        embs = _embed(chunks)
        vectors = [(f"{key}::{i}", e, {"text": c, "s3_key": key}) for i, (c, e) in enumerate(zip(chunks, embs))]
        _upsert_pinecone(vectors)
        total += len(chunks)

    return {"statusCode": 200, "body": json.dumps({"message": "embedded", "chunks": total})}
