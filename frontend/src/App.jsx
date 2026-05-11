import { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import MapPanel from './components/MapPanel';
import ChartPanel from './components/ChartPanel';

function App() {
  const [fleetData, setFleetData] = useState([]);
  const [metrics, setMetrics] = useState({ health: 100, alerts: 0, vehicles: 0 });
  
  // WebSocket Connection
  useEffect(() => {
    // In production, use wss:// and point to actual server domain
    const ws = new WebSocket('ws://127.0.0.1:8000/ws/telemetry');
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setFleetData(prev => {
        // Keep only latest 1000 records to prevent memory leak
        const next = [data, ...prev].slice(0, 1000);
        return next;
      });
    };

    return () => ws.close();
  }, []);

  // Poll Fleet Metrics
  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const res = await fetch('http://127.0.0.1:8000/api/telemetry/fleet-status');
        const data = await res.json();
        setMetrics({
          health: data.fleet_health_score,
          alerts: data.critical_alerts,
          vehicles: data.active_vehicles
        });
      } catch (e) {
        console.error("Failed to fetch metrics", e);
      }
    };
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex h-screen bg-dark-900 overflow-hidden">
      <Sidebar metrics={metrics} />
      <main className="flex-1 flex flex-col relative">
        {/* Top bar */}
        <header className="h-16 border-b border-dark-700 bg-dark-800/50 backdrop-blur-md flex items-center px-6 justify-between z-10">
          <h1 className="text-xl font-bold tracking-tight">Fleet Command Center</h1>
          <div className="flex items-center space-x-4">
            <span className="flex h-3 w-3 relative">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-brand-green opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-brand-green"></span>
            </span>
            <span className="text-sm text-gray-400">Live Telemetry Active</span>
          </div>
        </header>

        {/* Content Grid */}
        <div className="flex-1 grid grid-cols-3 gap-4 p-4 overflow-hidden relative">
          <div className="col-span-2 glass-panel overflow-hidden relative">
            <MapPanel data={fleetData} />
          </div>
          
          <div className="col-span-1 flex flex-col gap-4 overflow-hidden">
            <div className="flex-1 glass-panel p-4 overflow-hidden flex flex-col">
              <h2 className="text-lg font-semibold mb-4">Live Telemetry Trends</h2>
              <div className="flex-1 min-h-0">
                 <ChartPanel data={fleetData} />
              </div>
            </div>
            
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
