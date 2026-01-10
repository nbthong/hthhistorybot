import { useState, useEffect } from "react";

function SuggestionsSection({ onSelectSuggestion }) {
  const [clickedIndex, setClickedIndex] = useState(null);
  const [isVisible, setIsVisible] = useState(false);

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
      color: "from-yellow-50 to-yellow-100",
      borderColor: "border-yellow-200",
    },
    {
      type: "Nhân vật",
      question: "Kể về cuộc đời và sự nghiệp của Hồ Chí Minh",
      icon: "👤",
      color: "from-blue-50 to-blue-100",
      borderColor: "border-blue-200",
    },
    {
      type: "Sự kiện",
      question: "Chiến thắng Điện Biên Phủ diễn ra như thế nào?",
      icon: "⚔️",
      color: "from-red-50 to-red-100",
      borderColor: "border-red-200",
    },
    {
      type: "So sánh",
      question: "So sánh Cách mạng tháng Tám và Cách mạng tháng Mười",
      icon: "⚖️",
      color: "from-purple-50 to-purple-100",
      borderColor: "border-purple-200",
    },
    {
      type: "Timeline",
      question: "Trình bày diễn biến cuộc kháng chiến chống Pháp (1945-1954)",
      icon: "📅",
      color: "from-green-50 to-green-100",
      borderColor: "border-green-200",
    },
    {
      type: "Tạo Quiz",
      question: "Tạo 5 câu hỏi trắc nghiệm về Chiến tranh Việt Nam",
      icon: "✍️",
      color: "from-indigo-50 to-indigo-100",
      borderColor: "border-indigo-200",
    },
  ];

  // Animation khi component mount
  useEffect(() => {
    setIsVisible(true);
  }, []);

  const handleSuggestionClick = (question, index) => {
    if (clickedIndex !== null) return; // Prevent multiple clicks
    
    setClickedIndex(index);
    
    // Small delay để show loading state
    setTimeout(() => {
      if (onSelectSuggestion) {
        onSelectSuggestion(question);
      }
    }, 200);
  };

  return (
    <div className="flex-1 overflow-y-auto px-4 md:px-6 py-4 md:py-6">
      <div className="max-w-5xl mx-auto">
        {/* Greeting với animation - Compact hơn */}
        <div
          className={`text-center mb-4 md:mb-6 transition-all duration-700 ${
            isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"
          }`}
        >
          <h1 className="text-xl md:text-2xl font-semibold mb-1.5 text-gray-800">
            Xin chào! Bạn muốn học gì về Lịch Sử Việt Nam hôm nay?
          </h1>
          <p className="text-xs md:text-sm text-gray-500">
            Chọn một gợi ý bên dưới hoặc tự đặt câu hỏi
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 md:gap-6">
          {/* Left: Features Cards - Compact hơn */}
          <div className="space-y-2.5 flex flex-col">
            {features.map((feature, index) => (
              <div
                key={index}
                className={`bg-black text-white rounded-lg p-3 shadow-md hover:shadow-lg transition-all duration-300 hover:scale-[1.01] flex-1 flex flex-col ${
                  isVisible
                    ? "opacity-100 translate-x-0"
                    : "opacity-0 -translate-x-4"
                }`}
                style={{
                  transitionDelay: `${index * 80}ms`,
                }}
              >
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-lg flex-shrink-0">{feature.icon}</span>
                  <h3 className="font-semibold text-xs md:text-sm">
                    {feature.title}
                  </h3>
                </div>
                <p className="text-xs text-white/70 leading-snug flex-1">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>

          {/* Right: Suggestion Cards - Compact hơn */}
          <div className="lg:col-span-2 grid grid-cols-1 md:grid-cols-2 gap-2.5 md:gap-3">
            {suggestions.map((suggestion, index) => (
              <div
                key={index}
                onClick={() => handleSuggestionClick(suggestion.question, index)}
                className={`bg-white rounded-lg p-3 md:p-3.5 shadow-sm hover:shadow-xl transition-all duration-300 cursor-pointer group border ${
                  suggestion.borderColor
                } hover:border-indigo-400 relative overflow-hidden flex flex-col h-full ${
                  clickedIndex === index
                    ? "scale-95 opacity-75"
                    : "hover:scale-[1.03] hover:-translate-y-1"
                } ${
                  isVisible
                    ? "opacity-100 translate-y-0"
                    : "opacity-0 translate-y-4"
                }`}
                style={{
                  transitionDelay: `${(index % 2) * 40 + 200}ms`,
                }}
              >
                {/* Background gradient on hover - Enhanced */}
                <div
                  className={`absolute inset-0 bg-gradient-to-br ${suggestion.color} opacity-0 group-hover:opacity-30 transition-all duration-300`}
                />
                
                {/* Shine effect on hover */}
                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent opacity-0 group-hover:opacity-100 group-hover:translate-x-full transition-all duration-700 -translate-x-full" />
                
                <div className="relative flex flex-col h-full z-10">
                  <div className="flex justify-between items-start mb-1">
                    <div className="flex items-center gap-1.5 flex-1 min-w-0">
                      <span className={`text-base md:text-lg flex-shrink-0 transition-all duration-300 group-hover:scale-110 group-hover:rotate-12 ${
                        clickedIndex === index ? "scale-90" : ""
                      }`}>
                        {suggestion.icon}
                      </span>
                      <h4 className={`font-semibold text-xs text-gray-800 transition-colors duration-300 ${
                        clickedIndex === index ? "" : "group-hover:text-indigo-600"
                      }`}>
                        {suggestion.type}
                      </h4>
                    </div>
                    <span
                      className={`text-gray-400 group-hover:text-indigo-500 group-hover:scale-125 transition-all duration-300 flex-shrink-0 ml-1.5 text-sm ${
                        clickedIndex === index ? "scale-0" : "group-hover:translate-x-1"
                      }`}
                    >
                      →
                    </span>
                  </div>
                  <p className={`text-xs leading-snug flex-1 line-clamp-2 transition-colors duration-300 ${
                    clickedIndex === index ? "text-gray-600" : "text-gray-600 group-hover:text-gray-800"
                  }`}>
                    {suggestion.question}
                  </p>
                </div>

                {/* Loading indicator */}
                {clickedIndex === index && (
                  <div className="absolute inset-0 flex items-center justify-center bg-white/80 rounded-lg z-20">
                    <div className="flex items-center gap-1.5 text-indigo-500">
                      <div className="w-3 h-3 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
                      <span className="text-xs font-medium">Đang tải...</span>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export default SuggestionsSection;
