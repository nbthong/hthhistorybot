import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [
    react({
      babel: {
        plugins: [['babel-plugin-react-compiler']],
      },
    }),
  ],
  server: {
    port: 3000,  // 👈 đổi sang cổng 3000
    host: true,  // (tuỳ chọn) giúp mở cho mạng LAN nếu bạn cần debug từ máy khác
  }
})
