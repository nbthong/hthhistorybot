function SuggestionsSection({ onSelectSuggestion }) {
  const features = [
    {
      icon: "📚",
      title: "Hỏi đáp",
      description: "Hỏi về sự kiện, nhân vật lịch sử Việt Nam lớp 10, 11, 12",
    },
    {
      icon: "✍️",
      title: "Tạo Quiz",
      description: "Tạo câu hỏi trắc nghiệm về chủ đề lịch sử bạn chọn",
    },
    {
      icon: "🔍",
      title: "Giải thích",
      description: "Giải thích chi tiết các sự kiện, nguyên nhân và ý nghĩa",
    },
  ];

  const suggestions = [
    {
      type: "Giải thích",
      question: "Giải thích về cuộc khởi nghĩa Lam Sơn",
      icon: "💡",
    },
    {
      type: "Nhân vật",
      question: "Kể về cuộc đời và sự nghiệp của Hồ Chí Minh",
      icon: "👤",
    },
    {
      type: "Sự kiện",
      question: "Chiến thắng Điện Biên Phủ diễn ra như thế nào?",
      icon: "⚔️",
    },
    {
      type: "So sánh",
      question: "So sánh Cách mạng tháng Tám và Cách mạng tháng Mười",
      icon: "⚖️",
    },
    {
      type: "Timeline",
      question: "Trình bày diễn biến cuộc kháng chiến chống Pháp (1945-1954)",
      icon: "📅",
    },
    {
      type: "Tạo Quiz",
      question: "Tạo 5 câu hỏi trắc nghiệm về Chiến tranh Việt Nam",
      icon: "✍️",
    },
  ];

  const handleSuggestionClick = (question) => {
    if (onSelectSuggestion) {
      onSelectSuggestion(question);
    }
  };

  return (
    <div className="flex-1 overflow-y-auto px-10 py-8">
      <div className="max-w-6xl mx-auto">
        {/* Greeting */}
        <h1 className="text-3xl md:text-4xl font-semibold text-center mb-12 text-gray-800">
          Xin chào! Bạn muốn học gì về Lịch Sử Việt Nam hôm nay?
        </h1>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left: Features Cards */}
          <div className="space-y-4">
            {features.map((feature, index) => (
              <div
                key={index}
                className="bg-black text-white rounded-xl p-5 shadow-lg hover:shadow-xl transition"
              >
                <div className="flex items-center gap-3 mb-2">
                  <span className="text-2xl">{feature.icon}</span>
                  <h3 className="font-semibold">{feature.title}</h3>
                </div>
                <p className="text-xs text-white/70 leading-relaxed">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>

          {/* Right: Suggestion Cards */}
          <div className="lg:col-span-2 grid grid-cols-1 md:grid-cols-2 gap-4">
            {suggestions.map((suggestion, index) => (
              <div
                key={index}
                onClick={() => handleSuggestionClick(suggestion.question)}
                className="bg-white rounded-xl p-5 shadow hover:shadow-md transition cursor-pointer group border border-gray-100 hover:border-indigo-200"
              >
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-lg">{suggestion.icon}</span>
                      <h4 className="font-semibold text-sm text-gray-800">
                        {suggestion.type}
                      </h4>
                    </div>
                    <p className="text-sm text-gray-600 leading-relaxed">
                      {suggestion.question}
                    </p>
                  </div>
                  <span className="text-gray-400 group-hover:text-indigo-500 transition ml-2">
                    →
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export default SuggestionsSection;
