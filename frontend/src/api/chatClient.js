import axios from "axios";

import { getStoredParticipantCode } from "./authClient";

const API_BASE =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

function participantHeaders() {
  const code = getStoredParticipantCode();

  if (!code) {
    throw new Error("Participant code is not available");
  }

  return {
    "X-Participant-Code": code,
  };
}

function requestFailure(err) {
  const status = err?.response?.status ?? null;
  const detail = err?.response?.data?.detail ?? null;

  const failure = new Error(detail || err?.message || "Request failed");
  failure.status = status;
  failure.detail = detail;
  failure.cause = err;

  return failure;
}

export async function startSession() {
  try {
    const res = await axios.get(`${API_BASE}/tutor/start`, {
      headers: participantHeaders(),
    });

    return res.data;
  } catch (err) {
    throw requestFailure(err);
  }
}

export async function sendMessage(sessionId, message) {
  try {
    const res = await axios.post(
      `${API_BASE}/tutor/message`,
      {
        session_id: sessionId,
        message,
      },
      {
        headers: participantHeaders(),
      }
    );

    return res.data;
  } catch (err) {
    throw requestFailure(err);
  }
}
