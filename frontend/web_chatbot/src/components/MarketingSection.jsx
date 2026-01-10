function MarketingSection() {
  return (
    <section
      className="relative overflow-hidden text-white p-10 flex flex-col justify-between"
      style={{
        background: "linear-gradient(135deg, #5A7CFF, #9C6BFF, #FF8FA3)",
      }}
    >
      {/* Logo */}
      <div>
        <h1 className="text-sm font-semibold tracking-widest">CHAT A.I+</h1>
      </div>

      {/* Headline */}
      <div className="max-w-md">
        <h2 className="text-4xl font-bold leading-tight mb-4">
          Học Lịch Sử Việt Nam<br />
          Thông Minh & Hiệu Quả
        </h2>
        <p className="text-white/80 text-sm">
          AI Tutor chuyên về Lịch Sử lớp 10, 11, 12. Hỏi đáp, giải thích sự kiện, 
          tạo câu hỏi trắc nghiệm và khám phá lịch sử Việt Nam một cách dễ dàng.
        </p>
      </div>

      {/* Chat Preview Card */}
      <div className="bg-white/10 backdrop-blur-xl rounded-2xl p-5 max-w-lg shadow-lg">
        <div className="text-xs text-white/60 mb-2">📚 LỊCH SỬ AI TUTOR</div>

        <div className="space-y-3 text-sm">
          <p className="font-semibold">
            Giải thích về cuộc khởi nghĩa Lam Sơn
          </p>

          <p className="text-white/80 text-xs leading-relaxed">
            Cuộc khởi nghĩa Lam Sơn (1418-1427) do Lê Lợi lãnh đạo là một trong những 
            cuộc khởi nghĩa vĩ đại nhất trong lịch sử Việt Nam...
          </p>

          <ul className="list-disc list-inside text-xs text-white/80 space-y-1">
            <li>Hỏi đáp về sự kiện, nhân vật lịch sử</li>
            <li>Tạo câu hỏi trắc nghiệm tự động</li>
            <li>Giải thích chi tiết các chủ đề</li>
            <li>Lưu lịch sử trò chuyện của bạn</li>
          </ul>
        </div>

        {/* Chat Input Preview */}
        <div className="mt-4 flex items-center gap-2 bg-white/20 rounded-full px-4 py-2">
          <input
            className="bg-transparent text-xs flex-1 placeholder-white/60 outline-none"
            placeholder="Hỏi về lịch sử Việt Nam..."
            disabled
          />
          <button
            className="w-8 h-8 rounded-full bg-indigo-500 flex items-center justify-center"
            disabled
          >
            ➤
          </button>
        </div>
      </div>
    </section>
  );
}

export default MarketingSection;
