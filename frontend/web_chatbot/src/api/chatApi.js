import { getAccessToken } from "../utils/auth";

const apiURL = import.meta.env.VITE_API_URL;

export async function getConversationHistory() {
  try {
    const token = getAccessToken();
    const headers = {
      "Content-Type": "application/json",
    };

    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const res = await fetch(`${apiURL}/chat/history?limit=1000`, {
      method: "GET",
      headers,
    });

    if (!res.ok) {
      throw new Error("Failed to fetch conversation history");
    }

    const data = await res.json();
    const history = data.history || [];

    const sessionMap = new Map();
    
    history.forEach((msg) => {
      const sessionId = msg.session_id;
      if (!sessionId) return;

      if (!sessionMap.has(sessionId)) {
        const title = msg.content
          ? msg.content.substring(0, 50).trim()
          : "New Conversation";
        
        sessionMap.set(sessionId, {
          session_id: sessionId,
          title: title,
          id: sessionId, 
        });
      }
    });

    return Array.from(sessionMap.values()).reverse();
  } catch (error) {
    console.error("Error fetching conversation history:", error);
    return [];
  }
}


export async function getConversationDetail(sessionId, limit = 100) {
  try {
    const token = getAccessToken();
    const headers = {
      "Content-Type": "application/json",
    };

    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const res = await fetch(
      `${apiURL}/chat/history?session_id=${sessionId}&limit=${limit}`,
      {
        method: "GET",
        headers,
      }
    );

    if (!res.ok) {
      throw new Error("Failed to fetch conversation detail");
    }

    const data = await res.json();
    const history = data.history || [];

    return history.map((msg) => ({
      role: msg.role === "user" ? "user" : "bot",
      text: msg.content || "",
    }));
  } catch (error) {
    console.error("Error fetching conversation detail:", error);
    return [];
  }
}

export async function sendMessage(message) {
  return { reply: "res: " + message };
}
