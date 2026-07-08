import os
import uuid
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter
import pdfplumber
from groq import Groq
from dotenv import load_dotenv
import logging
import re

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(title="AkademikAI RAG Service", version="1.2.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Configuration ===
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_store")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 600))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 80))
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "paraphrase-multilingual-MiniLM-L12-v2")

# Threshold tunggal untuk seluruh sistem
SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", 0.35))

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY tidak ditemukan. Set di file .env terlebih dahulu.")

# === Initialize ChromaDB ===
chroma_client = chromadb.PersistentClient(
    path=CHROMA_PERSIST_DIR,
    settings=Settings(anonymized_telemetry=False)
)

collection_name = "akademikai_docs"

collection = chroma_client.get_or_create_collection(
    name=collection_name,
    metadata={"hnsw:space": "cosine"}
)
logger.info(f"Collection '{collection_name}' ready (metric: cosine, total: {collection.count()} chunks)")

# === Initialize Embedding Model ===
embedder = SentenceTransformer(EMBEDDING_MODEL)
logger.info(f"Embedding model '{EMBEDDING_MODEL}' loaded")

# === Initialize Groq Client ===
groq_client = Groq(api_key=GROQ_API_KEY)

# === Text Splitter ===
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    separators=["\n\n", "\n", ". ", " ", ""],
)

# === Pydantic Models ===
class QueryRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5
    similarity_threshold: Optional[float] = SIMILARITY_THRESHOLD

class ChunkResponse(BaseModel):
    text: str
    source_file: str
    page_number: int
    chunk_index: str
    similarity_score: float

class QueryResponse(BaseModel):
    status: str
    query: str
    chunks: List[ChunkResponse]
    found: bool
    threshold_used: float

class ChatRequest(BaseModel):
    query: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    session_id: str
    answer: str
    sources: List[Dict[str, Any]]
    hallucination_risk_flag: bool

# === Helper Functions ===

def extract_pdf_text(file_path: str) -> Dict[int, str]:
    """Ekstrak teks dari PDF, dikelompokkan per nomor halaman."""
    page_texts = {}
    try:
        with pdfplumber.open(file_path) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text and text.strip():
                    page_texts[i + 1] = text.strip()
        return page_texts
    except Exception as e:
        logger.error(f"Error extracting PDF {file_path}: {e}")
        return {}

def process_document(file_path: str, source_file: str):
    """Proses satu dokumen PDF: ekstrak, chunking, embed, simpan ke ChromaDB."""
    logger.info(f"Processing document: {source_file}")

    page_texts = extract_pdf_text(file_path)
    if not page_texts:
        logger.warning(f"No text extracted from {source_file}")
        return

    all_chunks = []
    for page_num, text in page_texts.items():
        chunks = text_splitter.split_text(text)
        for chunk_idx, chunk in enumerate(chunks):
            chunk_id = f"{source_file}_page{page_num}_chunk{chunk_idx}"
            all_chunks.append({
                "id": chunk_id,
                "text": chunk,
                "metadata": {
                    "source_file": source_file,
                    "page_number": page_num,
                    "chunk_index": f"chunk_{chunk_idx}",
                    "content_type": "document_text"
                }
            })

    if not all_chunks:
        logger.warning(f"Tidak ada chunk dihasilkan dari {source_file}")
        return

    texts = [chunk["text"] for chunk in all_chunks]
    embeddings = embedder.encode(texts, convert_to_numpy=True).tolist()

    ids = [chunk["id"] for chunk in all_chunks]
    metadatas = [chunk["metadata"] for chunk in all_chunks]
    documents = [chunk["text"] for chunk in all_chunks]

    try:
        collection.add(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=documents
        )
        logger.info(f"Added {len(all_chunks)} chunks from {source_file}")
    except Exception as e:
        logger.error(f"Error adding to ChromaDB: {e}")

def search_documents(query: str, top_k: int = 5, threshold: float = SIMILARITY_THRESHOLD) -> List[Dict]:
    """
    Cari chunk yang relevan secara semantik dan LANGSUNG memfilter
    berdasarkan threshold di sini.
    """
    query_embedding = embedder.encode([query], convert_to_numpy=True).tolist()

    candidate_count = max(top_k * 3, 15)

    raw_results = collection.query(
        query_embeddings=query_embedding,
        n_results=min(candidate_count, collection.count()) or 1,
        include=["documents", "metadatas", "distances"]
    )

    chunks = []
    if raw_results["documents"] and raw_results["documents"][0]:
        for i, doc in enumerate(raw_results["documents"][0]):
            metadata = raw_results["metadatas"][0][i]
            distance = raw_results["distances"][0][i]
            similarity_score = 1 - distance

            if similarity_score >= threshold:
                chunks.append({
                    "text": doc,
                    "source_file": metadata.get("source_file", "Unknown"),
                    "page_number": int(metadata.get("page_number", 0)),
                    "chunk_index": metadata.get("chunk_index", ""),
                    "similarity_score": similarity_score
                })

    chunks.sort(key=lambda c: c["similarity_score"], reverse=True)
    return chunks[:top_k]

def generate_answer(query: str, chunks: List[Dict]) -> Dict:
    """
    Susun jawaban lewat Groq, HANYA berdasarkan chunk yang sudah lolos
    filter similarity di search_documents().
    """
    if not chunks:
        return {
            "answer": (
                "Maaf, saya tidak menemukan informasi yang cukup relevan dalam "
                "dokumen resmi prodi untuk menjawab pertanyaan ini. Silakan "
                "perjelas pertanyaan Anda atau tanyakan langsung ke dosen "
                "pembimbing/admin prodi."
            ),
            "sources": [],
            "hallucination_risk_flag": True
        }

    context = ""
    sources = []
    for chunk in chunks:
        context += f"[Sumber: {chunk['source_file']}, Hal. {chunk['page_number']}]\n{chunk['text']}\n\n"
        sources.append({
            "source_file": chunk["source_file"],
            "page_number": chunk["page_number"],
            "chunk_index": chunk["chunk_index"],
            "similarity_score": round(chunk["similarity_score"], 4)
        })

    system_prompt = """Anda adalah AkademikAI, asisten akademik yang berbasis dokumen resmi.
Anda HANYA boleh menjawab berdasarkan konteks dokumen yang diberikan.
JANGAN menggunakan pengetahuan umum di luar dokumen.
Jika informasi tidak ada dalam konteks, katakan bahwa informasi tidak tersedia.
Jawab dengan bahasa Indonesia yang jelas dan sopan.
Sertakan sumber referensi (nama file dan halaman) untuk setiap klaim."""

    user_prompt = f"""Pertanyaan: {query}

Dokumen Referensi:
{context}

Jawab pertanyaan berdasarkan dokumen di atas. Berikan jawaban yang akurat dan lengkap dengan sumber yang jelas."""

    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=1024
        )

        answer = completion.choices[0].message.content

        # ============================================================
        # 🔥 CITATION_VALIDATOR() - SESUAI DESAIN SESI 14 🔥
        # ============================================================
        # Deteksi apakah LLM sendiri mengakui bahwa informasi tidak tersedia.
        # Kalau iya, tandai sebagai hallucination_risk_flag = True
        # dan kosongkan sources.
        refusal_markers = [
            "tidak tersedia",
            "tidak disebutkan",
            "tidak ditemukan",
            "tidak ada informasi",
            "maaf, informasi",
            "tidak dapat menemukan",
            "tidak menyebutkan",
            "informasi tentang.*tidak tersedia",
            "tidak terdapat dalam dokumen",
            "di luar cakupan dokumen",
        ]

        answer_lower = answer.lower()
        is_actually_refusal = False
        for marker in refusal_markers:
            if re.search(marker, answer_lower):
                is_actually_refusal = True
                logger.info(f"⚠️  Refusal detected: '{marker}' found in answer")
                break

        # Validasi tambahan: cek apakah answer menyebutkan "tidak ada" atau "maaf"
        # dengan konteks penolakan.
        if is_actually_refusal:
            return {
                "answer": answer,
                "sources": [],  # Kosongkan sources - tidak ada grounding!
                "hallucination_risk_flag": True  # Tandai sebagai risiko!
            }

        # ============================================================
        # VALIDASI LANJUTAN: cek setiap klaim di jawaban punya sumber
        # ============================================================
        # Simple citation validator: cek apakah ada klaim tanpa sumber
        # (deteksi kalimat yang menyatakan fakta tanpa menyebut file/halaman)
        sentences = re.split(r'[.!?]+', answer)
        suspicious_claims = []
        for sent in sentences:
            sent = sent.strip()
            if len(sent) < 20:  # Skip kalimat pendek
                continue
            # Jika kalimat mengandung kata kunci fakta tapi tidak ada sumber
            fact_keywords = ['adalah', 'merupakan', 'berdasarkan', 'menurut', 'terdiri dari', 'yaitu']
            has_fact = any(kw in sent.lower() for kw in fact_keywords)
            has_source = any(ref in sent for ref in ['Sumber:', 'panduan_', 'rubrik_', 'silabus_', '.pdf', 'Hal.'])
            
            if has_fact and not has_source and len(sent) > 30:
                suspicious_claims.append(sent[:50] + "...")

        if suspicious_claims and len(suspicious_claims) > 2:
            logger.warning(f"⚠️  Potensi klaim tanpa sumber: {len(suspicious_claims)} ditemukan")
            # Tidak langsung flag, tapi log untuk monitoring

        return {
            "answer": answer,
            "sources": sources,
            "hallucination_risk_flag": False
        }

    except Exception as e:
        logger.error(f"Groq API error: {e}")
        return {
            "answer": f"Terjadi kesalahan saat memproses permintaan: {str(e)}",
            "sources": [],
            "hallucination_risk_flag": True
        }

# === API Endpoints ===

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "akademikai-rag-python",
        "collection": collection_name,
        "total_chunks": collection.count(),
        "embedding_model": EMBEDDING_MODEL,
        "similarity_threshold": SIMILARITY_THRESHOLD
    }

@app.post("/index")
async def index_document(file: UploadFile = File(...)):
    """Upload dan index satu dokumen PDF baru ke ChromaDB."""
    file_path = f"./temp_{file.filename}"
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    try:
        process_document(file_path, file.filename)
        return {
            "status": "success",
            "message": f"Document '{file.filename}' indexed successfully",
            "total_chunks": collection.count()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

@app.post("/search", response_model=QueryResponse)
async def search(request: QueryRequest):
    """Cari chunk relevan saja (tanpa generate jawaban LLM)."""
    threshold = request.similarity_threshold
    chunks = search_documents(
        query=request.query,
        top_k=request.top_k,
        threshold=threshold
    )

    return QueryResponse(
        status="success",
        query=request.query,
        chunks=[
            ChunkResponse(
                text=c["text"],
                source_file=c["source_file"],
                page_number=c["page_number"],
                chunk_index=c["chunk_index"],
                similarity_score=c["similarity_score"]
            )
            for c in chunks
        ],
        found=len(chunks) > 0,
        threshold_used=threshold
    )

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat dengan AkademikAI — full RAG pipeline (retrieve -> validate -> generate)."""
    session_id = request.session_id or str(uuid.uuid4())

    chunks = search_documents(request.query, top_k=5, threshold=SIMILARITY_THRESHOLD)
    result = generate_answer(request.query, chunks)

    return ChatResponse(
        session_id=session_id,
        answer=result["answer"],
        sources=result["sources"],
        hallucination_risk_flag=result["hallucination_risk_flag"]
    )

@app.get("/collection/stats")
async def collection_stats():
    return {
        "collection_name": collection_name,
        "total_chunks": collection.count(),
        "persist_directory": CHROMA_PERSIST_DIR,
        "embedding_model": EMBEDDING_MODEL,
        "similarity_threshold": SIMILARITY_THRESHOLD
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)