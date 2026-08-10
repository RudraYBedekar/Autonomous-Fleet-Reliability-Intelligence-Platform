import { useState, useEffect, useRef, useCallback } from 'react';
import { Bot, Sparkles } from 'lucide-react';
import FleetPanel from './components/FleetPanel';
import FleetMap from './components/Map';
import CopilotPanel from './components/CopilotPanel';
import ErrorBoundary from './components/ErrorBoundary';
import { apiUrl, wsTelemetryUrl } from './api';

function App() {
  const [fleetData, setFleetData] = useState([]);
  const [manifest, setManifest] = useState(null);
  const [chargingStations, setChargingStations] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [replayPath, setReplayPath] = useState([]);
  const [replayPoint, setReplayPoint] = useState(null);
  const [isCopilotOpen, setIsCopilotOpen] = useState(false);
  const liveRef = useRef(new globalThis.Map());

  const handleSelect = useCallback((vehicleId) => {
    setSelectedId(vehicleId);
    setReplayPath([]);
    setReplayPoint(null);
  }, []);

  const handleReplayPath = useCallback((path) => {
    setReplayPath(path);
  }, []);

  const handleReplayPoint = useCallback((point) => {
    setReplayPoint(point);
  }, []);

  const flushLive = useCallback(() => {
    setFleetData(Array.from(liveRef.current.values()));
  }, []);

  useEffect(() => {
    let ws;
    let retryTimer;
    let flushTimer;

    const connect = () => {
      ws = new WebSocket(wsTelemetryUrl());

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        liveRef.current.set(data.vehicle_id, data);
      };

      ws.onclose = () => {
        retryTimer = setTimeout(connect, 2000);
      };
    };

    connect();
    flushTimer = setInterval(flushLive, 200);

    return () => {
      clearTimeout(retryTimer);
      clearInterval(flushTimer);
      ws?.close();
    };
  }, [flushLive]);

  useEffect(() => {
    fetch(apiUrl('/api/fleet/manifest'))
      .then((res) => res.json())
      .then(setManifest)
      .catch((err) => console.error('Failed to load fleet manifest', err));

    fetch(apiUrl('/api/fleet/charging-stations'))
      .then((res) => res.json())
      .then((data) => setChargingStations(Array.isArray(data) ? data : []))
      .catch((err) => console.error('Failed to load charging stations', err));
  }, []);

  return (
    <div className="flex h-screen w-screen overflow-hidden relative">
      <ErrorBoundary>
        <FleetPanel
          fleetData={fleetData}
          selectedId={selectedId}
          onSelect={handleSelect}
          manifest={manifest}
          onReplayPath={handleReplayPath}
          onReplayPoint={handleReplayPoint}
          onToggleCopilot={() => setIsCopilotOpen((prev) => !prev)}
        />
      </ErrorBoundary>
      <main className="flex-1 min-w-0 min-h-0 h-full relative">
        <ErrorBoundary>
          <FleetMap
            data={fleetData}
            selectedId={selectedId}
            onSelect={handleSelect}
            manifest={manifest}
            chargingStations={chargingStations}
            replayPath={replayPath}
            replayPoint={replayPoint}
          />
        </ErrorBoundary>

        {/* Floating AI Chatbot Button */}
        {!isCopilotOpen && (
          <button
            onClick={() => setIsCopilotOpen(true)}
            className="fixed bottom-6 right-6 z-40 flex items-center gap-2 px-4 py-3 bg-gradient-to-r from-brand-blue to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white font-semibold rounded-2xl shadow-xl shadow-brand-blue/30 border border-white/20 transition-all duration-200 hover:scale-105 active:scale-95 group"
          >
            <div className="relative">
              <Bot className="w-5 h-5 group-hover:rotate-12 transition-transform" />
              <span className="absolute -top-1 -right-1 flex h-2.5 w-2.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
              </span>
            </div>
            <span className="text-sm">AI Fleet Chatbot</span>
            <Sparkles className="w-4 h-4 text-purple-300 animate-pulse" />
          </button>
        )}

        {/* AI Copilot Drawer */}
        <CopilotPanel
          isOpen={isCopilotOpen}
          onClose={() => setIsCopilotOpen(false)}
          onSelect={handleSelect}
          selectedId={selectedId}
        />
      </main>
    </div>
  );
}

export default App;

