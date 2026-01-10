import { Routes, Route } from "react-router-dom";
import Home from "./pages/Home";
import TheLayout from "./layouts/TheLayout";
import Chatbot from "./pages/Chatbot";
import NotFound from "./pages/NotFound";
import Login from "./pages/Login";
import Register from "./pages/Register";

function App() {
  return (
    <>
      <Routes>
        {/* Routes dùng layout */}
        <Route element={<TheLayout />}>
          <Route path="/" element={<Home />} />
          <Route path="/chatbot" element={<Chatbot />} />
          <Route path="/chat/:session_id" element={<Chatbot />} />
        </Route>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </>
  );
}

export default App;
