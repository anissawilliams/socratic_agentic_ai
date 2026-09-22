import axios from "axios";

import { getStoredParticipantCode } from "./authClient";


const API_BASE = import.meta.env.VITE_API_BASE_URL;

if (!API_BASE) {
  throw new Error("VITE_API_BASE_URL is not configured");
}


function participantHeaders() {
  const code = getStoredParticipantCode();

  return {
    "X-Participant-Code": code,
  };
}


export async function startAssessment() {
  const response = await axios.post(
    `${API_BASE}/assessment/start`,
    {},
    {
      headers: participantHeaders(),
    }
  );

  return response.data;
}


export async function submitAssessment(submission) {
  const response = await axios.post(
    `${API_BASE}/assessment/submit`,
    submission,
    {
      headers: participantHeaders(),
    }
  );

  return response.data;
}