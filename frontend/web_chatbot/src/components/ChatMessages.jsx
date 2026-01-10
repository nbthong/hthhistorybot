import { useEffect, useRef } from "react";
import { useState } from "react";
import QuizModal from "./QuizModal";
import SuggestionsSection from "./SuggestionsSection";

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

function ChatMessages({
  messages,
  onSuggestionSelect,
  statusLoading,
  statusLoadingQuiz,
  loadingConversationDetail,
}) {
  const bottomRef = useRef(null);
  const [showQuiz, setShowQuiz] = useState(false);
  const [quiz, setQuiz] = useState([]);

  const isValidQuizFormat = (input) => {
    if (!input || !input.includes("||")) return false;
    const blocks = input.split("||");
    return blocks.every((block) => {
      const parts = block.split(">>").map((p) => p.trim());
      if (parts.length < 6) return false;
      const options = parts.slice(1, 5);
      const correct = parts[5];
      return options.includes(correct);
    });
  };

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Hiển thị loading state khi đang load conversation detail
  if (loadingConversationDetail) {
    return (
      <div className="flex-1 overflow-y-auto flex items-center justify-center px-10 py-8">
        <div className="flex flex-col items-center gap-3">
          <div className="flex gap-1">
            <div
              className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce"
              style={{ animationDelay: "0ms" }}
            />
            <div
              className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce"
              style={{ animationDelay: "150ms" }}
            />
            <div
              className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce"
              style={{ animationDelay: "300ms" }}
            />
          </div>
          <p className="text-sm text-gray-500">Đang tải cuộc trò chuyện...</p>
        </div>
      </div>
    );
  }

  // Chỉ hiển thị suggestions khi không có messages và không đang load
  if (!messages || messages.length === 0) {
    return <SuggestionsSection onSelectSuggestion={onSuggestionSelect} />;
  }

  return (
    <>
      {showQuiz && (
        <QuizModal onClose={() => setShowQuiz(false)} questions={quiz} />
      )}
      <div className="flex-1 overflow-y-auto space-y-8 px-10 py-8 pr-4">
        {messages.map((m, i) => {
          const isUser = m.role === "user";
          const isBot = m.role === "bot" || m.role === "assistant";

          if (isUser) {
            return (
              <div key={i} className="flex gap-4 justify-end">
                <div className="bg-white rounded-2xl p-6 max-w-3xl shadow-sm">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-6 h-6 rounded-full bg-gray-300 flex items-center justify-center text-xs text-gray-600">
                      U
                    </div>
                    <span className="text-sm text-gray-500">You</span>
                    <button className="ml-auto text-gray-400 hover:text-gray-600 text-xs">
                      ✎
                    </button>
                  </div>
                  <p className="text-sm text-gray-700 whitespace-pre-wrap">
                    {m.text.replace("Yêu cầu Quiz:", "")}
                  </p>
                </div>
              </div>
            );
          }

          if (isBot) {
            return (
              <div
                key={i}
                className={statusLoading ? "flex gap-4 items-end" : "flex gap-4"}
              >
                <div className="w-9 h-9 rounded-full bg-indigo-500 flex items-center flex justify-center text-white font-bold flex-shrink-0">
                  {statusLoading && i == messages.length - 1 ? (
                    <span className="loading-spinner">⏳️</span>
                  ) : (
                    "AI"
                  )}
                </div>
                <div className="bg-white rounded-2xl p-6 max-w-3xl shadow-sm flex-1">
                  {isValidQuizFormat(m.text) ? (
                    <>
                      <p className="font-semibold mb-2">
                        Làm bài test với nội dung: [
                        {messages[i - 1].text.replace("Yêu cầu Quiz:", "")}]
                      </p>
                      <button
                        onClick={() => {
                          setQuiz(parseQuestions(m.text));
                          setShowQuiz(true);
                        }}
                        className="mt-4 px-4 py-2 bg-indigo-500 text-white rounded-lg hover:bg-indigo-600 transition"
                      >
                        Bắt Đầu Làm Bài
                      </button>
                    </>
                  ) : (
                    <>
                      <div
                        className="text-sm text-gray-700 prose prose-sm max-w-none"
                        dangerouslySetInnerHTML={{
                          __html: (statusLoading && statusLoadingQuiz
                            ? "Đang tạo bài thi trắc nghiệm"
                            : m.text
                          )
                            .replace(/\n/g, "<br/>")
                            .replace(/\*\*(.+?):\*\*/g, "<strong>$1:</strong>")
                            .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>"),
                        }}
                      />
                      <div className="mt-4 flex items-center gap-4 text-xs text-gray-400">
                        <button className="hover:text-gray-600 transition">
                          👍
                        </button>
                        <button className="hover:text-gray-600 transition">
                          👎
                        </button>
                        <button className="hover:text-gray-600 transition">
                          📋
                        </button>
                        <button className="hover:text-gray-600 transition">
                          🔗
                        </button>
                      </div>
                    </>
                  )}
                </div>
              </div>
            );
          }

          return null;
        })}
        <div ref={bottomRef} />
      </div>
    </>
  );
}

export default ChatMessages;
