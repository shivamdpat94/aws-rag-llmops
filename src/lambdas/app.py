# at top of app.py
import json, os, urllib.parse, boto3, requests

print("BOOT OK: app.py loaded")
DOCS_BUCKET      = os.environ["DOCS_BUCKET"]
OPENAI_API_KEY   = os.environ["OPENAI_API_KEY"]
PINECONE_API_KEY = os.environ["PINECONE_API_KEY"]
PINECONE_INDEX   = os.environ["PINECONE_INDEX"]  # e.g., aws-rag-dev-docs

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
    chunks, start, n = [], 0, len(text)
    while start < n:
        end = min(start + chunk_size, n)
        piece = text[start:end].strip()
        if piece:
            chunks.append(piece)
        if end == n:
            break
        start = max(end - overlap, 0)
    return chunks

def _embed_texts(texts):
    url = "https://api.openai.com/v1/embeddings"
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
    # Batch in groups to keep payloads sane if needed; start simple
    body = {"model": "text-embedding-3-small", "input": texts}
    r = requests.post(url, headers=headers, json=body, timeout=30)
    r.raise_for_status()
    data = r.json()
    # returns list of {embedding: [...], index: i}
    return [d["embedding"] for d in data["data"]]

def _pinecone_upsert(vectors):
    # serverless write endpoint format:
    # https://api.pinecone.io/indexes/{index_name}/vectors/upsert
    url = f"https://api.pinecone.io/indexes/{PINECONE_INDEX}/vectors/upsert"
    headers = {"Api-Key": PINECONE_API_KEY, "Content-Type": "application/json"}
    payload = {"vectors": [{"id": vid, "values": values, "metadata": meta} for vid, values, meta in vectors]}
    r = requests.post(url, headers=headers, json=payload, timeout=30)
    r.raise_for_status()
    return r.json()

def lambda_handler(event, context):
    records = event.get("Records", [])
    total_chunks = 0
    for r in records:
        bucket = r["s3"]["bucket"]["name"]
        key = urllib.parse.unquote_plus(r["s3"]["object"]["key"])
        text = _read_pdf(bucket, key) if key.lower().endswith(".pdf") else _read_text(bucket, key)
        chunks = _chunk(text)
        if not chunks:
            continue
        embs = _embed_texts(chunks)
        vectors = [(f"{key}::{i}", emb, {"text": chunk, "s3_key": key}) for i, (chunk, emb) in enumerate(zip(chunks, embs))]
        _pinecone_upsert(vectors)
        total_chunks += len(chunks)
    return {"statusCode": 200, "body": json.dumps({"message":"embedded", "chunks": total_chunks})}
