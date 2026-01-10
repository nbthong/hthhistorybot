import { useEffect, useRef } from "react";
import { useState } from "react";
import QuizModal from "./QuizModal";

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
function ChatMessages({ messages }) {
  const bottomRef = useRef(null);
  const [showQuiz, setShowQuiz] = useState(false);
  const [quiz, setQuiz] = useState([]);

  const isValidQuizFormat = (input) => {
    console.log(input);
    const blocks = input.split("||");
    if (!input.includes("||")) return false;

    return blocks.every((block) => {
      const parts = block.split(">>").map((p) => p.trim());
      if (parts.length !== 6) return false;

      const options = parts.slice(1, 5);
      const correct = parts[5];
      const note = parts[6] || "";

      // Kiểm tra correct có nằm trong options không
      if (!options.includes(correct)) return false;

      return true;
    });
  };
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  if (!messages || messages.length == 0)
    return (
      <div className="messages">
        <div className="container container-messages">
          <div className="text-start">
            <h1 className="fw-bold">
              <span className="fs-4">📚</span>Lịch Sử 10, 11, 12 AI Tutor –
              Chatbot
            </h1>
          </div>

          <div className="mt-4">
            <div className="d-flex text-start gap-2">
              <h4 className="mb-0">
                Xin chào, mình là Lịch Sử 10, 11, 12 AI Tutor.
              </h4>
            </div>
          </div>

          <div className="mt-3">
            <p className="fs-5 text-start">Bạn có thể:</p>
            <ul className="mx-auto">
              <li className="">
                Hỏi giải thích các sự kiện, nhân vật lịch sử lớp 10, 11, 12.
              </li>
              <li className="">
                Yêu cầu tạo quiz / câu hỏi trắc nghiệm về một chủ đề lịch sử.
              </li>
            </ul>
          </div>
        </div>
      </div>
    );

  return (
    <div className="messages">
      {showQuiz && (
        <QuizModal onClose={() => setShowQuiz(false)} questions={quiz} />
      )}
      {messages.map((m, i) => (
        <div key={i} className={`message ${m.role}`}>
          <div className="bubble">
            {isValidQuizFormat(m.text) ? (
              <>
                <div>Làm bài test</div>
                <button
                  onClick={() => {
                    setQuiz(parseQuestions(m.text));
                    setShowQuiz(true);
                  }}
                >
                  Start
                </button>
              </>
            ) : (
              <div
                dangerouslySetInnerHTML={{
                  __html: m.text
                    .replace(/\n/g, "<br/>")
                    .replace(/\*\*(.+?):\*\*/g, "<strong>$1:</strong>"),
                }}
              />
            )}
          </div>
        </div>
      ))}
      <div ref={bottomRef} />
    </div>
  );
}

export default ChatMessages;
