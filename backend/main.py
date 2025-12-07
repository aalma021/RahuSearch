from opensearchpy import OpenSearch
import os
from dotenv import load_dotenv

# ENV load
load_dotenv()

OPENSEARCH_URL = os.getenv("OPENSEARCH_URL", "http://localhost:9200")
OPENSEARCH_INDEX = os.getenv("OPENSEARCH_INDEX", "products")
OPENSEARCH_PASSWORD = os.getenv("OPENSEARCH_PASSWORD")

def main():
    client = OpenSearch(
        hosts=[OPENSEARCH_URL],
        http_auth=("admin", OPENSEARCH_PASSWORD),
        verify_certs=False,
        ssl_show_warn=False,
        timeout=30
    )

    print("\nConnected to OpenSearch")
    print(f"Index: {OPENSEARCH_INDEX}\n")

    # Sample query: match all, first 10 records
    query = {
        "size": 10,
        "query": {"match_all": {}}
    }

    res = client.search(index=OPENSEARCH_INDEX, body=query)

    hits = res.get("hits", {}).get("hits", [])
    print(f"Found {len(hits)} hits\n")

    for h in hits:
        src = h["_source"]
        print("------------------------------")
        print("ID:", src.get("id"))
        print("Brand:", src.get("brand"))
        print("Title EN:", src.get("title_en"))
        print("Store:", src.get("store"))

        price = src.get("price_final")
        currency = src.get("currency")

        print("Price:", f"{price} {currency}" if price else "-")

        combined = src.get("combined_text") or ""
        print("Combined:", combined[:80], "...")

if __name__ == "__main__":
    main()
