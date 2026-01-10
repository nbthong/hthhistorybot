import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import MarketingSection from "../components/MarketingSection";

export default function Register() {
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const navigate = useNavigate();
  const apiURL = import.meta.env.VITE_API_URL || "";

  const handleRegister = async (e) => {
    e.preventDefault();
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
        setSuccess(true);
        setTimeout(() => {
          navigate("/login");
        }, 1000);
      }
    } catch (err) {
      setError("Không kết nối được tới server");
    } finally {
      setLoading(false);
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

        {/* RIGHT: Sign up Form */}
        <section className="flex items-center justify-center p-8">
          <div className="w-full max-w-sm">
            <h3 className="text-2xl font-semibold mb-2">
              Bắt đầu học lịch sử miễn phí
            </h3>
            <p className="text-sm text-gray-500 mb-6">
              Đăng ký tài khoản miễn phí để lưu lịch sử trò chuyện và học lịch sử Việt Nam hiệu quả hơn.
            </p>

            {/* Error Message */}
            {error && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-600">
                {error}
              </div>
            )}

            {/* Success Message */}
            {success && (
              <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg text-sm text-green-600">
                ✔ Đăng ký thành công! Đang chuyển đến trang đăng nhập...
              </div>
            )}

            <form onSubmit={handleRegister} className="space-y-4">
              <div>
                <label className="text-xs text-gray-600">Họ và tên</label>
                <input
                  type="text"
                  placeholder="Nhập họ và tên của bạn"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="w-full mt-1 px-4 py-2 rounded-lg bg-gray-100 outline-none focus:ring-2 focus:ring-indigo-500"
                  required
                />
              </div>

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
                  placeholder="Nhập mật khẩu (tối thiểu 6 ký tự)"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full mt-1 px-4 py-2 rounded-lg bg-gray-100 outline-none focus:ring-2 focus:ring-indigo-500"
                  required
                  minLength={6}
                />
              </div>

              <p className="text-xs text-gray-400">
                Bằng việc đăng ký, bạn đồng ý với{" "}
                <span className="text-indigo-500 cursor-pointer">Điều khoản sử dụng</span> và{" "}
                <span className="text-indigo-500 cursor-pointer">Chính sách bảo mật</span> của chúng tôi.
              </p>

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-indigo-500 hover:bg-indigo-600 transition text-white py-2 rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? "Đang đăng ký..." : "Bắt đầu miễn phí"}
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
              Đã có tài khoản?{" "}
              <Link to="/login" className="text-indigo-500 cursor-pointer hover:underline">
                Đăng nhập
              </Link>
            </p>
          </div>
        </section>
      </div>
    </div>
  );
}
