import { useEffect, useMemo, useState } from 'react';
import {
  MapPin, Navigation, Battery, HeartPulse, Gauge, User, Wrench, Users, Route, Clock, Activity,
} from 'lucide-react';
import MessageModal from './MessageModal';
import VehicleContactActions from './VehicleContactActions';
import AlertsPanel from './AlertsPanel';
import ReplayScrubber from './ReplayScrubber';

const GROUND_VEHICLE_PATTERN = /^car-\d{3}$/;

const ZONE_BADGE = {
  highway: 'bg-blue-500/20 text-blue-300',
  arterial: 'bg-green-500/20 text-green-300',
  residential: 'bg-slate-500/20 text-slate-300',
  school_zone: 'bg-yellow-500/20 text-yellow-300',
  intersection: 'bg-red-500/20 text-red-300',
};

const ZONE_LABEL = {
  highway: 'Highway',
  arterial: 'Arterial',
  residential: 'Residential',
  school_zone: 'School zone',
  intersection: 'Intersection',
};

const DIFFICULTY_STYLE = {
  basic: 'bg-green-500/20 text-green-400',
  moderate: 'bg-amber-500/20 text-amber-400',
  complex: 'bg-red-500/20 text-red-400',
};

function healthColor(score) {
  if (score >= 90) return 'text-green-400';
  if (score >= 75) return 'text-amber-400';
  return 'text-red-400';
}

function healthBarColor(score) {
  if (score >= 90) return 'bg-green-500';
  if (score >= 75) return 'bg-amber-500';
  return 'bg-red-500';
}

function speedLabel(speed) {
  if (speed <= 0) return { text: 'Stopped', cls: 'text-red-400' };
  if (speed <= 25) return { text: `${speed} km/h`, cls: 'text-amber-400' };
  return { text: `${speed} km/h`, cls: 'text-green-400' };
}

const TRIP_STATUS_LABEL = {
  at_pickup: 'At pickup',
  en_route: 'En route',
  delayed: 'Delayed',
  at_destination: 'At destination',
  idle: 'Idle',
};

const TRIP_STATUS_STYLE = {
  at_pickup: 'text-green-400',
  en_route: 'text-brand-blue',
  delayed: 'text-amber-400',
  at_destination: 'text-purple-300',
  idle: 'text-gray-400',
};

export default function FleetPanel({
  fleetData, selectedId, onSelect, manifest, onReplayPath, onReplayPoint,
}) {
  const [loading, setLoading] = useState(!manifest);
  const [messageVehicle, setMessageVehicle] = useState(null);
  const [toast, setToast] = useState(null);

  useEffect(() => {
    if (manifest) setLoading(false);
  }, [manifest]);

  useEffect(() => {
    if (!toast) return undefined;
    const timer = setTimeout(() => setToast(null), 3500);
    return () => clearTimeout(timer);
  }, [toast]);

  const handleActionComplete = ({ type, vehicle, data, error }) => {
    if (error) {
      setToast({ type: 'error', text: `Could not reach ${vehicle.vehicle_id}. Try again.` });
      return;
    }
    if (type === 'call') {
      setToast({ type: 'success', text: data?.detail ?? `Calling ${vehicle.vehicle_id}...` });
    }
  };

  const handleMessageSent = (data) => {
    setToast({ type: 'success', text: data.detail ?? 'Message sent to passengers.' });
  };

  const liveByVehicle = useMemo(() => {
    const latest = {};
    fleetData.forEach((d) => {
      if (!GROUND_VEHICLE_PATTERN.test(d.vehicle_id)) return;
      if (
        !latest[d.vehicle_id] ||
        new Date(d.timestamp) > new Date(latest[d.vehicle_id].timestamp)
      ) {
        latest[d.vehicle_id] = d;
      }
    });
    return latest;
  }, [fleetData]);

  const vehicleForMessage = useMemo(() => {
    if (!messageVehicle) return null;
    const live = liveByVehicle[messageVehicle.vehicle_id];
    return {
      ...messageVehicle,
      passenger_count: live?.passenger_count ?? messageVehicle.passenger_count,
    };
  }, [messageVehicle, liveByVehicle]);

  const selectedLive = selectedId ? liveByVehicle[selectedId] : null;
  const selectedManifest = selectedId
    ? manifest?.find((m) => m.vehicle_id === selectedId)
    : null;

  if (loading) {
    return (
      <aside className="w-[360px] shrink-0 bg-dark-900 border-r border-dark-700 flex items-center justify-center text-gray-500 text-sm">
        Loading fleet...
      </aside>
    );
  }

  return (
    <aside className="w-[360px] shrink-0 bg-dark-900 border-r border-dark-700 flex flex-col h-full">
      <div className="p-4 border-b border-dark-700">
        <h1 className="text-lg font-bold text-white tracking-tight">Fleet Dispatch</h1>
        <p className="text-xs text-gray-500 mt-1">Redwood City, California · 15 local routes</p>
      </div>

      <AlertsPanel onSelectVehicle={onSelect} />

      {selectedManifest && (
        <div className="p-4 border-b border-dark-700 bg-dark-800/60 space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-semibold text-brand-blue">{selectedManifest.vehicle_id}</h2>
            <button
              onClick={() => onSelect(null)}
              className="text-xs text-gray-500 hover:text-white"
            >
              Clear
            </button>
          </div>

          <div className="flex flex-wrap gap-1.5">
            <span className={`text-[9px] px-2 py-0.5 rounded uppercase tracking-wide ${DIFFICULTY_STYLE[selectedManifest.route_difficulty] || DIFFICULTY_STYLE.basic}`}>
              {selectedManifest.route_difficulty} route
            </span>
            <span className="text-[9px] px-2 py-0.5 rounded bg-brand-blue/20 text-brand-blue uppercase tracking-wide">
              {selectedManifest.route_name}
            </span>
            {selectedLive?.road_zone && (
              <span className={`text-[9px] px-2 py-0.5 rounded uppercase tracking-wide ${ZONE_BADGE[selectedLive.road_zone] || ZONE_BADGE.residential}`}>
                {ZONE_LABEL[selectedLive.road_zone] || selectedLive.road_zone}
              </span>
            )}
            {selectedManifest.turn_count != null && (
              <span className="text-[9px] px-2 py-0.5 rounded bg-orange-500/20 text-orange-300 uppercase tracking-wide">
                {selectedManifest.turn_count} turns
              </span>
            )}
            <span className="text-[9px] px-2 py-0.5 rounded bg-purple-500/20 text-purple-300 uppercase tracking-wide flex items-center gap-1">
              <Users size={9} />
              {(selectedLive?.passenger_count ?? selectedManifest.passenger_count)} passengers
            </span>
          </div>

          {selectedManifest.route_features?.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {selectedManifest.route_features.map((feat) => (
                <span
                  key={feat}
                  className="text-[9px] px-1.5 py-0.5 rounded bg-dark-700 text-gray-400 border border-dark-600"
                >
                  {feat}
                </span>
              ))}
            </div>
          )}

          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="glass-panel p-2 col-span-2">
              <div className="flex items-start gap-2 text-gray-400 mb-1">
                <MapPin size={12} className="mt-0.5 shrink-0 text-green-400" />
                <div>
                  <div className="text-[10px] uppercase tracking-wide text-gray-500">Pickup</div>
                  <div className="text-gray-200 leading-snug">{selectedManifest.pickup_address}</div>
                </div>
              </div>
            </div>
            <div className="glass-panel p-2 col-span-2">
              <div className="flex items-start gap-2 text-gray-400">
                <Navigation size={12} className="mt-0.5 shrink-0 text-red-400" />
                <div>
                  <div className="text-[10px] uppercase tracking-wide text-gray-500">Destination</div>
                  <div className="text-gray-200 leading-snug">{selectedManifest.destination_address}</div>
                </div>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="glass-panel p-2">
              <div className="flex items-center gap-1 text-gray-500 mb-1">
                <Gauge size={11} /> Speed
              </div>
              <div className={speedLabel(selectedLive?.speed_kmh ?? 0).cls}>
                {speedLabel(selectedLive?.speed_kmh ?? 0).text}
              </div>
            </div>
            <div className="glass-panel p-2">
              <div className="flex items-center gap-1 text-gray-500 mb-1">
                <Users size={11} /> Passengers
              </div>
              <div className="text-gray-200">
                {selectedLive?.passenger_count ?? selectedManifest.passenger_count}
              </div>
            </div>
            <div className="glass-panel p-2">
              <div className="flex items-center gap-1 text-gray-500 mb-1">
                <Clock size={11} /> ETA
              </div>
              <div className="text-gray-200">
                {selectedLive?.eta_minutes != null
                  ? `${selectedLive.eta_minutes.toFixed(0)} min`
                  : '—'}
              </div>
            </div>
            <div className="glass-panel p-2">
              <div className="flex items-center gap-1 text-gray-500 mb-1">
                <Activity size={11} /> Trip
              </div>
              <div className={TRIP_STATUS_STYLE[selectedLive?.trip_status] || 'text-gray-200'}>
                {TRIP_STATUS_LABEL[selectedLive?.trip_status] || '—'}
              </div>
            </div>
            <div className="glass-panel p-2">
              <div className="flex items-center gap-1 text-gray-500 mb-1">
                <HeartPulse size={11} /> Health
              </div>
              <div className={healthColor(selectedLive?.health_score ?? selectedManifest.health_score)}>
                {(selectedLive?.health_score ?? selectedManifest.health_score).toFixed(1)}%
              </div>
            </div>
            <div className="glass-panel p-2">
              <div className="flex items-center gap-1 text-gray-500 mb-1">
                <Battery size={11} /> Battery
              </div>
              <div className="text-gray-200">
                {(selectedLive?.battery_pct ?? selectedManifest.battery_pct).toFixed(1)}%
              </div>
            </div>
            <div className="glass-panel p-2 col-span-2">
              <div className="flex items-center gap-1 text-gray-500 mb-1">
                <User size={11} /> Driver
              </div>
              <div className="text-gray-200">{selectedManifest.driver_name}</div>
              {selectedManifest.driver_phone && (
                <div className="text-[10px] text-gray-500 mt-0.5 font-mono">
                  {selectedManifest.driver_phone}
                </div>
              )}
            </div>
            <div className="glass-panel p-2 col-span-2">
              <div className="flex items-center justify-between text-gray-500 mb-1">
                <span className="flex items-center gap-1 text-[10px]">
                  <Wrench size={11} /> Maintenance RUL
                </span>
                <span className="text-gray-300 text-xs">
                  {(selectedLive?.maintenance_rul_pct ?? 85).toFixed(0)}%
                </span>
              </div>
              <div className="h-1.5 bg-dark-700 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full ${
                    (selectedLive?.maintenance_rul_pct ?? 100) < 25 ? 'bg-red-500'
                      : (selectedLive?.maintenance_rul_pct ?? 100) < 40 ? 'bg-amber-500' : 'bg-green-500'
                  }`}
                  style={{ width: `${selectedLive?.maintenance_rul_pct ?? 85}%` }}
                />
              </div>
              <div className="text-[10px] text-gray-500 mt-1">
                Engine: {selectedManifest.engine_status}
                {selectedLive?.active_alert && (
                  <span className="block text-amber-400 mt-0.5">{selectedLive.active_alert}</span>
                )}
              </div>
            </div>
          </div>

          <ReplayScrubber
            vehicleId={selectedManifest.vehicle_id}
            onReplayPoint={onReplayPoint}
            onPathLoaded={onReplayPath}
          />

          <VehicleContactActions
            vehicle={selectedManifest}
            onMessageClick={setMessageVehicle}
            onActionComplete={handleActionComplete}
          />

          <div>
            <div className="flex justify-between text-[10px] text-gray-500 mb-1">
              <span>Trip progress</span>
              <span>{(selectedLive?.trip_progress_pct ?? 0).toFixed(0)}%</span>
            </div>
            <div className="h-1.5 bg-dark-700 rounded-full overflow-hidden">
              <div
                className="h-full bg-brand-blue rounded-full transition-all duration-500"
                style={{ width: `${selectedLive?.trip_progress_pct ?? 0}%` }}
              />
            </div>
          </div>

          <div className="flex gap-2 text-[10px] text-gray-500">
            <span className="flex items-center gap-1">
              <Wrench size={10} /> Engine: {selectedManifest.engine_status}
            </span>
            <span>Status: {selectedLive?.status ?? '—'}</span>
          </div>

          {selectedLive && (
            <div className="text-[10px] text-gray-500 font-mono">
              {selectedLive.lat?.toFixed(5)}, {selectedLive.lng?.toFixed(5)}
            </div>
          )}
        </div>
      )}

      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {manifest?.map((vehicle) => {
          const live = liveByVehicle[vehicle.vehicle_id];
          const isSelected = selectedId === vehicle.vehicle_id;
          const health = live?.health_score ?? vehicle.health_score;
          const pax = live?.passenger_count ?? vehicle.passenger_count;
          const diff = vehicle.route_difficulty;

          return (
            <div
              key={vehicle.vehicle_id}
              role="button"
              tabIndex={0}
              onClick={() => onSelect(vehicle.vehicle_id)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  onSelect(vehicle.vehicle_id);
                }
              }}
              className={`w-full text-left p-3 rounded-lg border transition-all cursor-pointer ${
                isSelected
                  ? 'border-brand-blue bg-brand-blue/10 shadow-lg shadow-brand-blue/10'
                  : 'border-dark-700 bg-dark-800/50 hover:border-dark-500 hover:bg-dark-800'
              }`}
            >
              <div className="flex items-center justify-between mb-1.5">
                <span className="font-semibold text-sm text-white">{vehicle.vehicle_id}</span>
              <div className="flex items-center gap-1.5">
                {live?.road_zone && (
                  <span className={`text-[8px] px-1 py-0.5 rounded ${ZONE_BADGE[live.road_zone] || ''}`}>
                    {ZONE_LABEL[live.road_zone]?.slice(0, 4) || live.road_zone}
                  </span>
                )}
                <span className={`text-[9px] px-1.5 py-0.5 rounded uppercase ${DIFFICULTY_STYLE[diff] || DIFFICULTY_STYLE.basic}`}>
                    {diff}
                  </span>
                  <span className={`text-xs ${speedLabel(live?.speed_kmh ?? 0).cls}`}>
                    {live ? `${live.speed_kmh} km/h` : '—'}
                  </span>
                </div>
              </div>

              <div className="flex items-center gap-2 text-[10px] text-gray-500 mb-1.5">
                <Route size={10} />
                <span className="truncate">{vehicle.route_name}</span>
                {live?.trip_status && (
                  <span className={`shrink-0 ${TRIP_STATUS_STYLE[live.trip_status] || ''}`}>
                    {TRIP_STATUS_LABEL[live.trip_status]}
                  </span>
                )}
                {live?.eta_minutes != null && (
                  <span className="text-gray-400 shrink-0">{live.eta_minutes.toFixed(0)}m ETA</span>
                )}
                <span className="flex items-center gap-0.5 text-purple-300 ml-auto shrink-0">
                  <Users size={9} /> {pax}
                </span>
              </div>

              <div className="space-y-1 text-[11px] text-gray-400 leading-snug">
                <div className="flex gap-1.5">
                  <MapPin size={10} className="shrink-0 mt-0.5 text-green-400" />
                  <span className="line-clamp-1">{vehicle.pickup_address}</span>
                </div>
                <div className="flex gap-1.5">
                  <Navigation size={10} className="shrink-0 mt-0.5 text-red-400" />
                  <span className="line-clamp-1">{vehicle.destination_address}</span>
                </div>
              </div>

              <div className="mt-2 flex items-center gap-2">
                <div className="flex-1 h-1 bg-dark-700 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${healthBarColor(health)}`}
                    style={{ width: `${health}%` }}
                  />
                </div>
                <span className={`text-[10px] ${healthColor(health)}`}>{health.toFixed(0)}%</span>
              </div>

              <VehicleContactActions
                vehicle={vehicle}
                compact
                onMessageClick={setMessageVehicle}
                onActionComplete={handleActionComplete}
              />
            </div>
          );
        })}
      </div>

      {toast && (
        <div
          className={`mx-3 mb-3 px-3 py-2 rounded-lg text-xs border ${
            toast.type === 'error'
              ? 'bg-red-500/10 border-red-500/30 text-red-300'
              : 'bg-green-500/10 border-green-500/30 text-green-300'
          }`}
        >
          {toast.text}
        </div>
      )}

      <MessageModal
        vehicle={vehicleForMessage}
        open={Boolean(messageVehicle)}
        onClose={() => setMessageVehicle(null)}
        onSent={handleMessageSent}
      />
    </aside>
  );
}
