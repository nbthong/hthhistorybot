import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import MarketingSection from "../components/MarketingSection";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e?.preventDefault();
    setError("");

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
          user_id: "frontend-login-request",
        },
        body: JSON.stringify({ email, password }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || "Đăng nhập thất bại");
      }

      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("login_email", email);

      navigate("/");
    } catch (err) {
      setError("❌ " + err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const handleOAuth = (provider) => {
    console.log(`OAuth login with ${provider}`);
  };

  return (
    <div className="min-h-screen bg-white">
      <div className="min-h-screen grid grid-cols-1 lg:grid-cols-2">
        {/* LEFT: Marketing Section */}
        <MarketingSection />

        {/* RIGHT: Login Form */}
        <section className="flex items-center justify-center p-8">
          <div className="w-full max-w-sm">
            <h3 className="text-2xl font-semibold mb-2">
              Chào mừng trở lại
            </h3>
            <p className="text-sm text-gray-500 mb-6">
              Đăng nhập để tiếp tục học lịch sử và xem lại lịch sử trò chuyện của bạn.
            </p>

            {/* Error Message */}
            {error && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-600">
                {error}
              </div>
            )}

            <form onSubmit={handleLogin} className="space-y-4">
              <div>
                <label className="text-xs text-gray-600">Địa chỉ Email</label>
                <input
                  type="email"
                  placeholder="email@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full mt-1 px-4 py-2 rounded-lg bg-gray-100 outline-none focus:ring-2 focus:ring-indigo-500"
                  required
                />
              </div>

              <div>
                <label className="text-xs text-gray-600">Mật khẩu</label>
                <input
                  type="password"
                  placeholder="Nhập mật khẩu"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full mt-1 px-4 py-2 rounded-lg bg-gray-100 outline-none focus:ring-2 focus:ring-indigo-500"
                  required
                />
              </div>

              {/* Remember + Forgot */}
              <div className="flex items-center justify-between">
                <label className="flex items-center gap-2 text-xs text-gray-600">
                  <input
                    type="checkbox"
                    className="w-4 h-4 rounded border-gray-300 text-indigo-500 focus:ring-indigo-500"
                  />
                  Ghi nhớ đăng nhập
                </label>
                <Link
                  to="#"
                  className="text-xs text-indigo-500 hover:underline"
                >
                  Quên mật khẩu?
                </Link>
              </div>

              <button
                type="submit"
                disabled={submitting}
                className="w-full bg-indigo-500 hover:bg-indigo-600 transition text-white py-2 rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {submitting ? "Đang đăng nhập..." : "Đăng nhập"}
              </button>
            </form>

            {/* Divider */}
            <div className="flex items-center gap-3 my-6">
              <div className="h-px bg-gray-200 flex-1"></div>
              <span className="text-xs text-gray-400">or</span>
              <div className="h-px bg-gray-200 flex-1"></div>
            </div>

            {/* OAuth Buttons */}
            <div className="space-y-3">
              <button
                onClick={() => handleOAuth("google")}
                className="w-full flex items-center justify-center gap-2 border rounded-lg py-2 text-sm hover:bg-gray-50 transition"
              >
                <img
                  src="https://www.svgrepo.com/show/475656/google-color.svg"
                  alt="Google"
                  className="w-4 h-4"
                />
                Continue with Google
              </button>

              <button
                onClick={() => handleOAuth("apple")}
                className="w-full flex items-center justify-center gap-2 border rounded-lg py-2 text-sm hover:bg-gray-50 transition"
              >
                <img
                  src="https://www.svgrepo.com/show/511330/apple-173.svg"
                  alt="Apple"
                  className="w-4 h-4"
                />
                Continue with Apple
              </button>
            </div>

            <p className="text-xs text-center text-gray-500 mt-6">
              Chưa có tài khoản?{" "}
              <Link to="/register" className="text-indigo-500 cursor-pointer hover:underline">
                Đăng ký ngay
              </Link>
            </p>
          </div>
        </section>
      </div>
    </div>
  );
}
