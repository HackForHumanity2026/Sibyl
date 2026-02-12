import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AppShell } from "@/components/Layout/AppShell";
import { HomePage } from "@/pages/HomePage";
import { AnalysisPage } from "@/pages/AnalysisPage";
import { ReportPage } from "@/pages/ReportPage";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppShell />}>
          <Route path="/" element={<HomePage />} />
          <Route path="/analysis" element={<AnalysisPage />} />
          <Route path="/analysis/:reportId" element={<AnalysisPage />} />
          <Route path="/report" element={<ReportPage />} />
          <Route path="/report/:reportId" element={<ReportPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
