import useIsMobile from "../common/useIsMobile";
import { useState } from "react";

function Sidebar({
  collapsed,
  onToggle,
  conversations = [],
  activeConversationId,
  onNewChat,
  onSelectConversation,
  isUser = false,
  loadingHistory = false,
  userEmail = null,
  onLogout,
}) {
  const isMobile = useIsMobile();
  const [editingId, setEditingId] = useState(null);

  const displayConversations = isUser ? conversations : [];

  if (collapsed && !isMobile) {
    return (
      <aside className="w-20 bg-white rounded-r-3xl shadow-md flex flex-col items-center py-4 transition-all duration-300">
        <button
          onClick={onToggle}
          className="w-10 h-10 rounded-full hover:bg-gray-100 flex items-center justify-center text-gray-600 transition-colors"
          aria-label="Mở sidebar"
        >
          ☰
        </button>
        <button
          onClick={onNewChat}
          className="mt-4 w-10 h-10 rounded-full bg-indigo-500 text-white flex items-center justify-center hover:bg-indigo-600 transition-all text-xl"
          aria-label="Chat mới"
        >
          +
        </button>
      </aside>
    );
  }

  return (
    <aside className={`w-72 bg-white rounded-r-3xl shadow-md flex flex-col h-screen transition-all duration-300 ${
      isMobile && collapsed ? "transform -translate-x-full" : ""
    } ${isMobile ? "fixed left-0 top-0 z-50" : ""}`}>
      {/* Header */}
      <div className="p-4 border-b">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-xl font-bold tracking-tight">
            CHAT A<span className="text-indigo-500">I+</span>
          </h1>
          {isMobile && (
            <button
              onClick={onToggle}
              className="w-8 h-8 rounded-full hover:bg-gray-100 flex items-center justify-center text-gray-600 transition-colors"
              aria-label="Đóng sidebar"
            >
              ✕
            </button>
          )}
          {!isMobile && (
            <button
              onClick={onToggle}
              className="w-8 h-8 rounded-full hover:bg-gray-100 flex items-center justify-center text-gray-600 transition-colors"
              aria-label="Thu gọn sidebar"
              title="Thu gọn sidebar"
            >
              ←
            </button>
          )}
        </div>
        <button
          onClick={onNewChat}
          className="w-full flex items-center justify-center gap-2 bg-indigo-500 text-white py-2 rounded-xl hover:bg-indigo-600 transition"
        >
          <span className="text-lg">+</span>
          Tạo cuộc trò chuyện mới
        </button>
      </div>

      {isUser && (
        <div className="flex-1 overflow-y-auto p-4 space-y-2 text-sm">
          <div className="flex items-center justify-between mb-2">
            <p className="text-gray-400 text-xs">Cuộc trò chuyện của bạn</p>
            {displayConversations.length > 0 && (
              <button className="text-xs text-gray-400 hover:text-gray-600">
                Xóa tất cả
              </button>
            )}
          </div>

          {loadingHistory ? (
            <div className="flex items-center justify-center py-8">
              <p className="text-xs text-gray-400">Loading...</p>
            </div>
          ) : displayConversations.length === 0 ? (
            <div className="flex items-center justify-center py-8">
              <p className="text-xs text-gray-400 text-center">
                No conversations yet.<br />
                Start a new chat to begin!
              </p>
            </div>
          ) : (
            <div className="space-y-1">
              {displayConversations.map((conv) => (
                <div
                  key={conv.id || conv.session_id}
                  className={`px-3 py-2 rounded-lg cursor-pointer flex justify-between items-center group ${
                    activeConversationId === (conv.id || conv.session_id)
                      ? "bg-indigo-50 text-indigo-600 font-medium"
                      : "hover:bg-gray-100"
                  }`}
                  onClick={() =>
                    onSelectConversation &&
                    onSelectConversation(conv.id || conv.session_id)
                  }
                >
                  <span className="flex-1 truncate">{conv.title.replace("Yêu cầu Quiz:", "")}</span>
                  {activeConversationId === (conv.id || conv.session_id) && (
                    <span className="text-xs ml-2">●</span>
                  )}
                  <div className="opacity-0 group-hover:opacity-100 flex items-center gap-1 ml-2">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setEditingId(conv.id || conv.session_id);
                      }}
                      className="w-5 h-5 flex items-center justify-center hover:bg-gray-200 rounded text-gray-500"
                    >
                      ✎
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                      }}
                      className="w-5 h-5 flex items-center justify-center hover:bg-gray-200 rounded text-gray-500"
                    >
                      🗑
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {!isUser && (
        <div className="flex-1 overflow-y-auto p-4 space-y-2 text-sm">
          <div className="flex items-center justify-center py-8">
            <p className="text-xs text-gray-400 text-center">
              <a
                href="/login"
                className="text-indigo-500 hover:underline"
              >
                Login
              </a>{" "}
              để lưu và xem lịch sử cuộc trò chuyện của bạn
            </p>
          </div>
        </div>
      )}

      {/* User Profile */}
      <div className="p-4 border-t">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-9 h-9 rounded-full bg-gray-300 flex items-center justify-center text-gray-600 text-xs">
            {isUser && userEmail
              ? userEmail.substring(0, 2).toUpperCase()
              : "GU"}
          </div>
          <div className="flex-1">
            <p className="text-sm font-medium">
              {isUser && userEmail ? userEmail : "Guest"}
            </p>
            <p className="text-xs text-gray-400">
              {isUser ? (
                <span className="text-gray-400">Cài đặt</span>
              ) : (
                <a href="/login" className="text-indigo-500 hover:underline">
                  Login
                </a>
              )}
            </p>
          </div>
        </div>
        
        {isUser && onLogout && (
          <button
            onClick={onLogout}
            className="w-full mt-2 px-3 py-2 text-sm text-red-600 hover:bg-red-50 rounded-lg transition flex items-center justify-center gap-2"
          >
            <span>🚪</span>
            Đăng xuất
          </button>
        )}
      </div>
    </aside>
  );
}

export default Sidebar;
