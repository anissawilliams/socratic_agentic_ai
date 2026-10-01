import axios from "axios";

import { getStoredParticipantCode } from "./authClient";

const API_BASE = import.meta.env.VITE_API_BASE_URL;

function headers() {
  return { "X-Participant-Code": getStoredParticipantCode() };
}

/** Returns the running timer, or null if the phase hasn't started yet. */
export async function getTimer() {
  try {
    const response = await axios.get(`${API_BASE}/study/timer`, { headers: headers() });
    return response.data;
  } catch (error) {
    if (error?.response?.status === 404) return null;
    throw error;
  }
}

export async function expireTutor() {
  const response = await axios.post(`${API_BASE}/study/timer/expire-tutor`, null, {
    headers: headers(),
  });
  return response.data;
}

export async function submitAssessmentOnTimeout(payload) {
  const response = await axios.post(`${API_BASE}/study/timer/submit-assessment`, payload, {
    headers: headers(),
  });
  return response.data;
}

/** Participant chooses to move on after the tutor minimum time. */
export async function finishTutor() {
  const response = await axios.post(`${API_BASE}/study/timer/finish-tutor`, null, {
    headers: headers(),
  });
  return response.data;
}
