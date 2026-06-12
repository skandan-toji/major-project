import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { useSimulation } from '../context/SimulationContext';
import HeroSection from '../sections/HeroSection';
import TrustStrip from '../sections/TrustStrip';
import FeaturesSection from '../sections/FeaturesSection';
import PipelineSection from '../sections/PipelineSection';
import MetricsSection from '../sections/MetricsSection';
import FAQSection from '../sections/FAQSection';
import CTASection from '../sections/CTASection';
import FooterSection from '../sections/FooterSection';

export default function HomePage() {
  const { isRunning, startSimulation, stopSimulation } = useSimulation();
  const [meterCount, setMeterCount] = useState(100);
  const navigate = useNavigate();

  const handleStart = () => startSimulation(meterCount);
  const handleStop = () => stopSimulation();
  const goLive = () => navigate('/live');

  return (
    <div style={{ position: 'relative', zIndex: 1 }}>
      <HeroSection
        meterCount={meterCount}
        setMeterCount={setMeterCount}
        isRunning={isRunning}
        onStart={handleStart}
        onStop={handleStop}
      />
      <TrustStrip />
      <FeaturesSection />
      <PipelineSection />
      <MetricsSection />
      <FAQSection />
      <CTASection onStart={handleStart} goLive={goLive} />
      <FooterSection />
    </div>
  );
}
