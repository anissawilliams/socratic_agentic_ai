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


// Streaming is opt-in so the blocking flow stays the default until tested.
export const STREAMING_ENABLED =
  import.meta.env.VITE_STREAM_TUTOR === "true";

function parseSseBlock(block) {
  let event = "message";
  const dataLines = [];
  for (const line of block.split("\n")) {
    if (line.startsWith("event:")) {
      event = line.slice(6).trim();
    } else if (line.startsWith("data:")) {
      dataLines.push(line.slice(5).trimStart());
    }
  }
  return { event, data: dataLines.length ? JSON.parse(dataLines.join("\n")) : null };
}

/**
 * Send a message and receive the tutor reply as it is generated.
 * Calls onToken(text) for each piece of the reply and resolves with the same
 * payload as sendMessage() once the turn is saved.
 */
export async function streamMessage(sessionId, message, { onToken } = {}) {
  let res;
  try {
    res = await fetch(`${API_BASE}/tutor/message/stream`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...participantHeaders(),
      },
      body: JSON.stringify({ session_id: sessionId, message }),
    });
  } catch (err) {
    throw requestFailure(err);
  }

  if (!res.ok) {
    let detail = null;
    try {
      detail = (await res.json())?.detail ?? null;
    } catch {
      // non-JSON error body
    }
    const failure = new Error(detail || `Request failed (${res.status})`);
    failure.status = res.status;
    failure.detail = detail;
    throw failure;
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    let boundary;
    while ((boundary = buffer.indexOf("\n\n")) !== -1) {
      const block = buffer.slice(0, boundary);
      buffer = buffer.slice(boundary + 2);
      if (!block.trim()) continue;

      const { event, data } = parseSseBlock(block);
      if (event === "token") {
        onToken?.(data.text);
      } else if (event === "done") {
        return data;
      } else if (event === "error") {
        const failure = new Error(data?.detail || "Tutor error");
        failure.status = 500;
        failure.detail = data?.detail ?? null;
        throw failure;
      }
    }
  }

  const failure = new Error("The tutor stream ended before the reply finished.");
  failure.status = 500;
  throw failure;
}
