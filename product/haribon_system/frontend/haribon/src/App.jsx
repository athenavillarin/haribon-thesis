import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import SeaStats from './pages/SeaStats';
import FAQs from './pages/FAQs';
import { LocationProvider } from './context/LocationContext';

function App() {
  return (
    <BrowserRouter>
      <LocationProvider>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Dashboard />} />
            <Route path="seastats" element={<SeaStats />} />
            <Route path="faqs" element={<FAQs />} />
          </Route>
        </Routes>
      </LocationProvider>
    </BrowserRouter>
  );
}

export default App;
