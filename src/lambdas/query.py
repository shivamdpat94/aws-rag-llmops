import os
import json
import requests

PINECONE_KEY = os.environ.get("PINECONE_API_KEY")
PINECONE_HOST = os.environ.get("PINECONE_HOST")
OPENAI_KEY = os.environ.get("OPENAI_API_KEY")

def lambda_handler(event, context):
    try:
        body = json.loads(event.get("body", "{}"))
        query_text = body.get("query", "")

        if not query_text:
            return {"statusCode": 400, "body": json.dumps({"error": "Missing 'query'"})}

        # 1. Embed query
        emb = requests.post(
            "https://api.openai.com/v1/embeddings",
            headers={"Authorization": f"Bearer {OPENAI_KEY}", "Content-Type": "application/json"},
            json={"model": "text-embedding-3-small", "input": query_text},
        )
        vec = emb.json()["data"][0]["embedding"]

        # 2. Query Pinecone
        search = requests.post(
            f"{PINECONE_HOST}/query",
            headers={"Api-Key": PINECONE_KEY, "Content-Type": "application/json"},
            json={"vector": vec, "topK": 3, "includeMetadata": True},
        )

        return {
            "statusCode": 200,
            "body": json.dumps(search.json())
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
