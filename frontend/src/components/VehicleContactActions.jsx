import { useState } from 'react';
import { MessageSquare, Phone } from 'lucide-react';
import { apiUrl } from '../api';

function phoneHref(phone) {
  return `tel:${phone.replace(/[^\d+]/g, '')}`;
}

export default function VehicleContactActions({
  vehicle,
  compact = false,
  onMessageClick,
  onActionComplete,
}) {
  const [calling, setCalling] = useState(false);

  const handleCall = async (e) => {
    e.stopPropagation();
    if (calling) return;
    setCalling(true);
    try {
      const res = await fetch(apiUrl(`/api/fleet/${vehicle.vehicle_id}/call`), {
        method: 'POST',
      });
      if (!res.ok) throw new Error('Call failed');
      const data = await res.json();
      onActionComplete?.({ type: 'call', vehicle, data });
      if (vehicle.driver_phone) {
        window.location.href = phoneHref(vehicle.driver_phone);
      }
    } catch {
      onActionComplete?.({
        type: 'call',
        vehicle,
        error: true,
      });
    } finally {
      setCalling(false);
    }
  };

  const handleMessage = (e) => {
    e.stopPropagation();
    onMessageClick?.(vehicle);
  };

  const btnBase = compact
    ? 'flex-1 flex items-center justify-center gap-1 px-2 py-1.5 text-[10px] rounded-md border transition-colors'
    : 'flex-1 flex items-center justify-center gap-1.5 px-3 py-2 text-xs rounded-lg border transition-colors';

  return (
    <div
      className={`flex gap-2 ${compact ? 'mt-2' : ''}`}
      onClick={(e) => e.stopPropagation()}
      onKeyDown={(e) => e.stopPropagation()}
      role="group"
      aria-label={`Contact ${vehicle.vehicle_id}`}
    >
      <button
        type="button"
        onClick={handleCall}
        disabled={calling}
        title={`Call ${vehicle.vehicle_id} (${vehicle.driver_name})`}
        className={`${btnBase} border-green-500/30 bg-green-500/10 text-green-400 hover:bg-green-500/20 hover:border-green-500/50 disabled:opacity-50`}
      >
        <Phone size={compact ? 11 : 13} />
        {calling ? 'Calling...' : compact ? 'Call' : 'Call car'}
      </button>
      <button
        type="button"
        onClick={handleMessage}
        title={`Message passengers on ${vehicle.vehicle_id}`}
        className={`${btnBase} border-brand-blue/30 bg-brand-blue/10 text-brand-blue hover:bg-brand-blue/20 hover:border-brand-blue/50`}
      >
        <MessageSquare size={compact ? 11 : 13} />
        {compact ? 'Message' : 'Message passengers'}
      </button>
    </div>
  );
}
