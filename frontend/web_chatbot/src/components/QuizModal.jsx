import { useState } from "react";

export default function QuizModal({ questions, onClose }) {
  const [selected, setSelected] = useState(Array(questions.length).fill(null));
  const [score, setScore] = useState(null);
  const [submitted, setSubmitted] = useState(false);

  const handleSelect = (questionIndex, optionIndex) => {
    if (submitted) return; 
    
    const clone = [...selected];
    clone[questionIndex] = optionIndex;
    setSelected(clone);
  };

  const handleSubmit = () => {
    let s = 0;
    selected.forEach((selectedIndex, i) => {
      if (selectedIndex === questions[i].answer) {
        s++;
      }
    });
    setScore(s);
    setSubmitted(true);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4" style={{ background: "rgba(0,0,0,0.5)" }}>
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col">
        <div className="flex items-center justify-between p-6 border-b">
          <h5 className="text-2xl font-bold text-gray-800">Quiz Lịch sử</h5>
          <button
            type="button"
            onClick={onClose}
            className="w-8 h-8 rounded-full hover:bg-gray-100 flex items-center justify-center text-gray-500 hover:text-gray-700 transition-colors"
            aria-label="Đóng"
          >
            ✕
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-6">
            {questions.map((item, i) => (
              <div key={i} className="mb-4">
                <p className="fw-semibold mb-3 text-gray-800">{i + 1}. {item.q}</p>
                {item.options.map((opt, j) => {
                  const isSelected = selected[i] === j;
                  const isCorrect = submitted && j === item.answer;
                  const isWrong = submitted && isSelected && j !== item.answer;
                  
                  return (
                    <div key={j} className="mb-2">
                      <label
                        htmlFor={`q${i}_o${j}`}
                        className={`flex items-center p-2 rounded-lg cursor-pointer transition-all ${
                          submitted
                            ? isCorrect
                              ? "bg-green-50 border-2 border-green-500"
                              : isWrong
                              ? "bg-red-50 border-2 border-red-500"
                              : "bg-gray-50 border border-gray-200"
                            : isSelected
                            ? "bg-indigo-50 border-2 border-indigo-500"
                            : "bg-white border border-gray-200 hover:bg-gray-50 hover:border-indigo-300"
                        }`}
                      >
                        <input
                          type="radio"
                          name={`question-${i}`}
                          id={`q${i}_o${j}`}
                          className="mr-3 w-4 h-4 text-indigo-600 focus:ring-indigo-500 cursor-pointer"
                          disabled={submitted}
                          checked={isSelected}
                          onChange={() => handleSelect(i, j)}
                        />
                        <span className={`flex-1 text-sm ${
                          submitted && isCorrect
                            ? "text-green-700 font-medium"
                            : submitted && isWrong
                            ? "text-red-700 font-medium"
                            : "text-gray-700"
                        }`}>
                          {opt}
                        </span>
                        {submitted && isCorrect && (
                          <span className="ml-2 text-green-600 font-bold">✓</span>
                        )}
                        {submitted && isWrong && (
                          <span className="ml-2 text-red-600 font-bold">✗</span>
                        )}
                      </label>
                    </div>
                  );
                })}
                {submitted && item.note && (
                  <div className="mt-2 p-2 bg-blue-50 border border-blue-200 rounded-lg">
                    <p className="text-xs text-blue-700">{item.note}</p>
                  </div>
                )}
              </div>
            ))}

            {submitted && score !== null && (
              <div className="mt-4 p-4 bg-green-50 border-2 border-green-500 rounded-xl text-center">
                <p className="text-lg font-semibold text-green-700">
                  🎯 Kết quả: <strong>{score} / {questions.length}</strong>
                </p>
                <p className="text-sm text-green-600 mt-1">
                  {score === questions.length
                    ? "Xuất sắc! Bạn đã trả lời đúng tất cả!"
                    : score >= questions.length / 2
                    ? "Khá tốt! Hãy tiếp tục cố gắng!"
                    : "Hãy ôn tập thêm nhé!"}
                </p>
              </div>
            )}
        </div>

        <div className="flex gap-3 p-6 border-t bg-gray-50 rounded-b-2xl">
          <button
            className="flex-1 bg-indigo-500 hover:bg-indigo-600 text-white font-medium py-3 px-4 rounded-xl transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            onClick={handleSubmit}
            disabled={submitted}
          >
            Nộp bài
          </button>
          <button
            className="px-6 py-3 border border-gray-300 hover:bg-gray-100 text-gray-700 font-medium rounded-xl transition-colors"
            onClick={onClose}
          >
            Đóng
          </button>
        </div>
      </div>
    </div>
  );
}