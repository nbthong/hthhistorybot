import { useState } from "react";
import { sendMessage } from "../api/chatApi";
import ChatInput from "../components/ChatInput";

export default function Chatbot() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");

  const handleSend = async ({ text, file }) => {
    setMessages((m) => [...m, { role: "user", text: text }]);

    const res = await sendMessage(text);

    setMessages((m) => [...m, { role: "assistant", text: res.reply }]);
  };

  return (
    <div className="container chat-page mt-4 d-flex flex-column">
      {/* Messages */}
      <div className="border chat-messages rounded p-3 flex-grow-1">
        {messages.map((m, i) => (
          <div
            key={i}
            className={`mb-2 ${m.role === "user" ? "text-end" : "text-start"}`}
          >
            <div className="d-inline-block p-2 rounded bg-light">
              <strong>{m.role}:</strong> {m.text}
            </div>
          </div>
        ))}
      </div>

      {/* Fixed Chat Input */}
      <div className="chat-input-fixed">
        <ChatInput onSend={handleSend} />
      </div>
    </div>
  );
}
