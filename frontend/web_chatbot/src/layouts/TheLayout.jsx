import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import ChatMessages from "../components/ChatMessages";
import ChatInput from "../components/ChatInput";
import QuizModal from "../components/QuizModal";
import useIsMobile from "../common/useIsMobile";
import {
  isAuthenticated,
  getAccessToken,
  getUserEmail,
  logoutWithAPI,
} from "../utils/auth";
import { getConversationHistory, getConversationDetail } from "../api/chatApi";

function generateSessionId() {
  return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

export default function TheLayout() {
  const navigate = useNavigate();
  const isMobile = useIsMobile();
  const [collapsed, setCollapsed] = useState(false);
  const [messages, setMessages] = useState([]);
  const [showQuiz, setShowQuiz] = useState(false);
  const [quiz, setQuiz] = useState([]);
  const [loading, setLoading] = useState(false);
  const [loadingQuiz, setLoadingQuiz] = useState(false);

  const [currentSessionId, setCurrentSessionId] = useState(() =>
    generateSessionId()
  );
  const [conversations, setConversations] = useState([]);
  const [activeConversationId, setActiveConversationId] = useState(null);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const isUser = isAuthenticated();

  useEffect(() => {
    if (isUser) {
      loadConversationHistory();
    }
  }, [isUser]);

  const loadConversationHistory = async () => {
    if (!isUser) return;

    setLoadingHistory(true);
    try {
      const history = await getConversationHistory();
      const formattedHistory = history.map((item) => ({
        id: item.session_id,
        session_id: item.session_id,
        title: item.title || item.message || "New Conversation",
      }));
      setConversations(formattedHistory);
    } catch (error) {
      console.error("Error loading conversation history:", error);
    } finally {
      setLoadingHistory(false);
    }
  };

  const handleSelectConversation = async (sessionId) => {
    if (!isUser || !sessionId) return;

    setLoadingHistory(true);
    setActiveConversationId(sessionId);
    setCurrentSessionId(sessionId);

    try {
      const messages = await getConversationDetail(sessionId);
      setMessages(messages);
      setCollapsed(false);
    } catch (error) {
      console.error("Error loading conversation detail:", error);
      setMessages([]);
    } finally {
      setLoadingHistory(false);
    }
  };

  const handleNewChat = () => {
    const newSessionId = generateSessionId();
    setCurrentSessionId(newSessionId);
    setActiveConversationId(null);
    setMessages([]);
    setCollapsed(false);
  };

  const handleLogout = async () => {
    try {
      await logoutWithAPI();

      setMessages([]);
      setConversations([]);
      setActiveConversationId(null);
      setCurrentSessionId(generateSessionId());
      setShowQuiz(false);
      setQuiz([]);

      navigate("/login");
    } catch (error) {
      console.error("Error during logout:", error);
      navigate("/login");
    }
  };

  const parseQuestions = (contentQuestions) => {
    let questions = [];
    for (let contentQuestion of contentQuestions.split("||")) {
      const parts = contentQuestion.split(">>").map((p) => p.trim());
      const q = parts[0];
      const options = parts.slice(1, 5);

      const correctText = parts[5];
      const answerIndex = options.findIndex((o) => o === correctText);

      const note = parts[6] || "";

      questions.push({ q, options, answer: answerIndex, note });
    }

    return questions;
  };

  const callAPI = async (text) => {
    setLoading(true);
    let isShowQuiz = false;

    const isFirstMessage = messages.length === 0;
    const isNewConversation = activeConversationId === null;

    // Thêm user + 1 bot placeholder
    setMessages((prev) => [
      ...prev,
      { role: "user", text },
      { role: "bot", text: "" },
    ]);

    try {
      const apiURL = import.meta.env.VITE_API_URL;
      const headers = {
        "Content-Type": "application/json",
      };

      const token = getAccessToken();
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }

      const body = {
        message: text,
      };

      if (isUser && currentSessionId) {
        body.session_id = currentSessionId;
      }

      const res = await fetch(`${apiURL}/chat`, {
        method: "POST",
        headers,
        body: JSON.stringify(body),
      });

      if (!res.ok || !res.body) throw new Error("Server error");

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let buffer_err = "";
      let startedText = false;

      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          if (isShowQuiz) {
            const questions = parseQuestions(buffer);
            setQuiz(questions);
            setShowQuiz(true);
            setLoadingQuiz(false);
          }
          break;
        }

        let str_buffer = decoder.decode(value, { stream: true });
        let arr_buffer = str_buffer.split("\n");
        for (let item_buffer of arr_buffer) {
          let data = null;
          try {
            if (
              item_buffer == undefined ||
              item_buffer == null ||
              item_buffer == ""
            )
              break;

            const item_json = JSON.parse(item_buffer);
            buffer_err = "";
            data = item_json;
            console.log(item_json);
          } catch (error) {
            buffer_err += item_buffer;
            try {
              console.log(buffer_err);
              const item_json = JSON.parse(buffer_err);
              data = item_json;
              console.log(item_json);
            } catch (error) {
              console.log(error);
            }
          }
          if (data == null || data == undefined) break;
          if (
            data.message != undefined &&
            data.message.indexOf("tạo câu hỏi trắc nghiệm") > 0
          ) {
            isShowQuiz = true;
            setLoadingQuiz(true);
          }
          setMessages((prev) => {
            const clone = [...prev];
            const botMsg = clone.findLast((m) => m.role === "bot");

            // Status chỉ hiện khi chưa có text
            if (data.type === "status" && !startedText) {
              botMsg.text = data.message;
            }

            // Khi có text → reset status cũ và bắt đầu in text
            if (data.type === "text") {
              if (!startedText) {
                startedText = true;
                botMsg.text = "";
              }
              botMsg.text += data.content;
              if (isShowQuiz) {
                buffer = botMsg.text;
              }
            }

            // Khi có image → chèn ảnh HTML vào bubble
            if (data.type === "image") {
              botMsg.text += `<img src="data:${data.mime_type};base64,${data.data}" class="chat-image"/>`;
            }

            return clone;
          });
        }
      }
    } catch (err) {
      console.error(err);
      setMessages((prev) => {
        const clone = [...prev];
        const botMsg = clone.findLast((m) => m.role === "bot");
        botMsg.text = "❌ Lỗi kết nối server";
        return clone;
      });
    } finally {
      setLoading(false);

      if (isUser && isFirstMessage && isNewConversation) {
        // Debounce để tránh reload quá nhiều lần và đợi backend lưu xong
        setTimeout(() => {
          loadConversationHistory();
        }, 1000);
      }
    }
  };

  const handleSend = (inputText) => {
    if (!inputText.trim()) return;
    callAPI(inputText);
  };

  const status_display = isMobile ? !collapsed : collapsed;
  const userEmail = getUserEmail();

  return (
    <div className="bg-[#FDEDEA] h-screen overflow-hidden">
      <div className="flex h-full">
        <Sidebar
          collapsed={status_display}
          onToggle={() => setCollapsed(!collapsed)}
          onNewChat={handleNewChat}
          activeConversationId={activeConversationId}
          conversations={conversations}
          onSelectConversation={handleSelectConversation}
          isUser={isUser}
          loadingHistory={loadingHistory}
          userEmail={userEmail}
          onLogout={handleLogout}
        />

        {isMobile && !status_display && (
          <div
            className="fixed inset-0 bg-black bg-opacity-40 z-40"
            onClick={() => setCollapsed(true)}
          />
        )}

        {/* Main Chat Area */}
        <main className="flex-1 flex flex-col overflow-hidden relative">
          {showQuiz && (
            <QuizModal onClose={() => setShowQuiz(false)} questions={quiz} />
          )}
          <ChatMessages
            messages={messages}
            onSuggestionSelect={(question) => {
              handleSend(question);
            }}
            statusLoading={loading}
            statusLoadingQuiz={loadingQuiz}
          />
          <ChatInput onSend={handleSend} disabled={loading} />
        </main>
      </div>
    </div>
  );
}
