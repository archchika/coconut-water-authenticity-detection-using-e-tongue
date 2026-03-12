import { Routes, Route } from "react-router-dom";
import { AuthProvider } from "./contexts/AuthContext";
import PublicLayout from "./layouts/PublicLayout";
import AdminLayout from "./layouts/AdminLayout";
import PublicDashboard from "./pages/PublicDashboard";
import Methodology from "./pages/Methodology";
import About from "./pages/About";
import Quality from "./pages/Quality";
import Contact from "./pages/Contact";
import AdminDashboard from "./pages/AdminDashboard";

function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route element={<PublicLayout />}>
          <Route path="/" element={<PublicDashboard />} />
          <Route path="/about" element={<About />} />
          <Route path="/quality" element={<Quality />} />
          <Route path="/contact" element={<Contact />} />
          <Route path="/methodology" element={<Methodology />} />
        </Route>
        <Route path="/admin" element={<AdminLayout />}>
          <Route index element={<AdminDashboard />} />
        </Route>
      </Routes>
    </AuthProvider>
  );
}

export default App;
