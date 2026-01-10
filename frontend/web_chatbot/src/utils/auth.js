/**
 * Kiểm tra user đã login chưa
 * @returns {boolean}
 */
export function isAuthenticated() {
  const token = localStorage.getItem("access_token");
  return !!token;
}

/**
 * Lấy access token từ localStorage
 * @returns {string|null}
 */
export function getAccessToken() {
  return localStorage.getItem("access_token");
}

/**
 * Lấy user email từ localStorage
 * @returns {string|null}
 */
export function getUserEmail() {
  return localStorage.getItem("login_email");
}

/**
 * Logout user - chỉ xóa localStorage (dùng khi không cần gọi API)
 */
export function logout() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("login_email");
}

/**
 * Logout user và gọi API logout
 * @returns {Promise<void>}
 */
export async function logoutWithAPI() {
  const token = getAccessToken();
  
  if (token) {
    try {
      const apiURL = import.meta.env.VITE_API_URL;
      await fetch(`${apiURL}/logout`, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      });
    } catch (error) {
      console.error("Error calling logout API:", error);
    }
  }
  
  logout();
}
