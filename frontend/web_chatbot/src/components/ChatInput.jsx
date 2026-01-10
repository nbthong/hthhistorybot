import { useState, useRef } from "react";

function ChatInput({ onSend, disabled = false }) {
  const [text, setText] = useState("");
  const inputRef = useRef(null);

  const handleChange = (e) => {
    setText(e.target.value);
  };

  const handleSubmit = (e) => {
    e?.preventDefault();
    if (!text.trim() || disabled) return;
    onSend(text);
    setText("");
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="mt-6 px-10">
      <form onSubmit={handleSubmit} className="bg-white rounded-full shadow-md flex items-center px-5 py-3 gap-3">
        <div className="w-8 h-8 rounded-full bg-pink-100 flex items-center justify-center flex-shrink-0">
          <span className="text-pink-500 text-sm">🧠</span>
        </div>
        
        <input
          ref={inputRef}
          type="text"
          placeholder="Hỏi gì về lịch sử đi em"
          className="flex-1 outline-none text-sm bg-transparent border-none"
          value={text}
          onChange={handleChange}
          onKeyPress={handleKeyPress}
          disabled={disabled}
        />
        
        <button
          type="submit"
          disabled={disabled || !text.trim()}
          className="w-10 h-10 rounded-full bg-indigo-500 text-white flex items-center justify-center hover:bg-indigo-600 transition flex-shrink-0 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          ➤
        </button>
      </form>
    </div>
  );
}

export default ChatInput;
