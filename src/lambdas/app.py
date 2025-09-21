import json, os, boto3, urllib.parse
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from openai import OpenAI
from pinecone import Pinecone

DOCS_BUCKET      = os.environ["DOCS_BUCKET"]
OPENAI_API_KEY   = os.environ["OPENAI_API_KEY"]
PINECONE_API_KEY = os.environ["PINECONE_API_KEY"]
PINECONE_ENV     = os.environ["PINECONE_ENV"]
PINECONE_INDEX   = os.environ["PINECONE_INDEX"]

s3 = boto3.client("s3")

def _read_pdf(bucket, key):
    obj = s3.get_object(Bucket=bucket, Key=key)
    reader = PdfReader(obj["Body"])
    return "\n".join((p.extract_text() or "") for p in reader.pages)

def _read_text(bucket, key):
    obj = s3.get_object(Bucket=bucket, Key=key)
    return obj["Body"].read().decode("utf-8", errors="ignore")

def _chunk(text):
    splitter = RecursiveCharacterTextSplitter(chunk_size=900, chunk_overlap=150)
    return [c for c in splitter.split_text(text) if c.strip()]

def _embed(texts):
    client = OpenAI(api_key=OPENAI_API_KEY)
    resp = client.embeddings.create(model="text-embedding-3-small", input=texts)
    return [d.embedding for d in resp.data]

def _upsert_pinecone(vectors):
    pc = Pinecone(api_key=PINECONE_API_KEY, environment=PINECONE_ENV)
    index = pc.Index(PINECONE_INDEX)
    index.upsert(vectors=vectors)

def lambda_handler(event, context):
    records = event.get("Records", [])
    total_chunks = 0

    for r in records:
        bucket = r["s3"]["bucket"]["name"]
        key = urllib.parse.unquote_plus(r["s3"]["object"]["key"])

        text = _read_pdf(bucket, key) if key.lower().endswith(".pdf") else _read_text(bucket, key)
        if not text:
            continue

        chunks = _chunk(text)
        embs = _embed(chunks)
        vectors = [(f"{key}::{i}", e, {"text": c, "s3_key": key}) for i, (c, e) in enumerate(zip(chunks, embs))]

        _upsert_pinecone(vectors)
        total_chunks += len(chunks)

    return {"statusCode": 200, "body": json.dumps({"msg": "embedded", "chunks": total_chunks})}
