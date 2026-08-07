import { useMemo, useState, useEffect, useCallback } from 'react';
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

const DEFAULT_ROUTE_COLOR = [34, 197, 94, 200];

const DIFFICULTY_ROUTE_COLOR = {
  basic: [34, 197, 94, 200],
  moderate: [245, 158, 11, 200],
  complex: [239, 68, 68, 200],
};

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

const CHARGE_ROUTE_COLOR = [250, 204, 21, 220];

function speedColor(speedKmh, selected) {
  const s = Number(speedKmh) || 0;
  if (selected) return [255, 255, 255, 255];
  if (s <= 0) return [239, 68, 68, 240];
  if (s <= 25) return [245, 158, 11, 240];
  return [34, 197, 94, 240];
}

function isValidCoord(lng, lat) {
  return Number.isFinite(lng) && Number.isFinite(lat)
    && Math.abs(lat) <= 90 && Math.abs(lng) <= 180;
}

function cleanPath(path) {
  if (!Array.isArray(path)) return [];
  return path.filter(([lng, lat]) => isValidCoord(Number(lng), Number(lat)));
}

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
    vehicle_type: raw.vehicle_type,
    navigation_mode: raw.navigation_mode,
    destination_address: raw.destination_address,
    route_path_live: raw.route_path_live,
    charger_station_id: raw.charger_station_id,
    charger_station_name: raw.charger_station_name,
  };
}

function normalizeViewState(vs) {
  return {
    longitude: Number(vs.longitude),
    latitude: Number(vs.latitude),
    zoom: Number(vs.zoom) || 14,
    pitch: Number(vs.pitch) || 0,
    bearing: Number(vs.bearing) || 0,
  };
}

export default function FleetMap({
  data, selectedId, onSelect, manifest, chargingStations = [],
  replayPath = [], replayPoint = null,
}) {
  const [viewState, setViewState] = useState(DEFAULT_VIEW);
  const [mapMode, setMapMode] = useState('satellite');

  const handleViewStateChange = useCallback(({ viewState: vs }) => {
    setViewState(normalizeViewState(vs));
  }, []);

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
    return Object.values(latest).filter((v) => isValidCoord(v.lng, v.lat));
  }, [data]);

  const selectedVehicle = vehiclePositions.find((v) => v.vehicle_id === selectedId);
  const selectedManifest = manifest?.find((m) => m.vehicle_id === selectedId);

  useEffect(() => {
    const lng = selectedVehicle?.lng ?? selectedManifest?.pickup_lng;
    const lat = selectedVehicle?.lat ?? selectedManifest?.pickup_lat;
    if (!isValidCoord(Number(lng), Number(lat))) return;

    setViewState((prev) => ({
      ...prev,
      longitude: Number(lng),
      latitude: Number(lat),
      zoom: Math.max(prev.zoom ?? 14, 15),
    }));
  }, [
    selectedId,
    selectedVehicle?.lat,
    selectedVehicle?.lng,
    selectedManifest?.pickup_lat,
    selectedManifest?.pickup_lng,
  ]);

  const safeReplayPath = useMemo(
    () => cleanPath(replayPath),
    [replayPath],
  );

  const layers = useMemo(() => {
    const result = [];
    const liveRoute = cleanPath(selectedVehicle?.route_path_live);
    const isEvDetour = selectedVehicle?.navigation_mode === 'emergency_charge';

    if (chargingStations.length) {
      result.push(
        new ScatterplotLayer({
          id: 'charging-stations',
          data: chargingStations.filter((s) => isValidCoord(s.lng, s.lat)),
          getPosition: (d) => [d.lng, d.lat],
          getFillColor: [250, 204, 21, 230],
          getRadius: 12,
          radiusMinPixels: 8,
          stroked: true,
          getLineColor: [0, 0, 0, 180],
          lineWidthMinPixels: 2,
          pickable: false,
        })
      );
    }

    if (liveRoute.length >= 2) {
      result.push(
        new PathLayer({
          id: 'selected-live-route',
          data: [{ path: liveRoute }],
          getPath: (d) => d.path,
          getColor: CHARGE_ROUTE_COLOR,
          getWidth: 7,
          widthMinPixels: 5,
          capRounded: true,
          jointRounded: true,
        })
      );
    } else if (selectedManifest?.route_zones_path?.length && !isEvDetour) {
      const zoneData = selectedManifest.route_zones_path
        .map((segment) => ({ ...segment, path: cleanPath(segment.path) }))
        .filter((segment) => segment.path.length >= 2);

      if (zoneData.length) {
        result.push(
          new PathLayer({
            id: 'selected-route-zones',
            data: zoneData,
            getPath: (d) => d.path,
            getColor: (d) => (Array.isArray(d.color) ? d.color : DEFAULT_ROUTE_COLOR),
            getWidth: 6,
            widthMinPixels: 4,
            capRounded: true,
            jointRounded: true,
          })
        );
      }
    } else if (selectedManifest?.route_path?.length && !isEvDetour) {
      const path = cleanPath(selectedManifest.route_path);
      if (path.length >= 2) {
        const diff = selectedManifest.route_difficulty || 'basic';
        result.push(
          new PathLayer({
            id: 'selected-route',
            data: [{ path }],
            getPath: (d) => d.path,
            getColor: DIFFICULTY_ROUTE_COLOR[diff] || DEFAULT_ROUTE_COLOR,
            getWidth: 5,
            widthMinPixels: 4,
            capRounded: true,
            jointRounded: true,
          })
        );
      }
    }

    if (safeReplayPath.length >= 2) {
      result.push(
        new PathLayer({
          id: 'replay-trail',
          data: [{ path: safeReplayPath }],
          getPath: (d) => d.path,
          getColor: [168, 85, 247, 180],
          getWidth: 4,
          widthMinPixels: 3,
          capRounded: true,
          jointRounded: true,
        })
      );
    }

    if (replayPoint && isValidCoord(replayPoint.lng, replayPoint.lat)) {
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
      const markers = [];
      const routingToCharger = isEvDetour;

      if (!routingToCharger && isValidCoord(selectedManifest.pickup_lng, selectedManifest.pickup_lat)) {
        markers.push({
          kind: 'pickup',
          lng: selectedManifest.pickup_lng,
          lat: selectedManifest.pickup_lat,
          color: [34, 197, 94, 255],
        });
      }
      if (routingToCharger && selectedVehicle?.charger_station_name) {
        const station = chargingStations.find((s) => s.station_id === selectedVehicle.charger_station_id);
        const lng = station?.lng ?? selectedManifest.destination_lng;
        const lat = station?.lat ?? selectedManifest.destination_lat;
        if (isValidCoord(lng, lat)) {
          markers.push({
            kind: 'charger',
            lng,
            lat,
            color: [250, 204, 21, 255],
          });
        }
      } else if (isValidCoord(selectedManifest.destination_lng, selectedManifest.destination_lat)) {
        markers.push({
          kind: 'destination',
          lng: selectedManifest.destination_lng,
          lat: selectedManifest.destination_lat,
          color: [239, 68, 68, 255],
        });
      }
      if (markers.length) {
        result.push(
          new ScatterplotLayer({
            id: 'trip-endpoints',
            data: markers,
            getPosition: (d) => [d.lng, d.lat],
            getFillColor: (d) => d.color,
            getRadius: 14,
            radiusMinPixels: 10,
            stroked: true,
            getLineColor: [255, 255, 255, 255],
            lineWidthMinPixels: 2,
            pickable: false,
          })
        );
      }
    }

    if (vehiclePositions.length) {
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
            if (info.object?.vehicle_id) onSelect?.(info.object.vehicle_id);
          },
          updateTriggers: {
            getFillColor: [selectedId],
            getRadius: [selectedId],
          },
        })
      );
    }

    return result;
  }, [vehiclePositions, selectedId, selectedManifest, selectedVehicle, onSelect, safeReplayPath, replayPoint, chargingStations]);

  const mapStyle = mapMode === 'satellite' ? SATELLITE_STYLE : STREET_STYLE;

  return (
    <div className="w-full h-full min-h-0 relative">
      <DeckGL
        viewState={viewState}
        onViewStateChange={handleViewStateChange}
        controller
        layers={layers}
        getTooltip={({ object }) => {
          if (!object?.vehicle_id) return null;
          const zone = object.road_zone ? ZONE_LABELS[object.road_zone] || object.road_zone : '';
          const battery = object.battery_pct != null ? `\nBattery: ${object.battery_pct}%` : '';
          return `${object.vehicle_id} (EV)\n${object.speed_kmh} km/h · ${object.passenger_count ?? 0} pax${battery}${zone ? `\nZone: ${zone}` : ''}`;
        }}
        onClick={(info) => {
          if (info.object?.vehicle_id) return;
          if (!info.object) onSelect?.(null);
        }}
      >
        <MapLibreMap
          mapLib={maplibregl}
          mapStyle={mapStyle}
          reuseMaps
          attributionControl={false}
        />
      </DeckGL>

      <div className="absolute top-4 right-4 flex flex-col gap-2 items-end pointer-events-none">
        <div className="flex gap-1 pointer-events-auto">
          <button
            type="button"
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
            type="button"
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
          <div className="font-medium text-white">{vehiclePositions.length} EVs · Redwood City</div>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-yellow-400" /> Charger / low-battery route
          </div>
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
              <div>Route: {selectedVehicle?.route_name || selectedManifest.route_name}</div>
              {selectedVehicle?.trip_status === 'routing_to_charger' && (
                <div className="text-yellow-300">Auto-routing to charger (&lt;15% battery)</div>
              )}
              {selectedVehicle?.trip_status === 'charging' && (
                <div className="text-yellow-300">Charging @ {selectedVehicle.charger_station_name || 'station'}</div>
              )}
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
