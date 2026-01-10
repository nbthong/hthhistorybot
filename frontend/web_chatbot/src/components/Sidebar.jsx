import useIsMobile from "../common/useIsMobile";
import { useState } from "react";

function Sidebar({ collapsed, onToggle }) {
  const isMobile = useIsMobile();
  const [history, setHistory] = useState([]);

  const history_chats = async () => {
    const apiURL = import.meta.env.VITE_API_URL;
    const access_token = localStorage.getItem("access_token");
    const res = await fetch(`${apiURL}/chat/history`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${access_token}`,
      },
    });
    if (!res.ok || !res.body) throw new Error("Server error");
    const data = await res.json();
    console.log(data);
    const result = Object.values(
      data.history
        .filter((item) => item.role === "user")
        .reduce((acc, item) => {
          const key = item.session_id;

          if (
            !acc[key] ||
            new Date(item.timestamp) < new Date(acc[key].timestamp)
          ) {
            acc[key] = item;
          }

          return acc;
        }, {})
    );
    setHistory(result);
  };
  history_chats();
  return (
    <div className={`sidebar ${collapsed ? "collapsed" : ""}`}>
      {/* Row 1 */}
      <div className="sidebar-header">
        <strong>
          <img src="./logo.jpg" />
        </strong>
        <button
          className="btn btn-sm btn-outline-secondary btn-menu"
          onClick={onToggle}
        >
          {isMobile ? "✕" : "☰"}
        </button>
      </div>

      {/* Row 2 */}
      <div className="p-2">
        <a className="btn btn-primary w-100" href="/">
          <i className="bi bi-chat-left-dots me-2"></i>
          {!collapsed && "Chat mới"}
        </a>
      </div>
      {/* Row 3 */}
      <div className="sidebar-body">
        <span>Lịch sử</span>
        {!collapsed &&
          history.map((item) => (
            <a
              className="list-group-item list-group-item-action history-item"
              href={`/chat/${item.session_id}`}
            >
              {item.content}
            </a>
          ))}
      </div>
    </div>
  );
}

export default Sidebar;
