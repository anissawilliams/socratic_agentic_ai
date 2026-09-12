import axios from "axios";

import { supabase } from "./supabase";

const API_BASE =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

// Read the token per request instead of capturing it once. A tutoring session
// can outlive a single access token, and supabase-js refreshes it in the
// background, so asking for the current session avoids sending a stale one.
async function authHeaders() {
  const {
    data: { session },
  } = await supabase.auth.getSession();

  if (!session) {
    throw new Error("Not signed in");
  }

  return { Authorization: `Bearer ${session.access_token}` };
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
      headers: await authHeaders(),
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
        headers: await authHeaders(),
      }
    );

    return res.data;
  } catch (err) {
    throw requestFailure(err);
  }
}
