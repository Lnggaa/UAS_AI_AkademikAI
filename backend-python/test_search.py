from app.main import search_documents

query = "Kalau Turnitin saya kena 30%, nilai saya dipotong berapa persen?"
results = search_documents(query, top_k=5, threshold=0.0)

for r in results:
    print(f"{r['similarity_score']:.3f} | {r['source_file']} hal.{r['page_number']} | {r['text'][:70]}...")
    
    from app.main import search_documents

queries = [
    "Kalau Turnitin saya kena 30%, nilai saya dipotong berapa persen?",
    "Resep rendang daging sapi yang enak gimana ya?",  # query tidak relevan, sengaja
]

for query in queries:
    print(f"\n=== Query: {query} ===")
    results = search_documents(query, top_k=3, threshold=0.0)
    for r in results:
        print(f"{r['similarity_score']:.3f} | {r['source_file']} hal.{r['page_number']} | {r['text'][:70]}...")