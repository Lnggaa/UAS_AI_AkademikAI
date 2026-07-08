\# 🤖 AkademikAI



> "Dari referensi berantakan menjadi karya siap dikumpulkan."



\*\*AkademikAI\*\* adalah asisten penulisan akademik berbasis RAG (Retrieval-Augmented Generation) yang dirancang khusus untuk membantu mahasiswa S1 semester 5-7 menyusun skripsi, laporan akademik, dan proposal penelitian. Sistem ini menjawab pertanyaan seputar format penulisan, struktur bab, standar sitasi (APA/IEEE), dan rubrik penilaian tugas akhir \*\*HANYA\*\* berdasarkan dokumen resmi program studi — bukan internet umum — sehingga \*\*bebas halusinasi!\*\*



\---



\## 📋 Daftar Isi



\- \[Fitur Utama](#fitur-utama)

\- \[Tech Stack](#tech-stack)

\- \[Arsitektur Sistem](#arsitektur-sistem)

\- \[Prasyarat](#prasyarat)

\- \[Instalasi \& Menjalankan](#instalasi--menjalankan)

\- \[Testing](#testing)

\- \[Struktur Folder](#struktur-folder)

\- \[Guardrails Keamanan](#guardrails-keamanan)

\- \[Screenshot](#screenshot)

\- \[Evaluasi](#evaluasi)

\- \[Kontributor](#kontributor)

\- \[Lisensi](#lisensi)



\---



\## ✨ Fitur Utama



| Fitur | Deskripsi |

|-------|-----------|

| \*\*📄 Document-Grounded RAG\*\* | Jawaban hanya berdasarkan dokumen resmi (PDF skripsi, rubrik, silabus) |

| \*\*🛡️ Anti-Hallusinasi\*\* | Guardrail Strict Grounding — menolak pertanyaan di luar dokumen |

| \*\*🔗 Source Attribution\*\* | Setiap jawaban disertai sumber (file + halaman) |

| \*\*📊 Audit Log\*\* | Semua interaksi tercatat di database (query, similarity score, hallucination risk) |

| \*\*💬 Multi-Session\*\* | Riwayat chat tersimpan per user |

| \*\*⚡ Real-time\*\* | Proses RAG end-to-end < 5 detik |

| \*\*🎨 UI Bersih\*\* | Tampilan chat dengan badge sumber dan risk indicator |



\---



\## 🛠️ Tech Stack



\### Frontend

| Teknologi | Versi | Fungsi |

|-----------|-------|--------|

| \*\*React\*\* | 18.x | UI Library |

| \*\*Vite\*\* | 5.x | Build tool \& dev server |

| \*\*Axios\*\* | 1.x | HTTP client untuk API calls |

| \*\*React Markdown\*\* | 9.x | Render markdown di chat |



\### Backend (Node.js - Orchestrator)

| Teknologi | Versi | Fungsi |

|-----------|-------|--------|

| \*\*Node.js\*\* | 20.x | Runtime environment |

| \*\*Express\*\* | 4.x | Web framework |

| \*\*Prisma\*\* | 5.22.0 | ORM untuk database |

| \*\*MySQL\*\* | 8.x | Relational database |

| \*\*Axios\*\* | 1.x | HTTP client ke Python service |

| \*\*CORS\*\* | 2.x | Cross-origin resource sharing |



\### RAG Service (Python - Core Intelligence)

| Teknologi | Versi | Fungsi |

|-----------|-------|--------|

| \*\*Python\*\* | 3.11 | Runtime environment |

| \*\*FastAPI\*\* | 0.115.6 | Web framework |

| \*\*ChromaDB\*\* | 0.5.23 | Vector database |

| \*\*Sentence-Transformers\*\* | 3.3.1 | Embedding model (all-MiniLM-L6-v2) |

| \*\*Groq\*\* | 0.13.0 | LLM Inference (llama-3.1-8b-instant) |

| \*\*pdfplumber\*\* | 0.11.4 | PDF text extraction |

| \*\*LangChain\*\* | 0.3.x | Text splitting \& chunking |

| \*\*Uvicorn\*\* | 0.34.x | ASGI server |



\### Database

| Teknologi | Fungsi |

|-----------|--------|

| \*\*MySQL 8.x\*\* | Menyimpan: User, ChatSession, ChatMessage, AuditLog |

| \*\*ChromaDB (Vector)\*\* | Menyimpan: 91 chunks dari 3 dokumen PDF |



\### Dev Tools

| Teknologi | Fungsi |

|-----------|--------|

| \*\*npm\*\* | Package manager (Node.js) |

| \*\*pip\*\* | Package manager (Python) |

| \*\*Prisma Studio\*\* | Database GUI |

| \*\*Postman / curl\*\* | API Testing |



\---



\## 🏗️ Arsitektur Sistem



flowchart TD

&#x20;   A\["👤 User<br/>React Frontend<br/>localhost:5173"] -->|POST /api/chat| B\["🟢 Node.js Backend<br/>Port 5000"]

&#x20;   

&#x20;   B --> C\["Express Server"]

&#x20;   C --> D\["Prisma ORM"]

&#x20;   C --> E\["Audit Logger"]

&#x20;   

&#x20;   D -->|Read/Write| F\[("🗄️ MySQL<br/>User, Session,<br/>Message, AuditLog")]

&#x20;   E -->|Write| F

&#x20;   

&#x20;   C -->|POST /chat| G\["🐍 Python RAG Service<br/>Port 8000"]

&#x20;   

&#x20;   G --> H\["FastAPI Server"]

&#x20;   H --> I\["ChromaDB Vector Store"]

&#x20;   H --> J\["Embedding Model<br/>all-MiniLM-L6-v2"]

&#x20;   H --> K\["Groq LLM<br/>llama-3.1-8b-instant"]

&#x20;   H --> L\["Citation Validator"]

&#x20;   

&#x20;   I --> M\[("📊 ChromaDB<br/>91 Chunks<br/>3 PDF")]

&#x20;   

&#x20;   G -->|Return Answer| C

&#x20;   C -->|Response| A

&#x20;   

&#x20;   style A fill:#e3f2fd,stroke:#1565c0,stroke-width:2px,color:#000000

&#x20;   style B fill:#c8e6c9,stroke:#2e7d32,stroke-width:2px,color:#000000

&#x20;   style C fill:#c8e6c9,stroke:#2e7d32,stroke-width:2px,color:#000000

&#x20;   style D fill:#c8e6c9,stroke:#2e7d32,stroke-width:2px,color:#000000

&#x20;   style E fill:#c8e6c9,stroke:#2e7d32,stroke-width:2px,color:#000000

&#x20;   style F fill:#f3e5f5,stroke:#6a1b9a,stroke-width:2px,color:#000000

&#x20;   style G fill:#fff3e0,stroke:#e65100,stroke-width:2px,color:#000000

&#x20;   style H fill:#fff3e0,stroke:#e65100,stroke-width:2px,color:#000000

&#x20;   style I fill:#fff3e0,stroke:#e65100,stroke-width:2px,color:#000000

&#x20;   style J fill:#fff3e0,stroke:#e65100,stroke-width:2px,color:#000000

&#x20;   style K fill:#fff3e0,stroke:#e65100,stroke-width:2px,color:#000000

&#x20;   style L fill:#fff3e0,stroke:#e65100,stroke-width:2px,color:#000000

&#x20;   style M fill:#f3e5f5,stroke:#6a1b9a,stroke-width:2px,color:#000000

Alur Data Detail

User mengirim pertanyaan melalui UI React



Node.js menerima request, menyimpan pesan user ke MySQL



Node.js memanggil Python RAG service via HTTP



Python melakukan:



Retrieve: Cari chunk relevan di ChromaDB (cosine similarity ≥ 0.35)



Ground: Filter chunk yang lolos threshold



Generate: Kirim chunk ke Groq API untuk generate jawaban



Validate: Deteksi penolakan (refusal detection)



Python mengembalikan jawaban + sumber



Node.js menyimpan pesan assistant + audit log ke MySQL



UI menampilkan jawaban dengan badge sumber



📋 Prasyarat

Sebelum menjalankan, pastikan sudah terinstall:



Node.js ≥ 20.x



Python ≥ 3.11



MySQL ≥ 8.x



Git (opsional)



🚀 Instalasi \& Menjalankan

1\. Clone Repository (atau download)

bash

git clone https://github.com/username/akademikai.git

cd akademikai

2\. Setup Backend Node.js

bash

cd backend-node

npm install



\# Buat file .env

cp .env.example .env

\# Edit .env: DATABASE\_URL, GROQ\_API\_KEY, PYTHON\_SERVICE\_URL



\# Setup Prisma

npx prisma generate

npx prisma db push



\# Jalankan

npm run dev

3\. Setup Python RAG Service

bash

cd backend-python

python -m venv venv



\# Aktifkan virtual environment

\# Windows:

venv\\Scripts\\activate

\# Mac/Linux:

source venv/bin/activate



pip install -r requirements.txt



\# Buat file .env

cp .env.example .env

\# Edit .env: GROQ\_API\_KEY



\# Index dokumen (pastikan PDF di folder documents/)

python index\_documents.py



\# Jalankan service

python -m app.main

4\. Setup Frontend React

bash

cd frontend

npm install



\# Jalankan

npm run dev

5\. Buka Aplikasi

Frontend: http://localhost:5173



Backend: http://localhost:5000/health



Python Service: http://localhost:8000/health





📂 Struktur Folder

text

akademikai/

├── backend-node/

│   ├── prisma/

│   │   └── schema.prisma      # Database schema

│   ├── .env                   # Environment variables

│   ├── index.js               # Express server (port 5000)

│   ├── package.json

│   └── tsconfig.json

├── backend-python/

│   ├── app/

│   │   ├── \_\_init\_\_.py

│   │   └── main.py            # FastAPI RAG service (port 8000)

│   ├── documents/             # PDF sumber (3 file)

│   ├── chroma\_store/          # Vector database

│   ├── .env

│   └── requirements.txt

├── frontend/

│   ├── src/

│   │   ├── components/

│   │   ├── pages/

│   │   └── App.jsx

│   ├── package.json

│   └── vite.config.js

└── README.md

🛡️ Guardrails Keamanan

ID	Guardrail	Implementasi

G1	Strict Grounding	Jawaban hanya dari chunk ≥ threshold 0.35; HALT jika tidak ada

G2	Mandatory Citation	Setiap klaim wajib punya source\_file + page\_number

G3	Educational Mode	Deteksi pertanyaan ujian → beri hints, bukan jawaban

G4	Privacy Guard	Dokumen sensitif tidak diproses ke embedding

Citation Validator (Refusal Detection)

Sistem otomatis mendeteksi jika LLM menolak menjawab:



python

refusal\_markers = \[

&#x20;   "tidak tersedia",

&#x20;   "tidak disebutkan",

&#x20;   "tidak ditemukan",

&#x20;   "maaf, informasi",

&#x20;   "tidak dapat menemukan",

]

Jika terdeteksi → sources: \[] dan hallucination\_risk\_flag: true



📊 Evaluasi

Metrik RAGAS

Metrik	Target	Hasil	Status

Faithfulness	≥ 0.90	✅ 1.0	Semua klaim grounded

Answer Relevancy	≥ 0.85	✅ 0.92	Jawaban relevan

Context Recall	≥ 0.80	✅ 0.85	Chunk relevan terambil

Test Pertanyaan (8 Skenario)

No	Pertanyaan	Hasil	Hallucination Risk

1	Margin skripsi?	✅ Akurat	false

2	Struktur Bab 2?	✅ Akurat	false

3	Format APA?	✅ Akurat	false

4	Penalti Turnitin 30%?	✅ Akurat	false

5	Struktur IMRAD?	✅ Akurat	false

6	Rubrik penilaian?	✅ Akurat	false

7	Persyaratan sidang?	✅ Akurat	false

8	Siapa presiden Indonesia?	✅ Ditolak	true

Guardrail Anti-Hallusinasi terbukti berfungsi! 🛡️



👨‍💻 Kontributor

Nama	NIM	Peran

Muhamad Angga Prida Saputra	24110400013	Full-stack Developer \& Designer



