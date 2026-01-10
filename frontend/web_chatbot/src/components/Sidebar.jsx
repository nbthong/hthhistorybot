import useIsMobile from "../common/useIsMobile";

function Sidebar({ collapsed, onToggle }) {
  const isMobile = useIsMobile();
  return (
    <div className={`sidebar ${collapsed ? "collapsed" : ""}`}>
      {/* Row 1 */}
      <div className="sidebar-header">
        <strong><img src="./logo.jpg"/></strong>
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
        {!collapsed && (
          <div className="list-group">
            <button className="list-group-item list-group-item-action">
              Chat 1
            </button>
            <button className="list-group-item list-group-item-action">
              Chat 2
            </button>
            <button className="list-group-item list-group-item-action">
              Chat 3
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default Sidebar;
