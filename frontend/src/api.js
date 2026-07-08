const API_BASE = "http://localhost:5000";

export async function sendChatMessage(query, sessionId, userId = "test-user") {
  const response = await fetch(`${API_BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, sessionId, userId }),
  });
  if (!response.ok) {
    throw new Error(
      "Gagal menghubungi server. Pastikan backend-node dan backend-python aktif.",
    );
  }
  return response.json();
}

export async function fetchSessions(userId = "test-user") {
  const response = await fetch(`${API_BASE}/api/sessions/${userId}`);
  if (!response.ok) throw new Error("Gagal memuat daftar sesi.");
  const data = await response.json();
  return data.sessions;
}

export async function fetchSessionMessages(sessionId) {
  const response = await fetch(
    `${API_BASE}/api/sessions/${sessionId}/messages`,
  );
  if (!response.ok) throw new Error("Gagal memuat riwayat pesan.");
  const data = await response.json();
  return data.messages;
}
