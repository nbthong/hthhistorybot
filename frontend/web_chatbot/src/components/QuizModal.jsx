import { useState } from "react";

export default function QuizModal({ questions, onClose }) {

  const [selected, setSelected] = useState(Array(questions.length).fill([]));
  const [score, setScore] = useState(null);
  const [submitted, setSubmitted] = useState(false);

  const handleCheck = (indexQ, indexO) => {
    const clone = [...selected];
    const current = clone[indexQ];

    if (current.includes(indexO)) {
      clone[indexQ] = current.filter(x => x !== indexO);
    } else {
      clone[indexQ] = [...current, indexO];
    }

    setSelected(clone);
  };

  const handleSubmit = () => {
    let s = 0;
    selected.forEach((arr, i) => {
      if (arr.includes(questions[i].answer)) s++;
    });
    setScore(s);
    setSubmitted(true);
    setSubmitted(true);
  };

  return (
    <div className="modal d-block" style={{ background: "rgba(0,0,0,0.5)" }}>
      <div className="modal-dialog modal-dialog-centered">
        <div className="modal-content rounded-4 shadow-lg p-2">
          <div className="modal-header border-0">
            <h5 className="modal-title fw-bold fs-4">Quiz Lịch sử</h5>
            <button type="button" className="btn-close" onClick={onClose}></button>
          </div>

          <div className="modal-body pt-1">
            {questions.map((item, i) => (
              <div key={i} className="mb-3">
                <p className="fw-semibold mb-2">{i + 1}. {item.q}</p>
                {item.options.map((opt, j) => (
                  <div key={j} className="form-check mb-1">
                    <input
                      type="checkbox"
                      className="form-check-input"
                      id={`q${i}_o${j}`}
                      disabled={submitted}
                      checked={selected[i].includes(j)}
                      onChange={() => handleCheck(i, j)}
                    />
                    <label className="form-check-label" htmlFor={`q${i}_o${j}`}>
                      {opt}
                    </label>
                  </div>
                ))}
              </div>
            ))}

            {submitted && score !== null && (
              <div className="alert alert-success text-center py-2 rounded-3">
                🎯 Kết quả: <strong>{score} / {questions.length}</strong>
              </div>
            )}
          </div>

          <div className="modal-footer border-0 d-flex gap-2">
            <button className="btn btn-dark flex-grow-1 rounded-3" onClick={handleSubmit} disabled={submitted}>
              Nộp bài
            </button>
            <button className="btn btn-outline-secondary px-3 rounded-3" onClick={onClose}>
              Đóng
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}