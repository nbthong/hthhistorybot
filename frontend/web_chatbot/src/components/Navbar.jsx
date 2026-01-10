import { Link } from "react-router-dom";

export default function Navbar({ collapsed, onToggle }) {
  return (
    <>
      <div
        id="sidebar"
        className="sidebar"
        className={`sidebar ${collapsed ? "collapsed" : ""}`}
      >
        <div className="sidebar-header">
          <strong>LOGO</strong>
          <button className="btn btn-sm btn-outline-secondary" onClick={onToggle}>
            ☰
          </button>
        </div>

        <div className="p-2">
          <button className="btn btn-primary w-100">+ Chat mới</button>
        </div>

        <div className="sidebar-body">
          <div className="chat-history">
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
              <button className="list-group-item list-group-item-action">
                Chat 4
              </button>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
