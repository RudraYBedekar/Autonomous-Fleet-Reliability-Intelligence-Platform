import { useEffect, useMemo, useState } from 'react';
import { History } from 'lucide-react';
import { apiUrl } from '../api';

export default function ReplayScrubber({ vehicleId, onReplayPoint, onPathLoaded }) {
  const [history, setHistory] = useState([]);
  const [index, setIndex] = useState(-1);
  const [enabled, setEnabled] = useState(false);

  useEffect(() => {
    if (!vehicleId) {
      setHistory([]);
      setIndex(-1);
      setEnabled(false);
      onReplayPoint?.(null);
      onPathLoaded?.([]);
      return undefined;
    }

    const load = () => {
      fetch(apiUrl(`/api/fleet/${vehicleId}/history?minutes=5`))
        .then((r) => r.json())
        .then((data) => {
          const pts = data.points || [];
          setHistory(pts);
          onPathLoaded?.(pts.map((p) => [p.lng, p.lat]));
          if (enabled && pts.length) {
            setIndex(pts.length - 1);
          }
        })
        .catch(() => {});
    };

    load();
    const t = setInterval(load, 5000);
    return () => clearInterval(t);
  }, [vehicleId, enabled, onPathLoaded]);

  useEffect(() => {
    if (!enabled || index < 0 || !history[index]) {
      onReplayPoint?.(null);
      return;
    }
    onReplayPoint?.(history[index]);
  }, [index, history, enabled, onReplayPoint]);

  const label = useMemo(() => {
    if (!history.length) return 'Collecting history…';
    if (index < 0) return 'Live';
    const pt = history[index];
    return `${new Date(pt.timestamp).toLocaleTimeString()} · ${pt.speed_kmh} km/h`;
  }, [history, index]);

  if (!vehicleId) return null;

  return (
    <div className="glass-panel p-2 space-y-2">
      <div className="flex items-center justify-between text-[10px] text-gray-500">
        <span className="flex items-center gap-1">
          <History size={11} /> Route replay (5 min)
        </span>
        <button
          type="button"
          onClick={() => {
            setEnabled((e) => !e);
            setIndex(history.length ? history.length - 1 : -1);
          }}
          className={`px-2 py-0.5 rounded text-[9px] border ${
            enabled ? 'border-brand-blue text-brand-blue' : 'border-dark-600 text-gray-400'
          }`}
        >
          {enabled ? 'Replay on' : 'Live only'}
        </button>
      </div>
      <input
        type="range"
        min={0}
        max={Math.max(0, history.length - 1)}
        value={Math.max(0, index)}
        disabled={!enabled || history.length < 2}
        onChange={(e) => setIndex(Number(e.target.value))}
        className="w-full accent-brand-blue disabled:opacity-40"
      />
      <div className="text-[10px] text-gray-400">{label}</div>
    </div>
  );
}
