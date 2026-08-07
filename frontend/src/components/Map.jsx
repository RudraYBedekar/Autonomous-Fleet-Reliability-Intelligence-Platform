import { useMemo, useState, useEffect } from 'react';
import DeckGL from '@deck.gl/react';
import { ScatterplotLayer, PathLayer } from '@deck.gl/layers';
import { Map as MapLibreMap } from 'react-map-gl';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';

const GROUND_VEHICLE_PATTERN = /^car-\d{3}$/;

const STREET_STYLE = 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json';

const SATELLITE_STYLE = {
  version: 8,
  sources: {
    satellite: {
      type: 'raster',
      tiles: [
        'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
      ],
      tileSize: 256,
      attribution: 'Esri, Maxar, Earthstar Geographics',
    },
    labels: {
      type: 'raster',
      tiles: [
        'https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}',
      ],
      tileSize: 256,
    },
  },
  layers: [
    { id: 'satellite', type: 'raster', source: 'satellite' },
    { id: 'labels', type: 'raster', source: 'labels', paint: { 'raster-opacity': 0.7 } },
  ],
};

const DEFAULT_VIEW = {
  longitude: -122.2320,
  latitude: 37.4865,
  zoom: 14,
  pitch: 0,
  bearing: 0,
};

const DIFFICULTY_ROUTE_COLOR = {
  basic: [34, 197, 94, 200],
  moderate: [245, 158, 11, 200],
  complex: [239, 68, 68, 200],
};

function speedColor(speedKmh, selected) {
  const s = Number(speedKmh) || 0;
  if (selected) return [255, 255, 255, 255];
  if (s <= 0) return [239, 68, 68, 240];
  if (s <= 25) return [245, 158, 11, 240];
  return [34, 197, 94, 240];
}

const ZONE_LABELS = {
  highway: 'Highway',
  arterial: 'Arterial',
  residential: 'Residential',
  school_zone: 'School zone',
  intersection: 'Intersection',
};

const ZONE_LEGEND_COLORS = {
  highway: 'bg-blue-500',
  arterial: 'bg-green-500',
  residential: 'bg-slate-400',
  school_zone: 'bg-yellow-400',
  intersection: 'bg-red-500',
};

function normalizePoint(raw) {
  return {
    vehicle_id: raw.vehicle_id,
    timestamp: raw.timestamp,
    lat: raw.lat ?? raw.latitude,
    lng: raw.lng ?? raw.longitude,
    speed_kmh: raw.speed_kmh ?? 0,
    status: raw.status ?? 'moving',
    health_score: raw.health_score,
    battery_pct: raw.battery_pct,
    trip_progress_pct: raw.trip_progress_pct,
    passenger_count: raw.passenger_count,
    route_difficulty: raw.route_difficulty,
    route_name: raw.route_name,
    road_zone: raw.road_zone,
    turn_count: raw.turn_count,
    eta_minutes: raw.eta_minutes,
    trip_status: raw.trip_status,
    maintenance_rul_pct: raw.maintenance_rul_pct,
    active_alert: raw.active_alert,
    alert_severity: raw.alert_severity,
  };
}

export default function FleetMap({
  data, selectedId, onSelect, manifest, replayPath = [], replayPoint = null,
}) {
  const [viewState, setViewState] = useState(DEFAULT_VIEW);
  const [mapMode, setMapMode] = useState('satellite');

  const vehiclePositions = useMemo(() => {
    const latest = {};
    data.forEach((d) => {
      if (!GROUND_VEHICLE_PATTERN.test(d.vehicle_id)) return;
      const normalized = normalizePoint(d);
      if (
        normalized.lat == null ||
        normalized.lng == null ||
        !latest[normalized.vehicle_id] ||
        new Date(normalized.timestamp) > new Date(latest[normalized.vehicle_id].timestamp)
      ) {
        latest[normalized.vehicle_id] = normalized;
      }
    });
    return Object.values(latest);
  }, [data]);

  const selectedVehicle = vehiclePositions.find((v) => v.vehicle_id === selectedId);
  const selectedManifest = manifest?.find((m) => m.vehicle_id === selectedId);

  useEffect(() => {
    if (selectedVehicle?.lat != null && selectedVehicle?.lng != null) {
      setViewState((prev) => ({
        ...prev,
        longitude: selectedVehicle.lng,
        latitude: selectedVehicle.lat,
        zoom: Math.max(prev.zoom, 15),
        transitionDuration: 800,
      }));
    }
  }, [selectedId, selectedVehicle?.lat, selectedVehicle?.lng]);

  const layers = useMemo(() => {
    const result = [];

    if (selectedManifest?.route_zones_path?.length) {
      selectedManifest.route_zones_path.forEach((segment, idx) => {
        result.push(
          new PathLayer({
            id: `selected-route-zone-${idx}`,
            data: [segment],
            getPath: (d) => d.path,
            getColor: (d) => d.color,
            getWidth: 6,
            widthMinPixels: 4,
            capRounded: true,
            jointRounded: true,
          })
        );
      });
    } else if (selectedManifest?.route_path?.length) {
      const diff = selectedManifest.route_difficulty || 'basic';
      result.push(
        new PathLayer({
          id: 'selected-route',
          data: [{ path: selectedManifest.route_path }],
          getPath: (d) => d.path,
          getColor: DIFFICULTY_ROUTE_COLOR[diff] || DIFFICULTY_ROUTE_COLOR.basic,
          getWidth: 5,
          widthMinPixels: 4,
          capRounded: true,
          jointRounded: true,
        })
      );
    }

    if (replayPath?.length >= 2) {
      result.push(
        new PathLayer({
          id: 'replay-trail',
          data: [{ path: replayPath }],
          getPath: (d) => d.path,
          getColor: [168, 85, 247, 180],
          getWidth: 4,
          widthMinPixels: 3,
          capRounded: true,
          jointRounded: true,
        })
      );
    }

    if (replayPoint) {
      result.push(
        new ScatterplotLayer({
          id: 'replay-scrub-marker',
          data: [{ lng: replayPoint.lng, lat: replayPoint.lat }],
          getPosition: (d) => [d.lng, d.lat],
          getFillColor: [168, 85, 247, 255],
          getRadius: 18,
          radiusMinPixels: 12,
          stroked: true,
          getLineColor: [255, 255, 255, 255],
          lineWidthMinPixels: 2,
          pickable: false,
        })
      );
    }

    if (selectedManifest) {
      result.push(
        new ScatterplotLayer({
          id: 'pickup-marker',
          data: [{ lng: selectedManifest.pickup_lng, lat: selectedManifest.pickup_lat }],
          getPosition: (d) => [d.lng, d.lat],
          getFillColor: [34, 197, 94, 255],
          getRadius: 14,
          radiusMinPixels: 10,
          stroked: true,
          getLineColor: [255, 255, 255, 255],
          lineWidthMinPixels: 2,
          pickable: false,
        }),
        new ScatterplotLayer({
          id: 'destination-marker',
          data: [{ lng: selectedManifest.destination_lng, lat: selectedManifest.destination_lat }],
          getPosition: (d) => [d.lng, d.lat],
          getFillColor: [239, 68, 68, 255],
          getRadius: 14,
          radiusMinPixels: 10,
          stroked: true,
          getLineColor: [255, 255, 255, 255],
          lineWidthMinPixels: 2,
          pickable: false,
        })
      );
    }

    result.push(
      new ScatterplotLayer({
        id: 'ground-vehicle-layer',
        data: vehiclePositions,
        getPosition: (d) => [d.lng, d.lat],
        getFillColor: (d) => speedColor(d.speed_kmh, d.vehicle_id === selectedId),
        getRadius: (d) => (d.vehicle_id === selectedId ? 16 : 12),
        radiusMinPixels: 8,
        radiusMaxPixels: 18,
        stroked: true,
        getLineColor: [0, 0, 0, 200],
        lineWidthMinPixels: 2,
        pickable: true,
        onClick: (info) => {
          if (info.object) onSelect?.(info.object.vehicle_id);
        },
        updateTriggers: {
          getFillColor: [selectedId, vehiclePositions.map((v) => v.speed_kmh).join(',')],
          getPosition: vehiclePositions.map((v) => `${v.lng},${v.lat}`).join('|'),
        },
      })
    );

    return result;
  }, [vehiclePositions, selectedId, selectedManifest, onSelect, replayPath, replayPoint]);

  const mapStyle = mapMode === 'satellite' ? SATELLITE_STYLE : STREET_STYLE;

  return (
    <div className="w-full h-full relative">
      <DeckGL
        viewState={viewState}
        onViewStateChange={({ viewState: vs }) => setViewState(vs)}
        controller={true}
        layers={layers}
        getTooltip={({ object }) => {
          if (!object?.vehicle_id) return null;
          const zone = object.road_zone ? ZONE_LABELS[object.road_zone] || object.road_zone : '';
          return `${object.vehicle_id}\n${object.speed_kmh} km/h · ${object.passenger_count ?? 0} pax${zone ? `\nZone: ${zone}` : ''}`;
        }}
        onClick={(info) => {
          if (!info.object) onSelect?.(null);
        }}
      >
        <MapLibreMap mapLib={maplibregl} mapStyle={mapStyle} />
      </DeckGL>

      <div className="absolute top-4 right-4 flex flex-col gap-2 items-end pointer-events-none">
        <div className="flex gap-1 pointer-events-auto">
          <button
            onClick={() => setMapMode('satellite')}
            className={`px-3 py-1.5 text-xs rounded-l-lg border ${
              mapMode === 'satellite'
                ? 'bg-brand-blue text-white border-brand-blue'
                : 'bg-white/95 text-gray-700 border-gray-200'
            }`}
          >
            Satellite
          </button>
          <button
            onClick={() => setMapMode('street')}
            className={`px-3 py-1.5 text-xs rounded-r-lg border ${
              mapMode === 'street'
                ? 'bg-brand-blue text-white border-brand-blue'
                : 'bg-white/95 text-gray-700 border-gray-200'
            }`}
          >
            Street
          </button>
        </div>

        <div className="bg-black/70 backdrop-blur px-3 py-2 rounded shadow text-xs text-gray-200 space-y-1">
          <div className="font-medium text-white">{vehiclePositions.length} cars · Redwood City</div>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-red-500" /> Stopped
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500" /> 1–25 km/h
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-green-500" /> 26–50 km/h
          </div>
          {selectedManifest && (
            <div className="pt-1 border-t border-gray-600 text-gray-400 space-y-1">
              <div>Route: {selectedManifest.route_name}</div>
              {selectedVehicle?.road_zone && (
                <div>Zone: {ZONE_LABELS[selectedVehicle.road_zone] || selectedVehicle.road_zone}</div>
              )}
              {selectedManifest.turn_count != null && (
                <div>{selectedManifest.turn_count} turns on route</div>
              )}
            </div>
          )}
          <div className="pt-1 border-t border-gray-600 space-y-0.5">
            {Object.entries(ZONE_LEGEND_COLORS).map(([zone, cls]) => (
              <div key={zone} className="flex items-center gap-2 text-gray-400">
                <span className={`w-2.5 h-2.5 rounded-full ${cls}`} />
                {ZONE_LABELS[zone]}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
