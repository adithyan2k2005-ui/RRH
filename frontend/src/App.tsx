import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Shell } from './components/layout/Shell';
import { Overview } from './pages/Overview';
import { DataExplorer } from './pages/DataExplorer';
import { MatchReplay } from './pages/MatchReplay';
import { PressureLab } from './pages/PressureLab';
import { PlayerIntelligence } from './pages/PlayerIntelligence';
import { ReliabilityRankings } from './pages/ReliabilityRankings';
import { MethodologyReports } from './pages/MethodologyReports';

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Shell />}>
          <Route index element={<Overview />} />
          <Route path="explorer" element={<DataExplorer />} />
          <Route path="replay" element={<MatchReplay />} />
          <Route path="pressure" element={<PressureLab />} />
          <Route path="players" element={<PlayerIntelligence />} />
          <Route path="rankings" element={<ReliabilityRankings />} />
          <Route path="reports" element={<MethodologyReports />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
};

export default App;
