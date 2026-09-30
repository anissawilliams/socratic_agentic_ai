import axios from "axios";

import { getStoredParticipantCode } from "./authClient";

const API_BASE = import.meta.env.VITE_API_BASE_URL;

function participantHeaders() {
  return { "X-Participant-Code": getStoredParticipantCode() };
}

function readableError(error) {
  const detail = error?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && detail[0]?.msg) {
    return detail[0].msg.replace(/^Value error, /, "");
  }
  return "Your responses could not be saved. Please try again.";
}

async function post(path, body) {
  try {
    const response = await axios.post(`${API_BASE}${path}`, body, {
      headers: participantHeaders(),
    });
    return response.data;
  } catch (error) {
    throw new Error(readableError(error), { cause: error });
  }
}

export function submitDemographics(demographics) {
  return post("/study/demographics", demographics);
}

export async function getSurvey() {
  const response = await axios.get(`${API_BASE}/study/survey`, {
    headers: participantHeaders(),
  });
  return response.data;
}

export function submitSurvey(submission) {
  return post("/study/survey", submission);
}
