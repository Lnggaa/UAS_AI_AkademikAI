require("dotenv").config();
const express = require("express");
const cors = require("cors");
const axios = require("axios");
const { PrismaClient } = require("@prisma/client");

const app = express();
const prisma = new PrismaClient();

app.use(cors());
app.use(express.json());

const PYTHON_SERVICE_URL =
  process.env.PYTHON_SERVICE_URL || "http://localhost:8000";

// ===== Health check =====
app.get("/health", async (req, res) => {
  try {
    const userCount = await prisma.user.count();
    res.json({
      status: "ok",
      message: "Backend Node + Prisma + MySQL terkoneksi",
      totalUser: userCount,
    });
  } catch (error) {
    console.error("Health check error:", error);
    res.status(500).json({ status: "error", message: error.message });
  }
});

// ===== Helper: panggil Python RAG service =====
async function callPythonRAG(query, sessionId) {
  const response = await axios.post(
    `${PYTHON_SERVICE_URL}/chat`,
    { query, session_id: sessionId },
    { timeout: 30000 },
  );
  return response.data;
}

// ===== Endpoint utama: chat =====
app.post("/api/chat", async (req, res) => {
  const startTime = Date.now();
  const { query, sessionId, userId = "test-user" } = req.body;

  if (!query || query.trim() === "") {
    return res
      .status(400)
      .json({ status: "error", message: "Query tidak boleh kosong" });
  }

  let session;
  let pythonResult;
  let statusCode = 200;
  let errorMessage = null;

  try {
    // 1. Cari atau buat session
    if (sessionId) {
      session = await prisma.chatSession.findUnique({
        where: { id: sessionId },
      });
    }
    if (!session) {
      session = await prisma.chatSession.create({
        data: {
          userId,
          title: query.substring(0, 50),
        },
      });
    }

    // 2. Simpan pesan user
    await prisma.chatMessage.create({
      data: {
        sessionId: session.id,
        role: "user",
        content: query,
      },
    });

    // 3. Panggil Python RAG service (document_retriever + citation_validator + generate)
    pythonResult = await callPythonRAG(query, session.id);

    // 4. Simpan pesan assistant, lengkap dengan sumber dan flag risiko
    await prisma.chatMessage.create({
      data: {
        sessionId: session.id,
        role: "assistant",
        content: pythonResult.answer,
        documentsSearched: JSON.stringify(
          pythonResult.sources.map((s) => s.source_file),
        ),
        sourceEvidence: JSON.stringify(pythonResult.sources),
        hallucinationRisk: pythonResult.hallucination_risk_flag,
      },
    });
  } catch (error) {
    statusCode = 500;
    errorMessage = error.message;
    console.error("Chat error:", error.message);
  }

  const responseTime = Date.now() - startTime;

  // 5. Audit log — WAJIB tercatat baik sukses maupun gagal
  try {
    await prisma.auditLog.create({
      data: {
        sessionId: session ? session.id : "unknown-session",
        query,
        toolCalled: "document_retriever+citation_validator",
        toolArgs: JSON.stringify({ query, top_k: 5 }),
        similarityScore: pythonResult?.sources?.[0]?.similarity_score ?? null,
        sourceChunks: pythonResult
          ? JSON.stringify(pythonResult.sources)
          : null,
        hallucinationRisk: pythonResult?.hallucination_risk_flag ?? true,
        fallbackUsed: false, // search_api() belum diimplementasi di fase ini
        approvalStatus: "not_required",
        responseTime,
        statusCode,
        errorMessage,
      },
    });
  } catch (auditError) {
    console.error("Gagal menyimpan audit log:", auditError.message);
  }

  // 6. Kirim response ke client
  if (statusCode === 200) {
    res.json({
      status: "success",
      sessionId: session.id,
      answer: pythonResult.answer,
      sources: pythonResult.sources,
      hallucinationRiskFlag: pythonResult.hallucination_risk_flag,
    });
  } else {
    res.status(500).json({ status: "error", message: errorMessage });
  }
});

// ===== Endpoint: ambil semua sesi milik user =====
app.get("/api/sessions/:userId", async (req, res) => {
  try {
    const sessions = await prisma.chatSession.findMany({
      where: { userId: req.params.userId },
      orderBy: { updatedAt: "desc" },
    });
    res.json({ status: "success", sessions });
  } catch (error) {
    res.status(500).json({ status: "error", message: error.message });
  }
});

// ===== Endpoint: ambil semua pesan dalam satu sesi =====
app.get("/api/sessions/:sessionId/messages", async (req, res) => {
  try {
    const messages = await prisma.chatMessage.findMany({
      where: { sessionId: req.params.sessionId },
      orderBy: { timestamp: "asc" },
    });
    res.json({ status: "success", messages });
  } catch (error) {
    res.status(500).json({ status: "error", message: error.message });
  }
});

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
  console.log(`Server backend-node jalan di http://localhost:${PORT}`);
});
