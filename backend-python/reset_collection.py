import chromadb
from chromadb.config import Settings

client = chromadb.PersistentClient(
    path="./chroma_store",
    settings=Settings(anonymized_telemetry=False)
)

try:
    client.delete_collection("akademikai_docs")
    print("Collection lama (metric salah) berhasil dihapus.")
except Exception as e:
    print(f"Tidak ada collection lama, lanjut: {e}")

client.get_or_create_collection(
    name="akademikai_docs",
    metadata={"hnsw:space": "cosine"}
)
print("Collection baru dibuat dengan metric cosine.")