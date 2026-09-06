// frontend/src/api/authClient.js

import axios from "axios";

const API_BASE =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export async function getParticipant(accessToken) {
  const response = await axios.get(`${API_BASE}/auth/me`, {
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });

  return response.data;
}