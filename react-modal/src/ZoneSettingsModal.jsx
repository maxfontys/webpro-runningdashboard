import React, { useState } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import { Info, AlertCircle } from 'lucide-react';
import { toast } from '../../static/js/dashboard/toast.js';

const ZoneSettingsModal = ({ averageHR }) => {
  const savedSettings = JSON.parse(localStorage.getItem('hrSettings') || '{}');

  const defaultZones = {
    1: { min: 50, max: 59, name: "Recovery" },
    2: { min: 60, max: 69, name: "Aerobic Endurance" },
    3: { min: 70, max: 79, name: "Tempo" },
    4: { min: 80, max: 89, name: "Threshold" },
    5: { min: 90, max: 100, name: "VO2 Max" },
  };

  const [maxHR, setMaxHR] = useState(savedSettings.maxHR || 200);
  const [zones, setZones] = useState(savedSettings.zones || defaultZones);
  const [errorMessages, setErrorMessages] = useState([]);
  const [open, setOpen] = useState(false); // Start with the modal closed

  const resetToSavedSettings = () => {
    const savedSettings = JSON.parse(localStorage.getItem('hrSettings') || '{}');
    setMaxHR(savedSettings.maxHR || 200);
    setZones(savedSettings.zones || defaultZones);
    setErrorMessages([]);
  };

  const handleSave = () => {
    console.log('Saving settings:', { maxHR, zones });  // Debug frontend state
    const errors = [];
    let prevMax = -1;

    // Validate zones
    Object.entries(zones).forEach(([zone, { min, max }]) => {
      if (min <= prevMax) errors.push(`Zone ${zone} must start after the previous zone.`);
      if (max <= min) errors.push(`Zone ${zone}'s max percentage must be greater than its min percentage.`);
      if (max > 100) errors.push(`Zone ${zone}'s max percentage cannot exceed 100%.`);
      if (min < 0 || max < 0) errors.push(`Zone ${zone} cannot have negative values.`);
      prevMax = max;
    });

    // Ensure no gaps between zones
    const zoneValues = Object.values(zones);
    for (let i = 1; i < zoneValues.length; i++) {
      const previousMax = zoneValues[i - 1].max;
      const currentMin = zoneValues[i].min;
      if (currentMin !== previousMax + 1) {
        errors.push(`There is a gap between Zone ${i} and Zone ${i + 1}.`);
      }
    }

    const uniqueErrors = [...new Set(errors)];
    if (uniqueErrors.length > 0) {
      setErrorMessages(uniqueErrors);
      return;
    }

    // Save settings via API
    const settings = { maxHR, zones };
    fetch('http://127.0.0.1:5000/api/save-settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(settings),
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.error) {
          setErrorMessages(data.details || ['Failed to save settings. Please try again.']);
          resetToSavedSettings();
        } else {
          setErrorMessages([]);
          localStorage.setItem('hrSettings', JSON.stringify(settings));
          toast.showToast('Settings saved successfully!', 'success');

          // Strip "bpm" from averageHR and convert to number
          const averageHRValue = parseFloat(averageHR.replace(' bpm', ''));

          // Fetch updated zone based on the new settings
          fetch('http://127.0.0.1:5000/api/calculate-zone', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ average_hr: averageHR }), // Use the prop here
          })
            .then((res) => res.json())
            .then((zoneData) => {
              const zoneDisplay = document.querySelector('.clr-strava');
              if (zoneDisplay) {
                if (zoneData.zone === "Invalid") {
                  zoneDisplay.textContent = zoneData.name;
                } else if (zoneData.zone === "Unknown Zone") {
                  zoneDisplay.textContent = "Unknown Zone: No matching zone found";
                } else {
                  zoneDisplay.textContent = `${zoneData.zone}: ${zoneData.name}`;
                }
              }
            })
            .catch((err) => console.error('Error fetching updated zone:', err));

          setOpen(false);
        }
      })
      .catch((error) => {
        console.error('Error saving settings:', error);
        setErrorMessages(['Failed to save settings. Please try again.']);
        resetToSavedSettings();
      });
  };

  const handleZoneChange = (zoneNumber, field, value) => {
    setZones((prev) => ({
      ...prev,
      [zoneNumber]: {
        ...prev[zoneNumber],
        [field]: Math.max(0, parseFloat(value) || 0),
      },
    }));
  };

  return (
    <Dialog.Root
      open={open}
      onOpenChange={(isOpen) => {
        if (!isOpen) resetToSavedSettings(); // Revert changes when modal closes
        setOpen(isOpen);
      }}
    >
      <Dialog.Trigger asChild>
        <button
          className="inline-flex items-center text-gray-500 hover:text-gray-700 translate-y-[3px]"
          aria-label="Open Zone Settings"
        >
          <Info className="w-4 h-4" />
        </button>
      </Dialog.Trigger>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black bg-opacity-50 z-[999]" />
        <Dialog.Content
          className="fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 bg-white rounded-xl shadow-lg w-full max-w-[calc(100%-3rem)] sm:max-w-md p-6 z-[999] fm-inter"
        >
          <Dialog.Title className="text-lg font-semibold mb-2">
            Edit your maximum heart rate or zones
          </Dialog.Title>
          <p className="text-sm text-gray-500 mb-4">
            Heart rate zones help track training intensity. They are calculated as a percentage of your maximum heart rate. Adjust them here if you know your zones.
          </p>

          {errorMessages.length > 0 && (
            <div className="bg-red-100 text-red-600 p-4 rounded mb-4 text-sm flex items-center gap-2">
              <AlertCircle className="w-5 h-5" />
              <div>
                {errorMessages.map((msg, index) => (
                  <div key={index}>{msg}</div>
                ))}
              </div>
            </div>
          )}

          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium mb-2">
                Maximum Heart Rate (bpm)
              </label>
                <input
                  type="number"
                  value={maxHR}
                  onChange={(e) => {
                    const newValue = e.target.value;

                    // Allow empty input without forcing a default value
                    if (newValue === "") {
                      setMaxHR(""); 
                      return;
                    }

                    // Parse the value and enforce max limit
                    const parsedValue = parseInt(newValue, 10);
                    setMaxHR(parsedValue > 220 ? 220 : parsedValue);
                  }}
                  className="w-full px-3 py-2 border border-gray-300 rounded text-sm"
                />
            </div>

            <div className="space-y-4">
              {Object.entries(zones).map(([zone, values]) => (
                <div key={zone} className="flex justify-between items-center">
                  <div className="text-sm font-medium">
                    Zone {zone}: {values.name}
                  </div>
                  <div className="flex items-center gap-2">
                    <input
                      type="number"
                      value={values.min}
                      onChange={(e) =>
                        handleZoneChange(zone, 'min', e.target.value)
                      }
                      className="w-14 px-2 py-1 text-sm border border-gray-300 rounded"
                    />
                    <span>-</span>
                    <input
                      type="number"
                      value={values.max}
                      onChange={(e) =>
                        handleZoneChange(zone, 'max', e.target.value)
                      }
                      className="w-14 px-2 py-1 text-sm border border-gray-300 rounded"
                    />
                    <span>%</span>
                  </div>
                </div>
              ))}
            </div>

            <div className="flex justify-end gap-2 mt-4">
              <Dialog.Close asChild>
                <button className="btn-primary px-4 py-2 rounded">
                  Cancel
                </button>
              </Dialog.Close>
              <button
                onClick={handleSave}
                className="btn-secondary px-4 py-2 rounded"
              >
                Save
              </button>
            </div>
          </div>

          <Dialog.Close asChild>
            <button
              className="absolute text-gray-500 hover:text-gray-700 font-light text-2xl top-3 right-5"
              aria-label="Close"
            >
              ×
            </button>
          </Dialog.Close>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
};

export default ZoneSettingsModal;