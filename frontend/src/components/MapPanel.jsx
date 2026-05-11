import { useMemo, useState } from 'react';
import DeckGL from '@deck.gl/react';
import { ScatterplotLayer } from '@deck.gl/layers';
import { Map } from 'react-map-gl';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';

const INITIAL_VIEW_STATE = {
  longitude: -121.986932,
  latitude: 37.532745,
  zoom: 13,
  pitch: 45,
  bearing: 0
};

export default function MapPanel({ data }) {
  const [selectedVehicle, setSelectedVehicle] = useState(null);
  const [address, setAddress] = useState("");
  
  // Extract unique vehicles and their latest positions
  const vehiclePositions = useMemo(() => {
    const latest = {};
    // Iterate backwards to get latest timestamp first, or just overwrite since the stream is ordered
    data.forEach(d => {
      if (!latest[d.vehicle_id] || new Date(d.timestamp) > new Date(latest[d.vehicle_id].timestamp)) {
        latest[d.vehicle_id] = d;
      }
    });
    return Object.values(latest);
  }, [data]);

  const handleVehicleClick = async (info) => {
    if (info.object) {
      const v = info.object;
      setSelectedVehicle(v);
      setAddress("Fetching address...");
      try {
        const res = await fetch(`https://nominatim.openstreetmap.org/reverse?lat=${v.latitude}&lon=${v.longitude}&format=json`);
        const data = await res.json();
        setAddress(data.display_name || "Address not found");
      } catch (e) {
        setAddress("Failed to fetch address");
      }
    } else {
      setSelectedVehicle(null);
    }
  };

  const layers = [
    new ScatterplotLayer({
      id: 'vehicle-layer',
      data: vehiclePositions,
      getPosition: d => [d.longitude, d.latitude],
      getFillColor: d => d.status === 'Critical' ? [239, 68, 68, 200] : [59, 130, 246, 200], // Red if critical, else Blue
      getRadius: 15,
      radiusMinPixels: 5,
      radiusMaxPixels: 20,
      pickable: true,
      onClick: handleVehicleClick,
      transitions: {
        getPosition: 500 // Smooth transition between updates
      }
    })
  ];

  return (
    <div className="w-full h-full relative">
      <DeckGL
        initialViewState={INITIAL_VIEW_STATE}
        controller={true}
        layers={layers}
        getTooltip={({object}) => object && `${object.vehicle_id}\nStatus: ${object.status}`}
        onClick={(info) => {
          if (!info.object) setSelectedVehicle(null);
        }}
      >
        <Map 
          mapLib={maplibregl}
          mapStyle="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json" 
        />
      </DeckGL>
      
      {/* Overlay Stats */}
      <div className="absolute top-4 left-4 bg-dark-900/80 backdrop-blur px-4 py-2 rounded shadow border border-dark-700 pointer-events-none">
        <div className="text-xs text-gray-400">Live Tracking</div>
        <div className="text-sm font-semibold">{vehiclePositions.length} Vehicles</div>
      </div>

      {/* Vehicle Info Popup */}
      {selectedVehicle && (
        <div className="absolute bottom-4 left-4 right-4 md:right-auto md:w-96 bg-dark-900/90 backdrop-blur p-4 rounded-lg shadow-lg border border-brand-blue/50 z-10 animate-fade-in pointer-events-auto">
          <div className="flex justify-between items-start mb-2">
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-brand-blue animate-pulse"></span>
              {selectedVehicle.vehicle_id}
            </h3>
            <button onClick={() => setSelectedVehicle(null)} className="text-gray-400 hover:text-white transition-colors cursor-pointer">✕</button>
          </div>
          <div className="grid grid-cols-2 gap-y-2 text-sm text-gray-300 mb-3">
            <div><span className="text-gray-500">Status:</span> <span className={selectedVehicle.status === 'Critical' ? 'text-red-400' : 'text-green-400'}>{selectedVehicle.status}</span></div>
            <div><span className="text-gray-500">Speed:</span> {selectedVehicle.sensor_id === 'Speed' ? selectedVehicle.temperature_c : '--'} km/h</div>
            <div><span className="text-gray-500">Lat:</span> {selectedVehicle.latitude.toFixed(4)}</div>
            <div><span className="text-gray-500">Lon:</span> {selectedVehicle.longitude.toFixed(4)}</div>
          </div>
          <div className="bg-dark-800 p-2 rounded border border-dark-700 text-xs text-left">
            <span className="text-gray-500 block mb-1">Current Address:</span>
            <span className="text-white leading-relaxed">{address}</span>
          </div>
        </div>
      )}
    </div>
  );
}
