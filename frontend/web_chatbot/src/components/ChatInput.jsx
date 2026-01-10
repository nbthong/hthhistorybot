import { useState, useRef } from "react";

function ChatInput({ onSend }) {
  const [text, setText] = useState("");
  const [rows, setRows] = useState(1);
  const textareaRef = useRef(null);

  const MAX_ROWS = 5;

  const handleChange = (e) => {
    const value = e.target.value;
    setText(value);
    const currentRows = text.split("\n").length;

    setRows(currentRows > MAX_ROWS ? MAX_ROWS : currentRows);
  };

  const handleSubmit = () => {
    if (!text.trim()) return;
    onSend(text);
    setText("");
  };

  return (
    <div className="chat-input">
      <div className="input-group align-items-end">
        {/* Textarea */}
        <textarea
          ref={textareaRef}
          className="form-control textarea"
          rows={rows}
          placeholder="Nhập tin nhắn..."
          value={text}
          onChange={handleChange}
          onBlur={handleChange}
          style={{ resize: "none" }}
        />

        {/* Send */}
        <button className="btn btn-primary" onClick={handleSubmit}>
          ➤
        </button>
      </div>
    </div>
  );
}

export default ChatInput;
