import { useEffect, useState } from 'react';
import { AlertTriangle, Bell } from 'lucide-react';
import { apiUrl } from '../api';

const SEVERITY_STYLE = {
  critical: 'border-red-500/40 bg-red-500/10 text-red-300',
  warning: 'border-amber-500/40 bg-amber-500/10 text-amber-300',
  info: 'border-blue-500/40 bg-blue-500/10 text-blue-300',
};

export default function AlertsPanel({ onSelectVehicle }) {
  const [alerts, setAlerts] = useState([]);

  useEffect(() => {
    const load = () => {
      fetch(apiUrl('/api/fleet/alerts'))
        .then((r) => r.json())
        .then(setAlerts)
        .catch(() => {});
    };
    load();
    const t = setInterval(load, 3000);
    return () => clearInterval(t);
  }, []);

  if (!alerts.length) {
    return (
      <div className="px-4 py-2 border-b border-dark-700 text-[10px] text-gray-500 flex items-center gap-1.5">
        <Bell size={11} /> No active alerts
      </div>
    );
  }

  return (
    <div className="border-b border-dark-700 max-h-36 overflow-y-auto">
      <div className="px-4 py-1.5 text-[10px] uppercase tracking-wide text-gray-500 flex items-center gap-1.5 sticky top-0 bg-dark-900">
        <AlertTriangle size={11} className="text-amber-400" />
        Live alerts ({alerts.length})
      </div>
      <div className="px-3 pb-2 space-y-1">
        {alerts.slice(0, 8).map((a) => (
          <button
            key={`${a.vehicle_id}-${a.code}-${a.timestamp}`}
            type="button"
            onClick={() => onSelectVehicle?.(a.vehicle_id)}
            className={`w-full text-left text-[10px] px-2 py-1.5 rounded border ${SEVERITY_STYLE[a.severity] || SEVERITY_STYLE.info}`}
          >
            {a.message}
          </button>
        ))}
      </div>
    </div>
  );
}
