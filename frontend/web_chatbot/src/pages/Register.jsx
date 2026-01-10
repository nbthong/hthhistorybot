import { useState } from "react";
import { useNavigate } from "react-router-dom";

export default function Register() {
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const navigate = useNavigate();

  const apiURL = import.meta.env.VITE_API_URL || "";

  const handleRegister = async (e) => {
    e.preventDefault();
    setMessage("");
    setError("");
    setLoading(true);

    try {
      const res = await fetch(`${apiURL}/register`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email,
          full_name: fullName,
          password,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        setError(data.detail || "Đăng ký thất bại");
      } else {
        setMessage("Đăng ký thành công! ID: " + data.id);
        setSuccess(true);
      }
    } catch (err) {
      setError("Không kết nối được tới server");
    } finally {
      setLoading(false);
    }
  };
  if (success) return navigate(`/login`);
  return (
    <div className="container d-flex justify-content-center align-items-center vh-100">
      <link href="/register.css" rel="stylesheet" />
      <div className="card p-4 shadow-lg rounded-4" style={{ width: 360 }}>
        <h2 className="text-center fw-bold mb-3">Register</h2>

        {error && <div className="alert alert-danger py-2">{error}</div>}
        {message && <div className="alert alert-success py-2">{message}</div>}

        <form onSubmit={handleRegister}>
          <div className="mb-3">
            <label className="form-label fw-semibold">Full Name</label>
            <input
              type="text"
              className="form-control rounded-4"
              placeholder="Enter your full name"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              required
            />
          </div>

          <div className="mb-3">
            <label className="form-label fw-semibold">Email</label>
            <div className="input-wrapper">
              <input
                type="email"
                className="form-control rounded-4 login-input"
                placeholder="Enter your email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
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
                placeholder="Create password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={6}
              />
              <i className="bi bi-lock input-icon"></i>
            </div>
          </div>

          <button
            type="submit"
            className="btn btn-dark w-100 rounded-4 fw-semibold"
            disabled={loading}
          >
            {loading ? "Registering..." : "Register"}
          </button>
        </form>

        <p className="text-center mt-3">
          Already have an account?{" "}
          <a
            href="/login"
            className="text-primary fw-bold text-decoration-none"
          >
            Login
          </a>
        </p>
      </div>
    </div>
  );
}
