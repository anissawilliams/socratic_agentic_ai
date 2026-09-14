import axios from "axios";

const API_BASE = import.meta.env.VITE_API_BASE_URL;

if (!API_BASE) {
  throw new Error("VITE_API_BASE_URL is not configured");
}

function authHeaders(accessToken) {
  return {
    Authorization: `Bearer ${accessToken}`,
  };
}

export async function getParticipant(accessToken) {
  const response = await axios.get(`${API_BASE}/auth/me`, {
    headers: authHeaders(accessToken),
  });

  return response.data;
}

export async function claimParticipantCode(code, accessToken) {
  const response = await axios.post(
    `${API_BASE}/auth/code`,
    { code },
    {
      headers: authHeaders(accessToken),
    }
  );

  return response.data;
}