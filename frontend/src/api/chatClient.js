import axios from "axios";

const API_BASE =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export async function startSession() {
    const res = await axios.get(`${API_BASE}/tutor/start`);
    return res.data;
}

export async function sendMessage(sessionId, message) {
  const res = await axios.post(`${API_BASE}/tutor/message`, {
    session_id: sessionId,
    message,
  });

  return res.data;
}