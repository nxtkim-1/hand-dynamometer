import { useEffect } from "react";
import { Route, Routes, useLocation } from "react-router-dom";
import { DeviceProvider } from "./components/DeviceContext";
import { Footer, Header } from "./components/Layout";
import HomePage from "./pages/HomePage";
import HowItWorksPage from "./pages/HowItWorksPage";
import NotFoundPage from "./pages/NotFoundPage";
import ReportPage from "./pages/ReportPage";
import ResultsPage from "./pages/ResultsPage";
import TestPage from "./pages/TestPage";

const TITLES: Record<string, string> = {
  "/": "GripCheck · Open grip dynamometer",
  "/test": "Grip test · GripCheck",
  "/results": "Results · GripCheck",
  "/how-it-works": "How it works · GripCheck",
};

function ScrollAndTitle() {
  const { pathname, hash } = useLocation();
  useEffect(() => {
    document.title = TITLES[pathname] ?? (pathname.startsWith("/results/") ? "Report · GripCheck" : "GripCheck");
    if (hash) document.getElementById(hash.slice(1))?.scrollIntoView();
    else window.scrollTo(0, 0);
  }, [pathname, hash]);
  return null;
}

export default function App() {
  return (
    <DeviceProvider>
      <ScrollAndTitle />
      <a className="skip-link" href="#main">
        Skip to content
      </a>
      <Header />
      <main id="main">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/test" element={<TestPage />} />
          <Route path="/results" element={<ResultsPage />} />
          <Route path="/results/:id" element={<ReportPage />} />
          <Route path="/how-it-works" element={<HowItWorksPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </main>
      <Footer />
    </DeviceProvider>
  );
}
