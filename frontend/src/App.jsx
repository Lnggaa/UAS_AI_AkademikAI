import { useState, useEffect, useRef } from "react";
import { sendChatMessage, fetchSessions, fetchSessionMessages } from "./api";
import "./App.css";

function parseJsonSafely(value) {
  if (!value) return null;
  try {
    return JSON.parse(value);
  } catch {
    return null;
  }
}

function formatTime(dateString) {
  const date = new Date(dateString);
  return date.toLocaleTimeString("id-ID", {
    hour: "2-digit",
    minute: "2-digit",
  });
}

function SourceStrip({ sources, hallucinationRisk }) {
  const [expandedIndex, setExpandedIndex] = useState(null);

  if (hallucinationRisk || !sources || sources.length === 0) {
    return (
      <div className="risk-banner">
        Sumber resmi tidak ditemukan untuk pertanyaan ini. Periksa kembali
        pertanyaan Anda atau tanyakan langsung ke dosen pembimbing.
      </div>
    );
  }

  return (
    <div className="source-strip">
      {sources.map((source, index) => (
        <button
          key={index}
          className="source-chip"
          onClick={() =>
            setExpandedIndex(expandedIndex === index ? null : index)
          }
        >
          <span className="chip-file">{source.source_file}</span>
          <span className="chip-page">Hal. {source.page_number}</span>
          {expandedIndex === index && (
            <span className="chip-score">
              skor {source.similarity_score.toFixed(3)}
            </span>
          )}
        </button>
      ))}
    </div>
  );
}

function MessageBubble({ message }) {
  const isUser = message.role === "user";
  const sources = message.sources || parseJsonSafely(message.sourceEvidence);
  const hallucinationRisk =
    message.hallucinationRiskFlag ?? message.hallucinationRisk ?? false;

  return (
    <div className={`message-row ${isUser ? "message-row-user" : ""}`}>
      <div
        className={`message-bubble ${isUser ? "bubble-user" : "bubble-assistant"}`}
      >
        <p className="message-text">{message.content || message.answer}</p>
        {!isUser && (
          <SourceStrip
            sources={sources}
            hallucinationRisk={hallucinationRisk}
          />
        )}
      </div>
    </div>
  );
}

function Sidebar({
  sessions,
  currentSessionId,
  onSelectSession,
  onNewSession,
}) {
  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <h1 className="app-title">AkademikAI</h1>
        <p className="app-subtitle">
          Asisten penulisan akademik berbasis dokumen resmi
        </p>
      </div>
      <button className="new-session-btn" onClick={onNewSession}>
        Sesi Baru
      </button>
      <div className="session-list">
        {sessions.length === 0 && (
          <p className="empty-note">Belum ada riwayat percakapan.</p>
        )}
        {sessions.map((session) => (
          <button
            key={session.id}
            className={`session-item ${session.id === currentSessionId ? "session-item-active" : ""}`}
            onClick={() => onSelectSession(session.id)}
          >
            {session.title}
          </button>
        ))}
      </div>
    </aside>
  );
}

export default function App() {
  const [sessions, setSessions] = useState([]);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    loadSessions();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function loadSessions() {
    try {
      const data = await fetchSessions();
      setSessions(data);
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleSelectSession(sessionId) {
    setCurrentSessionId(sessionId);
    setError(null);
    try {
      const data = await fetchSessionMessages(sessionId);
      setMessages(data);
    } catch (err) {
      setError(err.message);
    }
  }

  function handleNewSession() {
    setCurrentSessionId(null);
    setMessages([]);
    setError(null);
  }

  async function handleSend() {
    const query = input.trim();
    if (!query || loading) return;

    setInput("");
    setError(null);
    setMessages((prev) => [...prev, { role: "user", content: query }]);
    setLoading(true);

    try {
      const result = await sendChatMessage(query, currentSessionId);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: result.answer,
          sources: result.sources,
          hallucinationRiskFlag: result.hallucinationRiskFlag,
        },
      ]);

      if (!currentSessionId) {
        setCurrentSessionId(result.sessionId);
        loadSessions();
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(event) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      handleSend();
    }
  }

  return (
    <div className="app-layout">
      <Sidebar
        sessions={sessions}
        currentSessionId={currentSessionId}
        onSelectSession={handleSelectSession}
        onNewSession={handleNewSession}
      />

      <main className="chat-panel">
        <div className="chat-messages">
          {messages.length === 0 && (
            <div className="empty-state">
              <h2>Mulai percakapan baru</h2>
              <p>
                Tanyakan seputar format penulisan, struktur bab, sitasi, atau
                rubrik penilaian tugas akhir. Jawaban AkademikAI hanya
                berdasarkan dokumen resmi program studi.
              </p>
            </div>
          )}

          {messages.map((message, index) => (
            <MessageBubble key={index} message={message} />
          ))}

          {loading && (
            <div className="message-row">
              <div className="message-bubble bubble-assistant bubble-loading">
                Mencari referensi dan menyusun jawaban...
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {error && <div className="error-banner">{error}</div>}

        <div className="chat-input-area">
          <textarea
            className="chat-input"
            placeholder="Tulis pertanyaan Anda di sini..."
            value={input}
            onChange={(event) => setInput(event.target.value)}
            onKeyDown={handleKeyDown}
            rows={1}
          />
          <button className="send-btn" onClick={handleSend} disabled={loading}>
            Kirim
          </button>
        </div>
      </main>
    </div>
  );
}
