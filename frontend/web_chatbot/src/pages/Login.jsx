import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

export default function LoginLayout() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async () => {
    setError("");
    setSuccess(false);

    if (!email.trim() || !password.trim()) {
      setError("⚠ Vui lòng nhập email và password");
      return;
    }

    setSubmitting(true);

    try {
      const apiURL = import.meta.env.VITE_API_URL;
      const res = await fetch(`${apiURL}/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          user_id: "frontend-login-request", // header bổ sung theo yêu cầu
        },
        body: JSON.stringify({ email, password }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || "Đăng nhập thất bại");
      }

      // Lưu token + email vào localStorage
      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("login_email", email);

      setSuccess(true);
    } catch (err) {
      setError("❌ " + err.message);
    } finally {
      setSubmitting(false);
    }
  };

  if (success) return navigate(`/`);
  return (
    <div className="d-flex justify-content-center align-items-center vh-100 login-bg">
      <link href="/login.css" rel="stylesheet" />
      <div className="col-11 col-sm-8 col-md-6 col-lg-4">
        <div className="card border-0 shadow-lg rounded-5 login-card">
          <div className="card-body p-4">
            <h2 className="text-center fw-bold mb-4">Login</h2>

            {/* Error Alert */}
            {error && (
              <div className="alert alert-danger py-2 small text-center">
                {error}
              </div>
            )}

            {/* Success Alert */}
            {success && (
              <div className="alert alert-success py-2 small text-center">
                ✔ Đăng nhập thành công!
              </div>
            )}

            <div className="mb-3">
              <label className="form-label fw-semibold">Email ID</label>
              <div className="input-wrapper">
                <input
                  type="email"
                  className="form-control rounded-4 login-input"
                  placeholder="Enter your email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
                <i className="bi bi-envelope input-icon"></i>
              </div>
            </div>

            <div className="mb-3">
              <label className="form-label fw-semibold">Password</label>
              <div className="input-wrapper">
                <input
                  type="password"
                  className="form-control rounded-4 login-input"
                  placeholder="Enter password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
                <i className="bi bi-lock input-icon"></i>
              </div>
            </div>

            {/* Remember + Forgot */}
            <div className="d-flex justify-content-between align-items-center mb-4">
              <div className="form-check">
                <input
                  className="form-check-input login-checkbox"
                  type="checkbox"
                />
                <label className="form-check-label small">Remember me</label>
              </div>
              <a
                href="#"
                className="small text-primary text-decoration-none fw-bold"
              >
                Forgot Password?
              </a>
            </div>

            {/* Button Login */}
            <div className="d-grid mb-3">
              <button
                className="btn btn-dark rounded-4 py-2 fw-bold login-btn"
                onClick={handleLogin}
                disabled={submitting}
              >
                {submitting ? "Đang đăng nhập..." : "Login"}
              </button>
            </div>

            {/* Register */}
            <p className="text-center small mt-2">
              Don't have an account?{" "}
              <a
                href="/register"
                className="text-primary text-decoration-none fw-bold"
              >
                Register
              </a>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
