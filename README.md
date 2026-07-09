# AkademikAI

> "Dari referensi berantakan menjadi karya siap dikumpulkan."

AkademikAI adalah asisten penulisan akademik berbasis RAG (Retrieval-Augmented Generation) yang dirancang untuk membantu mahasiswa S1 semester 5-7 menyusun skripsi, laporan akademik, dan proposal penelitian. Sistem ini menjawab pertanyaan seputar format penulisan, struktur bab, standar sitasi (APA/IEEE), dan rubrik penilaian tugas akhir hanya berdasarkan dokumen resmi program studi, bukan pengetahuan umum internet, sehingga risiko halusinasi informasi dapat ditekan seminimal mungkin.

---

## Daftar Isi

- [Fitur Utama](#fitur-utama)
- [Tech Stack](#tech-stack)
- [Arsitektur Sistem](#arsitektur-sistem)
- [Prasyarat](#prasyarat)
- [Instalasi dan Menjalankan](#instalasi-dan-menjalankan)
- [Testing](#testing)
- [Struktur Folder](#struktur-folder)
- [Guardrails Keamanan](#guardrails-keamanan)
- [Evaluasi dan Pengujian](#evaluasi-dan-pengujian)
- [Keterbatasan yang Diketahui](#keterbatasan-yang-diketahui)
- [Kontributor](#kontributor)

---

## Fitur Utama

| Fitur | Deskripsi |
|---|---|
| Document-Grounded RAG | Jawaban hanya berdasarkan dokumen resmi (panduan skripsi, rubrik evaluasi, silabus) |
| Strict Grounding | Guardrail yang menolak menjawab pertanyaan di luar cakupan dokumen |
| Citation Validator | Mendeteksi kalau jawaban LLM sendiri menyatakan informasi tidak tersedia, lalu mengosongkan sumber dan menandai risiko halusinasi |
| Source Attribution | Setiap jawaban yang grounded disertai sumber (nama file dan halaman) |
| Audit Log | Setiap interaksi tercatat di database: query, similarity score, status halusinasi |
| Multi-Session | Riwayat percakapan tersimpan dan dapat dibuka ulang per pengguna |
| Antarmuka Chat | Tampilan chat dengan chip sumber yang dapat diperluas untuk melihat skor similarity |

---

## Tech Stack

### Frontend

| Teknologi | Fungsi |
|---|---|
| React (Vite) | UI library dan build tool |
| Fetch API (native) | Komunikasi HTTP ke backend-node |

### Backend Node.js (Orchestrator)

| Teknologi | Fungsi |
|---|---|
| Express | Web framework |
| Prisma ORM | Akses database MySQL |
| MySQL | Menyimpan User, ChatSession, ChatMessage, AuditLog |
| Axios | HTTP client untuk memanggil Python RAG service |
| CORS | Mengizinkan request dari frontend |

### Backend Python (RAG Core)

| Teknologi | Fungsi |
|---|---|
| FastAPI | Web framework untuk RAG service |
| ChromaDB | Vector database (metric: cosine similarity) |
| Sentence-Transformers | Model embedding: `paraphrase-multilingual-MiniLM-L12-v2` |
| Groq API | LLM inference (`llama-3.1-8b-instant`) |
| pdfplumber | Ekstraksi teks PDF per halaman |
| langchain-text-splitters | Chunking teks (`RecursiveCharacterTextSplitter`) |
| Uvicorn | ASGI server |

Versi persis setiap dependency dapat dicek langsung di `frontend/package.json`, `backend-node/package.json`, dan `backend-python/requirements.txt`.

### Database

| Komponen | Isi |
|---|---|
| MySQL | User, ChatSession, ChatMessage, AuditLog |
| ChromaDB | 91 chunk dari 3 dokumen PDF (panduan skripsi, rubrik evaluasi, silabus) |

---

## Arsitektur Sistem

```mermaid
flowchart TD
    A["User<br/>React Frontend<br/>localhost:5173"] -->|POST /api/chat| B["Node.js Backend<br/>Port 5000"]

    B --> C["Express Server"]
    C --> D["Prisma ORM"]
    C --> E["Audit Logger"]

    D -->|Read/Write| F[("MySQL<br/>User, Session,<br/>Message, AuditLog")]
    E -->|Write| F

    C -->|POST /chat| G["Python RAG Service<br/>Port 8000"]

    G --> H["FastAPI Server"]
    H --> I["ChromaDB Vector Store"]
    H --> J["Embedding Model<br/>paraphrase-multilingual-MiniLM-L12-v2"]
    H --> K["Groq LLM<br/>llama-3.1-8b-instant"]
    H --> L["Citation Validator"]

    I --> M[("ChromaDB<br/>91 Chunks<br/>3 PDF")]

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

1. User mengirim pertanyaan melalui UI React.
2. Node.js menerima request, mencari atau membuat ChatSession, menyimpan pesan user ke MySQL.
3. Node.js memanggil Python RAG service melalui HTTP (`POST /chat`).
4. Python melakukan:
   - Retrieve: mencari chunk relevan di ChromaDB berdasarkan cosine similarity.
   - Filter: hanya chunk dengan similarity di atas threshold (0.35) yang dipakai.
   - Generate: chunk yang lolos dikirim ke Groq API untuk menyusun jawaban.
   - Validate: Citation Validator memeriksa apakah jawaban LLM sendiri menyatakan informasi tidak ditemukan; jika iya, sumber dikosongkan dan `hallucination_risk_flag` diset `true`.
5. Python mengembalikan jawaban, daftar sumber, dan status risiko halusinasi.
6. Node.js menyimpan pesan assistant beserta metadata sumber, dan mencatat audit log (similarity score, tool yang dipanggil, status risiko) ke MySQL.
7. UI menampilkan jawaban, disertai chip sumber (jika grounded) atau banner peringatan (jika ditolak).

---

## Prasyarat

- Node.js versi 20 atau lebih baru
- Python versi 3.11 atau lebih baru
- MySQL versi 8 atau lebih baru

---

## Instalasi dan Menjalankan

Jalankan ketiga komponen ini secara bersamaan, masing-masing di terminal terpisah.

### 1. Backend Node.js

```bash
cd backend-node
npm install
npx prisma generate
npx prisma db push
node seed.js
npm run dev
```

Isi `backend-node/.env`:
```env
DATABASE_URL="mysql://root:password_kamu@localhost:3306/akademikai_db"
GROQ_API_KEY="tidak dipakai langsung di sini, hanya cadangan"
PYTHON_SERVICE_URL="http://localhost:8000"
PORT=5000
```

### 2. Backend Python (RAG Service)

```bash
cd backend-python
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate # Mac/Linux
pip install -r requirements.txt
python reset_collection.py
python reindex_all.py
uvicorn app.main:app --reload --port 8000
```

Isi `backend-python/.env`:
```env
GROQ_API_KEY="isi_dengan_api_key_groq"
CHROMA_PERSIST_DIR="./chroma_store"
CHUNK_SIZE=600
CHUNK_OVERLAP=80
EMBEDDING_MODEL="paraphrase-multilingual-MiniLM-L12-v2"
SIMILARITY_THRESHOLD=0.35
```

### 3. Frontend React

```bash
cd frontend
npm install
npm run dev
```

### Akses Aplikasi

- Frontend: `http://localhost:5173`
- Backend Node: `http://localhost:5000/health`
- Python RAG Service: `http://localhost:8000/health`

---

## Testing

```bash
curl http://localhost:5000/health
curl http://localhost:8000/health

curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"Bagaimana margin skripsi yang benar?\"}"

curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"Bagaimana margin skripsi yang benar?\"}"
```
---

## Guardrails Keamanan

| ID | Guardrail | Mekanisme |
|---|---|---|
| G1 | Strict Grounding | Jawaban hanya disusun dari chunk dengan cosine similarity di atas 0.35. Jika tidak ada chunk yang lolos, sistem menolak menjawab. |
| G2 | Mandatory Citation | Setiap jawaban yang grounded menyertakan `source_file` dan `page_number` untuk setiap sumber yang dipakai. |
| G3 | Citation Validator | Jika teks jawaban LLM sendiri mengandung frasa penolakan ("tidak tersedia", "tidak ditemukan", dan sejenisnya), sistem mengosongkan sumber dan menandai `hallucination_risk_flag = true`, meski secara similarity chunk sempat lolos threshold. |
| G4 | Privacy Guard (rencana) | Dokumen yang mengandung data sensitif tidak diproses ke embedding. Belum diimplementasikan penuh di iterasi saat ini. |

---

## Evaluasi dan Pengujian

Evaluasi dilakukan secara manual melalui pengujian skenario nyata end-to-end (UI React → Node.js → Python → ChromaDB/Groq → MySQL), bukan menggunakan framework RAGAS otomatis. Berikut temuan aktual dari proses pengujian.

### 1. Kalibrasi model embedding dan threshold

Model embedding awal (`all-MiniLM-L6-v2`) tidak cukup baik membedakan pertanyaan relevan dan tidak relevan dalam Bahasa Indonesia:

| Query | Similarity Tertinggi |
|---|---|
| "Kalau Turnitin saya kena 30%..." (relevan) | 0.623 |
| "Resep rendang daging sapi..." (tidak relevan) | 0.526 |

Selisih hanya 0.097, terlalu sempit untuk threshold yang aman. Setelah beralih ke model multibahasa (`paraphrase-multilingual-MiniLM-L12-v2`):

| Query | Similarity Tertinggi |
|---|---|
| "Kalau Turnitin saya kena 30%..." (relevan) | 0.493 |
| "Resep rendang daging sapi..." (tidak relevan) | 0.138 |

Selisih menjadi 0.355, memberi ruang aman untuk menetapkan threshold di 0.35.

### 2. Pengujian Guardrail G1 (Strict Grounding)

| Pertanyaan | Hasil |
|---|---|
| "Berapa margin yang benar untuk laporan skripsi?" | Dijawab lengkap, sumber `panduan_skripsi_si.pdf` Hal. 1, dengan chip sumber tambahan dari 3 dokumen |
| "Dosen bilang pakai struktur IMRAD, urutannya apa aja?" | Dijawab lengkap, sumber `silabus_technical_writing.pdf` Hal. 6, urutan IMRAD sesuai dokumen |
| "Bab 2 saya harus isi apa aja?" | Dijawab lengkap dengan sumber `rubrik_evaluasi_si.pdf` |
| "Siapa presiden Indonesia saat ini?" | Ditolak, tidak ada sumber ditampilkan, `hallucination_risk_flag: true` |
| "Siapa wakil presiden Indonesia saat ini?" | Ditolak, tidak ada sumber ditampilkan, `hallucination_risk_flag: true` |

### 3. Temuan dan perbaikan Citation Validator

Pada iterasi awal, ditemukan celah: untuk pertanyaan "Siapa presiden Indonesia saat ini?", jawaban LLM sudah benar menyatakan informasi tidak tersedia, tetapi sistem tetap menampilkan chip sumber seolah jawaban itu grounded. Penyebabnya, satu chunk kebetulan lolos threshold similarity meski isinya tidak relevan dengan pertanyaan.

Perbaikan dilakukan dengan menambahkan pemeriksaan pada teks jawaban itu sendiri: jika jawaban mengandung frasa penolakan, sistem mengosongkan sumber dan menandai `hallucination_risk_flag = true`, terlepas dari hasil similarity chunk. Setelah perbaikan ini diterapkan, pengujian ulang pada pertanyaan yang sama dan pertanyaan sejenis ("siapa wakil presiden...") menunjukkan perilaku yang konsisten dan benar.

### 4. Pengujian sesi multi-turn

Pertanyaan lanjutan dalam satu sesi ("Berapa margin..." lalu dilanjutkan "ohh oke lalu Dosen bilang pakai struktur IMRAD...") berhasil tetap tersimpan dalam `ChatSession` yang sama, dan riwayat percakapan tetap dapat dibuka kembali melalui sidebar.

---

## Keterbatasan yang Diketahui

- Non-determinisme LLM: pada pengujian dengan chunk sumber yang identik, jawaban Groq API untuk pertanyaan yang sama dapat berbeda antar percobaan, kadang menghasilkan detail yang kurang konsisten (misalnya salah menyebut satuan poin sebagai persen). Ini adalah karakteristik dasar LLM generatif, bukan kesalahan pada logika retrieval. Mitigasi yang diterapkan adalah menyediakan chip sumber yang dapat diperluas untuk melihat similarity score, agar pengguna tetap dapat memverifikasi klaim secara manual sebelum mengutipnya ke tugas akhir.
- Evaluasi belum menggunakan metrik otomatis seperti RAGAS (Faithfulness, Answer Relevancy, Context Recall). Evaluasi saat ini bersifat pengujian skenario manual.
- Guardrail G4 (Privacy Guard) belum diimplementasikan secara teknis, masih sebatas rancangan.

---

## Kontributor

| Nama | NIM | Peran |
|---|---|---|
| Muhamad Angga Prida Saputra | 24110400013 | Full-stack Developer |
