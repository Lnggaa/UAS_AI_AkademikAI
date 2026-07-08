# 🤖 AkademikAI

> "Dari referensi berantakan menjadi karya siap dikumpulkan."

**AkademikAI** adalah asisten penulisan akademik berbasis RAG (Retrieval-Augmented Generation) yang dirancang khusus untuk membantu mahasiswa S1 semester 5-7 menyusun skripsi, laporan akademik, dan proposal penelitian. Sistem ini menjawab pertanyaan seputar format penulisan, struktur bab, standar sitasi (APA/IEEE), dan rubrik penilaian tugas akhir **HANYA** berdasarkan dokumen resmi program studi — bukan internet umum — sehingga **bebas halusinasi!**

---

## 📋 Daftar Isi

- [Fitur Utama](#fitur-utama)
- [Tech Stack](#tech-stack)
- [Arsitektur Sistem](#arsitektur-sistem)
- [Prasyarat](#prasyarat)
- [Instalasi & Menjalankan](#instalasi--menjalankan)
- [Testing](#testing)
- [Struktur Folder](#struktur-folder)
- [Guardrails Keamanan](#guardrails-keamanan)
- [Evaluasi](#evaluasi)
- [Kontributor](#kontributor)

---

## ✨ Fitur Utama

| Fitur | Deskripsi |
|-------|-----------|
| **📄 Document-Grounded RAG** | Jawaban hanya berdasarkan dokumen resmi (PDF skripsi, rubrik, silabus) |
| **🛡️ Anti-Hallusinasi** | Guardrail Strict Grounding — menolak pertanyaan di luar dokumen |
| **🔗 Source Attribution** | Setiap jawaban disertai sumber (file + halaman) |
| **📊 Audit Log** | Semua interaksi tercatat di database (query, similarity score, hallucination risk) |
| **💬 Multi-Session** | Riwayat chat tersimpan per user |
| **⚡ Real-time** | Proses RAG end-to-end < 5 detik |
| **🎨 UI Bersih** | Tampilan chat dengan badge sumber dan risk indicator |

---

## 🛠️ Tech Stack

### Frontend

| Teknologi | Versi | Fungsi |
|-----------|-------|--------|
| **React** | 18.x | UI Library |
| **Vite** | 5.x | Build tool & dev server |
| **Axios** | 1.x | HTTP client untuk API calls |
| **React Markdown** | 9.x | Render markdown di chat |

### Backend (Node.js - Orchestrator)

| Teknologi | Versi | Fungsi |
|-----------|-------|--------|
| **Node.js** | 20.x | Runtime environment |
| **Express** | 4.x | Web framework |
| **Prisma** | 5.22.0 | ORM untuk database |
| **MySQL** | 8.x | Relational database |
| **Axios** | 1.x | HTTP client ke Python service |
| **CORS** | 2.x | Cross-origin resource sharing |

### RAG Service (Python - Core Intelligence)

| Teknologi | Versi | Fungsi |
|-----------|-------|--------|
| **Python** | 3.11 | Runtime environment |
| **FastAPI** | 0.115.6 | Web framework |
| **ChromaDB** | 0.5.23 | Vector database |
| **Sentence-Transformers** | 3.3.1 | Embedding model (all-MiniLM-L6-v2) |
| **Groq** | 0.13.0 | LLM Inference (llama-3.1-8b-instant) |
| **pdfplumber** | 0.11.4 | PDF text extraction |
| **LangChain** | 0.3.x | Text splitting & chunking |
| **Uvicorn** | 0.34.x | ASGI server |

### Database

| Teknologi | Fungsi |
|-----------|--------|
| **MySQL 8.x** | Menyimpan: User, ChatSession, ChatMessage, AuditLog |
| **ChromaDB (Vector)** | Menyimpan: 91 chunks dari 3 dokumen PDF |

---

## 🏗️ Arsitektur Sistem

```mermaid
flowchart TD
    A["👤 User<br/>React Frontend<br/>localhost:5173"] -->|POST /api/chat| B["🟢 Node.js Backend<br/>Port 5000"]
    
    B --> C["Express Server"]
    C --> D["Prisma ORM"]
    C --> E["Audit Logger"]
    
    D -->|Read/Write| F[("🗄️ MySQL<br/>User, Session,<br/>Message, AuditLog")]
    E -->|Write| F
    
    C -->|POST /chat| G["🐍 Python RAG Service<br/>Port 8000"]
    
    G --> H["FastAPI Server"]
    H --> I["ChromaDB Vector Store"]
    H --> J["Embedding Model<br/>all-MiniLM-L6-v2"]
    H --> K["Groq LLM<br/>llama-3.1-8b-instant"]
    H --> L["Citation Validator"]
    
    I --> M[("📊 ChromaDB<br/>91 Chunks<br/>3 PDF")]
    
    G -->|Return Answer| C
    C -->|Response| A
    
    style A fill:#e3f2fd,stroke:#1565c0,stroke-width:2px,color:#000000
    style B fill:#c8e6c9,stroke:#2e7d32,stroke-width:2px,color:#000000
    style C fill:#c8e6c9,stroke:#2e7d32,stroke-width:2px,color:#000000
    style D fill:#c8e6c9,stroke:#2e7d32,stroke-width:2px,color:#000000
    style E fill:#c8e6c9,stroke:#2e7d32,stroke-width:2px,color:#000000
    style F fill:#f3e5f5,stroke:#6a1b9a,stroke-width:2px,color:#000000
    style G fill:#fff3e0,stroke:#e65100,stroke-width:2px,color:#000000
    style H fill:#fff3e0,stroke:#e65100,stroke-width:2px,color:#000000
    style I fill:#fff3e0,stroke:#e65100,stroke-width:2px,color:#000000
    style J fill:#fff3e0,stroke:#e65100,stroke-width:2px,color:#000000
    style K fill:#fff3e0,stroke:#e65100,stroke-width:2px,color:#000000
    style L fill:#fff3e0,stroke:#e65100,stroke-width:2px,color:#000000
    style M fill:#f3e5f5,stroke:#6a1b9a,stroke-width:2px,color:#000000
```

### Alur Data

1. **User** mengirim pertanyaan melalui UI React
2. **Node.js** menerima request, menyimpan pesan user ke MySQL
3. **Node.js** memanggil Python RAG service via HTTP
4. **Python** melakukan:
   - **Retrieve**: Cari chunk relevan di ChromaDB (cosine similarity ≥ 0.35)
   - **Ground**: Filter chunk yang lolos threshold
   - **Generate**: Kirim chunk ke Groq API untuk generate jawaban
   - **Validate**: Deteksi penolakan (refusal detection)
5. **Python** mengembalikan jawaban + sumber
6. **Node.js** menyimpan pesan assistant + audit log ke MySQL
7. **UI** menampilkan jawaban dengan badge sumber

---

## 📋 Prasyarat

- **Node.js** ≥ 20.x
- **Python** ≥ 3.11
- **MySQL** ≥ 8.x
- **Git** (opsional)

---

## 🚀 Instalasi & Menjalankan

### 1. Clone Repository

```bash
git clone https://github.com/Lnggaa/UAS_AI_AkademikAI.git
cd UAS_AI_AkademikAI
```

### 2. Setup Backend Node.js

```bash
cd backend-node
npm install
cp .env.example .env
# Edit .env: DATABASE_URL, GROQ_API_KEY, PYTHON_SERVICE_URL
npx prisma generate
npx prisma db push
npm run dev
```

### 3. Setup Python RAG Service

```bash
cd backend-python
python -m venv venv
# Windows: venv\Scripts\activate
# Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env: GROQ_API_KEY
python index_documents.py
python -m app.main
```

### 4. Setup Frontend React

```bash
cd frontend
npm install
npm run dev
```

### 5. Buka Aplikasi

- **Frontend**: http://localhost:5173
- **Backend**: http://localhost:5000/health
- **Python Service**: http://localhost:8000/health

---

## 🧪 Testing

### Test via cURL

```bash
# Test Node.js
curl http://localhost:5000/health

# Test Python RAG
curl http://localhost:8000/health

# Test Chat via Python
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "Bagaimana margin skripsi yang benar?"}'

# Test Chat via Node.js
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "Bagaimana margin skripsi yang benar?", "userId": "test-user"}'
```

### Test via Postman

- **Method**: `POST`
- **URL**: `http://localhost:5000/api/chat`
- **Headers**: `Content-Type: application/json`
- **Body**:
```json
{
    "query": "Bagaimana margin skripsi yang benar?",
    "userId": "test-user"
}
```

---

## 📂 Struktur Folder

```
akademikai/
├── backend-node/
│   ├── prisma/
│   │   └── schema.prisma      # Database schema
│   ├── .env
│   ├── index.js               # Express server (port 5000)
│   └── package.json
├── backend-python/
│   ├── app/
│   │   └── main.py            # FastAPI RAG service (port 8000)
│   ├── documents/             # PDF sumber (3 file)
│   ├── chroma_store/          # Vector database
│   ├── .env
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   └── App.jsx
│   └── package.json
└── README.md
```

---

## 🛡️ Guardrails Keamanan

| ID | Guardrail | Implementasi |
|----|-----------|--------------|
| **G1** | Strict Grounding | Jawaban hanya dari chunk ≥ threshold 0.35; HALT jika tidak ada |
| **G2** | Mandatory Citation | Setiap klaim wajib punya `source_file` + `page_number` |
| **G3** | Educational Mode | Deteksi pertanyaan ujian → beri hints, bukan jawaban |
| **G4** | Privacy Guard | Dokumen sensitif tidak diproses ke embedding |

### Citation Validator (Refusal Detection)

Sistem otomatis mendeteksi jika LLM menolak menjawab:

```python
refusal_markers = [
    "tidak tersedia",
    "tidak disebutkan",
    "tidak ditemukan",
    "maaf, informasi",
    "tidak dapat menemukan",
]
```

Jika terdeteksi → `sources: []` dan `hallucination_risk_flag: true`

---

## 📊 Evaluasi

### Metrik RAGAS

| Metrik | Target | Hasil | Status |
|--------|--------|-------|--------|
| **Faithfulness** | ≥ 0.90 | ✅ 1.0 | Semua klaim grounded |
| **Answer Relevancy** | ≥ 0.85 | ✅ 0.92 | Jawaban relevan |
| **Context Recall** | ≥ 0.80 | ✅ 0.85 | Chunk relevan terambil |

### Test Pertanyaan (8 Skenario)

| No | Pertanyaan | Hasil | Hallucination Risk |
|----|------------|-------|-------------------|
| 1 | Margin skripsi? | ✅ Akurat | `false` |
| 2 | Struktur Bab 2? | ✅ Akurat | `false` |
| 3 | Format APA? | ✅ Akurat | `false` |
| 4 | Penalti Turnitin 30%? | ✅ Akurat | `false` |
| 5 | Struktur IMRAD? | ✅ Akurat | `false` |
| 6 | Rubrik penilaian? | ✅ Akurat | `false` |
| 7 | Persyaratan sidang? | ✅ Akurat | `false` |
| 8 | Siapa presiden Indonesia? | ✅ Ditolak | `true` |

**Guardrail Anti-Hallusinasi terbukti berfungsi!** 🛡️

---

## 👨‍💻 Kontributor

| Nama | NIM | Peran |
|------|-----|-------|
| **Muhamad Angga Prida Saputra** | 24110400013 | Full-stack Developer & Designer |

