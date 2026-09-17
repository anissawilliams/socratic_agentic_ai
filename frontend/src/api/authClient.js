import axios from "axios";

const API_BASE = import.meta.env.VITE_API_BASE_URL;

if (!API_BASE) {
  throw new Error("VITE_API_BASE_URL is not configured");
}

const PARTICIPANT_CODE_KEY = "participantStudyCode";

export function getStoredParticipantCode() {
  return window.localStorage.getItem(PARTICIPANT_CODE_KEY);
}

export function clearParticipantCode() {
  window.localStorage.removeItem(PARTICIPANT_CODE_KEY);
}

function participantHeaders(code) {
  return {
    "X-Participant-Code": code,
  };
}

export async function getParticipant(code) {
  const response = await axios.get(`${API_BASE}/auth/me`, {
    headers: participantHeaders(code),
  });

  return response.data;
}

export async function authenticateParticipant(code) {
  const normalizedCode = code.trim().toUpperCase();
  const participant = await getParticipant(normalizedCode);

  window.localStorage.setItem(PARTICIPANT_CODE_KEY, normalizedCode);
  return participant;
}
