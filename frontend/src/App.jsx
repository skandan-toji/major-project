import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { SimulationProvider } from './context/SimulationContext';
import BackgroundEffect from './components/BackgroundEffect';
import Navbar from './components/Navbar';
import HomePage from './pages/HomePage';
import LiveOperationsPage from './pages/LiveOperationsPage';
import AnalyticsPage from './pages/AnalyticsPage';
import AttackIntelPage from './pages/AttackIntelPage';
import PerformancePage from './pages/PerformancePage';
import SystemInfoPage from './pages/SystemInfoPage';

function App() {
  return (
    <BrowserRouter>
      <SimulationProvider>
        <BackgroundEffect />
        <Navbar />
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/live" element={<LiveOperationsPage />} />
          <Route path="/analytics" element={<AnalyticsPage />} />
          <Route path="/attacks" element={<AttackIntelPage />} />
          <Route path="/performance" element={<PerformancePage />} />
          <Route path="/system" element={<SystemInfoPage />} />
        </Routes>
      </SimulationProvider>
    </BrowserRouter>
  );
}

export default App;
