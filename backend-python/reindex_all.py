import os
from app.main import process_document, collection

DOCUMENTS_DIR = "./documents"

for filename in os.listdir(DOCUMENTS_DIR):
    if filename.lower().endswith(".pdf"):
        file_path = os.path.join(DOCUMENTS_DIR, filename)
        print(f"Indexing: {filename}")
        process_document(file_path, filename)

print(f"\nTotal chunks sekarang: {collection.count()}")