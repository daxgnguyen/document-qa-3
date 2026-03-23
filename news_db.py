import os
import hashlib
import pandas as pd
from openai import OpenAI

__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import chromadb

# Config
CSV_PATH = "./HW-04-Data/news/news.csv"
CHROMA_PATH = "./news_chromadb"
COLLECTION_NAME = "news_collection"
EMBED_MODEL = "text-embedding-3-small"
BATCH_SIZE = 100

client = OpenAI(api_key=os.environ["openai_api_key"])
chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = chroma_client.get_or_create_collection(COLLECTION_NAME)

def make_id(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()

def build_document_text(row) -> str:
    return (
        f"Company: {row['company_name']}\n"
        f"Date: {row['Date']}\n"
        f"Article: {row['Document']}\n"
        f"Source: {row['URL']}"
    )

def embed_batch(texts: list[str]) -> list[list[float]]:
    response = client.embeddings.create(input=texts, model=EMBED_MODEL)
    return [item.embedding for item in response.data]

def main():
    df = pd.read_csv(CSV_PATH)
    print(f"Loaded {len(df)} rows from CSV")

    df = df.drop_duplicates(subset=["URL"])
    print(f"{len(df)} rows after deduplicating by URL")

    existing_ids = set(collection.get()["ids"])
    df["_id"] = df["URL"].apply(make_id)
    df = df[~df["_id"].isin(existing_ids)]
    print(f"{len(df)} new rows to embed")

    if df.empty:
        print("Nothing to add — DB is already up to date.")
        return

    rows = df.to_dict("records")
    total = 0
    for i in range(0, len(rows), BATCH_SIZE):
        batch = rows[i : i + BATCH_SIZE]
        texts = [build_document_text(r) for r in batch]
        ids = [r["_id"] for r in batch]
        metadatas = [
            {
                "company": r["company_name"],
                "date": str(r["Date"]),
                "url": r["URL"],
            }
            for r in batch
        ]

        embeddings = embed_batch(texts)
        collection.add(documents=texts, embeddings=embeddings, ids=ids, metadatas=metadatas)
        total += len(batch)
        print(f"  Added {total}/{len(rows)} articles...")

    print(f"\nDone. Collection now has {collection.count()} articles.")

if __name__ == "__main__":
    main()