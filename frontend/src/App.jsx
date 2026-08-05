import { useState, useEffect, useRef, useCallback } from 'react';
import FleetPanel from './components/FleetPanel';
import FleetMap from './components/Map';

function App() {
  const [fleetData, setFleetData] = useState([]);
  const [manifest, setManifest] = useState(null);
  const [selectedId, setSelectedId] = useState(null);
  const liveRef = useRef(new globalThis.Map());

  const flushLive = useCallback(() => {
    setFleetData(Array.from(liveRef.current.values()));
  }, []);

  useEffect(() => {
    let ws;
    let retryTimer;
    let flushTimer;

    const connect = () => {
      ws = new WebSocket('ws://127.0.0.1:8000/ws/telemetry');

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
    fetch('http://127.0.0.1:8000/api/fleet/manifest')
      .then((res) => res.json())
      .then(setManifest)
      .catch((err) => console.error('Failed to load fleet manifest', err));
  }, []);

  return (
    <div className="flex h-screen w-screen overflow-hidden">
      <FleetPanel
        fleetData={fleetData}
        selectedId={selectedId}
        onSelect={setSelectedId}
        manifest={manifest}
      />
      <main className="flex-1 min-w-0">
        <FleetMap
          data={fleetData}
          selectedId={selectedId}
          onSelect={setSelectedId}
          manifest={manifest}
        />
      </main>
    </div>
  );
}

export default App;
