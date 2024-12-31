import React from 'react';
import { createRoot } from 'react-dom/client';
import ZoneSettingsModal from './ZoneSettingsModal';
import './index.css';

const mount = () => {
  const container = document.getElementById('zone-settings-root');
  if (container) {
    const averageHR = container.dataset.averageHr;
    console.log(`Average HR from Python: ${averageHR}`); // Debugging line

    const root = createRoot(container);
    root.render(
      <React.StrictMode>
        <ZoneSettingsModal averageHR={averageHR} />
      </React.StrictMode>
    );
  }
};

document.addEventListener('DOMContentLoaded', mount);
if (document.readyState === 'complete') {
  mount();
}