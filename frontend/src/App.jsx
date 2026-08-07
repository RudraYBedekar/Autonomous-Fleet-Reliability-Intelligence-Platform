import { useState, useEffect, useRef, useCallback } from 'react';
import FleetPanel from './components/FleetPanel';
import FleetMap from './components/Map';
import ErrorBoundary from './components/ErrorBoundary';
import { apiUrl, wsTelemetryUrl } from './api';

function App() {
  const [fleetData, setFleetData] = useState([]);
  const [manifest, setManifest] = useState(null);
  const [chargingStations, setChargingStations] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [replayPath, setReplayPath] = useState([]);
  const [replayPoint, setReplayPoint] = useState(null);
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
    <div className="flex h-screen w-screen overflow-hidden">
      <ErrorBoundary>
        <FleetPanel
          fleetData={fleetData}
          selectedId={selectedId}
          onSelect={handleSelect}
          manifest={manifest}
          onReplayPath={handleReplayPath}
          onReplayPoint={handleReplayPoint}
        />
      </ErrorBoundary>
      <main className="flex-1 min-w-0 min-h-0 h-full">
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
      </main>
    </div>
  );
}

export default App;
