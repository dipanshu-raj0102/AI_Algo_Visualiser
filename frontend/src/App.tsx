import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { LandingPage } from "./pages/LandingPage";
import { AlgorithmsPage } from "./pages/AlgorithmsPage";
import { AlgorithmDetailPage } from "./pages/AlgorithmDetailPage";
import { VisualizerPage } from "./pages/VisualizerPage";
import { AboutPage, ComparisonPage, DashboardPage, LearnPage } from "./pages/StaticPages";

export default function App() {
  return <BrowserRouter><Layout><Routes><Route path="/" element={<LandingPage />} /><Route path="/algorithms" element={<AlgorithmsPage />} /><Route path="/algorithms/:algorithmId" element={<AlgorithmDetailPage />} /><Route path="/visualizer/:algorithmId" element={<VisualizerPage />} /><Route path="/comparison" element={<ComparisonPage />} /><Route path="/learn" element={<LearnPage />} /><Route path="/dashboard" element={<DashboardPage />} /><Route path="/about" element={<AboutPage />} /><Route path="*" element={<Navigate to="/" replace />} /></Routes></Layout></BrowserRouter>;
}
