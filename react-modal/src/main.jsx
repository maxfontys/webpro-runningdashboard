import React from 'react';
import { createRoot } from 'react-dom/client';
import ZoneSettingsModal from './ZoneSettingsModal'; // Ensure this path is correct
import './index.css'; // Ensure this exists and is correct

const mount = () => {
  const container = document.getElementById('zone-settings-root');
  if (container) {
    console.log('React is mounting to zone-settings-root'); // Debugging
    const root = createRoot(container);
    root.render(
      <React.StrictMode>
        <ZoneSettingsModal />
      </React.StrictMode>
    );
  } else {
    console.log('zone-settings-root not found'); // Debugging
  }
};

// Attach mounting logic
document.addEventListener('DOMContentLoaded', mount);
if (document.readyState === 'complete') {
  mount();
}
