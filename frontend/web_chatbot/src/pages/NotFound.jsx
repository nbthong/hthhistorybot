import { Link } from "react-router-dom";

export default function NotFound() {
  return (
    <div className="d-flex align-items-center justify-content-center vh-100 bg-light">
      <div className="text-center">
        <h1 className="display-1 fw-bold text-primary">404</h1>

        <p className="fs-4 mt-3">
          <span className="text-danger">Oops!</span> Không tìm thấy trang bạn yêu cầu.
        </p>

        <p className="text-muted mb-4">
          Trang có thể đã bị xóa hoặc đường dẫn không tồn tại.
        </p>

        <Link to="/" className="btn btn-primary btn-lg">
          Quay về trang chủ
        </Link>
      </div>
    </div>
  );
}
