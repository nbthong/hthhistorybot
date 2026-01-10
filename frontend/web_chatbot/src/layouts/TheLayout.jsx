import { useState } from "react";
import Sidebar from "../components/Sidebar";
import ChatMessages from "../components/ChatMessages";
import ChatInput from "../components/ChatInput";
import QuizModal from "../components/QuizModal";
import useIsMobile from "../common/useIsMobile";

export default function TheLayout() {
  const isMobile = useIsMobile();
  const [collapsed, setCollapsed] = useState(false);
  const [messages, setMessages] = useState([]);
  const [showQuiz, setShowQuiz] = useState(false);
  const [quiz, setQuiz] = useState([]);
  const [loading, setLoading] = useState(false);

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

    // Thêm user + 1 bot placeholder
    setMessages((prev) => [
      ...prev,
      { role: "user", text },
      { role: "bot", text: "" },
    ]);

    try {
      const apiURL = import.meta.env.VITE_API_URL;
      const res = await fetch(`${apiURL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
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
    }
  };

  const handleSend = (inputText) => {
    if (!inputText.trim()) return;
    callAPI(inputText);
  };

  const status_display = isMobile ? !collapsed : collapsed;
  console.log("showQuiz: ", showQuiz);
  return (
    <>
      <Sidebar
        collapsed={status_display}
        onToggle={() => setCollapsed(!collapsed)}
      />
      {isMobile && !status_display && (
        <div className="sidebar-overlay" onClick={() => setCollapsed(false)} />
      )}

      <div className={`main ${status_display ? "collapsed" : ""}`}>
        <div className="main-header p-2 border-bottom">
          <button
            className="btn-menu-mobile btn btn-light me-2"
            onClick={() => setCollapsed(!collapsed)}
          >
            ☰
          </button>
          <strong className="fs-5">Chat</strong>
          {loading && <span className="ms-3">(đang trả lời...)</span>}
        </div>
        {showQuiz && (
          <QuizModal onClose={() => setShowQuiz(false)} questions={quiz} />
        )}
        <ChatMessages messages={messages} />
        <ChatInput onSend={handleSend} disabled={loading} />
      </div>
    </>
  );
}
